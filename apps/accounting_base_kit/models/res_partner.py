# -*- coding: utf-8 -*-

import base64
import io
import json
import xlsxwriter
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
from datetime import date, timedelta
from odoo import fields, models, api, _


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = "res.partner"

    # Customer/ Supplier Payment Statement Report
    customer_report_ids = fields.Many2many(
        'account.move',
        compute='_compute_customer_report_ids',
        help='Partner Invoices related to Customer')
    vendor_statement_ids = fields.Many2many(
        'account.move',
        compute='_compute_vendor_statement_ids',
        help='Partner Bills related to Vendor')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id.id,
        help="currency related to Customer or Vendor"
    )
    show_paid_customer_invoice = fields.Boolean('Show Paid Invoices', default=True,
                                                help="If selected, will show both fully paid and unpaid customer invoices")
    show_paid_vendor_bill = fields.Boolean('Show Paid Bills', default=True,
                                           help="If selected, Will show both fully paid and unpaid vendor bills")

    @api.onchange('show_paid_customer_invoice')
    def _compute_customer_report_ids(self):
        """ For computing 'invoices' of partner"""
        for rec in self:
            inv_ids = self.env['account.move'].search(
                [('partner_id', '=', rec.id),
                 ('move_type', '=', 'out_invoice'),
                 ('payment_state', '!=', 'all' if rec.show_paid_customer_invoice else 'paid'),
                 ('state', '=', 'posted')])
            rec.customer_report_ids = inv_ids

    @api.onchange('show_paid_vendor_bill')
    def _compute_vendor_statement_ids(self):
        """ For computing 'bills' of partner """
        for rec in self:
            bills = self.env['account.move'].search(
                [('partner_id', '=', rec.id),
                 ('move_type', '=', 'in_invoice'),
                 ('payment_state', '!=', 'all' if rec.show_paid_vendor_bill else 'paid'),
                 ('state', '=', 'posted')])
            rec.vendor_statement_ids = bills

    def main_query(self):
        """Return select query"""
        query = """SELECT name , invoice_date, invoice_date_due,
                    amount_total_signed AS sub_total,
                    amount_residual_signed AS amount_due ,
                    amount_residual AS balance
            FROM account_move WHERE state ='posted'
            AND partner_id= '%s' AND company_id = '%s' """ % (self.id, self.env.company.id)
        return query

    def amount_query(self):
        """Return query for calculating total amount"""
        amount_query = """ SELECT SUM(amount_total_signed) AS total, 
                    SUM(amount_residual) AS balance
                FROM account_move WHERE state ='posted'
                AND partner_id= '%s' AND company_id = '%s' """ % (self.id, self.env.company.id)
        return amount_query

    def action_customer_share_pdf(self):
        """ Action for sharing customer pdf report"""
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('out_invoice')"""
            if not self.show_paid_customer_invoice:
                main_query += """ AND payment_state != 'paid' """
            amount = self.amount_query()
            amount += """ AND move_type IN ('out_invoice')"""
            if not self.show_paid_customer_invoice:
                amount += """ AND payment_state != 'paid' """
            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()

            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            report = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'accounting_base_kit.res_partner_action', self, data=data)
            data_record = base64.b64encode(report[0])
            ir_values = {
                'name': 'Statement Report',
                'type': 'binary',
                'datas': data_record,
                'mimetype': 'application/pdf',
                'res_model': 'res.partner'
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)
            email_values = {
                'email_to': self.email,
                'subject': 'Payment Statement Report',
                'body_html': '<p>Dear <strong> Mr/Miss. ' + self.name +
                             '</strong> </p> <p> We have attached your '
                             'payment statement. Please check </p> '
                             '<p>Best regards, </p> <p> ' + self.env.user.name,
                'attachment_ids': [attachment.id],
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Email Sent Successfully',
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError('There is no statement to send')

    def action_customer_print_pdf(self):
        """ Action for printing pdf report"""
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('out_invoice')"""
            if not self.show_paid_customer_invoice:
                main_query += """ AND payment_state != 'paid' """
            amount = self.amount_query()
            amount += """ AND move_type IN ('out_invoice')"""
            if not self.show_paid_customer_invoice:
                amount += """ AND payment_state != 'paid' """

            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            return self.env.ref('accounting_base_kit.res_partner_action'
                                ).report_action(self, data=data)
        else:
            raise ValidationError('There is no statement to print')

    def action_customer_print_xlsx(self):
        """ Action for printing xlsx report of customer """
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('out_invoice')"""
            if not self.show_paid_customer_invoice:
                main_query += """ AND payment_state != 'paid' """
            amount = self.amount_query()
            amount += """ AND move_type IN ('out_invoice')"""
            if not self.show_paid_customer_invoice:
                amount += """ AND payment_state != 'paid' """

            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            return {
                'type': 'ir.actions.report',
                'data': {
                    'model': 'res.partner',
                    'data': json.dumps(data, default=date_utils.json_default),
                    'output_format': 'xlsx',
                    'report_name': 'Payment Statement'
                },
                'report_type': 'xlsx',
            }
        else:
            raise ValidationError('There is no statement to print')

    def get_xlsx_report(self, data, response, report_name):
        """ Get xlsx report data """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format_with_color = workbook.add_format({
            'font_size': '14px', 'bold': True,
            'bg_color': 'yellow', 'border': 1})
        cell_format = workbook.add_format({'font_size': '14px', 'bold': True})
        txt = workbook.add_format({'font_size': '13px'})
        txt_border = workbook.add_format({'font_size': '13px', 'border': 1})
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '22px'})
        sheet.merge_range('B2:Q4', report_name, head)

        if data['customer']:
            sheet.merge_range('B7:D7', 'Customer/Supplier : ', cell_format)
            sheet.merge_range('E7:H7', data['customer'], txt)
        sheet.merge_range('B9:C9', 'Address : ', cell_format)
        if data['street']:
            sheet.merge_range('D9:F9', data['street'], txt)
        if data['street2']:
            sheet.merge_range('D10:F10', data['street2'], txt)
        if data['city']:
            sheet.merge_range('D11:F11', data['city'], txt)
        if data['state']:
            sheet.merge_range('D12:F12', data['state'], )
        if data['zip']:
            sheet.merge_range('D13:F13', data['zip'], txt)

        sheet.merge_range('B15:C15', 'Date', cell_format_with_color)
        sheet.merge_range('D15:G15', 'Invoice/Bill Number',
                          cell_format_with_color)
        sheet.merge_range('H15:I15', 'Due Date', cell_format_with_color)
        sheet.merge_range('J15:L15', 'Invoices/Debit', cell_format_with_color)
        sheet.merge_range('M15:O15', 'Amount Due', cell_format_with_color)
        sheet.merge_range('P15:R15', 'Balance Due', cell_format_with_color)

        row = 15
        column = 0
        for record in data['my_data']:
            sub_total = data['currency'] + str(record['sub_total'])
            amount_due = data['currency'] + str(record['amount_due'])
            balance = data['currency'] + str(record['balance'])
            total = data['currency'] + str(data['total'])
            remain_balance = data['currency'] + str(data['balance'])
            sheet.merge_range(row, column + 1, row, column + 2,
                              record['invoice_date'], txt_border)
            sheet.merge_range(row, column + 3, row, column + 6,
                              record['name'], txt_border)
            sheet.merge_range(row, column + 7, row, column + 8,
                              record['invoice_date_due'], txt_border)
            sheet.merge_range(row, column + 9, row, column + 11,
                              sub_total, txt_border)
            sheet.merge_range(row, column + 12, row, column + 14,
                              amount_due, txt_border)
            sheet.merge_range(row, column + 15, row, column + 17,
                              balance, txt_border)
            row = row + 1
        sheet.write(row + 2, column + 1, 'Total Amount: ', cell_format)
        sheet.merge_range(row + 2, column + 3, row + 2, column + 4,
                          total, txt)
        sheet.write(row + 4, column + 1, 'Balance Due: ', cell_format)
        sheet.merge_range(row + 4, column + 3, row + 4, column + 4,
                          remain_balance, txt)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def action_customer_share_xlsx(self):
        """ Action for sharing xlsx report via email"""
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('out_invoice')"""
            if not self.show_paid_customer_invoice:
                main_query += """ AND payment_state != 'paid' """
            amount = self.amount_query()
            amount += """ AND move_type IN ('out_invoice')"""
            if not self.show_paid_customer_invoice:
                amount += """ AND payment_state != 'paid' """

            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            sheet = workbook.add_worksheet()
            cell_format = workbook.add_format({
                'font_size': '14px', 'bold': True})
            txt = workbook.add_format({'font_size': '13px'})
            head = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_size': '22px'})
            sheet.merge_range('B2:P4', 'Payment Statement Report', head)
            date_style = workbook.add_format(
                {'text_wrap': True, 'align': 'center',
                 'num_format': 'yyyy-mm-dd'})

            if data['customer']:
                sheet.write('B7:C7', 'Customer : ', cell_format)
                sheet.merge_range('D7:G7', data['customer'], txt)
            sheet.write('B9:C7', 'Address : ', cell_format)
            if data['street']:
                sheet.merge_range('D9:F9', data['street'], txt)
            if data['street2']:
                sheet.merge_range('D10:F10', data['street2'], txt)
            if data['city']:
                sheet.merge_range('D11:F11', data['city'], txt)
            if data['state']:
                sheet.merge_range('D12:F12', data['state'], txt)
            if data['zip']:
                sheet.merge_range('D13:F13', data['zip'], txt)
            sheet.write('B15', 'Date', cell_format)
            sheet.write('D15', 'Invoice/Bill Number', cell_format)
            sheet.write('H15', 'Due Date', cell_format)
            sheet.write('J15', 'Invoices/Debit', cell_format)
            sheet.write('M15', 'Amount Due', cell_format)
            sheet.write('P15', 'Balance Due', cell_format)
            row = 16
            column = 0
            for record in data['my_data']:
                sub_total = data['currency'] + str(record['sub_total'])
                amount_due = data['currency'] + str(record['amount_due'])
                balance = data['currency'] + str(record['balance'])
                total = data['currency'] + str(data['total'])
                remain_balance = data['currency'] + str(data['balance'])

                sheet.merge_range(row, column + 1, row, column + 2,
                                  record['invoice_date'], date_style)
                sheet.merge_range(row, column + 3, row, column + 5,
                                  record['name'], txt)
                sheet.merge_range(row, column + 7, row, column + 8,
                                  record['invoice_date_due'], date_style)
                sheet.merge_range(row, column + 9, row, column + 10,
                                  sub_total, txt)
                sheet.merge_range(row, column + 12, row, column + 13,
                                  amount_due, txt)
                sheet.merge_range(row, column + 15, row, column + 16,
                                  balance, txt)
                row = row + 1
            sheet.write(row + 2, column + 1, 'Total Amount : ', cell_format)
            sheet.merge_range(row + 2, column + 4, row + 2, column + 5,
                              total, txt)
            sheet.write(row + 4, column + 1, 'Balance Due : ', cell_format)
            sheet.merge_range(row + 4, column + 4, row + 4, column + 5,
                              remain_balance, txt)
            workbook.close()
            output.seek(0)
            xlsx = base64.b64encode(output.read())
            output.close()
            ir_values = {
                'name': "Statement Report.xlsx",
                'type': 'binary',
                'datas': xlsx,
                'store_fname': xlsx,
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)
            email_values = {
                'email_to': self.email,
                'subject': 'Payment Statement Report',
                'body_html': '<p>Dear <strong> Mr/Miss. ' + self.name +
                             '</strong> </p> <p> We have attached your'
                             ' payment statement. Please check </p> '
                             '<p>Best regards, </p> <p> ' + self.env.user.name,
                'attachment_ids': [attachment.id],
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Email Sent Successfully',
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError('There is no statement to send')

    def auto_week_statement_report(self):
        """ Action for sending automatic weekly statement
            of both pdf and xlsx report """

        partner = []
        invoice = self.env['account.move'].search(
            [('move_type', 'in', ['out_invoice', 'in_invoice']),
             ('payment_state', '!=', 'all' if self.show_paid_customer_invoice else 'paid'),
             ('state', '=', 'posted')])

        for inv in invoice:
            if inv.partner_id not in partner:
                partner.append(inv.partner_id)

        for rec in partner:
            if rec.id:
                main_query = """ SELECT name , invoice_date, invoice_date_due,
                            amount_total_signed AS sub_total,
                            amount_residual_signed AS amount_due ,
                            amount_residual AS balance
                    FROM account_move WHERE move_type
                        IN ('out_invoice', 'in_invoice')
                       AND state ='posted'
                       AND company_id = '%s' AND partner_id = '%s'
                    GROUP BY name, invoice_date, invoice_date_due,
                    amount_total_signed, amount_residual_signed,
                    amount_residual
                    ORDER by name DESC""" % (self.env.company.id, rec.id)
                if not self.show_paid_customer_invoice:
                    main_query += """ AND payment_state != 'paid' """

                self.env.cr.execute(main_query)
                main = self.env.cr.dictfetchall()
                data = {
                    'customer': rec.display_name,
                    'street': rec.street,
                    'street2': rec.street2,
                    'city': rec.city,
                    'state': rec.state_id.name,
                    'zip': rec.zip,
                    'my_data': main,
                }
                report = self.env['ir.actions.report']._render_qweb_pdf(
                    'accounting_base_kit.res_partner_action', self, data=data)
                data_record = base64.b64encode(report[0])
                ir_values = {
                    'name': 'Statement Report',
                    'type': 'binary',
                    'datas': data_record,
                    'mimetype': 'application/pdf',
                    'res_model': 'res.partner',
                }
                attachment1 = self.env[
                    'ir.attachment'].sudo().create(ir_values)
                # FOR XLSX
                output = io.BytesIO()
                workbook = xlsxwriter.Workbook(output, {'in_memory': True})
                sheet = workbook.add_worksheet()
                cell_format = workbook.add_format(
                    {'font_size': '14px', 'bold': True})
                txt = workbook.add_format({'font_size': '13px'})
                head = workbook.add_format(
                    {'align': 'center', 'bold': True, 'font_size': '22px'})
                sheet.merge_range('B2:P4', 'Payment Statement Report', head)
                date_style = workbook.add_format(
                    {'text_wrap': True, 'align': 'center',
                     'num_format': 'yyyy-mm-dd'})

                if data['customer']:
                    sheet.write('B7:D7', 'Customer/Supplier : ', cell_format)
                    sheet.merge_range('E7:H7', data['customer'], txt)
                sheet.write('B9:C7', 'Address : ', cell_format)
                if data['street']:
                    sheet.merge_range('D9:F9', data['street'], txt)
                if data['street2']:
                    sheet.merge_range('D10:F10', data['street2'], txt)
                if data['city']:
                    sheet.merge_range('D11:F11', data['city'], txt)
                if data['state']:
                    sheet.merge_range('D12:F12', data['state'], txt)
                if data['zip']:
                    sheet.merge_range('D13:F13', data['zip'], txt)

                sheet.write('B15', 'Date', cell_format)
                sheet.write('D15', 'Invoice/Bill Number', cell_format)
                sheet.write('H15', 'Due Date', cell_format)
                sheet.write('J15', 'Invoices/Debit', cell_format)
                sheet.write('M15', 'Amount Due', cell_format)
                sheet.write('P15', 'Balance Due', cell_format)

                row = 16
                column = 0

                for record in data['my_data']:
                    sheet.merge_range(row, column + 1, row, column + 2,
                                      record['invoice_date'], date_style)
                    sheet.merge_range(row, column + 3, row, column + 5,
                                      record['name'], txt)
                    sheet.merge_range(row, column + 7, row, column + 8,
                                      record['invoice_date_due'], date_style)
                    sheet.merge_range(row, column + 9, row, column + 10,
                                      record['sub_total'], txt)
                    sheet.merge_range(row, column + 12, row, column + 13,
                                      record['amount_due'], txt)
                    sheet.merge_range(row, column + 15, row, column + 16,
                                      record['balance'], txt)
                    row = row + 1
                workbook.close()
                output.seek(0)
                xlsx = base64.b64encode(output.read())
                output.close()
                ir_values = {
                    'name': "Statement Report.xlsx",
                    'type': 'binary',
                    'datas': xlsx,
                    'store_fname': xlsx,
                }
                attachment2 = self.env['ir.attachment'].sudo().create(
                    ir_values)
                email_values = {
                    'email_to': rec.email,
                    'subject': 'Weekly Payment Statement Report',
                    'body_html': '<p>Dear <strong> Mr/Miss. ' + rec.name +
                                 '</strong> </p> <p> We have attached your '
                                 'payment statement. Please check </p> <p>'
                                 'Best regards, </p><p> ' + self.env.user.name,
                    'attachment_ids': [attachment1.id, attachment2.id]
                }
                mail = self.env['mail.mail'].sudo().create(email_values)
                mail.send()

    def auto_month_statement_report(self):
        """ Action for sending automatic monthly statement report
            of both pdf and xlsx report"""

        partner = []
        invoice = self.env['account.move'].search(
            [('move_type', 'in', ['out_invoice', 'in_invoice']),
             ('payment_state', '!=', 'all' if self.show_paid_customer_invoice else 'paid'),
             ('state', '=', 'posted')])

        for inv in invoice:
            if inv.partner_id not in partner:
                partner.append(inv.partner_id)

        for rec in partner:
            if rec.id:
                main_query = """SELECT name , invoice_date, invoice_date_due,
                        amount_total_signed AS sub_total,
                        amount_residual_signed AS amount_due ,
                        amount_residual AS balance
                   FROM account_move WHERE move_type
                        IN ('out_invoice', 'in_invoice')
                        AND state ='posted'
                        AND company_id = '%s' AND partner_id = '%s'
                   GROUP BY name, invoice_date, invoice_date_due,
                    amount_total_signed, amount_residual_signed,
                    amount_residual
                    ORDER by name DESC""" % (self.env.company.id, rec.id)
                if not self.show_paid_customer_invoice:
                    main_query += """ AND payment_state != 'paid' """

                self.env.cr.execute(main_query)
                main = self.env.cr.dictfetchall()
                data = {
                    'customer': rec.display_name,
                    'street': rec.street,
                    'street2': rec.street2,
                    'city': rec.city,
                    'state': rec.state_id.name,
                    'zip': rec.zip,
                    'my_data': main,
                }
                report = self.env['ir.actions.report']._render_qweb_pdf(
                    'accounting_base_kit.res_partner_action', self, data=data)
                data_record = base64.b64encode(report[0])
                ir_values = {
                    'name': 'Statement Report',
                    'type': 'binary',
                    'datas': data_record,
                    'mimetype': 'application/pdf',
                    'res_model': 'res.partner',
                }
                attachment1 = self.env['ir.attachment'].sudo().create(
                    ir_values)
                # FOR XLSX
                output = io.BytesIO()
                workbook = xlsxwriter.Workbook(output, {'in_memory': True})
                sheet = workbook.add_worksheet()
                cell_format = workbook.add_format(
                    {'font_size': '14px', 'bold': True})
                txt = workbook.add_format({'font_size': '13px'})
                head = workbook.add_format(
                    {'align': 'center', 'bold': True, 'font_size': '22px'})
                sheet.merge_range('B2:P4', 'Payment Statement Report', head)
                date_style = workbook.add_format(
                    {'text_wrap': True, 'align': 'center',
                     'num_format': 'yyyy-mm-dd'})

                if data['customer']:
                    sheet.write('B7:D7', 'Customer/Supplier : ', cell_format)
                    sheet.merge_range('E7:H7', data['customer'], txt)
                sheet.write('B9:C7', 'Address : ', cell_format)
                if data['street']:
                    sheet.merge_range('D9:F9', data['street'], txt)
                if data['street2']:
                    sheet.merge_range('D10:F10', data['street2'], txt)
                if data['city']:
                    sheet.merge_range('D11:F11', data['city'], txt)
                if data['state']:
                    sheet.merge_range('D12:F12', data['state'], txt)
                if data['zip']:
                    sheet.merge_range('D13:F13', data['zip'], txt)

                sheet.write('B15', 'Date', cell_format)
                sheet.write('D15', 'Invoice/Bill Number', cell_format)
                sheet.write('H15', 'Due Date', cell_format)
                sheet.write('J15', 'Invoices/Debit', cell_format)
                sheet.write('M15', 'Amount Due', cell_format)
                sheet.write('P15', 'Balance Due', cell_format)

                row = 16
                column = 0

                for record in data['my_data']:
                    sheet.merge_range(row, column + 1, row, column + 2,
                                      record['invoice_date'], date_style)
                    sheet.merge_range(row, column + 3, row, column + 5,
                                      record['name'], txt)
                    sheet.merge_range(row, column + 7, row, column + 8,
                                      record['invoice_date_due'], date_style)
                    sheet.merge_range(row, column + 9, row, column + 10,
                                      record['sub_total'], txt)
                    sheet.merge_range(row, column + 12, row, column + 13,
                                      record['amount_due'], txt)
                    sheet.merge_range(row, column + 15, row, column + 16,
                                      record['balance'], txt)
                    row = row + 1
                workbook.close()
                output.seek(0)
                xlsx = base64.b64encode(output.read())
                output.close()
                ir_values = {
                    'name': "Statement Report.xlsx",
                    'type': 'binary',
                    'datas': xlsx,
                    'store_fname': xlsx,
                }
                attachment2 = self.env['ir.attachment'].sudo().create(
                    ir_values)
                email_values = {
                    'email_to': rec.email,
                    'subject': 'Monthly Payment Statement Report',
                    'body_html': '<p>Dear <strong> Mr/Miss. ' + rec.name +
                                 '</strong> </p> <p> We have attached your '
                                 'payment statement. '
                                 'Please check </p> <p>Best regards,'
                                 ' </p> <p>' + self.env.user.name,
                    'attachment_ids': [attachment1.id, attachment2.id]
                }
                mail = self.env['mail.mail'].sudo().create(email_values)
                mail.send()

    def action_vendor_print_pdf(self):
        """ Action for printing vendor pdf report """
        if self.vendor_statement_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('in_invoice')"""
            if not self.show_paid_vendor_bill:
                main_query += """ AND payment_state != 'paid' """
            amount = self.amount_query()
            amount += """ AND move_type IN ('in_invoice')"""
            if not self.show_paid_vendor_bill:
                amount += """ AND payment_state != 'paid' """

            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            return self.env.ref(
                'accounting_base_kit.res_partner_action').report_action(
                self, data=data)
        else:
            raise ValidationError('There is no statement to print')

    def action_vendor_share_pdf(self):
        """ Action for sharing pdf report of vendor via email """
        if self.vendor_statement_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('in_invoice')"""
            if not self.show_paid_vendor_bill:
                main_query += """ AND payment_state != 'paid' """
            amount = self.amount_query()
            amount += """ AND move_type IN ('in_invoice')"""
            if not self.show_paid_vendor_bill:
                amount += """ AND payment_state != 'paid' """

            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            report = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'accounting_base_kit.res_partner_action', self, data=data)
            data_record = base64.b64encode(report[0])
            ir_values = {
                'name': 'Statement Report',
                'type': 'binary',
                'datas': data_record,
                'mimetype': 'application/pdf',
                'res_model': 'res.partner'
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)

            email_values = {
                'email_to': self.email,
                'subject': 'Payment Statement Report',
                'body_html': '<p>Dear <strong> Mr/Miss. ' + self.name +
                             '</strong> </p> <p> We have attached'
                             ' your payment statement. Please check </p> '
                             '<p>Best regards, </p> <p> ' + self.env.user.name,
                'attachment_ids': [attachment.id],
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Email Sent Successfully',
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError('There is no statement to send')

    def action_vendor_print_xlsx(self):
        """ Action for printing xlsx report of vendor """
        if self.vendor_statement_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('in_invoice')"""
            if not self.show_paid_vendor_bill:
                main_query += """ AND payment_state != 'paid' """
            amount = self.amount_query()
            amount += """ AND move_type IN ('in_invoice')"""
            if not self.show_paid_vendor_bill:
                amount += """ AND payment_state != 'paid' """

            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()

            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            return {
                'type': 'ir.actions.report',
                'data': {
                    'model': 'res.partner',
                    'options': json.dumps(data, default=date_utils.json_default),
                    'output_format': 'xlsx',
                    'report_name': 'Payment Statement'
                },
                'report_type': 'xlsx',
            }
        else:
            raise ValidationError('There is no statement to print')

    def action_vendor_share_xlsx(self):
        """ Action for sharing vendor xlsx report via email """
        if self.vendor_statement_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('in_invoice')"""
            if not self.show_paid_vendor_bill:
                main_query += """ AND payment_state != 'paid' """
            amount = self.amount_query()
            amount += """ AND move_type IN ('in_invoice')"""
            if not self.show_paid_vendor_bill:
                amount += """ AND payment_state != 'paid' """

            self.env.cr.execute(main_query)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            sheet = workbook.add_worksheet()
            cell_format = workbook.add_format({
                'font_size': '14px', 'bold': True})
            txt = workbook.add_format({'font_size': '13px'})
            head = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_size': '22px'})
            sheet.merge_range('B2:P4', 'Payment Statement Report', head)
            date_style = workbook.add_format({
                'text_wrap': True, 'align': 'center',
                'num_format': 'yyyy-mm-dd'})
            if data['customer']:
                sheet.write('B7:C7', 'Supplier : ', cell_format)
                sheet.merge_range('D7:G7', data['customer'], txt)
            sheet.write('B9:C7', 'Address : ', cell_format)
            if data['street']:
                sheet.merge_range('D9:F9', data['street'], txt)
            if data['street2']:
                sheet.merge_range('D10:F10', data['street2'], txt)
            if data['city']:
                sheet.merge_range('D11:F11', data['city'], txt)
            if data['state']:
                sheet.merge_range('D12:F12', data['state'], txt)
            if data['zip']:
                sheet.merge_range('D13:F13', data['zip'], txt)
            sheet.write('B15', 'Date', cell_format)
            sheet.write('D15', 'Invoice/Bill Number', cell_format)
            sheet.write('H15', 'Due Date', cell_format)
            sheet.write('J15', 'Invoices/Debit', cell_format)
            sheet.write('M15', 'Amount Due', cell_format)
            sheet.write('P15', 'Balance Due', cell_format)

            row = 16
            column = 0
            for record in data['my_data']:
                sub_total = data['currency'] + str(record['sub_total'])
                amount_due = data['currency'] + str(record['amount_due'])
                balance = data['currency'] + str(record['balance'])
                total = data['currency'] + str(data['total'])
                remain_balance = data['currency'] + str(data['balance'])

                sheet.merge_range(row, column + 1, row, column + 2,
                                  record['invoice_date'], date_style)
                sheet.merge_range(row, column + 3, row, column + 5,
                                  record['name'], txt)
                sheet.merge_range(row, column + 7, row, column + 8,
                                  record['invoice_date_due'], date_style)
                sheet.merge_range(row, column + 9, row, column + 10,
                                  sub_total, txt)
                sheet.merge_range(row, column + 12, row, column + 13,
                                  amount_due, txt)
                sheet.merge_range(row, column + 15, row, column + 16,
                                  balance, txt)
                row = row + 1

            sheet.write(row + 2, column + 1, 'Total Amount : ', cell_format)
            sheet.merge_range(row + 2, column + 4, row + 2, column + 5,
                              total, txt)
            sheet.write(row + 4, column + 1, 'Balance Due : ', cell_format)
            sheet.merge_range(row + 4, column + 4, row + 4, column + 5,
                              remain_balance, txt)

            workbook.close()
            output.seek(0)
            xlsx = base64.b64encode(output.read())
            output.close()
            ir_values = {
                'name': "Statement Report",
                'type': 'binary',
                'datas': xlsx,
                'store_fname': xlsx,
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)

            email_values = {
                'email_to': self.email,
                'subject': 'Payment Statement Report',
                'body_html': '<p>Dear <strong> Mr/Miss. ' + self.name +
                             '</strong> </p> <p> We have attached your '
                             'payment statement. Please check </p> '
                             '<p>Best regards, </p> <p> ' + self.env.user.name,
                'attachment_ids': [attachment.id],
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Email Sent Successfully',
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError('There is no statement to send')

    # Partner Related Documents
    document_count = fields.Char(compute='_compute_total_document_count',
                                 string='Document Count',
                                 help='Get the documents count')

    @api.depends('document_count')
    def _compute_total_document_count(self):
        """Get the document count on smart tab"""
        for record in self:
            record.document_count = self.env[
                'ir.attachment'].search_count(
                [('res_id', '=', self.id), ('res_model', '=', 'res.partner')])

    def action_partner_documents(self):
        """Return the documents of corresponding partner in the smart tab"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents',
            'view_mode': 'kanban,form',
            'res_model': 'ir.attachment',
            'domain': [('res_id', '=', self.id),
                       ('res_model', '=', 'res.partner')],
            'context': "{'create': True}"
        }

    invoice_list = fields.One2many('account.move', 'partner_id',
                                   string="Invoice Details",
                                   readonly=True,
                                   domain=(
                                       [('payment_state', '=', 'not_paid'),
                                        ('move_type', '=', 'out_invoice')]))
    total_due = fields.Monetary(compute='_compute_for_followup', store=False,
                                readonly=True)
    next_reminder_date = fields.Date(compute='_compute_for_followup',
                                     store=False, readonly=True)
    total_overdue = fields.Monetary(compute='_compute_for_followup',
                                    store=False, readonly=True)
    followup_status = fields.Selection(
        [('in_need_of_action', 'In need of action'),
         ('with_overdue_invoices', 'With overdue invoices'),
         ('no_action_needed', 'No action needed')],
        string='Followup status',
    )

    seller_ids = fields.One2many('product.supplierinfo', 'partner_id', string='Products')

    sellers_ids = fields.One2many('kit.purchase.report', 'partner_id', string='Vendor Products',
                                 compute='_compute_seller_ids', help='Products sold by vendor.')
    buyers_ids = fields.One2many('sales.report', 'partner_id', string='Customer Products',
                                compute='_compute_buyer_ids', help='Products bought by customer.')

    def _compute_seller_ids(self):
        self.sellers_ids = False
        purchase_order_line = self.env['purchase.order.line'].search([('state','in',['purchase', 'done']),
                                                                      ('order_id.partner_id', '=', self.id)])
        purchases_order_report = self.env['kit.purchase.report'].create([{
            'company_id': line.company_id.id,
            'name': line.order_id.name,
            'date_order': line.order_id.date_order,
            'partner_id': line.order_id.partner_id.id,
            'product_id': line.product_id.id,
            'qty': line.product_qty,
            'uom_id': line.product_uom.id,
            'price_unit': line.price_unit,
            'price_tax': line.price_tax,
            'tax_id': line.taxes_id.ids,
            'subtotal': line.price_subtotal,
            'total': line.price_total,
            'purchase_order_id' : line.order_id.id
        } for line in purchase_order_line])

    def _compute_buyer_ids(self):
        self.buyers_ids = False
        sale_order_line = self.env['sale.order.line'].search([('state', 'in', ['sale', 'done']),
                                                              ('order_id.partner_id', '=', self.id)])
        pos_order_line = self.env['pos.order.line'].search([('order_id.partner_id', '=', self.id)])
        sales_order_report = self.env['sales.report'].create([{
            'company_id': line.company_id.id,
            'name': line.order_id.name,
            'date_order': line.order_id.date_order,
            'partner_id': line.order_id.partner_id.id,
            'product_id': line.product_id.id,
            'qty': line.product_uom_qty,
            'uom_id': line.product_uom.id,
            'price_unit': line.price_unit,
            'price_tax': line.price_tax,
            'tax_id': line.tax_id.ids,
            'subtotal': line.price_subtotal,
            'total': line.price_total,
            'sale_order_id': line.order_id.id
        } for line in sale_order_line])

        sales_order_report.create([{
            'company_id': pline.order_id.company_id.id,
            'name': pline.order_id.name,
            'date_order': pline.order_id.date_order,
            'partner_id': pline.order_id.partner_id.id,
            'product_id': pline.product_id.id,
            'qty': pline.qty,
            'uom_id': pline.product_uom_id.id,
            'price_unit': pline.price_unit,
            'price_tax': (pline.price_subtotal_incl - pline.price_subtotal),
            'tax_id': pline.tax_ids_after_fiscal_position.ids,
            'subtotal': pline.price_subtotal,
            'total': pline.price_subtotal_incl,
            'pos_order_id': pline.order_id.id
        } for pline in pos_order_line])

    def _compute_for_followup(self):
        """
        Compute the fields 'total_due', 'total_overdue' , 'next_reminder_date' and 'followup_status'
        """
        for record in self:
            total_due = 0
            total_overdue = 0
            today = fields.Date.today()
            for am in record.invoice_list:
                if am.company_id == self.env.company:
                    amount = am.amount_residual
                    total_due += amount

                    is_overdue = today > am.invoice_date_due if am.invoice_date_due else today > am.date
                    if is_overdue:
                        total_overdue += amount or 0
            min_date = record.get_min_date()
            action = record.action_after()
            if min_date:
                date_reminder = min_date + timedelta(days=action)
                if date_reminder:
                    record.next_reminder_date = date_reminder
            else:
                date_reminder = today
                record.next_reminder_date = date_reminder
            if total_overdue > 0 and date_reminder > today:
                followup_status = "with_overdue_invoices"
            elif total_due > 0 and date_reminder <= today:
                followup_status = "in_need_of_action"
            else:
                followup_status = "no_action_needed"
            record.total_due = total_due
            record.total_overdue = total_overdue
            record.followup_status = followup_status

    def get_min_date(self):
        today = date.today()
        for this in self:
            if this.invoice_list:
                min_list = this.invoice_list.mapped('invoice_date_due')
                while False in min_list:
                    min_list.remove(False)
                return min(min_list)
            else:
                return today

    def get_delay(self):
        delay = """select id,delay from followup_line where followup_id =
        (select id from account_followup where company_id = %s)
         order by delay limit 1"""
        self._cr.execute(delay, [self.env.company.id])
        record = self._cr.dictfetchall()

        return record

    def action_after(self):
        lines = self.env['followup.line'].search([(
            'followup_id.company_id', '=', self.env.company.id)])

        if lines:
            record = self.get_delay()
            for i in record:
                return i['delay']

    lended_loan_ids = fields.One2many("account.loan", inverse_name="partner_id")
    lended_loan_count = fields.Integer(
        compute="_compute_lended_loan_count",
        help="How many Loans this partner lended to us?",
    )
    is_lender = fields.Boolean(
        string="Is Lender?",
        default=False,
        help="Company or individual that lends the money at an interest rate.",
    )

    @api.depends("lended_loan_ids")
    def _compute_lended_loan_count(self):
        for record in self:
            record.lended_loan_count = len(record.lended_loan_ids)

    def action_view_partner_lended_loans(self):

        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "accounting_base_kit.account_loan_action"
        )
        all_child = self.with_context(active_test=False).search(
            [("id", "child_of", self.ids)]
        )
        action["domain"] = [("partner_id", "in", all_child.ids)]
        return action

    city_id = fields.Many2one(
        'res.city', string='City', domain="[('state_id', '=', state_id)]")

    @api.onchange('state_id', 'country_id')
    def _onchange_state(self):
        super(ResPartner, self)._onchange_state()
        if not (self.state_id or self.country_id) or (
                self.state_id and self.state_id != self.city_id.state_id) or (
                self.country_id and self.country_id != self.city_id.country_id):
            self.city_id = False

    @api.onchange('city_id')
    def _onchange_city(self):
        if self.city_id:
            self.city = self.city_id.name

    def action_send_msg(self):
        """This function is called when the user clicks the
         'Send WhatsApp Message' button on a partner's form view. It opens a
          new wizard to compose and send a WhatsApp message."""
        compose_form_id = self.env.ref(
            'accounting_base_kit.whatsapp_send_message_view_form').id
        ctx = dict(self.env.context)
        ctx.update({
            'default_partner_id': self.id,
            'default_mobile': self.mobile,
            'default_image_1920': self.image_1920,
        })
        return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'whatsapp.send.message',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
                }

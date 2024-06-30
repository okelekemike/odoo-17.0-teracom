# -- coding: utf-8 --

from odoo import api, fields, models, _
from collections import defaultdict
from datetime import date, datetime, timedelta


class SaleProductsReport(models.Model):
    _name = "sale.products.report"
    _description = "Product Sales Report"
    _order = 'total_price_total desc'

    product_id = fields.Many2one('product.product', string='Product')
    total_price_subtotal = fields.Float('Subtotal')
    total_discount_amount = fields.Float('Discount Amount')
    total_price_total = fields.Float('Total')
    total_tax_amount = fields.Float('Tax Amount')
    total_quantity = fields.Float('Total Quantity')
    list_price = fields.Float('List Price')
    refund_total_price_total = fields.Float('Refund Total')
    refund_quantity = fields.Float('Refund Quantity')


class SalesProductsReport(models.AbstractModel):
    _name = "report.accounting_base_kit.sale_product_report"
    _description = "Sale Products Report"
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, obj):
        products = obj._query()
        date_from = obj.date_from
        date_to = obj.date_to
        header_title_format = workbook.add_format({
            'border': 0,
            'align': 'center',
            'font_color': '#0d084c',
            'bold': True,
            'valign': 'vcenter',
            'text_wrap': 'true',
        })
        header_title_format.set_text_wrap()
        header_title_format.set_font_size(18)

        header1_format = workbook.add_format({
            'border': 1,
            'border_color': 'black',
            'align': 'center',
            'font_color': 'black',
            'bold': False,
            'valign': 'vcenter',
            'fg_color': '#808080'})
        header1_format.set_text_wrap()
        header1_format.set_font_size(12)

        header2_format = workbook.add_format({
            'border': 1,
            'border_color': 'black',
            'align': 'center',
            'font_color': 'black',
            'bold': False,
            'valign': 'vcenter',
        })
        header2_format.set_text_wrap()
        header2_format.set_font_size(12)

        header3_format = workbook.add_format({
            'border': 1,
            'border_color': 'black',
            'align': 'center',
            'font_color': 'black',
            'bold': True,
            'valign': 'vcenter',
            'fg_color': '#d8d8d8',
        })
        header3_format.set_text_wrap()
        header4_format = workbook.add_format({
            'border': 1,
            'border_color': 'black',
            'align': 'center',
            'font_color': 'white',
            'bold': False,
            'valign': 'vcenter',
            'fg_color': '#454545'})
        header4_format.set_text_wrap()
        header4_format.set_font_size(12)
        worksheet = workbook.add_worksheet()

        worksheet.right_to_left()
        worksheet.set_column('A:A', 40)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 20)
        worksheet.set_row(0, 20)
        worksheet.set_row(1, 20)
        worksheet.set_row(2, 25)
        worksheet.set_row(3, 25)

        row = 4
        subtotal_sum = 0
        discount_sum = 0
        after_sum = 0
        tax_sum = 0
        qty_sum = 0
        refund_sum = 0
        refund_qty_sum = 0

        for product in products:
            worksheet.set_row(row, 30)
            worksheet.write(row, 0, product.get('name', {}).get('en_US') or product.get('name', ''), header2_format)
            worksheet.write(row, 1, '{:,.2f}'.format(product['total_price_subtotal']), header2_format)
            subtotal_sum += product['total_price_subtotal']
            worksheet.write(row, 2, '{:,.2f}'.format(product['total_discount_amount']), header2_format)
            discount_sum += product['total_discount_amount']
            worksheet.write(row, 3, '{:,.2f}'.format(product['total_price_total']), header2_format)
            after_sum += product['total_price_total']
            worksheet.write(row, 4, '{:,.2f}'.format(product['total_tax_amount']), header2_format)
            tax_sum += product['total_tax_amount']
            worksheet.write(row, 5, product['total_quantity'], header2_format)
            qty_sum += product['total_quantity']
            worksheet.write(row, 6, '{:,.2f}'.format(product['list_price']), header2_format)
            worksheet.write(row, 7, '{:,.2f}'.format(product['refund_total_price_total']), header2_format)
            refund_sum += product['refund_total_price_total']
            worksheet.write(row, 8, product['refund_quantity'], header2_format)
            refund_qty_sum += product['refund_quantity']

            row += 1

        worksheet.merge_range('A1:I1', 'Total Sales Report ', header3_format)
        worksheet.merge_range('B2:I2', 'Total ', header3_format)
        content = f'Date\nFrom: {date_from}\nTo: {date_to}'
        if date_from and date_to:
            worksheet.merge_range('A2:A4', content, header3_format)
        else:
            worksheet.merge_range('A2:A4', "Product", header3_format)
        worksheet.write(2, 1, 'Sub Total', header3_format)
        worksheet.write(2, 2, 'Discount Amount', header3_format)
        worksheet.write(2, 3, 'Total', header3_format)
        worksheet.write(2, 4, 'Tax Amount', header3_format)
        worksheet.write(2, 5, 'Total Quantity', header3_format)
        worksheet.write(2, 6, 'Sale Price', header3_format)
        worksheet.write(2, 7, 'Refund Amount', header3_format)
        worksheet.write(2, 8, 'Refund Quantity', header3_format)
        worksheet.write(3, 1, '{:,.2f}'.format(subtotal_sum), header2_format)
        worksheet.write(3, 2, '{:,.2f}'.format(discount_sum), header2_format)
        worksheet.write(3, 3, '{:,.2f}'.format(after_sum), header2_format)
        worksheet.write(3, 4, '{:,.2f}'.format(tax_sum), header2_format)
        worksheet.write(3, 5, '{:,.2f}'.format(qty_sum), header2_format)
        worksheet.write(3, 6, '', header2_format)
        worksheet.write(3, 7, '{:,.2f}'.format(refund_sum), header2_format)
        worksheet.write(3, 8, '{:,.2f}'.format(refund_qty_sum), header2_format)


class SalesProductsWizard(models.TransientModel):
    _name = "sale.products.wizard"
    _description = "Sale Products Report"

    date_from = fields.Date(string='Date')
    date_to = fields.Date(string='Date')
    product_ids = fields.Many2many('product.product')
    product_category_ids = fields.Many2many('product.category')
    include_pos = fields.Boolean('Include Point Of Sale ?')

    @api.onchange('product_category_ids')
    def _get_product_ids(self):
        self.product_ids = self.env['product.product'].search(
            [('categ_id', 'in', self.product_category_ids.ids)])

    def _query(self):
        if self.include_pos:
            query = """
                WITH merged_data AS (
        SELECT
            p.id AS product_id,
            tmpl.name AS name,
            MAX(tmpl.list_price) AS list_price,
            SUM(CASE WHEN am.move_type = 'out_invoice' THEN aml.quantity ELSE 0 END) AS total_quantity,
            SUM(CASE WHEN am.move_type = 'out_invoice' THEN (aml.discount * aml.price_subtotal) / 100 ELSE 0 END) AS total_discount_amount,  
            SUM(CASE WHEN am.move_type = 'out_invoice' THEN aml.price_subtotal + (aml.discount * aml.price_subtotal) / 100 ELSE 0 END) AS total_price_subtotal,
            SUM(CASE WHEN am.move_type = 'out_invoice' THEN aml.price_total ELSE 0 END) AS total_price_total,
            SUM(CASE WHEN am.move_type = 'out_invoice' THEN aml.price_total - aml.price_subtotal ELSE 0 END) AS total_tax_amount,
            SUM(CASE WHEN am.move_type = 'out_refund' THEN aml.price_total ELSE 0 END) AS refund_total_price_total,
            SUM(CASE WHEN am.move_type = 'out_refund' THEN aml.quantity ELSE 0 END) AS refund_quantity
        FROM  account_move_line aml
        JOIN account_move am ON aml.move_id = am.id
        JOIN product_product p ON aml.product_id = p.id
        LEFT JOIN product_template tmpl ON p.product_tmpl_id = tmpl.id
        WHERE
            am.state = 'posted'
            AND am.move_type IN ('out_invoice', 'out_refund')
            AND aml.product_id IS NOT NULL
            AND am.company_id = %s
            AND (%s IS NULL OR (am.date >= %s AND am.date <= %s))
            AND (NOT %s OR aml.product_id = ANY(%s))
        GROUP BY
            aml.product_id, p.id, tmpl.name

        UNION
    
        SELECT
            p.id AS product_id,
            tmpl.name AS name,
            MAX(tmpl.list_price) AS list_price,
            SUM(CASE WHEN pos.state not in ('draft', 'cancel') AND pol.qty > 0 THEN pol.qty ELSE 0 END) AS total_quantity,
            SUM(CASE WHEN pos.state not in ('draft', 'cancel') AND pol.qty > 0 THEN (pol.discount * pol.price_subtotal_incl) / 100 ELSE 0 END) AS total_discount_amount,
            SUM(CASE WHEN pos.state not in ('draft', 'cancel') AND pol.qty > 0 THEN pol.price_subtotal_incl + (pol.discount * pol.price_subtotal_incl) / 100 ELSE 0 END) AS total_price_subtotal,
            SUM(CASE WHEN pos.state not in ('draft', 'cancel') AND pol.qty > 0 THEN pol.price_subtotal_incl ELSE 0 END) AS total_price_total,
            SUM(CASE WHEN pos.state not in ('draft', 'cancel') AND pol.qty > 0 THEN pol.price_subtotal_incl - pol.price_subtotal ELSE 0 END) AS total_tax_amount,
            SUM(CASE WHEN pos.state not in ('draft', 'cancel') AND pol.qty < 0 THEN -pol.price_subtotal_incl ELSE 0 END) AS refund_total_price_total,
            SUM(CASE WHEN pos.state not in ('draft', 'cancel') AND pol.qty < 0 THEN -pol.qty ELSE 0 END) AS refund_quantity
        FROM pos_order_line pol
        JOIN pos_order pos ON pol.order_id = pos.id
        JOIN product_product p ON pol.product_id = p.id
        LEFT JOIN product_template tmpl ON p.product_tmpl_id = tmpl.id
        WHERE
            pos.state not in ('draft', 'cancel')
            AND pos.company_id = %s
            AND pol.product_id IS NOT NULL
            AND (%s IS NULL OR (pos.date_order >= %s AND pos.date_order <= %s))
            AND (NOT %s OR pol.product_id = ANY(%s))        
        GROUP BY
            pol.product_id, p.id, tmpl.name
    )
    SELECT
        product_id,
        name,
        MAX(list_price) AS list_price,
        SUM(total_quantity) AS total_quantity,
        SUM(total_discount_amount) AS total_discount_amount,
        SUM(total_price_subtotal) AS total_price_subtotal,
        SUM(total_price_total) AS total_price_total,
        SUM(total_tax_amount) AS total_tax_amount,
        SUM(refund_total_price_total) AS refund_total_price_total,
        SUM(refund_quantity) AS refund_quantity
    FROM
        merged_data
    GROUP BY
        product_id, name ;
        """
        else:
            query = """
                SELECT
                    p.id AS product_id,
                    tmpl.name AS name,
                    MAX(tmpl.list_price) AS list_price,
                    SUM(CASE WHEN am.move_type = 'out_invoice' THEN aml.quantity ELSE 0 END) AS total_quantity,
                    SUM(CASE WHEN am.move_type = 'out_invoice' THEN (aml.discount * aml.price_subtotal) / 100 ELSE 0 END) AS total_discount_amount,  
                    SUM(CASE WHEN am.move_type = 'out_invoice' THEN aml.price_subtotal + (aml.discount * aml.price_subtotal) / 100 ELSE 0 END) AS total_price_subtotal,
                    SUM(CASE WHEN am.move_type = 'out_invoice' THEN aml.price_total ELSE 0 END) AS total_price_total,
                    SUM(CASE WHEN am.move_type = 'out_invoice' THEN aml.price_total - aml.price_subtotal ELSE 0 END) AS total_tax_amount,
                    SUM(CASE WHEN am.move_type = 'out_refund' THEN aml.price_total ELSE 0 END) AS refund_total_price_total,
                    SUM(CASE WHEN am.move_type = 'out_refund' THEN aml.quantity ELSE 0 END) AS refund_quantity
                FROM  account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                JOIN product_product p ON aml.product_id = p.id
                LEFT JOIN product_template tmpl ON p.product_tmpl_id = tmpl.id
                WHERE
                    am.state = 'posted'
                    AND am.move_type IN ('out_invoice', 'out_refund')
                    AND aml.product_id IS NOT NULL
                    AND am.company_id = %s
                    AND (%s IS NULL OR (am.date >= %s AND am.date <= %s))
                    AND (NOT %s OR aml.product_id = ANY(%s))
                GROUP BY
                    aml.product_id, p.id, tmpl.name
                """

        company = self.env.company.id
        date_from = self.date_from if self.date_from else None
        date_to = self.date_to if self.date_to else None
        product_ids = self.product_ids.ids if self.product_ids.ids else []
        include_product_condition = bool(product_ids)
        if self.include_pos:
            self._cr.execute(query, [company, date_to, date_from, date_to, include_product_condition, product_ids,
                                     company, date_to, date_from, date_to, include_product_condition, product_ids])
        else:
            self._cr.execute(query,
                             [company, date_to, date_from, date_to, include_product_condition, product_ids,
                              ])
        products = self.env.cr.dictfetchall()
        return products

    def print_xlsx(self):
        data = {
            'form_data': self.read()[0]
        }
        return self.env.ref('accounting_base_kit.report_product_sales_xlsx').report_action(self)

    def print_pdf(self):
        products = self._query()
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'data': products,
        }
        return self.env.ref('accounting_base_kit.report_product_sales_pdf').with_context(landscape=True).report_action(
            self, data=data)

    def open_view(self):
        self.env['sale.products.report'].sudo().search([]).unlink()
        products = self._query()
        print(products)
        vals_list = []
        for product in products:
            vals = {
                'product_id': product['product_id'],
                'total_price_subtotal': product['total_price_subtotal'],
                'total_discount_amount': product['total_discount_amount'],
                'total_price_total': product['total_price_total'],
                'total_tax_amount': product['total_tax_amount'],
                'total_quantity': product['total_quantity'],
                'list_price': product['list_price'],
                'refund_total_price_total': product['refund_total_price_total'],
                'refund_quantity': product['refund_quantity'],
            }
            vals_list.append(vals)

        self.env['sale.products.report'].create(vals_list)
        return {
            'view_mode': 'tree,graph',
            'name': (_('Product Sales & Refunds')),
            'res_model': 'sale.products.report',
            'type': 'ir.actions.act_window',
        }

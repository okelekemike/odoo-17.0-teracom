# -*- coding: utf-8 -*-
try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO
from datetime import datetime
from itertools import groupby
import ast, math
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, format_amount, float_compare


class AccountMove(models.Model):
    """Inherits from the account.move model for adding the depreciation
    field to the account"""
    _inherit = 'account.move'

    partner_contact_person_id = fields.Many2one('res.partner', string="Contact Person", readonly=False)

    asset_depreciation_ids = fields.One2many('account.asset.depreciation.line', 'move_id',
                                             string='Assets Depreciation Lines')

    loan_line_id = fields.Many2one(
        "account.loan.line",
        readonly=True,
        ondelete="restrict",
    )
    loan_id = fields.Many2one(
        "account.loan",
        readonly=True,
        store=True,
        ondelete="restrict",
    )

    state = fields.Selection(
        selection_add=[('waiting_approval', 'Waiting For Approval'),
                       ('approved', 'Approved'),
                       ('rejected', 'Rejected')],
        ondelete={'waiting_approval': 'set default', 'approved': 'set default',
                  'rejected': 'set default'}, help="States of approval.")

    @api.model
    def _default_show_sign(self):
        """Get the default value for the 'Show Digital Signature' field on
        invoices."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.is_show_digital_sign_invoice')

    @api.model
    def _default_enable_sign(self):
        """Get the default value for the 'Enable Digital Signature Options'
        field on invoices."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.is_enable_options_invoice')

    @api.model
    def _default_show_sign_bill(self):
        """Get the default value for the 'Show Digital Signature on Bills'
        field on invoices."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.is_show_digital_sign_bill')

    digital_sign = fields.Binary(string='Digital Signature',
                                 help="Binary field to store digital signatures.")
    sign_by = fields.Char(string='Signed By',
                          help="Name of the person who signed the document.")
    designation = fields.Char(string='Designation',
                              help="Designation of the person who signed the document.")
    sign_on = fields.Datetime(string='Signed On',
                              help="Date and time when the document was signed.")
    is_show_signature = fields.Boolean(string='Show Signature',
                                       default=_default_show_sign,
                                       compute='_compute_show_signature',
                                       help="Determines whether the digital "
                                            "signature should be displayed "
                                            "on invoices.")
    is_show_sign_bill = fields.Boolean(string='Show Signature on Bills',
                                       default=_default_show_sign_bill,
                                       compute='_compute_show_sign_bill',
                                       help="Determines whether the digital "
                                            "signature should be displayed "
                                            "on bills.")
    is_enable_others = fields.Boolean(string="Enable Others",
                                      default=_default_enable_sign,
                                      compute='_compute_enable_others',
                                      help="Enables various digital signature "
                                           "options on invoices.")

    def button_cancel(self):
        """Button action to cancel the transfer"""
        for move in self:
            for line in move.asset_depreciation_ids:
                line.move_posted_check = False
        return super(AccountMove, self).button_cancel()

    def post(self):
        """Supering the post method to mapped the asset depreciation records"""
        self.mapped('asset_depreciation_ids').post_lines_and_close_asset()
        return super(AccountMove, self).action_post()

    @api.model
    def _refund_cleanup_lines(self, lines):
        """Supering the refund cleanup lines to check the asset category """
        result = super(AccountMove, self)._refund_cleanup_lines(lines)
        for i, line in enumerate(lines):
            for name, field in line._fields.items():
                if name == 'asset_category_id':
                    result[i][2][name] = False
                    break
        return result

    def action_cancel(self):
        """Action perform to cancel the asset record"""
        res = super(AccountMove, self).action_cancel()
        self.env['account.asset.asset'].sudo().search(
            [('invoice_id', 'in', self.ids)]).write({'active': False})
        return res

    def action_post(self):
        """Action used to post invoice"""
        result = super(AccountMove, self).action_post()
        for inv in self:
            context = dict(self.env.context)
            # Within the context of an invoice,
            # this default value is for the type of the invoice, not the type
            # of the asset. This has to be cleaned from the context before
            # creating the asset,otherwise it tries to create the asset with
            # the type of the invoice.
            context.pop('default_type', None)
            inv.invoice_line_ids.with_context(context).asset_create()

            loan_line_id = inv.loan_line_id
            if loan_line_id:
                inv.loan_id = loan_line_id.loan_id
                inv.loan_line_id._check_move_amount()
                inv.loan_line_id.loan_id._compute_posted_lines()
                if inv.loan_line_id.sequence == inv.loan_id.periods:
                    inv.loan_id.close()
        return result

    # Invoice Dashboard
    @api.model
    def retrieve_out_invoice_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the invoice order views.
        """
        result = {
            'draft': 0,
            'posted': 0,
            'cancelled': 0,
            'paid': 0,
            'not_paid_amount': 0,
            'paid_amount': 0,
            'lost_amount': 0,
            'expected_amount': 0,
            'company_currency_symbol': self.env.company.currency_id.symbol
        }
        account_move = self.env['account.move']
        sum_amount = 0
        sum_invoices = account_move.search([('payment_state', '=', 'paid'),
                                            ('move_type', '=', 'out_invoice')])
        for line in sum_invoices:
            sum_amount = sum_amount + line.amount_total
        amount = 0
        amount_invoices = account_move.search(
            [('payment_state', 'in', ('not_paid', 'partial')),
             ('move_type', '=', 'out_invoice')])
        for line in amount_invoices:
            amount = amount + line.amount_residual_signed
        lost = 0
        lost_invoices = account_move.search(
            [('state', '=', 'cancel'),
             ('move_type', '=', 'out_invoice')])
        for line in lost_invoices:
            lost = lost + line.amount_total
        expected = 0
        expected_invoices = account_move.search(
            [('state', '=', 'posted'), ('payment_state', 'in', ('not_paid', 'partial')),
             ('move_type', '=', 'out_invoice')])
        for line in expected_invoices:
            expected = expected + line.amount_residual
        result['paid_amount'] = format_amount(self.env, sum_amount or 0, self.env.company.currency_id)
        result['lost_amount'] = format_amount(self.env, lost or 0, self.env.company.currency_id)
        result['not_paid_amount'] = format_amount(self.env, amount or 0, self.env.company.currency_id)
        result['expected_amount'] = format_amount(self.env, expected or 0, self.env.company.currency_id)
        result['draft'] = account_move.search_count(
            [('state', '=', 'draft'), ('move_type', '=', 'out_invoice')])
        result['posted'] = account_move.search_count(
            [('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])
        result['cancelled'] = account_move.search_count(
            [('state', '=', 'cancel'), ('move_type', '=', 'out_invoice')])
        result['reversed'] = account_move.search_count(
            [('payment_state', '=', 'reversed'), ('move_type', '=', 'out_invoice')])
        result['paid'] = account_move.search_count(
            [('payment_state', '=', 'paid'), ('move_type', '=', 'out_invoice')])
        result['not_paid'] = account_move.search_count(
            [('payment_state', 'in', ('not_paid', 'partial')), ('state', '!=', 'draft'),
             ('move_type', '=', 'out_invoice')])
        return result

    @api.model
    def retrieve_in_invoice_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the invoice order views.
        """
        result = {
            'draft': 0,
            'posted': 0,
            'cancelled': 0,
            'paid': 0,
            'not_paid_amount': 0,
            'paid_amount': 0,
            'lost_amount': 0,
            'expected_amount': 0,
            'company_currency_symbol': self.env.company.currency_id.symbol
        }
        account_move = self.env['account.move']
        sum_amount = 0
        sum_invoices = account_move.search(
            [('payment_state', '=', 'paid'), ('move_type', '=', 'in_invoice')])
        for line in sum_invoices:
            sum_amount = sum_amount + line.amount_total
        amount = 0
        amount_invoices = account_move.search(
            [('payment_state', 'in', ('not_paid', 'partial')),
             ('move_type', '=', 'in_invoice')])
        for line in amount_invoices:
            amount = amount + line.amount_residual_signed
        lost = 0
        lost_invoices = account_move.search(
            [('state', '=', 'cancel'), ('move_type', '=', 'in_invoice')])
        for line in lost_invoices:
            lost = lost + line.amount_total
        expected = 0
        expected_invoices = account_move.search(
            [('state', '=', 'posted'), ('payment_state', 'in', ('not_paid', 'partial')),
             ('move_type', '=', 'in_invoice')])
        for line in expected_invoices:
            expected = expected + line.amount_residual
        result['paid_amount'] = format_amount(self.env, sum_amount or 0, self.env.company.currency_id)
        result['lost_amount'] = format_amount(self.env, lost or 0, self.env.company.currency_id)
        result['not_paid_amount'] = format_amount(self.env, amount or 0, self.env.company.currency_id)
        result['expected_amount'] = format_amount(self.env, expected or 0, self.env.company.currency_id)
        result['draft'] = account_move.search_count(
            [('state', '=', 'draft'), ('move_type', '=', 'in_invoice')])
        result['posted'] = account_move.search_count(
            [('state', '=', 'posted'), ('move_type', '=', 'in_invoice')])
        result['cancelled'] = account_move.search_count(
            [('state', '=', 'cancel'), ('move_type', '=', 'in_invoice')])
        result['reversed'] = account_move.search_count(
            [('payment_state', '=', 'reversed'), ('move_type', '=', 'in_invoice')])
        result['paid'] = account_move.search_count(
            [('payment_state', '=', 'paid'), ('move_type', '=', 'in_invoice')])
        result['not_paid'] = account_move.search_count(
            [('payment_state', 'in', ('not_paid', 'partial')), ('state', '!=', 'draft'),
             ('move_type', '=', 'in_invoice')])
        return result

    def action_customer_print_pdf(self):
        self.ensure_one()
        self.env['res.partner'].action_customer_print_pdf()

    def action_customer_print_xlsx(self):
        self.ensure_one()
        self.env['res.partner'].action_customer_print_xlsx()

    def action_customer_share_pdf(self):
        self.ensure_one()
        self.env['res.partner'].action_customer_share_pdf()

    def action_customer_share_xlsx(self):
        self.ensure_one()
        self.env['res.partner'].action_customer_share_xlsx()

    def action_vendor_print_pdf(self):
        self.ensure_one()
        self.env['res.partner'].action_vendor_print_pdf()

    def action_vendor_print_xlsx(self):
        self.ensure_one()
        self.env['res.partner'].action_vendor_print_xlsx()

    def action_vendor_share_pdf(self):
        self.ensure_one()
        self.env['res.partner'].action_vendor_share_pdf()

    def action_vendor_share_xlsx(self):
        self.ensure_one()
        self.env['res.partner'].action_vendor_share_xlsx()

    # Digital Signature In Purchase Order, Invoice, Inventory
    def _compute_show_signature(self):
        """Compute the 'Show Signature' field on invoices."""
        is_show_signature = self._default_show_sign()
        for record in self:
            record.is_show_signature = is_show_signature

    def _compute_enable_others(self):
        """Compute the 'Enable Digital Signature Options' field on invoices."""
        is_enable_others = self._default_enable_sign()
        for record in self:
            record.is_enable_others = is_enable_others

    def _compute_show_sign_bill(self):
        """Compute the 'Show Signature on Bills' field on invoices."""
        is_show_sign_bill = self._default_show_sign_bill()
        for record in self:
            record.is_show_sign_bill = is_show_sign_bill

    def action_invoice_sent(self):
        """Send the invoice and validate it, checking for the presence of a
        digital signature."""
        res = super(AccountMove, self).action_invoice_sent()
        if self.env[
            'ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.is_confirm_sign_invoice') and \
                self.digital_sign is False:
            raise UserError(_("Signature is missing"))
        return res

    number_to_words = fields.Char(string="Amount in Words: ",
                                  compute='_compute_number_to_words',
                                  help="To showing total amount in words")

    def _compute_number_to_words(self):
        """Compute the amount to words in Invoice"""
        for rec in self:
            rec.number_to_words = rec.currency_id.amount_to_text(
                rec.amount_total)

    def action_send_whatsapp(self):
        """ Action for sending whatsapp message."""
        compose_form_id = self.env.ref(
            'accounting_base_kit.whatsapp_send_message_view_form').id
        ctx = dict(self.env.context)
        message = (
                "Hi " + str(self.partner_id.name) + ", \n " +
                "Here is your Invoice: " + str(self.name) + " amounting " +
                self.currency_id.symbol + str(self.amount_total) + "\n " +
                "from " + str(self.company_id.name) + " is ready for review. \n " +
                "Please remit payment at your earliest convenience as agreed to this invoice. \n" +
                "Please use the following communication for your payment: " + str(self.name) + "\n\n\n" +
                "Please follow this link to access your invoice directly:" + "\n" +
                self.action_gen_qrcode())
        ctx.update({
            'default_message': message,
            'default_partner_id': self.partner_id.id,
            'default_mobile': self.partner_id.mobile,
            'default_image_1920': self.partner_id.image_1920,
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

    def check_customers(self, partner_ids):
        """ Check if the selected invoices belong to the same customer."""
        partners = groupby(partner_ids)
        return next(partners, True) and not next(partners, False)

    def action_whatsapp_multi(self):
        """
        Initiate WhatsApp messaging for multiple invoices and open a message
        composition wizard.
        """
        account_move_ids = self.env['account.move'].browse(
            self.env.context.get('active_ids'))
        partner_ids = []
        for account_move in account_move_ids:
            partner_ids.append(account_move.partner_id.id)
        partner_check = self.check_customers(partner_ids)
        if partner_check:
            account_move_numbers = account_move_ids.mapped('name')
            account_move_numbers = "\n".join(account_move_numbers)
            compose_form_id = self.env.ref(
                'accounting_base_kit.whatsapp_send_message_view_form').id
            ctx = dict(self.env.context)
            message = ("Hi" + " " + self.partner_id.name + ',' + '\n' +
                       "Your Orders are:" + '\n' + account_move_numbers + ' ' +
                       "is ready for review. Do not hesitate to contact us, if you have any questions.")
            ctx.update({
                'default_message': message,
                'default_partner_id': account_move_ids[0].partner_id.id,
                'default_mobile': account_move_ids[0].partner_id.mobile,
                'default_image_1920': account_move_ids[0].partner_id.image_1920,
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
        else:
            raise UserError(_(
                'It appears that you have selected orders from multiple'
                ' customers. Please select orders from a single customer.'))

    qr = fields.Binary(string='QR Code')

    def action_gen_qrcode(self):
        account_move_share_link_res = self.get_base_url() + self._get_share_url(redirect=True)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(account_move_share_link_res)
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_image = base64.b64encode(temp.getvalue())
        self.qr = qr_image
        return account_move_share_link_res

    # Interest for Overdue Invoice. Extending model Invoice model to compute the interest amount for
    # overdue invoices based on the chosen payment term configurations.

    interest_amount = fields.Monetary(string='Interest Amount', readonly=True,
                                      help='The amount of interest accrued.')
    interest_overdue_act = fields.Boolean(related="invoice_payment_term_id.interest_overdue_act",
                                          help='Flag indicating whether overdue interest is active.')
    interest_calculated_period = fields.Char(string="Interest calculated date",
                                             help='The date when interest was calculated.')
    interest_type = fields.Selection(related="invoice_payment_term_id.interest_type",
                                     help='The type of interest applied.')
    interest_percentage = fields.Float(related="invoice_payment_term_id.interest_percentage",
                                       help='The percentage rate of interest applied.')

    def get_period_time(self, today_date):
        """ Compute period duration based on Interest duration type. """
        self.ensure_one()
        r_obj = relativedelta(today_date, self.invoice_date_due)
        if self.invoice_payment_term_id.interest_type == 'monthly':
            period = (r_obj.years * 12) + r_obj.months
            if r_obj and r_obj.days > 0:
                period = period + 1
        elif self.invoice_payment_term_id.interest_type == 'weekly':
            period = math.ceil((today_date - self.invoice_date_due).days / 7)
        else:
            period = (today_date - self.invoice_date_due).days
        return period

    def action_interest_compute(self):
        """ Action for computing Interest amount based on the chosen payment term configurations"""
        today_date = fields.Date.today()
        for rec in self:
            if rec.invoice_date_due \
                    and rec.invoice_date_due < fields.Date.today() \
                    and rec.state == 'draft' \
                    and rec.move_type == 'out_invoice' \
                    and rec.interest_overdue_act \
                    and rec.invoice_payment_term_id.interest_percentage > 0:
                period = rec.get_period_time(today_date)
                if rec.invoice_payment_term_id.interest_type == 'monthly':
                    if rec.interest_calculated_period \
                            and rec.interest_calculated_period == str(period) \
                            + "-m":
                        raise ValidationError(_(
                            'Your payment term is monthly, and you can update it only once in a month.'
                        ))
                    rec.interest_calculated_period = str(period) + "-m"
                elif rec.invoice_payment_term_id.interest_type == 'weekly':
                    if rec.interest_calculated_period \
                            and rec.interest_calculated_period == str(period) \
                            + "-w":
                        raise ValidationError(_(
                            'Your payment term is weekly, and you can update it only once in a week.'
                        ))
                    rec.interest_calculated_period = str(period) + "-w"
                else:
                    if rec.interest_calculated_period \
                            and rec.interest_calculated_period == str(period) \
                            + "-d":
                        raise ValidationError(_(
                            'Your payment term is daily, and you can update it only once in a day.'
                        ))
                    rec.interest_calculated_period = str(period) + "-d"
                interest_line = rec.invoice_line_ids.search(
                    [('name', '=', 'Interest Amount for Overdue Invoice'),
                     ('move_id', '=', rec.id)], limit=1)
                if interest_line:
                    rec.invoice_line_ids = ([(2, interest_line.id, 0)])
                rec.interest_amount = rec.amount_total * rec \
                    .invoice_payment_term_id.interest_percentage * period / 100
                vals = {'name': 'Interest Amount for Overdue Invoice',
                        'price_unit': rec.interest_amount,
                        'quantity': 1, }
                if rec.invoice_payment_term_id.interest_account_id:
                    vals.update({
                        'account_id': rec.invoice_payment_term_id.interest_account_id.id})
                if rec.interest_amount > 0:
                    rec.invoice_line_ids = ([(0, 0, vals)])
            elif rec.interest_amount > 0:
                rec.action_interest_reset()

    def _get_interest_check(self):
        """ Method for Interest computation via scheduled action """

        today_date = fields.Date.today()
        for rec in self.sudo().search([('state', '=', 'draft')]):
            if rec.invoice_date_due and rec.invoice_date_due < today_date \
                    and rec.state == 'draft' \
                    and rec.move_type == 'out_invoice' \
                    and rec.interest_overdue_act \
                    and rec.invoice_payment_term_id.interest_percentage > 0:
                period = rec.get_period_time(today_date)
                if rec.invoice_payment_term_id.interest_type == 'monthly':
                    if rec.interest_calculated_period \
                            and rec.interest_calculated_period == str(period) \
                            + "-m":
                        continue
                    rec.interest_calculated_period = str(period) + "-m"
                elif rec.invoice_payment_term_id.interest_type == 'weekly':
                    if rec.interest_calculated_period \
                            and rec.interest_calculated_period == str(period) \
                            + "-w":
                        continue
                    rec.interest_calculated_period = str(period) + "-w"
                else:
                    if rec.interest_calculated_period \
                            and rec.interest_calculated_period == str(period) \
                            + "-d":
                        continue
                    rec.interest_calculated_period = str(period) + "-d"
                interest_line = rec.invoice_line_ids.search(
                    [('name', '=', 'Interest Amount for Overdue Invoice'),
                     ('move_id', '=', rec.id)], limit=1)
                if interest_line:
                    rec.invoice_line_ids = ([(2, interest_line.id, 0)])
                rec.interest_amount = rec.amount_total * rec \
                    .invoice_payment_term_id.interest_percentage * period / 100
                vals = {'name': 'Interest Amount for Overdue Invoice',
                        'price_unit': rec.interest_amount,
                        'quantity': 1,
                        }
                if rec.invoice_payment_term_id.interest_account_id:
                    vals.update({
                        'account_id': rec.invoice_payment_term_id.
                        interest_account_id.id})
                if rec.interest_amount > 0:
                    rec.invoice_line_ids = ([(0, 0, vals)])
            elif rec.interest_amount > 0:
                rec.action_interest_reset()

    def action_interest_reset(self):
        """Method for resetting the interest lines and Interest amount in
        Invoice"""
        self.interest_amount = 0
        interest_line = self.invoice_line_ids.search(
            [('name', '=', 'Interest Amount for Overdue Invoice'),
             ('move_id', '=', self.id)], limit=1)
        if interest_line:
            self.invoice_line_ids = ([(2, interest_line.id, 0)])
        self.interest_calculated_period = False

    @api.onchange('invoice_payment_term_id', 'invoice_line_ids', 'invoice_date_due')
    def _onchange_invoice_payment_term_id(self):
        """Method for removing interest from Invoice when user changes dependent values of interest."""
        for rec in self:
            if rec.move_type == 'out_invoice':
                rec.interest_amount = 0
                interest_line = rec.invoice_line_ids.search(
                    [('name', '=', 'Interest Amount for Overdue Invoice')], limit=1)
                if interest_line:
                    rec.invoice_line_ids = ([(2, interest_line.id, 0)])
                rec.interest_calculated_period = False
            return

    link_invoice = fields.Boolean(string="Select", help="Invoices that need to be linked")

    def action_unlink_invoice(self):
        """
        This method unlinks invoice from sale orders.
        """
        for invoice in self:
            invoice.line_ids.sale_line_ids = False

    def action_open_invoices(self):
        return self.env['sale.order'].action_open_invoices()

    def _post(self, soft=True):
        """Post/Validate the documents."""
        for invoice in self.filtered(lambda move: move.is_invoice(include_receipts=True)):
            if not invoice.invoice_date and invoice.is_purchase_document(include_receipts=True):
                invoice.invoice_date = fields.Date.context_today(self)
        return super(AccountMove, self)._post(soft)


class AccountPaymentTerms(models.Model):
    """ Module for extending account.payment.term model to add interest
    computation configuration features for computation of Interest in overdue
    invoices."""

    _inherit = "account.payment.term"

    interest_overdue_act = fields.Boolean(default=False,
                                          string="Interest on Overdue Invoices",
                                          help="Activate Interest computation for this Payment Term.")
    interest_type = fields.Selection(string='Interest Type', default='daily', copy=False,
                                     help="Base duration for interest calculation",
                                     selection=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')])
    interest_percentage = fields.Float(string="Interest Percentage",
                                       default="0", digits=(12, 6),
                                       help="Interest percentage ratio per selected Interest type duration.")
    interest_account_id = fields.Many2one('account.account',
                                          string='Account for Interest',
                                          company_dependent=True,
                                          domain="[('deprecated', '=', False), ('internal_group', '=','income')]",
                                          help="Account used for creating accounting entries.")

    @api.constrains('interest_percentage')
    def _check_interest_percentage(self):
        """ check constrains for validating the interest rate in percentage is not negative"""
        for rec in self:
            if rec.interest_overdue_act and rec.interest_percentage <= 0:
                raise ValidationError(_('Enter Positive value as Interest percentage'))


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    asset_category_id = fields.Many2one('account.asset.category',
                                        string='Asset Category')
    asset_start_date = fields.Date(string='Asset Start Date',
                                   compute='_get_asset_date', readonly=True,
                                   store=True)
    asset_end_date = fields.Date(string='Asset End Date',
                                 compute='_get_asset_date', readonly=True,
                                 store=True)
    asset_mrr = fields.Float(string='Monthly Recurring Revenue',
                             compute='_get_asset_date',
                             readonly=True, digits='Account',
                             store=True)

    loan_id = fields.Many2one('hr.loan', string='Loan Id',
                              help="Loan id on invoice line")

    product_image = fields.Binary(related='product_id.image_1920',
                                  string="Product Image", help="Product image")

    @api.depends('asset_category_id', 'move_id.invoice_date')
    def _get_asset_date(self):
        """Returns the asset_start_date and the asset_end_date of the Asset"""
        for record in self:
            record.asset_mrr = 0
            record.asset_start_date = False
            record.asset_end_date = False
            cat = record.asset_category_id
            if cat:
                if cat.method_number == 0 or cat.method_period == 0:
                    raise UserError(_(
                        'The number of depreciations or the period length of your asset category cannot be null.'))
                months = cat.method_number * cat.method_period
                if record.move_id in ['out_invoice', 'out_refund']:
                    record.asset_mrr = record.price_subtotal_signed / months
                if record.move_id.invoice_date:
                    start_date = datetime.strptime(
                        str(record.move_id.invoice_date), DF).replace(day=1)
                    end_date = (start_date + relativedelta(months=months,
                                                           days=-1))
                    record.asset_start_date = start_date.strftime(DF)
                    record.asset_end_date = end_date.strftime(DF)

    def asset_create(self):
        """Create function for the asset and its associated properties"""
        for record in self:
            if record.asset_category_id:
                vals = {
                    'name': record.name,
                    'code': record.move_id.name or False,
                    'category_id': record.asset_category_id.id,
                    'value': record.price_subtotal,
                    'partner_id': record.partner_id.id,
                    'company_id': record.move_id.company_id.id,
                    'currency_id': record.move_id.company_currency_id.id,
                    'date': record.move_id.invoice_date,
                    'invoice_id': record.move_id.id,
                }
                changed_vals = record.env[
                    'account.asset.asset'].onchange_category_id_values(
                    vals['category_id'])
                vals.update(changed_vals['value'])
                asset = record.env['account.asset.asset'].create(vals)
                if record.asset_category_id.open_asset:
                    asset.validate()
        return True

    @api.depends('asset_category_id')
    def onchange_asset_category_id(self):
        """On change function based on the category and its updates the
        account status"""
        if self.move_id.move_type == 'out_invoice' and self.asset_category_id:
            self.account_id = self.asset_category_id.account_asset_id.id
        elif self.move_id.move_type == 'in_invoice' and self.asset_category_id:
            self.account_id = self.asset_category_id.account_asset_id.id

    @api.onchange('product_id')
    def _onchange_uom_id(self):
        """Onchange function for product that's call the UOM compute function
         and the asset category function"""
        result = super(AccountInvoiceLine, self)._compute_product_uom_id()
        self.onchange_asset_category_id()
        return result

    @api.depends('product_id')
    def _onchange_product_id(self):
        """Onchange product values and it's associated with the move types"""
        vals = super(AccountInvoiceLine, self)._compute_price_unit()
        if self.product_id:
            if self.move_id.move_type == 'out_invoice':
                self.asset_category_id = self.product_id.product_tmpl_id.deferred_revenue_category_id
            elif self.move_id.move_type == 'in_invoice':
                self.asset_category_id = self.product_id.product_tmpl_id.asset_category_id
        return vals

    def _set_additional_fields(self, invoice):
        """The function adds additional fields that based on the invoice
        move types"""
        if not self.asset_category_id:
            if invoice.type == 'out_invoice':
                self.asset_category_id = self.product_id.product_tmpl_id.deferred_revenue_category_id.id
            elif invoice.type == 'in_invoice':
                self.asset_category_id = self.product_id.product_tmpl_id.asset_category_id.id
            self.onchange_asset_category_id()
        super(AccountInvoiceLine, self)._set_additional_fields(invoice)

    def get_invoice_line_account(self, type, product, fpos, company):
        """"It returns the invoice line and callback"""
        return product.asset_category_id.account_asset_id or super(
            AccountInvoiceLine, self).get_invoice_line_account(type, product,
                                                               fpos, company)

    @api.model
    def _query_get(self, domain=None):
        """Used to add domain constraints to the query"""
        self.check_access_rights('read')

        context = dict(self._context or {})
        domain = domain or []
        if not isinstance(domain, (list, tuple)):
            domain = ast.literal_eval(domain)

        date_field = 'date'
        if context.get('aged_balance'):
            date_field = 'date_maturity'
        if context.get('date_to'):
            domain += [(date_field, '<=', context['date_to'])]
        if context.get('date_from'):
            if not context.get('strict_range'):
                domain += ['|', (date_field, '>=', context['date_from']),
                           ('account_id.include_initial_balance', '=', True)]
            elif context.get('initial_bal'):
                domain += [(date_field, '<', context['date_from'])]
            else:
                domain += [(date_field, '>=', context['date_from'])]

        if context.get('journal_ids'):
            domain += [('journal_id', 'in', context['journal_ids'])]

        state = context.get('state')
        if state and state.lower() != 'all':
            domain += [('parent_state', '=', state)]

        if context.get('company_id'):
            domain += [('company_id', '=', context['company_id'])]
        elif context.get('allowed_company_ids'):
            domain += [('company_id', 'in', self.env.companies.ids)]
        else:
            domain += [('company_id', '=', self.env.company.id)]

        if context.get('reconcile_date'):
            domain += ['|', ('reconciled', '=', False), '|',
                       ('matched_debit_ids.max_date', '>', context['reconcile_date']),
                       ('matched_credit_ids.max_date', '>', context['reconcile_date'])]

        if context.get('account_tag_ids'):
            domain += [('account_id.tag_ids', 'in', context['account_tag_ids'].ids)]

        if context.get('account_ids'):
            domain += [('account_id', 'in', context['account_ids'].ids)]

        if context.get('analytic_tag_ids'):
            domain += [('analytic_tag_ids', 'in', context['analytic_tag_ids'].ids)]

        if context.get('analytic_account_ids'):
            domain += [('analytic_account_id', 'in', context['analytic_account_ids'].ids)]

        if context.get('partner_ids'):
            domain += [('partner_id', 'in', context['partner_ids'].ids)]

        if context.get('partner_categories'):
            domain += [('partner_id.category_id', 'in', context['partner_categories'].ids)]

        where_clause = ""
        where_clause_params = []
        tables = ''
        if domain:
            domain.append(('display_type', 'not in', ('line_section', 'line_note')))
            domain.append(('parent_state', '!=', 'cancel'))

            query = self._where_calc(domain)

            # Wrap the query with 'company_id IN (...)' to avoid bypassing company access rights.
            self._apply_ir_rules(query)

            tables, where_clause, where_clause_params = query.get_sql()
        return tables, where_clause, where_clause_params

    def _check_amls_exigibility_for_reconciliation(self, shadowed_aml_values=None):
        for aml in self:
            if aml.parent_state != 'posted':
                aml.parent_state = 'posted'

        return super(AccountInvoiceLine, self)._check_amls_exigibility_for_reconciliation(shadowed_aml_values)

    # Account Reconciliation
    invoice_due_date = fields.Date('Invoice Due Date',
                                   related="move_id.invoice_date_due",
                                   readonly=True,
                                   )

    def action_reconcile_manually(self):
        if not self:
            return {}
        accounts = self.mapped("account_id")
        if len(accounts) > 1:
            raise ValidationError(
                _("You can only reconcile journal items belonging to the same account.")
            )
        partner = self.mapped("partner_id")
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "accounting_base_kit.account_account_reconcile_act_window"
        )
        action["domain"] = [("account_id", "=", self.mapped("account_id").id)]
        if len(partner) == 1:
            action["domain"] += [("partner_id", "=", partner.id)]
        action["context"] = self.env.context.copy()
        action["context"]["default_account_move_lines"] = self.filtered(
            lambda r: not r.reconciled
        ).ids
        return action

    followup_line_id = fields.Many2one('followup.lines', 'Follow-Up Level')
    followup_date = fields.Date('Latest Follow-Up')
    result = fields.Float(compute='_get_result', string="Balance Amount")

    def _get_result(self):
        for aml in self:
            aml.result = aml.debit - aml.credit

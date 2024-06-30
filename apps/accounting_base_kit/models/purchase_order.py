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
from itertools import groupby
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    """ Extends the 'purchase.order' model to support digital signatures
        on invoices."""
    _inherit = "purchase.order"

    partner_contact_person_id = fields.Many2one('res.partner', string="Contact Person", readonly=False)

    qr = fields.Binary(string='QR Code')

    @api.model
    def _default_show_sign(self):
        """Get the default value for the 'Show Digital Signature' field on
        invoices."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.is_show_digital_sign_po')

    @api.model
    def _default_enable_sign(self):
        """Get the default value for the 'Enable Digital Signature Options'
        field on invoices."""
        return self.env['ir.config_parameter'].sudo().get_param('accounting_base_kit.is_enable_options_po')

    digital_sign = fields.Binary(string='Signature',
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
                                       help="Determines whether the digital signature should be displayed on invoices.")
    is_enable_others = fields.Boolean(string="Enable Others",
                                      default=_default_enable_sign,
                                      compute='_compute_enable_others',
                                      help="Enables various digital signature options on invoices.")

    def button_confirm(self):
        """Overriding confirm button to add user error if signature is
        missing"""
        res = super(PurchaseOrder, self).button_confirm()
        if self.env['ir.config_parameter'].sudo().get_param(
                'accounting_base_kit.is_confirm_sign_po') and \
                self.digital_sign is False:
            raise UserError(_("Signature is missing"))
        return res

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

    number_to_words = fields.Char(string="Amount in Words: ",
                                  compute='_compute_number_to_words',
                                  help="To showing total amount in words")

    def _compute_number_to_words(self):
        """Compute the amount to words in Purchase Order"""
        for rec in self:
            rec.number_to_words = rec.currency_id.amount_to_text(
                rec.amount_total)

    automate_print_bills = fields.Boolean(string='Create Bills',
                                          help="Create bills with purchase orders")

    @api.model_create_multi
    def create(self, vals_list):
        """Super the method create to confirm RFQ"""
        res = super(PurchaseOrder, self).create(vals_list)
        automate_purchase = self.env['ir.config_parameter'].sudo().get_param('automate_purchase')
        automate_bills = self.env['ir.config_parameter'].sudo().get_param('automate_bills')
        automate_print_bills = self.env['ir.config_parameter'].sudo().get_param('automate_print_bills')
        if automate_print_bills:
            res.automate_print_bills = True
        if automate_purchase:
            res.button_confirm()
            if automate_bills:
                for rec in vals_list.get('order_line'):
                    product = self.env['product.product'].search(
                        [('id', '=', rec[2].get('product_id'))])
                    if product.invoice_policy == 'delivery':
                        raise ValidationError(
                            _("Please choose only ordered invoicing policy products."))

                res.action_create_invoice()
        res.action_gen_qrcode()
        return res

    def action_gen_qrcode(self):
        purchase_order_share_link_res = self.get_base_url() + self._get_share_url(redirect=True)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(purchase_order_share_link_res)
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_image = base64.b64encode(temp.getvalue())
        self.qr = qr_image
        return purchase_order_share_link_res

    def action_print_bill(self):
        """Function to Print Bill"""
        return self.env.ref('account.account_invoices').report_action(self.invoice_ids)

    def action_send_whatsapp(self):
        """ Action for sending whatsapp message."""
        compose_form_id = self.env.ref(
            'accounting_base_kit.whatsapp_send_message_view_form').id
        ctx = dict(self.env.context)
        message = ("Hi " + str(self.partner_id.name) + ", \n" +
                   "Here is our RFQ: " + str(self.name) + " amounting " +
                   self.currency_id.symbol + str(self.amount_total) + " is ready for your review. \n" +
                   "Please send back to us your quotation, with your best prices for the items listed \n" +
                   "Do not hesitate to contact us, if you have any questions." + "\n\n\n" +
                   "Please follow this link to access your RFQ directly:" + "\n" +self.action_gen_qrcode())
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
        """ Check if the selected purchase orders belong to the same customer."""
        partners = groupby(partner_ids)
        return next(partners, True) and not next(partners, False)

    def action_whatsapp_multi(self):
        """
        Initiate WhatsApp messaging for multiple purchase orders and open a message
        composition wizard.
        """
        purchase_order_ids = self.env['purchase.order'].browse(self.env.context.get('active_ids'))
        partner_ids = []
        for purchase in purchase_order_ids:
            partner_ids.append(purchase.partner_id.id)
        partner_check = self.check_customers(partner_ids)
        if partner_check:
            purchase_numbers = purchase_order_ids.mapped('name')
            purchase_numbers = "\n".join(purchase_numbers)
            compose_form_id = self.env.ref(
                'accounting_base_kit.whatsapp_send_message_view_form').id
            ctx = dict(self.env.context)
            message = ("Hi" + " " + self.partner_id.name + "," + "\n" +
                       "Your RFQs are: \n" + purchase_numbers + " " + "\n" +
                       "Are ready for your review and prompt action. " + "\n" +
                       "Do not hesitate to contact us, if you have any questions.")
            ctx.update({
                'default_message': message,
                'default_partner_id': purchase_order_ids[0].partner_id.id,
                'default_mobile': purchase_order_ids[0].partner_id.mobile,
                'default_image_1920': purchase_order_ids[0].partner_id.image_1920,
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
                ' vendors. Please select orders from a single vendor.'))

    # Purchase Order Payment Status
    payment_status = fields.Char(string="Payment Status", compute="_compute_payment_status",
                                 help="Field to check the payment status of the purchase order")
    payment_details = fields.Binary(string="Payment Details", compute="_compute_payment_details",
                                    help="Shows the payment done details including date and amount")
    amount_due = fields.Float(string="Amount Due", compute="_compute_amount_due",
                              help="Shows the amount that in due for the corresponding purchase order")
    invoice_state = fields.Char(string="Invoice State", compute="_compute_invoice_state",
                                help="Field to check the invoice state of purchase order")

    @api.depends('invoice_ids')
    def _compute_payment_status(self):
        """ The function will compute the payment status of the purchase order, if
        an invoice is created for the corresponding purchase order.Payment status
        will be either in paid,not paid,partially paid, reversed etc."""
        for order in self:
            order.payment_status = 'No Invoice'
            payment_states = order.invoice_ids.mapped('payment_state')
            status_length = len(payment_states)
            if 'partial' in payment_states:
                order.payment_status = 'Partially Paid'
            elif 'not_paid' in payment_states and any(
                    (True for x in ['paid', 'in_payment', 'partial'] if
                     x in payment_states)):
                order.payment_status = 'Partially Paid'
            elif 'not_paid' in payment_states and status_length == \
                    payment_states.count('not_paid'):
                order.payment_status = 'Not Paid'
            elif 'paid' in payment_states and status_length == \
                    payment_states.count('paid') and order.amount_due == 0:
                order.payment_status = 'Paid'
            elif 'paid' in payment_states and status_length == \
                    payment_states.count('paid') and order.amount_due != 0:
                order.payment_status = 'Partially Paid'
            elif 'in_payment' in payment_states and status_length == \
                    payment_states.count('in_payment'):
                order.payment_status = 'In Payment'
            elif 'reversed' in payment_states and status_length == \
                    payment_states.count('reversed'):
                order.payment_status = 'Reversed'
            else:
                order.payment_status = 'No Invoice'

    @api.depends('invoice_ids')
    def _compute_invoice_state(self):
        """ The function will compute the state of the invoice, Once an invoice is existing in a purchase order. """
        for rec in self:
            rec.invoice_state = 'No Invoice'
            for order in rec.invoice_ids:
                if order.state == 'posted':
                    rec.invoice_state = 'posted'
                elif order.state != 'posted':
                    rec.invoice_state = 'draft'
                else:
                    rec.invoice_state = 'No Invoice'

    @api.depends('invoice_ids')
    def _compute_amount_due(self):
        """The function is used to compute the amount due from the invoice and if payment is registered."""

        for rec in self:
            amount_due = 0
            for order in rec.invoice_ids:
                amount_due = amount_due + (order.amount_total - order.amount_residual)
            rec.amount_due = rec.amount_total - amount_due

    def action_open_business_doc(self):
        """ This method is intended to be used in the context of an account.move record.
        It retrieves the associated payment record and opens it in a new window.

        :return: A dictionary describing the action to be performed.
        :rtype: dict """
        name = _("Journal Entry")
        move = self.env['account.move'].browse(self.id)
        res_model = 'account.payment'
        res_id = move.payment_id.id
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': res_model,
            'res_id': res_id,
            'target': 'current',
        }

    def js_remove_outstanding_partial(self, partial_id):
        """ Called by the 'payment' widget to remove a reconciled entry to the present invoice.

        :param partial_id: The id of an existing partial reconciled with the
        current invoice.
        """
        self.ensure_one()
        partial = self.env['account.partial.reconcile'].browse(partial_id)
        return partial.unlink()

    @api.depends('invoice_ids')
    def _compute_payment_details(self):
        """ Compute the payment details from invoices and added into the purchase order form view. """
        for rec in self:
            payment = []
            rec.payment_details = False
            if rec.invoice_ids:
                for line in rec.invoice_ids:
                    if line.invoice_payments_widget:
                        for pay in line.invoice_payments_widget['content']:
                            payment.append(pay)
                for line in rec.invoice_ids:
                    if line.invoice_payments_widget:
                        payment_line = line.invoice_payments_widget
                        payment_line['content'] = payment
                        rec.payment_details = payment_line
                        break
                    rec.payment_details = False

    def action_register_payment(self):
        """ Open the account.payment.register wizard to pay the selected journal entries.

        :return: An action opening the account.payment.register wizard.
        """
        self.ensure_one()
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.invoice_ids.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    available_qty = fields.Float(string="Available Qty", compute='compute_available_qty')

    @api.depends('product_id')
    def compute_available_qty(self):
        for line in self:
            if line.product_id:
                line.available_qty = line.product_id.qty_available
            else:
                line.available_qty = 0

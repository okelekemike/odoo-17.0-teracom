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
from itertools import groupby as _groupby
from odoo import fields, models, api, _
from odoo.tools import format_amount, float_compare
from odoo.tools.misc import groupby
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta
from odoo.addons.sale_stock.models.sale_order_line import SaleOrderLine
from odoo.addons.stock.models.stock_move import StockMove


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_contact_person_id = fields.Many2one('res.partner', string="Contact Person", readonly=False)

    qr = fields.Binary(string='QR Code')

    # Sale Order Dashboard
    @api.model
    def get_dashboard_values(self):
        """This method returns values to the dashboard in sale order views."""
        result = {
            'total_orders': 0,
            'draft_orders': 0,
            'sale_orders': 0,
            'my_orders': 0,
            'my_draft_orders': 0,
            'my_sale_orders': 0,
            'total_sale_amount': 0,
            'total_draft_amount': 0,
            'my_total_sale_amount': 0,
            'my_total_draft_amount': 0,
        }
        sale_order = self.env['sale.order']
        user = self.env.user
        result['total_orders'] = sale_order.search_count([])
        result['draft_orders'] = sale_order.search_count(
            [('state', 'in', ['draft', 'sent'])])
        result['sale_orders'] = sale_order.search_count(
            [('state', 'in', ['sale', 'done'])])
        result['my_orders'] = sale_order.search_count(
            [('user_id', '=', user.id)])
        result['my_draft_orders'] = sale_order.search_count(
            [('user_id', '=', user.id), ('state', 'in', ['draft', 'sent'])])
        result['my_sale_orders'] = sale_order.search_count(
            [('user_id', '=', user.id), ('state', 'in', ['sale', 'done'])])

        order_sum = """select sum(amount_total) from sale_order where state 
        in ('sale', 'done') and company_id=%s""" % (self.env.company.id)
        self._cr.execute(order_sum)
        res = self.env.cr.fetchone()
        result['total_sale_amount'] = format_amount(self.env, res[0] or 0, self.env.company.currency_id)
        draft_sum = """select sum(amount_total) from sale_order where state 
        in ('draft', 'sent') and company_id=%s""" % (self.env.company.id)
        self._cr.execute(draft_sum)
        res = self.env.cr.fetchone()
        result['total_draft_amount'] = format_amount(self.env, res[0] or 0, self.env.company.currency_id)

        my_order_sum = """select sum(amount_total) from sale_order where state 
        in ('sale', 'done') and company_id=%s and user_id=%s""" % (self.env.company.id, user.id)
        self._cr.execute(my_order_sum)
        res = self.env.cr.fetchone()
        result['my_total_sale_amount'] = format_amount(self.env, res[0] or 0, self.env.company.currency_id)
        my_draft_sum = """select sum(amount_total) from sale_order where state 
        in ('draft', 'sent') and company_id=%s and user_id=%s""" % (self.env.company.id, user.id)
        self._cr.execute(my_draft_sum)
        res = self.env.cr.fetchone()
        result['my_total_draft_amount'] = format_amount(self.env, res[0] or 0, self.env.company.currency_id)
        return result

    number_to_words = fields.Char(string="Amount in Words: ",
                                  compute='_compute_number_to_words',
                                  help="To showing total amount in words")

    def _compute_number_to_words(self):
        """Compute the amount to words in Sale Order"""
        for rec in self:
            rec.number_to_words = rec.currency_id.amount_to_text(
                rec.amount_total)

    def action_send_whatsapp(self):
        """ Action for sending whatsapp message."""
        compose_form_id = self.env.ref(
            'accounting_base_kit.whatsapp_send_message_view_form').id
        ctx = dict(self.env.context)
        message = ("Hi " + str(self.partner_id.name) + ", \n" +
                   "Here is your Quotation: " + str(self.name) + " amounting " +
                   self.currency_id.symbol + str(self.amount_total) + " is ready for review. \n" +
                   "Do not hesitate to contact us, if you have any questions." + "\n\n\n" +
                   "Please follow this link to access your quotation directly:" + "\n" +
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
        """ Check if the selected sale orders belong to the same customer."""
        partners = _groupby(partner_ids)
        return next(partners, True) and not next(partners, False)

    def action_whatsapp_multi(self):
        """
        Initiate WhatsApp messaging for multiple sale orders and open a message
        composition wizard.
        """
        sale_order_ids = self.env['sale.order'].browse(
            self.env.context.get('active_ids'))
        partner_ids = []
        for sale in sale_order_ids:
            partner_ids.append(sale.partner_id.id)
        partner_check = self.check_customers(partner_ids)
        if partner_check:
            sale_numbers = sale_order_ids.mapped('name')
            sale_numbers = "\n".join(sale_numbers)
            compose_form_id = self.env.ref(
                'accounting_base_kit.whatsapp_send_message_view_form').id
            ctx = dict(self.env.context)
            message = ("Hi" + " " + self.partner_id.name + "," + "\n" +
                       "Your Orders are: \n" + sale_numbers + " " + "\n" +
                       "Are ready for your review and prompt action. " + "\n" +
                       "Do not hesitate to contact us, if you have any questions.")
            ctx.update({
                'default_message': message,
                'default_partner_id': sale_order_ids[0].partner_id.id,
                'default_mobile': sale_order_ids[0].partner_id.mobile,
                'default_image_1920': sale_order_ids[0].partner_id.image_1920,
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

    automate_print_invoices = fields.Boolean(string='Print Invoices',
                                             help="Print invoices for corresponding purchase orders")

    @api.model_create_multi
    def create(self, vals_list):
        """
            Super the method create to confirm quotation, create and validate
            invoice
        """

        res = super(SaleOrder, self).create(vals_list)
        automate_sale = self.env['ir.config_parameter'].sudo().get_param('automate_sale')
        automate_invoice = self.env['ir.config_parameter'].sudo().get_param('automate_invoice')
        automate_print_invoices = self.env['ir.config_parameter'].sudo().get_param('automate_print_invoices')
        automate_validate_invoice = self.env['ir.config_parameter'].sudo().get_param('automate_validate_invoice')
        if automate_print_invoices:
            res.automate_print_invoices = True
        if automate_sale:
            res.action_confirm()
            if automate_invoice:
                for rec in vals_list[0].get('order_line'):
                    product = self.env['product.template'].search(
                        [('id', '=', rec[2].get('product_template_id'))])
                    if product.invoice_policy == 'delivery':
                        raise ValidationError(
                            _("Please choose only ordered invoicing policy products."))

                res._create_invoices()
                if automate_validate_invoice:
                    res.invoice_ids.action_post()
        res.action_gen_qrcode()
        return res

    def action_gen_qrcode(self):
        sale_order_share_link_res = self.get_base_url() + self._get_share_url(redirect=True)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(sale_order_share_link_res)
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_image = base64.b64encode(temp.getvalue())
        self.qr = qr_image
        return sale_order_share_link_res

    def action_print_invoice(self):
        """Method to print invoice"""
        return self.env.ref('account.account_invoices').report_action(self.invoice_ids)

    payment_status = fields.Char(string="Payment Status", compute="_compute_payment_status",
                                 help="Field to check the payment status of the sale order")
    payment_details = fields.Binary(string="Payment Details", compute="_compute_payment_details",
                                    help="Shows the payment done details including date and amount")
    amount_due = fields.Float(string="Amount Due", compute='_compute_amount_due',
                              help="Shows the amount that in due for the corresponding sale order")
    invoice_state = fields.Char(string="Invoice State", compute="_compute_invoice_state",
                                help="Field to check the invoice state of sale order")

    @api.depends('invoice_ids')
    def _compute_payment_status(self):
        """ The function will compute the payment status of the sale order, if
        an invoice is created for the corresponding sale order.Payment status
        will be either in paid,not paid,partially paid, reversed etc."""
        for order in self:
            order.payment_status = 'No Invoice'
            payment_states = order.invoice_ids.mapped('payment_state')
            status_length = len(payment_states)
            if 'partial' in payment_states:
                order.payment_status = 'Partially Paid'
            elif 'not_paid' in payment_states and any(
                    (True for x in ['paid', 'in_payment', 'partial'] if x in payment_states)):
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
        """ The function will compute the state of the invoice , Once an invoice
        is existing in a sale order. """
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
        """The function is used to compute the amount due from the invoice and
        if payment is registered."""
        for rec in self:
            amount_due = 0
            for order in rec.invoice_ids:
                amount_due = amount_due + (order.amount_total -
                                           order.amount_residual)
            rec.amount_due = rec.amount_total - amount_due

    def action_open_business_doc(self):
        """ This method is intended to be used in the context of an
        account.move record.
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
        """ Called by the 'payment' widget to remove a reconciled entry to the
        present invoice.

        :param partial_id: The id of an existing partial reconciled with the
        current invoice.
        """
        self.ensure_one()
        partial = self.env['account.partial.reconcile'].browse(partial_id)
        return partial.unlink()

    @api.depends('invoice_ids')
    def _compute_payment_details(self):
        """ Compute the payment details from invoices and added into the sale
        order form view. """
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
        """ Open the account.payment.register wizard to pay the selected journal
         entries.
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

    def action_open_invoices(self):
        """
        This method opens a new window to link invoices and remove invoices
        for the current sale order.
        """
        partner_invoices = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('sale_order_count', '=', 0)
        ])
        return {
            "type": "ir.actions.act_window",
            "name": "Link and Remove Invoices",
            "view_mode": "form",
            "res_model": "link.invoice",
            "target": "new",
            "context": {
                'default_invoice_ids': [(6, 0, partner_invoices.ids)],
                'default_sale_order_id': self.id
            }
        }

    delivery_split = fields.Boolean(
        string='Split Delivery',
        help='Enable the option to add recipients to each sale order line to split delivery')
    is_consolidate = fields.Boolean(
        string='Consolidate Orders', default=True,
        help='Enable the option to consolidate orders, if same recipients are selected in split delivery')

    @api.onchange("partner_id")
    def _onchange_product_template_id(self):
        """ Update recipients in order lines with the customer of sale order
        is changed """
        if self.delivery_split:
            for line in self.order_line:
                line.recipient_id = self.partner_id.id


class SaleOrderLine(models.Model):
    """ Inherits model 'sale.order.line' and added field 'recipient'  """
    _inherit = 'sale.order.line'

    recipient_id = fields.Many2one('res.partner', string='Recipient',
                                   help='Choose a recipient for split delivery',
                                   domain=['|',
                                           ('company_id', '=', lambda self: self.env.company.id),
                                           ('company_id', '=', False)])

    @api.onchange("product_template_id")
    def _onchange_product_template_id(self):
        """Update recipients in order lines with the customer of sale order as
        default recipient"""
        if self.order_id.delivery_split:
            for line in self:
                if not line.recipient_id:
                    line.recipient_id = self.order_id.partner_id.id

    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be
        created from a stock rule coming from a sale order line. This method
        could be override in order to add other custom key that could be used
        in move/po creation."""
        date_deadline = self.order_id.commitment_date or (
                self.order_id.date_order + timedelta(days=self.customer_lead or 0.0)
        )
        date_planned = date_deadline - timedelta(days=self.order_id.company_id.security_lead)
        values = {
            'group_id': group_id,
            'sale_line_id': self.id,
            'date_planned': date_planned,
            'date_deadline': date_deadline,
            'route_ids': self.route_id,
            'warehouse_id': self.order_id.warehouse_id or False,
            'product_description_variants': self.with_context(
                lang=self.order_id.partner_id.lang)._get_sale_order_line_multiline_description_variants(),
            'company_id': self.order_id.company_id,
            'product_packaging_id': self.product_packaging_id,
            'sequence': self.sequence,
        }
        if not self.recipient_id:
            self.recipient_id = self.order_id.partner_id.id
        if self.order_id.delivery_split:
            values.update({"partner_id": self.recipient_id.id})
        return values

    SaleOrderLine._prepare_procurement_values = _prepare_procurement_values

    available_qty = fields.Float(string="Available Qty", compute='compute_available_qty')

    @api.depends('product_id')
    def compute_available_qty(self):
        for line in self:
            available_quantity = self.env['stock.quant']._get_available_quantity(
                line.product_id,
                line.warehouse_id.lot_stock_id,
                allow_negative=True)
            line.available_qty = available_quantity


class StockMove(models.Model):
    """inheriting the stock move model"""
    _inherit = 'stock.move'

    def _assign_picking(self):
        """ Try to assign the moves to an existing picking that has not been
        reserved yet and has the same procurement group, locations and picking
        type (moves should already have them identical). Otherwise, create a
        new picking to assign them to. """
        grouped_moves = groupby(self, key=lambda m: m._key_assign_picking())
        for group, moves in grouped_moves:
            moves = self.env['stock.move'].concat(*moves)
            new_picking = False
            # Could pass the arguments contained in group but they are the same
            # for each move that why moves[0] is acceptable
            picking = moves[0]._search_picking_for_assignation()
            if picking:
                # If a picking is found, we'll append `move` to its move list
                # and thus its `partner_id` and `ref` field will refer to
                # multiple records.
                # In this case, we chose to wipe them.
                vals = {}
                if any(picking.partner_id.id != m.partner_id.id for m in moves):
                    vals['partner_id'] = False
                if any(picking.origin != m.origin for m in moves):
                    vals['origin'] = False
                if vals:
                    picking.write(vals)
            else:
                # Don't create picking for negative moves since they will be
                # reverse and assign to another picking
                moves = moves.filtered(lambda m: float_compare(
                    m.product_uom_qty, 0.0, precision_rounding=
                    m.product_uom.rounding) >= 0)
                if not moves:
                    continue
                new_picking = True
                pick_values = moves._get_new_picking_values()
                sale_order = self.env['sale.order'].search([
                    ('name', '=', pick_values['origin'])])
                if sale_order.delivery_split and not sale_order.is_consolidate:
                    for move in moves:
                        picking = picking.create(move._get_new_picking_values())
                        move.write({'picking_id': picking.id})
                        move._assign_picking_post_process(new=new_picking)
                elif sale_order.delivery_split and sale_order.is_consolidate:
                    move_line = sorted(moves, key=lambda x: x.partner_id.id)
                    for partner_id, lines in groupby(move_line, key=lambda x: x.partner_id):
                        new_moves = self.env['stock.move'].concat(*lines)
                        picking = picking.create(
                            new_moves._get_new_picking_values())
                        new_moves.write({'picking_id': picking.id})
                        new_moves._assign_picking_post_process(new=new_picking)

                else:
                    picking = picking.create(moves._get_new_picking_values())
                    moves.write({'picking_id': picking.id, 'partner_id': sale_order.partner_id.id})
                    moves._assign_picking_post_process(new=new_picking)
        return True

    StockMove._assign_picking = _assign_picking

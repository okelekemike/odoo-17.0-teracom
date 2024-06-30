# -*- coding: utf-8 -*-

from odoo import api, fields, models


class HrPayslip(models.Model):
    """Class for HR Payslip"""
    _inherit = 'hr.payslip'

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        """This function calculates the additional inputs
         for the employee payslip."""
        res = super(HrPayslip, self).get_inputs(contracts, date_from, date_to)
        amount_employee = 0
        employee_id = self.env['hr.contract'].browse(contracts.id).employee_id
        pantry_lines = self.env['pantry.order'].search([
            ('partner_id', '=', employee_id.user_id.partner_id.id)
        ])
        for adv_obj in pantry_lines:
            if self.date_from <= adv_obj.date_order.date() <= self.date_to:
                amount_employee += adv_obj.amount_total
                for result in res:
                    result['amount'] = amount_employee
        return res


class PantryOrder(models.Model):
    """A class that represents a new model pantry order"""
    _name = 'pantry.order'
    _description = 'Pantry Order'
    _inherit = 'mail.thread'

    name = fields.Char(string='Order Sequence', readonly=True,
                       help='Sequence of the order')
    partner_id = fields.Many2one('res.partner', string='Order User',
                                 default=lambda self: self.env.user.partner_id,
                                 help='The user who is ordering')
    state = fields.Selection(string='Status', required=True,
                             selection=[('draft', 'Draft'),
                                        ('to_approve', 'Waiting For Approval'),
                                        ('approved', 'Approved'),
                                        ('refused', 'Refused'),
                                        ('confirmed', 'Confirmed')],
                             default='draft',
                             help='The current status of the order')
    date_order = fields.Datetime(string='Order Date',
                                 default=fields.Datetime.now, readonly=True,
                                 help='The date order')
    order_line_ids = fields.One2many('pantry.order.line',
                                     'pantry_order_id',
                                     string='Order Line', help="Order lines")
    amount_total = fields.Float(string='Total', compute='_compute_amount_total',
                                help='The total amount of the order')

    @api.model_create_multi
    def create(self, vals_list):
        """Sequence for the order"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('pantry.order') or 'New'
        res = super(PantryOrder, self).create(vals_list)
        return res

    @api.depends('order_line_ids')
    def _compute_amount_total(self):
        """Calculates the amount_total"""
        for rec in self:
            rec.amount_total = sum(
                rec.mapped('order_line_ids').mapped('subtotal'))

    def action_confirm_pantry_order(self):
        """Change the state to confirmed"""
        self.state = 'confirmed'

    def action_approve(self):
        """Change state to approved when approve button clicks"""
        self.state = 'approved'

    def action_reject(self):
        """Change state refused when refuse button clicks"""
        self.state = 'refused'

    def action_sent_approval(self):
        """ 'Send For Approval' button action"""
        self.state = 'to_approve'


class PantryOrderLine(models.Model):
    """A class that represents a new model pantry order line"""
    _name = 'pantry.order.line'
    _description = 'Pantry Order Line'

    pantry_order_id = fields.Many2one('pantry.order', string='Pantry Order',
                                      required=True,
                                      help='The corresponding pantry order')
    product_id = fields.Many2one('product.product', string='Product',
                                 required=True,
                                 domain=[('pantry_product', '=', True)],
                                 help='The product to order')
    quantity = fields.Float(string='Quantity',
                            help='The quantity of the product')
    unit_price = fields.Float(string='Unit Price',
                              help='The unit price of the product')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal',
                            help='The subtotal of the order line')

    @api.depends('quantity')
    def _compute_subtotal(self):
        """Calculates the subtotal"""
        for rec in self:
            rec.subtotal = rec.quantity * rec.unit_price


class ProductProduct(models.Model):
    """Class for adding quantity button on product kanban view."""
    _inherit = "product.product"

    pantry_quantity = fields.Integer(string="Quantity", help="Quantity of the product", default=1)

    def action_quantity_decrement(self):
        """Function for increment the quantity of product"""
        if self.pantry_quantity > 1:
            self.pantry_quantity -= 1

    def action_quantity_increment(self):
        """Function for decrement the quantity of product"""
        self.pantry_quantity += 1

    def action_buy_pantry(self):
        """Make a quotation while purchasing a product from the pantry."""
        quotation = self.env['pantry.order'].search(
            [('partner_id', '=', self.env.user.partner_id.id),
             ('state', '=', 'draft')], limit=1, order='date_order desc')
        val_list = {
            'product_id': self.id,
            'unit_price': self.lst_price,
            'quantity': self.pantry_quantity,
        }
        if quotation:
            val_list['pantry_order_id'] = quotation[0].id
            product = quotation.order_line_ids.filtered(
                lambda sol: sol.product_id == self)
            if product:
                product[0].quantity += self.pantry_quantity
            else:
                quotation.write(
                    {'order_line_ids': [fields.Command.create(val_list)]})
        else:
            quotation = self.env['pantry.order'].create({
                'partner_id': self.env.user.partner_id.id,
                'order_line_ids': [fields.Command.create(val_list)]
            })
        self.pantry_quantity = 1
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pantry.order',
            'res_id': quotation.id,
            'view_mode': 'form',
            'target': 'current',
            'views': [[False, "form"]],
        }


class ProductTemplate(models.Model):
    """A class that represents already existing model product template"""
    _inherit = 'product.template'

    pantry_product = fields.Boolean(string="Is Pantry Product",
                                    help='Is this a pantry product or not')


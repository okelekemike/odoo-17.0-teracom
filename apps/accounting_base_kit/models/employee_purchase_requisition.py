# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


def _get_qty_balance(cur_qty, cur_uom, mof_qty, mof_uom):
    cur_mty = cur_qty * cur_uom.ratio if cur_uom.uom_type == 'bigger' \
        else cur_qty / cur_uom.ratio if cur_uom.uom_type == 'smaller' \
        else cur_qty
    mof_mty = mof_qty * mof_uom.ratio if mof_uom.uom_type == 'bigger' \
        else mof_qty / mof_uom.ratio if mof_uom.uom_type == 'smaller' \
        else mof_qty

    return mof_mty - cur_mty


class PurchaseRequisition(models.Model):
    """Class for adding fields and functions for purchase requisition model."""
    _name = 'employee.purchase.requisition'
    _description = 'Employee Purchase Requisition'
    _inherit = "mail.thread", "mail.activity.mixin"

    name = fields.Char(
        string="Reference No", readonly=True)
    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee',
        default=lambda self: self.env.user.employee_id.id,
        required=True, help='Select an employee')
    dept_id = fields.Many2one(
        comodel_name='hr.department', string='Department',
        related='employee_id.department_id', store=True,
        help='Select an department')
    employee_received_id = fields.Many2one(
        comodel_name='hr.employee', string='Releasing Employee',
        required=True, help='Select an employee the requisition was released')
    dept_received_id = fields.Many2one(
        comodel_name='hr.department', string='Department',
        related='employee_received_id.department_id', store=True,
        help='Select an department the requisition was released')
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible',
        required=True,
        domain=lambda self: [('share', '=', False)],
        default=lambda self: self.env.user,
        help='Select a user who is responsible for requisition')
    requisition_date = fields.Date(
        string="Requisition Date",
        default=lambda self: fields.Date.today(),
        help='Date of requisition')
    receive_date = fields.Date(
        string="Received Date", readonly=True,
        help='Received date')
    requisition_deadline = fields.Date(
        string="Requisition Deadline",
        help="End date of purchase requisition")
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company',
        default=lambda self: self.env.company,
        help='Select a company')
    requisition_order_ids = fields.One2many(
        comodel_name='requisition.order',
        inverse_name='requisition_product_id',
        required=True)
    confirm_id = fields.Many2one(
        comodel_name='res.users',
        string='Confirmed By',
        default=lambda self: self.env.uid,
        readonly=True,
        help='User who confirmed the requisition.')
    manager_id = fields.Many2one(
        comodel_name='res.users',
        string='Department Manager',
        readonly=True, help='Select a department manager')
    requisition_head_id = fields.Many2one(
        comodel_name='res.users',
        string='Approved By',
        readonly=True,
        help='User who approved the requisition.')
    confirmed_date = fields.Date(
        string='Confirmed Date', readonly=True,
        help='Date of requisition confirmation')
    department_approval_date = fields.Date(
        string='Department Approval Date',
        readonly=True,
        help='Department approval date')
    approval_date = fields.Date(
        string='Approved Date', readonly=True,
        help='Requisition approval date')
    rejected_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Rejected By',
        readonly=True,
        help='User who rejected the requisition')
    reject_date = fields.Date(
        string='Rejection Date', readonly=True,
        help='Requisition rejected date')
    rejected_reason = fields.Text(
        string='Rejection Reason',
        help='Reason for rejecting the requisition')
    source_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Source Location',
        help='Source location of requisition.')
    destination_location_id = fields.Many2one(
        comodel_name='stock.location',
        string="Destination Location",
        help='Destination location of requisition.')
    delivery_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string='Delivery To',
        help='Type of delivery.')
    internal_picking_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string="Internal Picking")
    manufacturing_picking_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string="Manufacturing Picking")
    requisition_description = fields.Text(
        string="Requisition Reason",
        help="Reason for the requisition order")
    purchase_count = fields.Integer(
        string='Purchase Count',
        help='Purchase count',
        compute='_compute_purchase_count')
    manufacturing_count = fields.Integer(
        string='Manufacturing Count',
        help='Manufacturing count',
        compute='_compute_manufacturing_count')
    internal_transfer_count = fields.Integer(
        string='Internal Transfer count',
        help='Internal transfer count',
        compute='_compute_internal_transfer_count')
    root_purchase_ids = fields.One2many('purchase.order', compute='_compute_root_purchase_ids',
                                        string='Purchase Orders', readonly=True)
    root_transfer_ids = fields.One2many('stock.picking', compute='_compute_root_transfer_ids',
                                        string='Internal Transfers', readonly=True)
    root_manufacturing_ids = fields.One2many('mrp.production', compute='_compute_root_manufacturing_ids',
                                             string='Manufacturing Orders', readonly=True)

    def _compute_root_purchase_ids(self):
        for purchase in self:
            purchase.root_purchase_ids = self.env['purchase.order'].search([
                ('requisition_order', '=', self.name),
                ('receiver_id', '=', self.employee_id.id), ], order='id desc')

    def _compute_root_transfer_ids(self):
        for transfer in self:
            transfer.root_transfer_ids = self.env['stock.picking'].search([
                ('requisition_order', '=', self.name),
                ('receiver_id', '=', self.employee_id.id), ], order='id desc')

    def _compute_root_manufacturing_ids(self):
        for manufacturing in self:
            manufacturing.root_manufacturing_ids = self.env['mrp.production'].search([
                ('requisition_order', '=', self.name),
                ('receiver_id', '=', self.employee_id.id), ], order='id desc')

    state = fields.Selection(
        [('new', 'New'),
         ('waiting_department_approval', 'Waiting Department Head Approval'),
         ('waiting_head_approval', 'Waiting Requisition Manager Approval'),
         ('approved', 'Approved'),
         ('order_created', 'Picking, MO & PO Created'),
         ('received', 'Received'),
         ('cancelled', 'Cancelled')],
        default='new', copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        """Function to generate purchase requisition sequence"""
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].with_company(
                    self.company_id).next_by_code('employee.purchase.requisition') or _('New')
        result = super(PurchaseRequisition, self).create(vals_list)
        return result

    def action_confirm_requisition(self):
        """Function to confirm purchase requisition"""
        self.source_location_id = (
            self.employee_received_id.employee_location_id.id) if (
            self.employee_received_id.employee_location_id) else (
            self.employee_received_id.department_id.department_location_id.id) if (
            self.employee_received_id.department_id.department_location_id) else (
            self.env.ref('stock.stock_location_stock').id)
        self.destination_location_id = (
            self.employee_id.employee_location_id.id) if (
            self.employee_id.employee_location_id) else (
            self.employee_id.department_id.department_location_id.id) if (
            self.employee_id.department_id.department_location_id) else (
            self.env.ref('stock.stock_location_stock').id)
        self.delivery_type_id = (
            self.source_location_id.warehouse_id.in_type_id.id)
        self.internal_picking_id = (
            self.source_location_id.warehouse_id.int_type_id.id)
        self.manufacturing_picking_id = (
            self.source_location_id.warehouse_id.manu_type_id.id)
        self.write({'state': 'waiting_department_approval'})
        self.confirm_id = self.env.uid
        self.confirmed_date = fields.Date.today()

    def action_department_approval(self):
        """Approval from department"""
        self.write({'state': 'waiting_head_approval'})
        self.manager_id = self.env.uid
        self.department_approval_date = fields.Date.today()

    def action_department_cancel(self):
        """Cancellation from department """
        self.write({'state': 'cancelled'})
        self.rejected_user_id = self.env.uid
        self.reject_date = fields.Date.today()

    def action_head_approval(self):
        """Approval from department head"""
        self.write({'state': 'approved'})
        self.requisition_head_id = self.env.uid
        self.approval_date = fields.Date.today()

    def action_approval_reversal(self):
        """Reversal of approval from department head"""
        if self.state == 'approved':
            self.write({'state': 'waiting_head_approval'})
            self.requisition_head_id = False
            self.approval_date = False
        elif self.state == 'waiting_head_approval':
            self.write({'state': 'waiting_department_approval'})
            self.manager_id = False
            self.department_approval_date = False
        elif self.state == 'waiting_department_approval':
            self.write({'state': 'new'})
            self.confirm_id = False
            self.confirmed_date = False

    def action_head_cancel(self):
        """Cancellation from department head"""
        self.write({'state': 'cancelled'})
        self.rejected_user_id = self.env.uid
        self.reject_date = fields.Date.today()

    def action_create_purchase_order(self):
        """Create purchase order and internal transfer"""
        for rec in self.requisition_order_ids:
            if rec.requisition_type == 'internal_transfer':
                req_internal_transfer = self.env['stock.picking'].search([
                    ('requisition_order', '=', self.name),
                    ('receiver_id', '=', self.employee_id.id),
                    ('state', 'in', ('draft', 'done')), ], order='state desc')
                if req_internal_transfer:
                    move_qty = 0
                    move_updated = False
                    for internal_transfer in req_internal_transfer:
                        if internal_transfer.state == 'done':
                            for move in internal_transfer.move_ids_without_package:
                                move_line_balance = _get_qty_balance(rec.quantity, rec.product_id.uom_id,
                                                                     move.product_uom_qty, move.product_uom)
                                if move.product_id.id == rec.product_id.id and move_line_balance > 0:
                                    move_updated = True
                                elif move.product_id.id == rec.product_id.id and move_line_balance < 0:
                                    move_qty = move_qty + move_line_balance
                        elif internal_transfer.state == 'draft':
                            for move in internal_transfer.move_ids_without_package:
                                if move.product_id.id == rec.product_id.id:
                                    move.write({
                                        'product_uom': rec.product_id.uom_id.id,
                                        'product_uom_qty': rec.quantity - move_qty,
                                        'location_id': self.source_location_id.id,
                                        'location_dest_id': self.destination_location_id.id,
                                    })
                                    move_updated = True
                                    break
                            if not move_updated:
                                internal_transfer.write({
                                    'move_ids_without_package': [(0, 0, {
                                        'name': rec.product_id.name,
                                        'product_id': rec.product_id.id,
                                        'product_uom': rec.product_id.uom_id.id,
                                        'product_uom_qty': rec.quantity,
                                        'location_id': self.source_location_id.id,
                                        'location_dest_id': self.destination_location_id.id,
                                    })]
                                })
                                move_updated = True
                    if not move_updated:
                        self.env['stock.picking'].create({
                            'location_id': self.source_location_id.id,
                            'location_dest_id': self.destination_location_id.id,
                            'picking_type_id': self.internal_picking_id.id,
                            'requisition_order': self.name,
                            'receiver_id': self.employee_id.id,
                            'partner_id': self.employee_id.partner_id.id,
                            'move_ids_without_package': [(0, 0, {
                                'name': rec.product_id.name,
                                'product_id': rec.product_id.id,
                                'product_uom': rec.product_id.uom_id.id,
                                'product_uom_qty': rec.quantity - move_qty,
                                'location_id': self.source_location_id.id,
                                'location_dest_id': self.destination_location_id.id,
                            })]
                        })
                else:
                    self.env['stock.picking'].create({
                        'location_id': self.source_location_id.id,
                        'location_dest_id': self.destination_location_id.id,
                        'picking_type_id': self.internal_picking_id.id,
                        'requisition_order': self.name,
                        'receiver_id': self.employee_id.id,
                        'partner_id': self.employee_id.partner_id.id,
                        'move_ids_without_package': [(0, 0, {
                            'name': rec.product_id.name,
                            'product_id': rec.product_id.id,
                            'product_uom': rec.product_id.uom_id.id,
                            'product_uom_qty': rec.quantity,
                            'location_id': self.source_location_id.id,
                            'location_dest_id': self.destination_location_id.id,
                        })]
                    })
            elif rec.requisition_type == 'purchase_order':
                if not rec.partner_id:
                    raise ValidationError(_('Select a vendor'))
                req_purchase_order = self.env['purchase.order'].search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('requisition_order', '=', self.name),
                    ('receiver_id', '=', self.employee_id.id),
                    ('state', 'in', ('draft', 'done')), ], order='state desc')
                if req_purchase_order:
                    line_qty = 0
                    line_updated = False
                    for purchase_order in req_purchase_order:
                        if purchase_order.state == 'done':
                            for line in purchase_order.order_line:
                                po_line_balance = _get_qty_balance(rec.quantity, rec.product_id.uom_id,
                                                                   line.product_qty, line.product_uom)
                                if line.product_id.id == rec.product_id.id and po_line_balance > 0:
                                    line_updated = True
                                elif line.product_id.id == rec.product_id.id and po_line_balance < 0:
                                    line_qty = line_qty + po_line_balance
                        elif purchase_order.state == 'draft':
                            for line in purchase_order.order_line:
                                if line.product_id.id == rec.product_id.id:
                                    line.write({
                                        'product_qty': rec.quantity - line_qty,
                                    })
                                    line_updated = True
                                    break
                            if not line_updated:
                                purchase_order.write({
                                    'order_line': [(0, 0, {
                                        'product_id': rec.product_id.id,
                                        'product_qty': rec.quantity,
                                    })]
                                })
                                line_updated = True
                    if not line_updated:
                        self.env['purchase.order'].create({
                            'partner_id': rec.partner_id.id,
                            'requisition_order': self.name,
                            'receiver_id': self.employee_id.id,
                            'picking_type_id': self.delivery_type_id.id,
                            'order_line': [(0, 0, {
                                'product_id': rec.product_id.id,
                                'product_qty': rec.quantity - line_qty,
                                'product_uom': rec.product_id.uom_id.id,
                            })]
                        })
                else:
                    self.env['purchase.order'].create({
                        'partner_id': rec.partner_id.id,
                        'requisition_order': self.name,
                        'receiver_id': self.employee_id.id,
                        'picking_type_id': self.delivery_type_id.id,
                        'order_line': [(0, 0, {
                            'product_id': rec.product_id.id,
                            'product_qty': rec.quantity,
                            'product_uom': rec.product_id.uom_id.id,
                        })]
                    })
            elif rec.requisition_type == 'manufacturing_order':
                req_manufacturing_order = self.env['mrp.production'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('requisition_order', '=', self.name),
                    ('receiver_id', '=', self.employee_id.id),
                    ('state', 'in', ('draft', 'done')), ], order='state desc')
                if req_manufacturing_order:
                    man_order_qty = 0
                    man_order_updated = False
                    for manufacturing_order in req_manufacturing_order:
                        if manufacturing_order.state == 'done':
                            man_order_balance = _get_qty_balance(rec.quantity, rec.product_id.uom_id,
                                                                 manufacturing_order.product_qty,
                                                                 manufacturing_order.product_uom_id)
                            if man_order_balance > 0:
                                man_order_updated = True
                            else:
                                man_order_qty = man_order_qty + man_order_balance
                        elif manufacturing_order.state == 'draft' and not man_order_updated:
                            manufacturing_order.write({
                                'product_qty': rec.quantity - man_order_qty,
                                'location_src_id': self.source_location_id.id,
                                'location_dest_id': self.destination_location_id.id,
                            })
                            man_order_updated = True
                            break
                    if not man_order_updated:
                        self.env['mrp.production'].create({
                            'requisition_order': self.name,
                            'receiver_id': self.employee_id.id,
                            'product_qty': rec.quantity - man_order_qty,
                            'product_uom_id': rec.product_id.uom_id.id,
                            'product_id': rec.product_id.id,
                            'user_id': self.env.uid,
                            'location_src_id': self.source_location_id.id,
                            'location_dest_id': self.destination_location_id.id,
                            'picking_type_id': self.manufacturing_picking_id.id,
                        })
                else:
                    self.env['mrp.production'].create({
                        'requisition_order': self.name,
                        'receiver_id': self.employee_id.id,
                        'product_qty': rec.quantity,
                        'product_uom_id': rec.product_id.uom_id.id,
                        'product_id': rec.product_id.id,
                        'user_id': self.env.uid,
                        'location_src_id': self.source_location_id.id,
                        'location_dest_id': self.destination_location_id.id,
                        'picking_type_id': self.manufacturing_picking_id.id,
                    })

        self.write({'state': 'order_created'})

    def action_add_internal_transfer(self):
        requisition_orders = self.env['stock.picking'].search([
            ('picking_type_id', '=', self.internal_picking_id.id),
            ('requisition_count', '=', 0)
        ])
        return {
            "type": "ir.actions.act_window",
            "name": "Link or Remove Internal Transfers",
            "view_mode": "form",
            "res_model": "link.transfer.orders",
            "target": "new",
            "context": {
                'default_root_transfer_ids': [(6, 0, requisition_orders.ids)],
                'default_requisition_id': self.id
            }
        }

    def action_add_purchase_order(self):
        requisition_orders = self.env['purchase.order'].search([
            ('requisition_count', '=', 0)
        ])
        return {
            "type": "ir.actions.act_window",
            "name": "Link or Remove Purchase Orders",
            "view_mode": "form",
            "res_model": "link.purchase.orders",
            "target": "new",
            "context": {
                'default_root_purchase_ids': [(6, 0, requisition_orders.ids)],
                'default_requisition_id': self.id
            }
        }

    def action_add_manufacturing_order(self):
        requisition_orders = self.env['mrp.production'].search([
            ('requisition_count', '=', 0)
        ])
        return {
            "type": "ir.actions.act_window",
            "name": "Link or Remove Manufacturing Orders",
            "view_mode": "form",
            "res_model": "link.manufacturing.orders",
            "target": "new",
            "context": {
                'default_root_manufacturing_ids': [(6, 0, requisition_orders.ids)],
                'default_requisition_id': self.id
            }
        }

    def action_receive(self):
        """Received purchase requisition"""
        for rec in self.requisition_order_ids:
            if rec.requisition_type == 'internal_transfer':
                req_internal_transfer = self.env['stock.picking'].search([
                    ('requisition_order', '=', self.name),
                    ('receiver_id', '=', self.employee_id.id),
                    ('state', 'not in', ('done', 'cancel')),
                ])
                if req_internal_transfer:
                    raise ValidationError('Internal transfer orders are still in process')
            elif rec.requisition_type == 'purchase_order':
                req_purchase_order = self.env['purchase.order'].search([
                    ('requisition_order', '=', self.name),
                    ('receiver_id', '=', self.employee_id.id),
                    ('state', 'not in', ('cancel', 'done')),
                ])
                if req_purchase_order:
                    raise ValidationError('Purchase orders are still in process')
            elif rec.requisition_type == 'manufacturing_order':
                req_manufacturing_order = self.env['mrp.production'].search([
                    ('requisition_order', '=', self.name),
                    ('receiver_id', '=', self.employee_id.id),
                    ('state', 'not in', ('cancel', 'done')),
                ])
                if req_manufacturing_order:
                    raise ValidationError('Manufacturing orders are still in process')
        self.write({'state': 'received'})
        self.receive_date = fields.Date.today()

    def _compute_purchase_count(self):
        """Function to compute the purchase count"""
        self.purchase_count = self.env['purchase.order'].search_count([
            ('requisition_order', '=', self.name),
            ('receiver_id', '=', self.employee_id.id), ])

    def get_purchase_order(self):
        """Purchase order smart button view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('requisition_order', '=', self.name),
                       ('receiver_id', '=', self.employee_id.id), ],
        }

    def _compute_manufacturing_count(self):
        """Function to compute the manufacturing count"""
        self.manufacturing_count = self.env['mrp.production'].search_count([
            ('requisition_order', '=', self.name),
            ('receiver_id', '=', self.employee_id.id), ])

    def get_manufacturing_order(self):
        """Manufacturing order smart button view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manufacturing Order',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'domain': [('requisition_order', '=', self.name),
                       ('receiver_id', '=', self.employee_id.id), ],
        }

    def _compute_internal_transfer_count(self):
        """Function to compute the transfer count"""
        self.internal_transfer_count = self.env['stock.picking'].search_count([
            ('requisition_order', '=', self.name),
            ('receiver_id', '=', self.employee_id.id), ])

    def get_internal_transfer(self):
        """Internal transfer smart tab view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Internal Transfers',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('requisition_order', '=', self.name),
                       ('receiver_id', '=', self.employee_id.id), ],
        }

    def action_print_report(self):
        """Print purchase requisition report"""
        data = {
            'employee': self.employee_id.name,
            'records': self.read(),
            'order_ids': self.requisition_order_ids.read(),
        }
        return (self.env.ref(
            'accounting_base_kit.action_report_purchase_requisition').report_action(self, data=data)
                )

    def action_print_thermal_report(self):
        """Print thermal purchase requisition report"""
        data = {
            'employee': self.employee_id.name,
            'records': self.read(),
            'order_ids': self.requisition_order_ids.read(),
        }
        return (self.env.ref(
            'accounting_base_kit.action_report_thermal_purchase_requisition').report_action(self, data=data)
                )


class Department(models.Model):
    """ Class for adding new field in employee department"""

    _inherit = 'hr.department'

    department_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Destination Location",
        help="Department default destination location for requisition orders")


class HrEmployeePrivate(models.Model):
    """Class to add new field in employee form"""

    _inherit = 'hr.employee'

    employee_location_id = fields.Many2one(
        comodel_name='stock.location',
        string="Destination Location",
        help="Employee default destination location for requisition orders")


class PurchaseOrder(models.Model):
    """Class to add new field in purchase order"""

    _inherit = 'purchase.order'

    requisition_order = fields.Char(
        readonly=True,
        string='Requisition Order',
        help='Set a requisition Order')

    receiver_id = fields.Many2one(
        readonly=True,
        comodel_name='hr.employee', string='Requisition Employee',
        help='Select a employee the will receive the requisition')

    requisition_count = fields.Integer(
        string='Requisition Count',
        help='Requisition count',
        compute='_compute_requisition_count')

    link_requisition = fields.Boolean(string="Select", help="Order that need to be linked")

    def action_unlink_requisition(self):
        """
        This method unlinks requisition from orders.
        """
        for order in self:
            order.requisition_order = False
            order.receiver_id = False

    def _compute_requisition_count(self):
        """Function to compute the requisition count"""
        self.requisition_count = self.env['employee.purchase.requisition'].search_count([
            ('name', '=', self.requisition_order)])

    def get_requisition_order(self):
        """Requisition order smart button view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Requisition Order',
            'view_mode': 'tree,form',
            'res_model': 'employee.purchase.requisition',
            'domain': [('name', '=', self.requisition_order)],
        }


class RequisitionProducts(models.Model):
    _name = 'requisition.order'
    _description = 'Requisition Order'
    _order = 'sequence'

    sequence = fields.Integer(default=10)
    requisition_product_id = fields.Many2one(
        comodel_name='employee.purchase.requisition',
        help='Requisition product.')

    state = fields.Selection(
        string='State',
        related='requisition_product_id.state')

    requisition_type = fields.Selection(
        string='Requisition Type',
        selection=[('manufacturing_order', 'Manufacturing Order'),
                   ('purchase_order', 'Purchase Order'),
                   ('internal_transfer', 'Internal Transfer'), ],
        help='Type of requisition', required=True, default='internal_transfer')

    product_id = fields.Many2one(
        comodel_name='product.product', required=True, help='Product')

    description = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False,
        precompute=True, help='Product description')

    quantity = fields.Integer(
        string='Quantity', help='Product quantity', default=1)

    uom = fields.Char(
        related='product_id.uom_id.name',
        string='Unit of Measure', help='Product unit of measure')

    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Vendor',
        help='Vendor for the requisition',
        readonly=False)

    _sql_constraints = [
        ('requisition_type_field',
         'unique (requisition_type, partner_id, product_id)',
         'Only one product per partner per requisition type is allowed'),
    ]

    @api.depends('product_id')
    def _compute_name(self):
        """Compute product description"""

        for option in self:
            if not option.product_id:
                continue
            product_lang = option.product_id.with_context(
                lang=self.requisition_product_id.employee_id.lang)
            option.description = product_lang.get_product_multiline_description_sale()

    @api.onchange('requisition_type')
    def _onchange_product(self):
        """Fetching product vendors"""

        vendors_list = [data.partner_id.id for data in
                        self.product_id.seller_ids]
        return {'domain': {'partner_id': [('id', 'in', vendors_list)]}}


class MrpProduction(models.Model):
    """Class to add new field in Manufacturing Orders"""

    _inherit = 'mrp.production'

    requisition_order = fields.Char(
        readonly=True,
        string='Requisition Order',
        help='Requisition order sequence')

    receiver_id = fields.Many2one(
        readonly=True,
        comodel_name='hr.employee', string='Requisition Employee',
        help='Select a employee the will receive the requisition')

    requisition_count = fields.Integer(
        string='Requisition Count',
        help='Requisition count',
        compute='_compute_requisition_count')

    link_requisition = fields.Boolean(string="Select", help="Order that need to be linked")

    def action_unlink_requisition(self):
        """
        This method unlinks requisition from orders.
        """
        for order in self:
            order.requisition_order = False
            order.receiver_id = False

    def _compute_requisition_count(self):
        """Function to compute the requisition count"""
        self.requisition_count = self.env['employee.purchase.requisition'].search_count([
            ('name', '=', self.requisition_order)])

    def get_requisition_order(self):
        """Requisition order smart button view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Requisition Order',
            'view_mode': 'tree,form',
            'res_model': 'employee.purchase.requisition',
            'domain': [('name', '=', self.requisition_order)],
        }

    customer_ids = fields.Many2many(
        comodel_name='res.partner',
        compute="_compute_customers",
        string="Customers",
    )
    source_sale_orders = fields.Char(
        compute="_compute_source_sale_orders",
        string="Sale Order(s)",
        store=True,
        compute_sudo=True,
    )
    source_sale_ids = fields.One2many(
        comodel_name="sale.order",
        compute="_compute_source_sale_ids",
        compute_sudo=True,
    )

    def _get_related_sales(self):
        self.ensure_one()
        return (
            self.mapped("procurement_group_id")
            .mapped("mrp_production_ids")
            .mapped("move_dest_ids")
            .mapped("group_id")
            .mapped("sale_id")
        )

    @api.depends(
        "procurement_group_id",
        "procurement_group_id.mrp_production_ids",
        "procurement_group_id.mrp_production_ids.move_dest_ids",
        "procurement_group_id.stock_move_ids.move_dest_ids",
    )
    def _compute_customers(self):
        for rec in self:
            rec.customer_ids = rec._get_related_sales().mapped("partner_id").ids
            if not rec.customer_ids:
                sources = rec._get_sources()
                if sources:
                    rec.customer_ids = sources.customer_ids

    @api.depends(
        "procurement_group_id",
        "procurement_group_id.mrp_production_ids",
        "procurement_group_id.mrp_production_ids.move_dest_ids",
        "procurement_group_id.stock_move_ids.move_dest_ids",
    )
    def _compute_source_sale_ids(self):
        for rec in self:
            source_sale_ids = rec._get_related_sales()
            sources = rec._get_sources()
            if not source_sale_ids and sources:
                source_sale_ids = sources.source_sale_ids
            rec.source_sale_ids = source_sale_ids

    @api.depends("source_sale_ids")
    def _compute_source_sale_orders(self):
        for rec in self:
            rec.source_sale_orders = (
                ", ".join(rec.source_sale_ids.mapped("name"))
                if rec.source_sale_ids
                else ""
            )


class Picking(models.Model):
    """Class to add new field in stock picking"""

    _inherit = 'stock.picking'

    requisition_order = fields.Char(
        readonly=True,
        string='Requisition Order',
        help='Requisition order sequence')

    receiver_id = fields.Many2one(
        readonly=True,
        comodel_name='hr.employee', string='Requisition Employee',
        help='Select a employee the will receive the requisition')

    requisition_count = fields.Integer(
        string='Requisition Count',
        help='Requisition count',
        compute='_compute_requisition_count')

    link_requisition = fields.Boolean(string="Select", help="Transfer that need to be linked")

    def action_unlink_requisition(self):
        """
        This method unlinks requisition from orders.
        """
        for order in self:
            order.requisition_order = False
            order.receiver_id = False

    mo_ref_id = fields.Many2one('mrp.production', string='MO Reference', help='Manufacturing Order Reference')

    def _compute_requisition_count(self):
        """Function to compute the requisition count"""
        self.requisition_count = self.env['employee.purchase.requisition'].search_count([
            ('name', '=', self.requisition_order)])

    def get_requisition_order(self):
        """Requisition order smart button view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Requisition Order',
            'view_mode': 'tree,form',
            'res_model': 'employee.purchase.requisition',
            'domain': [('name', '=', self.requisition_order)],
        }


class PickingType(models.Model):
    _inherit = 'stock.picking.type'

    def get_employee_requisition(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "accounting_base_kit.employee_purchase_requisition_action"
        )
        return action


class LinkTransferOrder(models.Model):
    """
    This model handles the linking of requisition to internal transfer orders.
    """
    _name = 'link.transfer.orders'
    _description = "Link Internal Transfer Orders"

    transfer_ids = fields.Many2many(
        comodel_name='stock.picking', string='Transfer Orders',
        compute="_compute_stock_picking", compute_sudo=True,
        help="Select the internal transfer orders you want to link to the requisition order.")

    requisition_id = fields.Many2one(
        'employee.purchase.requisition', string='Requisition Order',
        help="The default requisition order to which the selected internal transfer orders will be linked.")

    @api.depends('requisition_id')
    def _compute_stock_picking(self):
        for rec in self:
            rec.transfer_ids = (self.env['stock.picking'].search([
                ('state', 'not in', ['cancel', 'done']),
                ('picking_type_code', '=', 'internal'),
                ('requisition_count', '=', 0),
            ]).ids)

    def action_add_orders(self):
        """
        Add selected orders to the associated requisition order and perform validation checks.
        """
        products = []
        for rec in self.requisition_id.requisition_order_ids:
            if rec.requisition_type == 'internal_transfer':
                products.append({
                    'quantity': rec.quantity,
                    'product_id': rec.product_id
                })
        if not products:
            raise ValidationError(
                _("You can not process order with no internal transfer products"))

        for transfer in self.transfer_ids:
            if not transfer.link_requisition:
                continue

            if transfer.state in ['cancel', 'done']:
                raise ValidationError(
                    _("You can not select and order that is Done or Cancel: %s" % transfer.display_name))

            if transfer.requisition_order:
                raise ValidationError(
                    _("Order: %s is selected already to requisition: %s" % (
                        transfer.display_name, transfer.requisition_order)))

            for product in products:
                for order_line in transfer.move_ids_without_package:
                    if order_line.product_id.id == product['product_id'].id:
                        if (_get_qty_balance(
                                product['quantity'], product['product_id'].uom_id,
                                order_line.product_uom_qty, order_line.product_uom)) < 0:
                            raise ValidationError(
                                _("Not enough quantity of matching product: %s found in selected Order: %s"
                                  % (product['product_id'].display_name, transfer.display_name)))

            transfer.requisition_order = self.requisition_id.name
            transfer.receiver_id = self.requisition_id.employee_id.id
            transfer.link_requisition = False


class LinkPurchaseOrder(models.Model):
    """
    This model handles the linking of requisition to purchase orders.
    """
    _name = 'link.purchase.orders'
    _description = "Link Purchase Orders"

    purchase_ids = fields.Many2many(
        comodel_name='purchase.order', string='Purchase Orders',
        compute="_compute_purchase_orders", compute_sudo=True,
        help="Select the purchase orders you want to link to the requisition order.")

    requisition_id = fields.Many2one(
        'employee.purchase.requisition', string='Requisition Order',
        help="The default requisition order to which the selected purchase orders will be linked.")

    @api.depends('requisition_id')
    def _compute_purchase_orders(self):
        for rec in self:
            rec.purchase_ids = (self.env['purchase.order'].search([
                ('state', 'not in', ['cancel', 'done']),
                ('requisition_count', '=', 0),
            ]).ids)

    def action_add_orders(self):
        """
        Add selected orders to the associated requisition order and perform validation checks.
        """
        products = []
        for rec in self.requisition_id.requisition_order_ids:
            if rec.requisition_type == 'purchase_order':
                products.append({
                    'quantity': rec.quantity,
                    'product_id': rec.product_id
                })
        if not products:
            raise ValidationError(
                _("You can not process order with no purchase order products"))

        for purchase in self.purchase_ids:
            if not purchase.link_requisition:
                continue

            if purchase.state in ['cancel', 'done']:
                raise ValidationError(
                    _("You can not select and order that is Done or Cancel: %s" % purchase.display_name))

            if purchase.requisition_order:
                raise ValidationError(
                    _("Order: %s is selected already to requisition: %s" % (
                        purchase.display_name, purchase.requisition_order)))

            for product in products:
                for order_line in purchase.order_line:
                    if order_line.product_id.id == product['product_id'].id:
                        if (_get_qty_balance(
                                product['quantity'], product['product_id'].uom_id,
                                order_line.product_qty, order_line.product_uom)) < 0:
                            raise ValidationError(
                                _("Not enough quantity of matching product: %s found in selected Order: %s"
                                  % (product['product_id'].display_name, purchase.display_name)))

            purchase.requisition_order = self.requisition_id.name
            purchase.receiver_id = self.requisition_id.employee_id.id
            purchase.link_requisition = False

    @api.constrains('purchase_ids')
    def purchase_ids_field(self):
        """
        Check for partner mismatch between Requisition order and selected Purchase Order.
        """
        for purchase in self:
            for inv_line in purchase.purchase_ids:
                if inv_line.partner_id not in purchase.requisition_id.requisition_order_ids.search([
                    ('requisition_type', '=', 'purchase_order'),
                    ('requisition_product_id.name', '=', self.requisition_id.name)]).mapped('partner_id'):
                    raise ValidationError(_(
                        "Partner mismatch between Requisition and Purchase Order. "
                        "Please remove it to Link Purchase Order: %s" % inv_line.display_name))


class LinkManufacturingOrder(models.Model):
    """
    This model handles the linking of requisition to purchase orders.
    """
    _name = 'link.manufacturing.orders'
    _description = "Link Manufacturing Orders"

    manufacturing_ids = fields.Many2many(
        comodel_name='mrp.production', string='Manufacturing Orders',
        compute="_compute_manufacturing_orders", compute_sudo=True,
        help="Select the manufacturing orders you want to link to the requisition order.")

    requisition_id = fields.Many2one(
        'employee.purchase.requisition', string='Requisition Order',
        help="The default requisition order to which the selected manufacturing orders will be linked.")

    @api.depends('requisition_id')
    def _compute_manufacturing_orders(self):
        for rec in self:
            rec.manufacturing_ids = (self.env['mrp.production'].search([
                ('state', 'not in', ['cancel', 'done']),
                ('requisition_count', '=', 0),
            ]).ids)

    def action_add_orders(self):
        """
        Add selected orders to the associated requisition order and perform validation checks.
        """
        products = []
        for rec in self.requisition_id.requisition_order_ids:
            if rec.requisition_type == 'manufacturing_order':
                products.append({
                    'quantity': rec.quantity,
                    'product_id': rec.product_id
                })
        if not products:
            raise ValidationError(
                _("You can not process order with no manufacturing products"))

        for manufacturing in self.manufacturing_ids:
            if not manufacturing.link_requisition:
                continue

            if manufacturing.state in ['cancel', 'done']:
                raise ValidationError(
                    _("You can not select and order that is Done or Cancel: %s" % manufacturing.display_name))

            if manufacturing.requisition_order:
                raise ValidationError(
                    _("Order: %s is selected already to requisition: %s" % (
                        manufacturing.display_name, manufacturing.requisition_order)))

            for product in products:
                if manufacturing.product_id.id == product['product_id'].id:
                    if (_get_qty_balance(
                            product['quantity'], product['product_id'].uom_id,
                            manufacturing.product_uom_qty, manufacturing.product_uom_id)) < 0:
                        raise ValidationError(
                            _("Not enough quantity of matching product: %s found in selected Order: %s"
                              % (product['product_id'].display_name, manufacturing.display_name))
                        )

            manufacturing.requisition_order = self.requisition_id.name
            manufacturing.receiver_id = self.requisition_id.employee_id.id
            manufacturing.link_requisition = False

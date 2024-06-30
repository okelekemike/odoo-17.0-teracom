# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    """
    This class is created for inherited model Stock Picking.

    Methods:
        action_force_availability(self):
            Function for make quantity done.It also changes state in to assigned.

        _compute_show_qty_button(self):
            This function will super the compute function of a boolean field
             that related to set quantity button.It will avoid showing force
            availability button and set quantity button at the same time.

    """
    _inherit = 'stock.picking'

    is_available = fields.Boolean('Make Available', default=False,
                                  help='The Force Availability button will show based on this field.')

    def action_force_availability(self):
        """Function for make quantity done."""

        for lines in self.move_ids:
            lines.quantity = lines.product_uom_qty
        self.is_available = True
        self.state = 'assigned'

    @api.depends()
    def _compute_show_qty_button(self):
        """This function will super the compute function of a boolean field
        that related to set quantity button.It will avoid showing force
        availability button and set quantity button at the same time."""

        res = super(StockPicking, self)._compute_show_qty_button()
        if self.products_availability_state == 'late':
            self.show_set_qty_button = False
        return res

    # Stock Picking Dashboard
    @api.model
    def stock_picking_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the stock picking return result which includes the values of
            numbers in all stages """
        result = {
            'draft': 0,
            'waiting': 0,
            'assigned': 0,
            'done': 0,
            'receipts': 0,
            'outgoing': 0,
            'internal': 0,
            'cancel': 0,
            'receipts_mth': 0,
            'outgoing_mth': 0,
            'internal_mth': 0,
            'cancel_mth': 0
        }
        current_date = fields.datetime.now().date()
        start_date = current_date.replace(day=1)
        stock_picking = self.env['stock.picking']
        receipts = stock_picking.search_count(
            [('state', '=', 'done'),
             ('picking_type_id.code', '=', 'incoming')])
        receipts_mth = stock_picking.search_count(
            [('state', '=', 'done'),
             ('picking_type_id.code', '=', 'incoming'), ('date', '>=', start_date)])
        outgoing = stock_picking.search_count(
            [('state', '=', 'done'),
             ('picking_type_id.code', '=', 'outgoing')])
        outgoing_mth = stock_picking.search_count(
            [('state', '=', 'done'),
             ('picking_type_id.code', '=', 'outgoing'), ('date', '>=', start_date)])
        internal = stock_picking.search_count(
            [('state', '=', 'done'),
             ('picking_type_id.code', '=', 'internal')])
        internal_mth = stock_picking.search_count(
            [('state', '=', 'done'),
             ('picking_type_id.code', '=', 'internal'), ('date', '>=', start_date)])
        cancel = stock_picking.search_count([('state', '=', 'cancel')])
        cancel_mth = stock_picking.search_count(
            [('state', '=', 'cancel'), ('date', '>=', start_date)])
        result['cancel'] = cancel
        result['cancel_mth'] = cancel_mth
        result['internal'] = internal
        result['internal_mth'] = internal_mth
        result['outgoing'] = outgoing
        result['outgoing_mth'] = outgoing_mth
        result['receipts'] = receipts
        result['receipts_mth'] = receipts_mth
        result['draft'] = stock_picking.search_count([('state', '=', 'draft')])
        result['waiting'] = stock_picking.search_count([('state', 'in', ('waiting', 'confirmed'))])
        result['done'] = stock_picking.search_count([('state', '=', 'done')])
        result['assigned'] = stock_picking.search_count([('state', '=', 'assigned')])
        return result

    # Digital Signature
    def _default_show_sign(self):
        """Get the default value for the 'Show Digital Signature' field."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.is_show_digital_sign_inventory')

    def _default_enable_options(self):
        """Get the default value for the 'Enable Digital Signature Options'
        field."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.is_enable_options_inventory')

    digital_sign = fields.Binary(string='Signature',
                                 help="Digital signature file")
    sign_by = fields.Char(string='Signed By',
                          help="Name of the person who signed")
    designation = fields.Char(string='Designation',
                              help="Designation of the person who signed")
    sign_on = fields.Datetime(string='Signed On',
                              help="Date and time of signing")
    is_show_sign = fields.Boolean(string="Show Sign",
                                  compute='_compute_show_sign',
                                  default=_default_show_sign,
                                  help="Show or hide the digital signature")
    is_enable_option = fields.Boolean(string="Enable Option",
                                      compute='_compute_enable_option',
                                      default=_default_enable_options,
                                      help="Enable or disable digital "
                                           "signature options")
    sign_applicable = fields.Selection(
        [('picking_operations', 'Picking Operations'),
         ('delivery', 'Delivery Slip'), ('both', 'Both')],
        string="Sign Applicable inside", compute='_compute_sign_applicable',
        help="Define where the digital signature is applicable")

    def button_validate(self):
        """Extends the base method to enforce signature confirmation."""
        res = super(StockPicking, self).button_validate()
        if self.env['ir.config_parameter'].sudo().get_param(
                'accounting_base_kit.is_confirm_sign_inventory') and \
                self.digital_sign is False:
            raise UserError('Signature is missing')
        return res

    def _compute_show_sign(self):
        """Compute whether to show or hide the digital signature field."""
        is_show_signature = self._default_show_sign()
        for record in self:
            record.is_show_sign = is_show_signature

    def _compute_enable_option(self):
        """Compute whether to enable or disable digital signature options."""
        is_enable_others = self._default_enable_options()
        for record in self:
            record.is_enable_option = is_enable_others

    def _compute_sign_applicable(self):
        """Compute where the digital signature is applicable."""
        for rec in self:
            rec.sign_applicable = self.env[
                'ir.config_parameter'].sudo().get_param(
                'accounting_base_kit.sign_applicable')

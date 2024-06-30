# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    related_stock_picking_count = fields.Integer(string="Stock Picking Count",
                                                 compute="_compute_related_stock_picking_count",
                                                 help="Related Stock Picking Count")
    is_stock_picking_created = fields.Boolean(string="Stock Picking Created", default=False, copy=False)

    # Compute the count of related stock pickings for each manufacturing order.
    def _compute_related_stock_picking_count(self):
        for rec in self:
            rec.related_stock_picking_count = self.env['stock.picking'].search_count([('mo_ref_id', '=', rec.id)])

    # Smart button for view related stock pickings inside MO.
    def action_open_related_stock_picking(self):
        self.ensure_one()
        stock_pickings = self.env['stock.picking'].search([('mo_ref_id', '=', self.id)])
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('id', 'in', stock_pickings.ids)]
        return action

    # Function for creating stock pickings from MO with required components to complete the MO process.
    def action_create_stock_picking(self):
        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']
        StockPickingType = self.env['stock.picking.type']

        for production in self:
            moves = production.move_raw_ids.filtered(lambda move: move.state not in ('done', 'cancel'))
            if not moves:
                raise UserError("No raw materials to transfer.")

            picking_type = StockPickingType.search([('code', '=', 'internal')], limit=1)
            if not picking_type:
                raise UserError("Internal picking type not found.")

            picking_vals = {
                'picking_type_id': picking_type.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': production.location_src_id.id,
                'origin': production.name,
                'mo_ref_id': production.id,
                'show_operations': False,
            }

            picking = StockPicking.create(picking_vals)

            for move in moves:
                quantity_to_transfer = move.product_uom_qty - move.quantity
                if move.quantity < move.product_uom_qty:
                    move_vals = {
                        'name': move.product_id.display_name,
                        'product_id': move.product_id.id,
                        'quantity': quantity_to_transfer,
                        'product_uom_qty': quantity_to_transfer,
                        'product_uom': move.product_uom.id,
                        'location_id': picking.location_id.id,
                        'location_dest_id': picking.location_dest_id.id,
                        'picking_id': picking.id,
                    }
                    StockMove.create(move_vals)
                    picking.action_confirm()
                    production.is_stock_picking_created = True
        return True

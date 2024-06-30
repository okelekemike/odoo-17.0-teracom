# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import api, fields, models


class StockMove(models.Model):
    """class for mini passing values to mini dashboard
        retrieve_inventory_dashboard function for calculating values """
    _inherit = 'stock.move'

    @api.model
    def retrieve_inventory_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the stock move return result which includes the values of
            numbers in all stages"""
        result = {
            'draft': 0,
            'cancelled': 0,
            'waiting': 0,
            'partially_available': 0,
            'assigned': 0,
            'done': 0,
            'count': 0,
            'average_products': 0,

        }
        stock_move = self.env['stock.move']
        last_week = fields.datetime.now() - timedelta(days=7)
        stock_moves = stock_move.search(
            [('date', '>=', last_week.strftime('%Y-%m-%d %H:%M:%S'))])
        total_qty = sum(move.product_qty for move in stock_move.search([]))
        no_moves = len(stock_move.search([]))
        if no_moves > 0:
            avg_qty = int(total_qty / no_moves)
        else:
            avg_qty = 0
        picking_type_code = self.env.context.get('restricted_picking_type_code')
        result['average_products'] = avg_qty
        result['count'] = len(stock_moves)
        result['draft'] = stock_move.search_count([('state', '=', 'draft')])
        result['cancelled'] = stock_move.search_count([('state', '=', 'cancelled')])
        result['waiting'] = stock_move.search_count([('state', 'in', ('waiting', 'confirmed'))])
        result['partially_available'] = stock_move.search_count([('state', '=', 'partially_available')])
        result['assigned'] = stock_move.search_count([('state', '=', 'assigned')])
        result['done'] = stock_move.search_count([('state', '=', 'done'), ('picking_type_code', '=', picking_type_code)])
        return result

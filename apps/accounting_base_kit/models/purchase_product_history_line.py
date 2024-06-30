# -*- coding: utf-8 -*-

from odoo import fields, models


class PurchaseProductHistoryLine(models.Model):
    """Purchase product history datas for product purchase"""
    _name = 'purchase.product.history.line'
    _description = 'Product history line for product purchase'

    product_history_id = fields.Many2one('product.product', string='Product',
                                         help='Name of the product')
    order_date = fields.Date(string='Order Date', help='Order date of the product')
    order_reference_id = fields.Many2one('purchase.order', string='Order',
                                         help='Purchase order reference of the product')
    description = fields.Text(string='Description', help='Description of the product')
    price_unit = fields.Float(string='Unit Price', help='Unit price of the product')
    product_qty = fields.Float(string='Quantity', help='Product quantity')
    price_subtotal = fields.Float(string='Subtotal', help='Subtotal of the product')
    price_total = fields.Float(string='Total', help='Total of the product')


class SaleProductHistoryLine(models.Model):
    """Sale product history datas for product sales"""
    _name = 'sale.product.history.line'
    _description = 'Product history line for product sales'

    product_history_id = fields.Many2one('product.product', string='Product',
                                         help='Name of the product')
    order_date = fields.Date(string='Order Date', help='Order date of the product')
    order_reference_id = fields.Many2one('sale.order', string='Order',
                                         help='Sale order reference of the product')
    description = fields.Text(string='Description', help='Description of the product')
    price_unit = fields.Float(string='Unit Price', help='Unit price of the product')
    product_qty = fields.Float(string='Quantity', help='Product quantity')
    price_subtotal = fields.Float(string='Subtotal', help='Subtotal of the product')
    price_total = fields.Float(string='Total', help='Total of the product')


class POSProductHistoryLine(models.Model):
    """Point of Sale product history datas for POS product sales"""
    _name = 'pos.product.history.line'
    _description = 'Product history line for POS product sales'

    product_history_id = fields.Many2one('product.product', string='Product',
                                         help='Name of the product')
    order_date = fields.Date(string='Order Date', help='Order date of the product')
    order_reference_id = fields.Many2one('pos.order', string='Order',
                                         help='Point of Sale order reference of the product')
    description = fields.Text(string='Description', help='Description of the product')
    price_unit = fields.Float(string='Unit Price', help='Unit price of the product')
    product_qty = fields.Float(string='Quantity', help='Product quantity')
    price_subtotal = fields.Float(string='Subtotal', help='Subtotal of the product')
    price_total = fields.Float(string='Total', help='Total of the product')
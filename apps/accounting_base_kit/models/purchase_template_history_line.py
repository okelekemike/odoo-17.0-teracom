# -*- coding: utf-8 -*-

from odoo import fields, models


class PurchaseTemplateHistoryLine(models.Model):
    """Purchase product history datas for product.template"""
    _name = 'purchase.template.history.line'
    _description = 'Purchase history line for template'

    history_id = fields.Many2one('product.template', string='Product',
                                 help='Name of the product variant')
    order_date = fields.Date(string='Order Date', help='Order date of the product')
    order_reference_id = fields.Many2one('purchase.order', string='Order',
                                         help='Purchase order reference of the product')
    description = fields.Text(string='Description', help='Description of the product')
    price_unit = fields.Float(string='Unit Price', help='Unit price of the product')
    product_qty = fields.Float(string='Quantity', help='Product quantity')
    price_subtotal = fields.Float(string='Subtotal', help='Subtotal of the product')
    price_total = fields.Float(string='Total', help='Total of the product')


class SaleTemplateHistoryLine(models.Model):
    """Sale product history datas for product.template"""
    _name = 'sale.template.history.line'
    _description = 'Sale history line for template'

    history_id = fields.Many2one('product.template', string='Product',
                                 help='Name of the product variant')
    order_date = fields.Date(string='Order Date', help='Order date of the product')
    order_reference_id = fields.Many2one('sale.order', string='Order',
                                         help='Sale order reference of the product')
    description = fields.Text(string='Description', help='Description of the product')
    price_unit = fields.Float(string='Unit Price', help='Unit price of the product')
    product_qty = fields.Float(string='Quantity', help='Product quantity')
    price_subtotal = fields.Float(string='Subtotal', help='Subtotal of the product')
    price_total = fields.Float(string='Total', help='Total of the product')


class POSTemplateHistoryLine(models.Model):
    """Point of Sale product history datas for product.template"""
    _name = 'pos.template.history.line'
    _description = 'Point of Sale history line for template'

    history_id = fields.Many2one('product.template', string='Product',
                                 help='Name of the product variant')
    order_date = fields.Date(string='Order Date', help='Order date of the product')
    order_reference_id = fields.Many2one('pos.order', string='Order',
                                         help='Point of Sale order reference of the product')
    description = fields.Text(string='Description', help='Description of the product')
    price_unit = fields.Float(string='Unit Price', help='Unit price of the product')
    product_qty = fields.Float(string='Quantity', help='Product quantity')
    price_subtotal = fields.Float(string='Subtotal', help='Subtotal of the product')
    price_total = fields.Float(string='Total', help='Total of the product')

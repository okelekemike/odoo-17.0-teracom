# -*- coding: utf-8 -*-

from odoo import fields, models


class ScrapManagementLine(models.Model):
    """ This class define a new model for manage scrap components """
    _name = "scrap.management.line"
    _description = "Scrap Management Line"

    product_id = fields.Many2one('product.product',
                                 string="Product", readonly=True,
                                 help="Field to specify product")
    scrap_management_id = fields.Many2one('scrap.management',
                                          string="Product", readonly=True,
                                          help="Field to specify scrap management order")
    dismantle_qty = fields.Integer(string="Available quantity", readonly=True,
                                   help="Field to specify total quantity")
    useful_qty = fields.Integer(string="Useful Product Quantity",
                                help="Field to specify useful quantity")

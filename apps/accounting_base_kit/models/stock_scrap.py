# -*- coding: utf-8 -*-

from odoo import fields, models


class StockScrap(models.Model):
    """ This class inherit the model stock.scrap for adding some fields. """
    _inherit = "stock.scrap"

    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template', related='product_id.product_tmpl_id',
        help="Corresponding product of the variant")
    bill_of_material_id = fields.Many2one(
        'mrp.bom',
        domain="[('product_tmpl_id', '=', product_tmpl_id)]",
        string="Bill of Material",
        help="Field to specify sequence bill of material")
    typ_of_reuse = fields.Selection(
        [('none', 'None'), ('dismantle', 'Dismantle')],
        default="none", help="Field to specify type of scrap",
        string="Type of Operation")
    state_management = fields.Selection(
        [('none', 'None'), ('dismantled', 'Dismantled')],
        string="State", default="none",
        help="Field to specify type of scrap management")

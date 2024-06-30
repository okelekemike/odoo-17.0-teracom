# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockLot(models.Model):
    _inherit = "stock.lot"

    active = fields.Boolean(string="Active", default=True)
    auto_deactivate = fields.Boolean(string="Auto Deactivate", default=True,
                                     help="Automatically deactivate and archive lots with zero quantity.")

    @api.constrains("name", "product_id", "company_id")
    def _check_unique_lot(self):
        """Ensure that no other lot shares the same name, company, and product. 
        To prevent the creation of duplicate lot/company/name combinations, 
        especially when there exists another inactive entry, 
        it's necessary to set the active_test flag to False.
        """
        res = super(StockLot, self.with_context(active_test=False))
        return res._check_unique_lot()

    def _check_lot_active(self):
        if self.auto_deactivate:
            lots = self.env['stock.lot'].search([('product_qty', '=', 0)])
            for lot in lots:
                lot.write({"active": False})


    def _get_pos_info(self):
        # We will add this as a hook to add more fields if necessary
        return {
            "id": self.id,
            "name": self.name,
        }
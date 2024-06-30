# -*- coding: utf-8 -*-

from odoo import fields, models


class PriceHistory(models.Model):
    """
    Keep track of the price of products standard prices as they are changed.
    """
    _name = 'price.history'
    _description = 'Products Price History'
    _order = 'datetime desc'

    def _get_default_company_id(self):
        """Returns default company of the user"""
        return self._context.get('force_company', self.env.user.company_id.id)

    company_id = fields.Many2one('res.company', string='Company',
                                 default=_get_default_company_id,
                                 required=True, help="Choose your company")
    product_id = fields.Many2one('product.product', string='Product',
                                 ondelete='cascade', required=True,
                                 help="Choose product")
    datetime = fields.Datetime(string='Date', default=fields.Datetime.now,
                               help="Choose the date")
    cost = fields.Float(string='Cost', digits='Product Price',
                        help="Product Price")


class ProductProduct(models.Model):
    """Inheriting the product.product model and add a function to it"""
    _inherit = 'product.product'

    def get_history_price(self, company_id, date=None):
        """to get the previous price of the product"""
        return self.env['price.history'].search([
            ('company_id', '=', company_id),
            ('product_id', 'in', self.ids),
            ('datetime', '<=', date or fields.Datetime.now())],
            order='datetime desc,id desc', limit=1).cost or 0.0

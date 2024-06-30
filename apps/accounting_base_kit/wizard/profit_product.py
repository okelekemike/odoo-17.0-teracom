# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProfitProduct(models.TransientModel):
    """Transient model for wizard"""
    _name = "profit.product"
    _description = 'Product Profit'

    @api.model
    def _get_from_date(self):
        """This methode returns first day in the year"""
        return self.env.user.company_id.compute_fiscalyear_dates(
            fields.Date.today())['date_from']

    from_date = fields.Date(string='From Date', default=_get_from_date,
                            required=True,
                            help="From which date Report need to print")
    to_date = fields.Date(string='To Date', default=fields.Date.context_today,
                          required=True,
                          help="Date before which report need to print")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id.id,
        help="Select your company (only show when multi company is enabled")
    categ_id = fields.Many2one('product.category', string='Product Category',
                               required=True,
                               help="Choose Product category")
    product_id = fields.Many2one('product.product', string='Product',
                                 help="Select the Product")
    product_product_ids = fields.Many2many(
        'product.product', string="Products",
        help="When chosen the product category only the product in that "
             "category shows for this we use this field as a domain")

    def get_all_child_categories(self, category):
        """This function returns all child categories"""
        all_child_ids = category.child_id.ids
        for child_category in category.child_id:
            all_child_ids += self.get_all_child_categories(child_category)
        return all_child_ids

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        """Show products that correspond to the selected category"""
        self.product_id = False
        if self.categ_id:
            self.product_product_ids = [
                (6, 0, self.env['product.product'].search(
                    [('categ_id', 'in', [
                        self.categ_id.id] + self.get_all_child_categories(
                        self.categ_id))]).ids)]
        else:
            self.product_product_ids = [(5, 0, 0)]

    def action_print_pdf_report(self):
        """Print the pdf report"""
        report_action = self.env.ref(
            'accounting_base_kit.product_profit_report_action')
        return report_action.with_context(landscape=True).report_action(
            self, data={'form': self.read([])[0]})

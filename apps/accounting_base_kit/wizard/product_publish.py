# -*- coding: utf-8 -*-

from odoo import models


class ProductPublish(models.TransientModel):
    """ Wizard for multiple product publish in product template """
    _name = 'product.publish'
    _description = "Product Publish/Unpublish"

    def action_product_multi_publish(self):
        """ Function for publishing products on a website """
        active_ids = self._context.get('active_ids')
        products = self.env['product.template'].browse(active_ids)
        products = products.filtered(lambda product: product.sale_ok == True)
        for product in products:
            product.is_published = True

    def action_product_multi_unpublish(self):
        """ Function for un publish product in website"""
        active_ids = self._context.get('active_ids')
        products = self.env['product.template'].browse(active_ids)
        products = products.filtered(lambda product: product.sale_ok == True)
        for product in products:
            product.is_published = False

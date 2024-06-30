# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductImageSuggestion(models.TransientModel):
    """creates new model to store the searched image"""
    _name = "product.image.suggestion"
    _description = "Attach images and set image as the display image of product"

    image = fields.Binary(string='Image', attachment=True,
                          help="image field to store the image")
    product_tmpl_id = fields.Many2one('product.template',
                                      string='Related Product',
                                      help="product field to store the id of "
                                           "product from which the image "
                                           "is searched")

    def action_set_image(self):
        """Set product images from suggested images"""
        for rec in self:
            self_image = rec.image
            if self_image:
                rec.product_tmpl_id.image_1920 = self_image
        return{
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

# -*- coding: utf-8 -*-
import base64
import logging
import os
import tempfile
import requests
from PIL import Image
from resizeimage import resizeimage
from . import downloader
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    """
    Check if the searched image limit is greater than 10 and a warning
    message will be raised.
    """
    _inherit = 'product.template'

    search_image_ids = fields.One2many('product.image.suggestion', 'product_tmpl_id',
                                       string='Images', readonly=True, help="To show the images downloaded")
    search_field = fields.Char(string='Search Text', help="Type the text to be searched")
    image_limit = fields.Integer(string='Limit', default=5, help="Limit of images to display")
    resize_image = fields.Boolean(string='Resize Image', default=True, help="Resize the image")
    show_setting = fields.Boolean(string='Show Setting', default=False)

    @api.onchange('image_limit')
    def _onchange_image_limit(self):
        """
        Check if the searched image limit is greater than 10 and a warning
        message will be raised.
        """
        if self.image_limit > 10:
            raise UserError('This may slow down image search..!!! Try to reset the Limit')

    def action_search_image(self):
        """Clear search images and add new search"""
        for rec in self:
            rec.search_image_ids = [[5, 0, 0]]
            if rec.image_limit > 10:
                _logger.warning("High limit number slow down the image searches")
            try:
                if not rec.search_field:
                    rec.search_field = rec.name
                query_string = rec.search_field.replace(" ", "_").replace(",", "_")

                image_datas = downloader.download(query_string,
                                                  limit=rec.image_limit,
                                                  output_dir='dataset',
                                                  adult_filter_off=False,
                                                  timeout=60, verbose=True)
            except AttributeError:
                raise UserError(_('No internet connection available or Something wrong !'))
            if image_datas:
                for img in image_datas:
                    temp_name = ''
                    try:
                        img_request = requests.get(img.strip()).content
                        if self.resize_image:
                            temp_file, temp_name = tempfile.mkstemp(suffix='.png')
                            file = open(temp_name, "wb")
                            file.write(img_request)
                            file.close()
                            img_data = Image.open(temp_name)
                            img_data = resizeimage.resize_contain(img_data, [1024, 1024])
                            img_data.save(temp_name, img_data.format)
                            img_data.close()
                            with open(temp_name, "rb") as image_file:
                                binary_image = base64.b64encode(image_file.read())
                        else:
                            byte_image = bytearray(img_request)
                            binary_image = base64.b64encode(byte_image)
                        vals = {
                            'image': binary_image,
                            'product_tmpl_id': rec.id
                        }
                        self.env['product.image.suggestion'].create(vals)
                        if self.resize_image and image_file.close():
                            os.remove(temp_name)
                    except:
                        _logger.exception(_("failed to display in page"))
                        continue
            else:
                raise UserError(_('No image suggestions for this image'))

    @api.model_create_multi
    def create(self, vals_list):
        company = self.env.company
        for vals in vals_list:
            if company.avoid_products_name_duplication and 'name' in vals:
                existing_product = self.search([('name', '=ilike', vals['name'])])
                if existing_product:
                    raise UserError("A product with the same name already exists.")

            if company.avoid_internal_references_duplication and 'default_code' in vals and isinstance(
                    vals['default_code'], str) and vals['default_code'].strip():
                existing_product = self.search([('default_code', '=ilike', vals['default_code'].strip())])
                if existing_product:
                    raise UserError("A product with the same Internal Reference already exists.")

        return super(ProductTemplate, self).create(vals_list)

    def write(self, vals):
        company = self.env.company
        if company.avoid_products_name_duplication and 'name' in vals:
            existing_product = self.search([('name', '=ilike', vals['name'])])
            if existing_product:
                raise UserError("A product with the same name already exists.")

        if company.avoid_internal_references_duplication and 'default_code' in vals and isinstance(
                vals['default_code'], str) and vals['default_code'].strip():
            existing_product = self.search([('default_code', '=ilike', vals['default_code'].strip())])
            if existing_product:
                raise UserError("A product with the same Internal Reference already exists.")

        return super(ProductTemplate, self).write(vals)

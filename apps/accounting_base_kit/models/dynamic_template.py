# -*- coding: utf-8 -*-

from odoo import fields, models


class DynamicTemplate(models.Model):
    """Dynamic template for Products"""
    _name = "dynamic.template"
    _description = 'Dynamic Template'

    name = fields.Char(string='Name', required=True,
                       help='Name of the template')
    bc_height = fields.Char(string='Barcode Height', required=True,
                            help='Height of the barcode')
    bc_width = fields.Char(string='Barcode width', required=True,
                           help='Width of the barcode')
    dynamic_field_ids = fields.One2many('dynamic.fields', 'field_id', string='Fields',
                                        help='You can select the required field '
                                             'from the product with required '
                                             'size and color for viewing in the '
                                             'label report')


class DynamicFields(models.Model):
    """One2many fields of dynamic template"""
    _name = "dynamic.fields"
    _description = "Dynamic Fields"

    def set_domain(self):
        """Fields of the product model"""
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'product.product')])
        return [('model_id', '=', model_id.id), ('state', '=', 'base'), (
            'name', '=', ['name', 'categ_id', 'detailed_type', 'list_price']
        )]

    size = fields.Char(string='Font Size', help="Set the size of the field")
    color = fields.Char(string='Font Color', help="Set the colour of the field")
    fd_name_id = fields.Many2one('ir.model.fields', string='Field Name',
                                 domain=set_domain, help='Name of the field')
    type = fields.Selection(string='Type', related='fd_name_id.ttype',
                            help='Type of the field name')
    field_id = fields.Many2one('dynamic.template', string='Fields',
                               help='Relation from dynamic templates')

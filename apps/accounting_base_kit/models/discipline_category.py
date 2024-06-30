# -- coding: utf-8 --

from odoo import fields, models


class DisciplineCategory(models.Model):
    """Model for discipline categories"""
    _name = 'discipline.category'
    _description = 'Discipline Category'

    code = fields.Char(string="Code", required=True,
                       help="Discipline category code")
    name = fields.Char(string="Name", required=True,
                       help=" Discipline category name")
    category_type = fields.Selection([('disciplinary', 'Disciplinary Category'),
                                      ('action', 'Action Category')],
                                     string="Category Type",
                                     help="Choose the category type "
                                          "disciplinary or action")
    description = fields.Text(string="Details",
                              help="Details for this category")

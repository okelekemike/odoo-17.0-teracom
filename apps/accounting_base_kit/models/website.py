# -*- coding: utf-8 -*-

from odoo import fields, models


class Website(models.Model):
    """ Inheriting 'website' model to add mobile number."""
    _inherit = 'website'

    mobile_number = fields.Char(string='Mobile Number')

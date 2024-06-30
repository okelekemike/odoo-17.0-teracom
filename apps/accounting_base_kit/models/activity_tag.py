# -*- coding: utf-8 -*-

from random import randint
from odoo import fields, models


class ActivityTag(models.Model):
    """Model to add tags to an activity"""
    _name = "activity.tag"
    _description = "Activity Tag"

    name = fields.Char(string='Tag Name',
                       help='Name of the activity tag.',
                       required=True,
                       translate=True)

    color = fields.Integer(string='Color',
                           help='Field that gives color to the tag.',
                           default=randint(1, 11))

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"), ]

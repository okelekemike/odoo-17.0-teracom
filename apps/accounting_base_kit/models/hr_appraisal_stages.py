# -*- coding: utf-8 -*-

from odoo import fields, models


class HrAppraisalStages(models.Model):
    """Create the model Appraisal Stages to show the stages of the appraisal"""
    _name = 'hr.appraisal.stages'
    _description = 'Appraisal Stages'

    name = fields.Char(string="Name", help="Name of the appraisal stage")
    sequence = fields.Integer(string="Sequence",
                              help="Sequence of the appraisal stage to be "
                                   "shown")
    fold = fields.Boolean(string='Folded in Appraisal Pipeline',
                          help='This stage is folded in the kanban view when '
                               'there are no records in that stage to display.')

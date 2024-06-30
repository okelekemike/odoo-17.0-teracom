# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SurveyUserInput(models.Model):
    """Inherits the model survey.user_input to extend the model and make
    changes in the functionality."""
    _inherit = 'survey.user_input'

    appraisal_id = fields.Many2one('hr.appraisal', string="Appraisal id",
                                   help="Appraisal ID of the user input for "
                                        "the survey")

    @api.model_create_multi
    def create(self, vals_list):
        """inherits the create method of the model survey.user_input"""
        ctx = self.env.context
        if ctx.get('active_id') and ctx.get('active_model') == 'hr.appraisal':
            for vals in vals_list:
                vals['appraisal_id'] = ctx.get('active_id')
        return super(SurveyUserInput, self).create(vals_list)

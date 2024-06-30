# -*- coding: utf-8 -*-

from odoo import models


class SurveyQuestion(models.Model):
    """To write function for survey question buttons """

    _inherit = 'survey.question'

    def action_add_question(self):
        """Summary:
              Function to view question wizard
           Returns:
               returns the  view of the 'question.wizard' view.
        """
        return {
            'name': "Add To Survey",
            'view_mode': 'form',
            'res_model': 'question.duplicate',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

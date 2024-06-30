# -*- coding: utf-8 -*-

from odoo import http
from odoo.addons.survey.controllers import main
from odoo.http import request


class Survey(main.Survey):
    """Inherits the class survey to super the controller"""

    @http.route('/survey/start/<string:survey_token>', type='http', auth='public', website=True)
    def survey_start(self, survey_token, answer_token=None, email=False, **post):
        """Inherits the method survey_start to check whether the survey
        appraisal is cancelled, done or has not started"""
        res = super(Survey, self).survey_start(
            survey_token=survey_token, answer_token=answer_token, email=email, **post)
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=False)
        if access_data.get('answer_sudo').appraisal_id:
            if access_data.get('answer_sudo').appraisal_id.stage_id.name == "Cancel":
                return request.render("accounting_base_kit.appraisal_canceled",
                                      {'survey': access_data.get('survey_sudo')})
            elif access_data.get('answer_sudo').appraisal_id.stage_id.name == "Done":
                return request.render("accounting_base_kit.appraisal_done",
                                      {'survey': access_data.get('survey_sudo')})
            elif access_data.get('answer_sudo').appraisal_id.stage_id.name == "To Start":
                return request.render("accounting_base_kit.appraisal_draft",
                                      {'survey': access_data.get('survey_sudo')})
        return res

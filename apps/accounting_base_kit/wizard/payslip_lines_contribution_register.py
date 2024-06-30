# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil import relativedelta

from odoo import fields, models


class PayslipLinesContributionRegister(models.TransientModel):
    """Create new model Payslip Lines by Contribution Registers"""
    _name = 'payslip.lines.contribution.register'
    _description = 'Payslip Lines by Contribution Registers'

    date_from = fields.Date(string='Date From',
                            help="Starting Date for Payslip Lines",
                            required=True,
                            default=datetime.now().strftime('%Y-%m-01'))
    date_to = fields.Date(string='Date To',
                          help="Ending Date for Payslip Lines", required=True,
                          default=str(
                              datetime.now() + relativedelta.relativedelta(
                                  months=+1, day=1, days=-1))[:10])

    def action_print_report(self):
        """Function for Print Report"""
        active_ids = self.env.context.get('active_ids', [])
        datas = {
            'ids': active_ids,
            'model': 'hr.contribution.register',
            'form': self.read()[0]
        }
        return (self.env.ref(
            'accounting_base_kit.contribution_register_action')
                .report_action([], data=datas))

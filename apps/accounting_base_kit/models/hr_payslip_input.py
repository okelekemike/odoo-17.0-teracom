# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil import relativedelta
from odoo import fields, models


class HrPayslipInput(models.Model):
    """Create new model for adding fields"""
    _name = 'hr.payslip.input'
    _description = 'Payslip Input'
    _order = 'payslip_id, sequence'

    name = fields.Char(string='Description', required=True)

    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip',
                                 required=True,
                                 ondelete='cascade', help="Payslip", index=True)

    sequence = fields.Integer(required=True, index=True, default=10,
                              help="Sequence")

    code = fields.Char(required=True,
                       help="The code that can be used in the salary rules")

    date_from = fields.Date(string='Date From',
                            help="Starting Date for Payslip Lines",
                            required=True,
                            default=datetime.now().strftime('%Y-%m-01'))

    date_to = fields.Date(string='Date To',
                          help="Ending Date for Payslip Lines", required=True,
                          default=str(
                              datetime.now() + relativedelta.relativedelta(
                                  months=+1, day=1, days=-1))[:10])

    amount = fields.Float(string="Amount",
                          help="It is used in computation." 
                               "For e.g. A rule for sales having "
                               "1% commission of basic salary for" 
                               "per product can defined in "
                               "expression like result = "
                               "inputs.SALEURO.amount * contract.wage*0.01.")

    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  required=True,
                                  help="The contract for which applied"
                                       " this input")

    loan_line_id = fields.Many2one('hr.loan.line',
                                   string="Loan Installment",
                                   help="Loan installment associated "
                                        "with this payslip input.")

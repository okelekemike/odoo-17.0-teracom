# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipLine(models.Model):
    """Create new model for adding Payslip Line"""
    _name = 'hr.payslip.line'
    _inherit = 'hr.salary.rule'
    _description = 'Payslip Line'
    _order = 'contract_id, sequence'

    slip_id = fields.Many2one('hr.payslip', string='Pay Slip',
                              required=True,
                              ondelete='cascade',
                              help="Choose Payslip for line")
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Rule',
                                     required=True,
                                     help="Choose Salary Rule for line")
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True,
                                  help="Choose Employee for line")
    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  required=True, index=True,
                                  help="Choose Contract for line")
    rate = fields.Float(string='Rate (%)', help="Set Rate for payslip",
                        digits='Payroll Rate', default=100.0)
    amount = fields.Float(digits='Payroll', string="Amount",
                          help="Set Amount for line")
    quantity = fields.Float(digits='Payroll', default=1.0,
                            string="Quantity", help="Set Qty for line")
    total = fields.Float(compute='_compute_total', string='Total',
                         help="Total amount for Payslip",
                         digits='Payroll', store=True)

    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):
        """Function for compute total amount"""
        for line in self:
            line.total = float(line.quantity) * line.amount * line.rate / 100

    @api.model_create_multi
    def create(self, vals_list):
        """Function for change value at the time of creation"""
        for values in vals_list:
            if 'employee_id' not in values or 'contract_id' not in values:
                payslip = self.env['hr.payslip'].browse(values.get('slip_id'))
                values['employee_id'] = values.get(
                    'employee_id') or payslip.employee_id.id
                values['contract_id'] = (values.get(
                    'contract_id') or payslip.contract_id and
                                         payslip.contract_id.id)
                if not values['contract_id']:
                    raise UserError(
                        _('You must set a contract to create a payslip line.'))
        return super(HrPayslipLine, self).create(vals_list)

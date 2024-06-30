# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class EmployeePromotion(models.Model):
    """This model is necessary for add employee promotion details in employee
       module """
    _name = 'employee.promotion'
    _description = 'Employee Promotion Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'promotion_name'

    promotion_name = fields.Text(required=True, string='Promotion Name',
                                 help='Promotion name')
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True, help='Name of employee')
    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  help='Contract of employee',
                                  domain="[('employee_id', '=', employee_id)]")
    job_title_id = fields.Many2one('hr.job',
                                   string='Old Designation',
                                   help='Previous job of employee ')
    job_salary = fields.Float(string='Previous Salary',
                              required=True, help='Previous job salary')
    promotion_date = fields.Date(string='Promotion Date',
                                 default=fields.Date.today(),
                                 help='Date of promotion date')
    promotion_type_id = fields.Many2one('promotion.type',
                                        string='Promotion Type',
                                        required=True,
                                        help='Promotion type of promotion')
    new_designation_id = fields.Many2one('hr.job',
                                         string='New Designation',
                                         required=True,
                                         help='New designation of employee')
    new_salary = fields.Float(string='New Salary', required=True,
                              help='New salary')
    description = fields.Text(string='Description', help='Description of the'
                                                         ' promotion')

    @api.model_create_multi
    def create(self, vals_list):
        """It checks if the new salary is greater than the old salary,
           raising a UserError if it is not the case."""
        res = super(EmployeePromotion, self).create(vals_list)
        employee = self.env['hr.employee'].browse(res.employee_id.id)
        employee.write({
            'promotion_ids': [(4, res.id)],
            'job_id': res.new_designation_id.id
        })
        if res.job_salary >= res.new_salary:
            raise UserError("New Salary will be Higher than Old ")
        return res

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """This method is called when the employee_id field is changed.
           It searches for an open HR contract history
           record for the selected employee and sets the contract_id and
           job_salary fields based on the
           corresponding values in the contract.
           If no open contract is found, the fields are left blank."""
        self.job_title_id = self.employee_id.job_id.id
        contract = self.env['hr.contract.history'].search(
            [('employee_id', '=', self.employee_id.id), ('state', '=', 'open')])
        if contract:
            for contract_history in contract:
                self.contract_id = contract_history.name
                self.job_salary = contract_history.wage

    def write(self, vals):
        """ Override the default write method to check if the new salary is
            greater than the current job salary.
            If the new salary is greater,
            raise a UserError with a warning message."""
        res = super(EmployeePromotion, self).write(vals)
        if self.job_salary >= self.new_salary:
            raise UserError("New Salary should be Higher than Old Salary")
        return res


class HrEmployee(models.Model):
    """Inheriting employee to add employee promotion form as many 2many field"""
    _inherit = 'hr.employee'

    promotion_ids = fields.Many2many('employee.promotion',
                                     string='Promotions',
                                     help='The promotions that an employee has received')


class PromotionType(models.Model):
    """This model is used for the Promotion Type of Employee"""
    _name = 'promotion.type'
    _description = 'Promotion Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'promotion_type'

    promotion_type = fields.Text(string='Promotion Type', help='Promotion type')

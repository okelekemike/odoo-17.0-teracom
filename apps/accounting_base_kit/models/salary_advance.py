# -*- coding: utf-8 -*-

from datetime import datetime
import time
from odoo import exceptions
from odoo.exceptions import UserError
from odoo import api, fields, models, _


class SalaryAdvance(models.Model):
    """Class for the model salary_advance. Contains methods and fields of the
       model."""
    _name = "salary.advance"
    _description = "Salary Advance"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', readonly=True,
                       default=lambda self: 'Adv/',
                       help='Name of the the advanced salary.')
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True, help="Name of the Employee")
    date = fields.Date(string='Date', required=True,
                       default=lambda self: fields.Date.today(),
                       help="Submit date of the advanced salary.")
    reason = fields.Text(string='Reason', help="Reason for the advance salary"
                                               " request.")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True,
                                  help='Currency of the company.',
                                  default=lambda self: self.env.user.
                                  company_id.currency_id)
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True,
                                 help='Company of the employee,',
                                 default=lambda self: self.env.user.company_id)
    advance = fields.Float(string='Advance', required=True,
                           help='The requested money.')
    payment_method = fields.Many2one('account.journal',
                                     string='Payment Method',
                                     help='Pyment method of the salary'
                                          ' advance.')
    exceed_condition = fields.Boolean(string='Exceed than Maximum',
                                      help="The Advance is greater than the "
                                           "maximum percentage in salary "
                                           "structure")
    department = fields.Many2one('hr.department', string='Department',
                                 related='employee_id.department_id',
                                 help='Department of the employee.')
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'Submitted'),
                              ('waiting_approval', 'Waiting Approval'),
                              ('approve', 'Approved'),
                              ('cancel', 'Cancelled'),
                              ('reject', 'Rejected')], string='Status',
                             default='draft',
                             help='State of the salary advance.')
    debit = fields.Many2one('account.account', string='Debit Account',
                            help='Debit account of the salary advance.')
    credit = fields.Many2one('account.account', string='Credit Account',
                             help='Credit account of the salary advance.')
    journal = fields.Many2one('account.journal', string='Journal',
                              help='Journal of the salary advance.')
    employee_contract_id = fields.Many2one('hr.contract', string='Contract',
                                           related='employee_id.contract_id',
                                           help='Running contract of the '
                                                'employee.')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """This method will trigger when there is a change in company_id."""
        company = self.company_id
        domain = [('company_id.id', '=', company.id)]
        result = {
            'domain': {
                'journal': domain,
            },
        }
        return result

    def action_submit_to_manager(self):
        """Method of a button. Changing the state of the salary advance."""
        self.state = 'submit'

    def action_cancel(self):
        """Method of a button. Changing the state of the salary advance."""
        self.state = 'cancel'

    def action_reject(self):
        """Method of a button. Changing the state of the salary advance."""
        self.state = 'reject'

    @api.model_create_multi
    def create(self, vals_list):
        """Supering the create method to generate sequence for the salary
         advance."""
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].get('salary.advance.seq') or ' '
        res_id = super(SalaryAdvance, self).create(vals_list)
        return res_id

    def approve_request(self):
        """This Approves the employee salary advance request."""
        if not self.employee_id.address_id.id:
            raise UserError('Define home address for the employee. i.e address'
                            ' under private information of the employee.')
        salary_advance_search = self.search(
            [('employee_id', '=', self.employee_id.id), ('id', '!=', self.id),
             ('state', '=', 'approve')])
        current_month = datetime.strptime(str(self.date),
                                          '%Y-%m-%d').date().month
        for each_advance in salary_advance_search:
            existing_month = datetime.strptime(str(each_advance.date),
                                               '%Y-%m-%d').date().month
            if current_month == existing_month:
                raise UserError('Advance can be requested once in a month')
        if not self.employee_contract_id:
            raise UserError('Define a contract for the employee')
        if (self.advance > self.employee_contract_id.wage
                and not self.exceed_condition):
            raise UserError('Advance amount is greater than allotted')

        if not self.advance:
            raise UserError('You must Enter the Salary Advance amount')
        payslip_ids = self.env['hr.payslip'].search(
            [('employee_id', '=', self.employee_id.id),
             ('state', '=', 'done'), ('date_from', '<=', self.date),
             ('date_to', '>=', self.date)])
        if payslip_ids:
            raise UserError("This month salary already calculated")
        for slip in self.env['hr.payslip'].search(
                [('employee_id', '=', self.employee_id.id)]):
            slip_moth = datetime.strptime(str(slip.date_from),
                                          '%Y-%m-%d').date().month
            if current_month == slip_moth + 1:
                slip_day = datetime.strptime(str(slip.date_from),
                                             '%Y-%m-%d').date().day
                current_day = datetime.strptime(str(self.date),
                                                '%Y-%m-%d').date().day
                if (current_day - slip_day < self.
                        employee_contract_id.struct_id.advance_date):
                    raise exceptions.UserError(
                        _('Request can be done after "%s" Days From prevoius'
                          ' month salary') % self.
                        employee_contract_id.struct_id.advance_date)
        self.state = 'waiting_approval'

    def approve_request_acc_dept(self):
        """This Approves the employee salary advance request from accounting
         department."""
        salary_advance_search = self.search(
            [('employee_id', '=', self.employee_id.id), ('id', '!=', self.id),
             ('state', '=', 'approve')])
        current_month = datetime.strptime(str(self.date),
                                          '%Y-%m-%d').date().month
        for each_advance in salary_advance_search:
            existing_month = datetime.strptime(str(each_advance.date),
                                               '%Y-%m-%d').date().month
            if current_month == existing_month:
                raise UserError('Advance can be requested once in a month')
        if not self.debit or not self.credit or not self.journal:
            raise UserError("You must enter Debit & Credit account and"
                            " journal to approve ")
        if not self.advance:
            raise UserError('You must Enter the Salary Advance amount')
        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0
        for request in self:
            move = {
                'narration': 'Salary Advance Of ' + request.employee_id.name,
                'ref': request.name,
                'journal_id': request.journal.id,
                'date': time.strftime('%Y-%m-%d'),
            }
            if request.debit.id:
                debit_line = (0, 0, {
                    'name': request.employee_id.name,
                    'account_id': request.debit.id,
                    'journal_id': request.journal.id,
                    'date': time.strftime('%Y-%m-%d'),
                    'debit': request.advance > 0.0 and request.advance or 0.0,
                    'credit': request.advance < 0.0 and -request.advance or 0.0,
                })
                line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
            if request.credit.id:
                credit_line = (0, 0, {
                    'name': request.employee_id.name,
                    'account_id': request.credit.id,
                    'journal_id': request.journal.id,
                    'date': time.strftime('%Y-%m-%d'),
                    'debit': request.advance < 0.0 and -request.advance or 0.0,
                    'credit': request.advance > 0.0 and request.advance or 0.0,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2][
                    'debit']
            move.update({'line_ids': line_ids})
            draft = self.env['account.move'].create(move)
            draft.action_post()
            self.state = 'approve'
            return True

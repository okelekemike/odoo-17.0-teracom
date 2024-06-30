# -*- coding: utf-8 -*-
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import fields, models, _
from odoo.exceptions import UserError


class HrPayslipRun(models.Model):
    """Create new model for getting Payslip Batches"""
    _name = 'hr.payslip.run'
    _description = 'Payslip Batches'

    name = fields.Char(required=True, help="Name for Payslip Batches",
                       string="Name")
    slip_ids = fields.One2many('hr.payslip',
                               'payslip_run_id',
                               string='Payslips',
                               help="Choose Payslips for Batches")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('close', 'Close'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
                               help="Status for Payslip Batches")
    date_start = fields.Date(string='Date From', required=True,
                             help="start date for batch",
                             default=lambda self: fields.Date.to_string(
                                 date.today().replace(day=1)))
    date_end = fields.Date(string='Date To', required=True,
                           help="End date for batch",
                           default=lambda self: fields.Date.to_string(
                               (datetime.now() + relativedelta(months=+1, day=1,
                                                               days=-1)).date())
                           )
    credit_note = fields.Boolean(string='Credit Note',
                                 help="If its checked, indicates that all"
                                      "payslips generated from here are refund payslips.")

    journal_id = fields.Many2one(comodel_name='account.journal',
                                 string='Salary Journal',
                                 required=True, help="Journal associated with the record",
                                 default=lambda self: self.env[
                                     'account.journal'].search(
                                     [('type', '=', 'general')],
                                     limit=1))

    def action_payslip_run(self):
        """Function for state change"""
        return self.write({'state': 'draft'})

    def close_payslip_run(self):
        """Function for state change"""
        return self.write({'state': 'close'})

    def _check_options(self):
        """Check the options and call the corresponding methods."""
        if self.env['ir.config_parameter'].sudo().get_param('automatic_payroll.generate_payslip'):
            if self.env['ir.config_parameter'].sudo().get_param(
                    'automatic_payroll.option', 'first') == 'first':
                self.month_first()
            elif self.env['ir.config_parameter'].sudo().get_param(
                    'automatic_payroll.option', 'specific') == 'specific':
                self.specific_date()
            elif self.env['ir.config_parameter'].sudo().get_param(
                    'automatic_payroll.option', 'end') == 'end':
                self.month_end()
        else:
            raise UserError(_("Enable configuration settings"))

    def month_first(self):
        """Automates payslip generation for the 'Month First' option."""
        today = fields.Date.today()
        day = today.day
        if day == 1:
            self.generate_payslips()
        else:
            raise UserError(_("Today is not month first"))
            pass

    def month_end(self):
        """Automates payslip generation for the 'Month End' option"""
        today = fields.Date.today()
        day_today = today.day
        last_date = today + relativedelta(day=1, months=+1, days=-1)
        last_day = last_date.day
        if day_today == last_day:
            self.generate_payslips()
        else:
            raise UserError(_("Today is not month end"))
            pass

    def specific_date(self):
        """Automates payslip generation for the 'Specific date' option"""
        val = int(self.env['ir.config_parameter'].sudo().get_param('automatic_payroll.generate_day'))
        today = fields.Date.today()
        day = today.day
        if day == val:
            self.generate_payslips()
        else:
            raise UserError(_("Can't generate payslips today"))

    def generate_payslips(self):
        """Method for generate payslip batches and payslips,
        before that you must assign ongoing contracts for employees."""
        batch_id = self.create([{
            'name': 'Payslip Batch For ' + date.today().strftime(
                '%B') + ' ' + str(date.today().year),
            'date_start': fields.Date.to_string(date.today().replace(day=1)),
            'date_end': fields.Date.to_string((datetime.now() + relativedelta(
                months=+1, day=1, days=-1)).date())}])
        generate_payslip = self.env['hr.payslip.employees']
        contract_ids = self.env['hr.contract'].search([('state', '=', 'open')])
        employee_ids = []
        for line in contract_ids:
            employee_ids.append(line.employee_id)
            generate_payslip.create(
                {'employee_ids': [(4, line.employee_id.id)]})
        payslips = self.env['hr.payslip']
        [run_data] = batch_id.read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not employee_ids:
            raise UserError(_("You must select employees to generate payslip."))
        for employee in employee_ids:
            slip_data = self.env['hr.payslip'].onchange_employee_id(
                from_date, to_date, employee.id, contract_id=False)
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': batch_id.id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [
                    (0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id}
            payslips += self.env['hr.payslip'].create(res)
        payslips.action_compute_sheet()
        return {'type': 'ir.actions.act_window_close'}

# -*- coding: utf-8 -*-

from datetime import date, timedelta

from odoo import fields, models


class InheritResCompany(models.Model):
    _inherit = "res.company"

    # HR Contract Reminder
    contract_expiration_reminder = fields.Integer(
        string="Contract Expiration Reminder",
        default=7
    )
    hr_manager_contract_id = fields.Many2one(
        comodel_name="res.users",
        string="HR Manager",
    )


class InheritResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # HR Contract Reminder
    contract_expiration_reminder = fields.Integer(
        string="Contract Expiration Reminder",
        related="company_id.contract_expiration_reminder",
        readonly=False
    )
    hr_manager_contract_id = fields.Many2one(
        related="company_id.hr_manager_contract_id",
        string="HR Manager",
        readonly=False
    )


class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    struct_id = fields.Many2one('hr.payroll.structure',
                                string='Salary Structure',
                                help="Choose Payroll Structure")
    schedule_pay = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi-annually', 'Semi-annually'),
        ('annually', 'Annually'),
        ('weekly', 'Weekly'),
        ('bi-weekly', 'Bi-weekly'),
        ('bi-monthly', 'Bi-monthly'),
    ], string='Scheduled Pay', index=True, default='monthly',
        help="Defines the frequency of the wage payment.")
    resource_calendar_id = fields.Many2one(required=True,
                                           string="Working Schedule",
                                           help="Employee's working schedule.")
    hra = fields.Monetary(string='HRA', tracking=True, help="House rent allowance.")
    da = fields.Monetary(string="DA", help="Dearness allowance")
    travel_allowance = fields.Monetary(string="Travel Allowance", help="Travel allowance")
    meal_allowance = fields.Monetary(string="Meal Allowance", help="Meal allowance")
    medical_allowance = fields.Monetary(string="Medical Allowance", help="Medical allowance")
    other_allowance = fields.Monetary(string="Other Allowance", help="Other allowances")

    shift_schedule = fields.One2many('hr.shift.schedule', 'rel_hr_schedule',
                                     string="Shift Schedule", help="Shift schedule")
    working_hours = fields.Many2one('resource.calendar', string='Working Schedule', help="Working hours")

    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by
        hierarchy (parent=False first,then first level children and so on)
        and without duplicate
        """
        structures = self.mapped('struct_id')
        if not structures:
            return []
        # YTI TODO return browse records
        return list(set(structures._get_parent_structure().ids))

    def get_attribute(self, code, attribute):
        """Function for return code for Contract"""
        return self.env['hr.contract.advantage.template'].search(
                [('code', '=', code)],
                limit=1)[attribute]

    def set_attribute_value(self, code, active):
        """Function for set code for Contract"""
        for contract in self:
            if active:
                value = self.env['hr.contract.advantage.template'].search(
                    [('code', '=', code)], limit=1).default_value
                contract[code] = value
            else:
                contract[code] = 0.0

    # Payroll Accounting
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          string='Analytic Account',
                                          help="Select Analytic account")
    journal_id = fields.Many2one('account.journal',
                                 string='Salary Journal',
                                 help="Journal associated with the record")

    # Employee Notice Period
    def _default_notice_days(self):
        """Get the default notice period from the  configuration.
            :return: The default notice period in days.
            :rtype: int """
        if self.env['ir.config_parameter'].get_param(
                'accounting_base_kit.notice_period'):
            return self.env['ir.config_parameter'].get_param(
                'accounting_base_kit.no_of_days')
        else:
            return 0

    notice_days = fields.Integer(string="Notice Period",
                                 default=_default_notice_days,
                                 help="Number of days required for notice"
                                      " before termination.")
    # HR Contract Reminder
    def _send_email_to_hr_manager(self, hr_manager_contract_id, contracts):
        """
            Sends an email reminder to the HR manager about expiring contracts.
        """

        template_hr_manager_id = self.env.ref(
            'accounting_base_kit.mail_template_reminder_contract_hr_manager',
            raise_if_not_found=False
        )

        ctx_hr_manager = {
            'hr_manager_contract_id': hr_manager_contract_id.employee_id.name,
            'contracts': [contract.employee_id.name + " - " + (
                contract.date_end).strftime("%d-%m-%Y") for contract in contracts],
            'email_from': self.env.user.company_id.email,
            'email_to': str(hr_manager_contract_id.employee_id.work_email),
            'company_name': self.env.user.company_id.name
        }
        template_hr_manager_id.with_context(ctx_hr_manager).send_mail(self.id, force_send=True, raise_exception=False)

    def _send_email_to_employee(self, employee, contract):
        """
            Sends an email reminder to an employee about their expiring contract.
        """

        template_employee_id = self.env.ref(
            'accounting_base_kit.mail_template_reminder_contract_employee',
            raise_if_not_found=False
        )

        ctx_employee = {
            'employee_name': employee.name,
            'contract_date': (contract.date_end).strftime("%d-%m-%Y"),
            'email_from': self.env.user.company_id.email,
            'email_to': str(employee.work_email),
            'company_name': self.env.user.company_id.name
        }
        template_employee_id.with_context(ctx_employee).send_mail(self.id, force_send=True, raise_exception=False)

    def _cron_auto_reminder_hr_contract(self):
        """
            Cron job function to automatically send contract expiration reminders.
        """
        company = self.env['res.company'].sudo().search([], limit=1)
        if company:
            contract_expiration_reminder = company.contract_expiration_reminder
            hr_manager_contract_id = company.hr_manager_contract_id
            reminder = date.today() + timedelta(days=contract_expiration_reminder)
            contracts = self.search([("date_end", "=", reminder)])

            if contracts:
                self._send_email_to_hr_manager(hr_manager_contract_id, contracts)
                for contract in contracts:
                    employee = contract.employee_id
                    if employee:
                        self._send_email_to_employee(employee, contract)
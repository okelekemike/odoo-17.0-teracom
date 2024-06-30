# -*- coding: utf-8 -*-
import base64
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

GENDER_SELECTION = [('male', 'Male'),
                    ('female', 'Female'),
                    ('other', 'Other')]


class HrEmployee(models.Model):
    """Inherit hr_employee for getting Payslip Counts"""
    _inherit = 'hr.employee'

    slip_ids = fields.One2many('hr.payslip',
                               'employee_id', string='Payslips',
                               readonly=True,
                               help="Choose Payslip for Employee")

    payslip_count = fields.Integer(compute='_compute_payslip_count',
                                   string='Payslip Count',
                                   help="Set Payslip Count")

    resource_calendar_ids = fields.Many2one('resource.calendar', 'Working Hours', help="Calendar ids")

    barcode_image = fields.Binary(string='Badge Barcode', compute='generate_barcode_image', readonly=True)

    def _compute_payslip_count(self):
        """Function for count Payslips"""
        payslip_data = self.env['hr.payslip'].sudo().read_group(
            [('employee_id', 'in', self.ids)],
            ['employee_id'], ['employee_id'])
        result = dict(
            (data['employee_id'][0], data['employee_id_count']) for data in
            payslip_data)
        for employee in self:
            employee.payslip_count = result.get(employee.id, 0)

    @api.depends('barcode')
    def generate_barcode_image(self):
        """
        Generate a Barcode Image
        :return:
        """
        for rec in self:
            rec.barcode_image = None
            if rec.barcode:
                barcode = rec.barcode.strip()
                rec.barcode_image = base64.b64encode(self.env['ir.actions.report'].barcode(
                    'Code128', barcode, width=1000, height=300, humanreadable=1)
                )

    personal_mobile = fields.Char(string='Mobile', related='private_phone',
                                  help="Personal mobile number of the employee", store=True, )
    joining_date = fields.Date(compute='_compute_joining_date',
                               string='Joining Date', store=True,
                               help="Employee joining date computed from the contract start date")
    id_expiry_date = fields.Date(help='Expiry date of Identification document', string='Expiry Date', )
    passport_expiry_date = fields.Date(help='Expiry date of Passport ID', string='Passport Expiry Date')
    identification_attachment_ids = fields.Many2many(
        'ir.attachment', 'id_attachment_rel',
        'id_ref', 'attach_ref', string="Attachment",
        help='Attach the copy of Identification document')
    passport_attachment_ids = fields.Many2many(
        'ir.attachment',
        'passport_attachment_rel',
        'passport_ref', 'attach_ref1', string="Passport Attachment",
        help='Attach the copy of Passport')
    is_non_resident = fields.Boolean('Non Resident', default=False,
                                     help="Check if employee lives in a foreign country")
    family_info_ids = fields.One2many('hr.employee.family', 'employee_id',
                                      string='Family',
                                      help='Family Information')
    visa_issue_date = fields.Date(string='Visa Issue Date',
                                  help='Date of Visa Issued', )
    visa_expiry_days = fields.Integer(compute='_compute_visa_expiry_days',
                                      string='Visa Expiry Days',
                                      help="Set Visa Expiry Days")
    age = fields.Integer(compute='_compute_age', string='Age', help="Employee Age")

    @api.depends('visa_expire')
    def _compute_visa_expiry_days(self):
        for employee in self:
            employee.visa_expiry_days = 0
            if employee.visa_expire:
                employee.visa_expiry_days = (employee.visa_expire - fields.Date.today()).days

    @api.depends('birthday')
    def _compute_age(self):
        for employee in self:
            employee.age = 0
            if employee.birthday:
                employee.age = (fields.Date.today() - employee.birthday).days // 365

    hourly_cost = fields.Monetary('Hourly Cost', compute='_compute_hourly_cost',
                                  currency_field='currency_id',
                                  groups="hr.group_hr_user", default=0.0)

    @api.depends('contract_id')
    def _compute_joining_date(self):
        """Compute the joining date of the employee based on their contract
         information."""
        for employee in self:
            employee.joining_date = min(
                employee.contract_id.mapped('date_start')) \
                if employee.contract_id else False

    @api.depends('contract_id')
    def _compute_hourly_cost(self):
        for employee in self:
            if employee.contract_id:
                hours_per_month = employee.contract_id.mapped('resource_calendar_id').hours_per_day * 28
                wage_per_month = sum(employee.contract_id.mapped('wage'))
                employee.hourly_cost = wage_per_month / hours_per_month
            else:
                employee.hourly_cost = 0

    @api.onchange('spouse_complete_name', 'spouse_birthdate')
    def _onchange_spouse_complete_name(self):
        """Populates the family_info_ids field with the spouse's information,
         creating a family member record associated with the employee when
         spouse's complete name or birthdate changed."""
        relation = self.env.ref('accounting_base_kit.employee_relationship_spouse')
        if self.spouse_complete_name and self.spouse_birthdate:
            self.family_info_ids = [(0, 0, {
                'member_name': self.spouse_complete_name,
                'relation_id': relation.id,
                'birth_date': self.spouse_birthdate,
            })]

    def expiry_mail_reminder(self):
        """Sending ID and Passport expiry notification."""
        current_date = fields.Date.context_today(self) + timedelta(days=1)
        employee_ids = self.search(['|', ('id_expiry_date', '!=', False),
                                    ('passport_expiry_date', '!=', False)])
        for employee in employee_ids:
            if employee.id_expiry_date:
                exp_date = fields.Date.from_string(
                    employee.id_expiry_date) - timedelta(days=14)
                if current_date >= exp_date:
                    mail_content = ("Hello  " + employee.name + ",<br>Your ID "
                                    + employee.identification_id +
                                    " is going to expire on " +
                                    str(employee.id_expiry_date)
                                    + ". Please renew it before expiry date")
                    main_content = {
                        'subject': _('ID-%s Expired On %s') % (
                            employee.identification_id,
                            employee.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': employee.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
            if employee.passport_expiry_date:
                exp_date = fields.Date.from_string(
                    employee.passport_expiry_date) - timedelta(days=180)
                if current_date >= exp_date:
                    mail_content = ("  Hello  " + employee.name +
                                    ",<br>Your Passport " + employee.passport_id
                                    + " is going to expire on " +
                                    str(employee.passport_expiry_date) +
                                    ". Please renew it before expire")
                    main_content = {
                        'subject': _('Passport-%s Expired On %s') % (
                            employee.passport_id,
                            employee.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': employee.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()

    state = fields.Selection([('joined', 'Slap On'),
                              ('grounding', 'Grounding'),
                              ('test_period', 'Test Period'),
                              ('employment', 'Employment'),
                              ('notice_period', 'Notice Period'),
                              ('relieved', 'Resigned'),
                              ('terminate', 'Terminated')], string='Status',
                             default='joined', copy=False,
                             help="Employee Stages.\nSlap On: Joined \nGrounding: Training \nTest Period : Probation")

    stages_history_ids = fields.One2many('hr.employee.status.history',
                                         'employee_id', string='Stage History',
                                         help='It shows the duration and history of history stages')

    discipline_count = fields.Integer(compute="_compute_discipline_count")

    def _compute_discipline_count(self):
        """Compute the employee details based on the discipline count"""
        all_actions = self.env['disciplinary.action'].read_group([
            ('employee_name', 'in', self.ids),
            ('state', '=', 'action'),
        ], fields=['employee_name'], groupby=['employee_name'])
        mapping = dict(
            [(action['employee_name'][0], action['employee_name_count']) for
             action in all_actions])
        for employee in self:
            employee.discipline_count = mapping.get(employee.id, 0)

    @api.model_create_multi
    def create(self, vals_list):
        """This is used to create the default stage as 'Slap On'"""
        result = super().create(vals_list)
        result.action_start_joined()
        return result

    def action_start_joined(self):
        """This is used to create the joined stage on staging history"""
        self.state = 'joined'
        self.stages_history_ids.sudo().create({'start_date': fields.Date.today(),
                                               'employee_id': self.id,
                                               'state': 'joined'})

    def action_start_grounding(self):
        """This is used to create the ground stage on staging history"""
        self.state = 'grounding'
        self.stages_history_ids.sudo().create({'start_date': fields.Date.today(),
                                               'employee_id': self.id,
                                               'state': 'grounding'})

    def set_as_employee(self):
        """This is used to create the employee stage on staging history"""
        self.state = 'employment'
        stage_history_ids = self.stages_history_ids.search(
            [('employee_id', '=', self.id),
             ('state', '=', 'test_period')])
        if stage_history_ids:
            stage_history_ids.sudo().write({'end_date': fields.Date.today()})
        self.stages_history_ids.sudo().create({'start_date': fields.Date.today(),
                                               'employee_id': self.id,
                                               'state': 'employment'})

    def action_start_notice_period(self):
        """This is used to create the notice period stage on staging history"""
        self.state = 'notice_period'
        stage_history_ids = self.stages_history_ids.search(
            [('employee_id', '=', self.id),
             ('state', '=', 'employment')])
        if stage_history_ids:
            stage_history_ids.sudo().write({'end_date': fields.Date.today()})
        self.stages_history_ids.sudo().create({'start_date': fields.Date.today(),
                                               'employee_id': self.id,
                                               'state': 'notice_period'})

    def action_relived(self):
        """This is used to create the relived stage on staging history"""
        self.state = 'relieved'
        self.active = False
        stage_history_ids = self.stages_history_ids.search(
            [('employee_id', '=', self.id),
             ('state', '=',
              'notice_period')])
        if stage_history_ids:
            stage_history_ids.sudo().write({'end_date': fields.Date.today()})
        self.stages_history_ids.sudo().create({'end_date': fields.Date.today(),
                                               'employee_id': self.id,
                                               'state': 'relieved'})

    def action_start_test_period(self):
        """This is used to create the test period stage on staging history"""
        self.state = 'test_period'
        self.stages_history_ids.search([('employee_id', '=', self.id),
                                        ('state', '=',
                                         'grounding')]).sudo().write(
            {'end_date': fields.Date.today()})
        self.stages_history_ids.sudo().create({'start_date': fields.Date.today(),
                                               'employee_id': self.id,
                                               'state': 'test_period'})

    def action_terminate(self):
        """This is used to create the terminate stage on staging history"""
        self.state = 'terminate'
        self.active = False
        stage_history_ids = self.stages_history_ids.search(
            [('employee_id', '=', self.id),
             ('state', '=', 'employment')])
        if stage_history_ids:
            stage_history_ids.sudo().write({'end_date': fields.Date.today()})
        else:
            self.stages_history_ids.search([('employee_id', '=', self.id),
                                            ('state', '=',
                                             'grounding')]).sudo().write(
                {'end_date': fields.Date.today()})
        self.stages_history_ids.sudo().create({'end_date': fields.Date.today(),
                                               'employee_id': self.id,
                                               'state': 'terminate'})

    # Extends the 'hr.employee' model to include additional fields related to
    # employee resignation.

    resign_date = fields.Date('Resign Date', readonly=True,
                              help="Date of the resignation")
    resigned = fields.Boolean(string="Resigned", default=False,
                              help="If checked then employee has resigned")
    fired = fields.Boolean(string="Fired", default=False,
                           help="If checked then employee has fired")

    # Extends the 'hr.employee' model to include additional fields related to
    # employee loans.
    loan_count = fields.Integer(
        string="Loan Count",
        help="Number of loans associated with the employee",
        compute='_compute_loan_count')

    def _compute_loan_count(self):
        """Compute the number of loans associated with the employee."""
        self.loan_count = self.env['hr.loan'].search_count(
            [('employee_id', '=', self.id)])

    late_check_in_count = fields.Integer(
        string="Late Check-In", compute="_compute_late_check_in_count",
        help="Count of employee's late checkin")

    def action_to_open_late_check_in_records(self):
        """
            :return: dictionary defining the action to open the late check-in
            records window.
            :rtype: dict
        """
        return {
            'name': _('Employee Late Check-In'),
            'domain': [('employee_id', '=', self.id)],
            'res_model': 'late.check.in',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'limit': 80}

    def _compute_late_check_in_count(self):
        """Compute the late check-in count"""
        for rec in self:
            rec.late_check_in_count = self.env['late.check.in'].search_count(
                [('employee_id', '=', rec.id)])

    # Employee Announcement
    announcement_count = fields.Integer(compute='_compute_announcement_count',
                                        string='# Announcements',
                                        help="Count of Announcements")

    def _compute_announcement_count(self):
        """ Compute announcement count for an employee """
        for employee in self:
            announcement_ids_general = self.env[
                'hr.announcement'].sudo().search_count(
                [('is_announcement', '=', True),
                 ('state', 'in', ('approved', 'done')),
                 ('date_start', '<=', fields.Date.today())])
            announcement_ids_emp = (self.env['hr.announcement'].
            sudo().search_count(
                [('employee_ids', 'in', self.id),
                 ('state', 'in', ('approved', 'done')),
                 ('date_start', '<=', fields.Date.today())]))
            announcement_ids_dep = (self.env['hr.announcement'].
            sudo().search_count(
                [('department_ids', 'in', self.department_id.id),
                 ('state', 'in', ('approved', 'done')),
                 ('date_start', '<=', fields.Date.today())]))
            announcement_ids_job = (self.env['hr.announcement'].
            sudo().search_count(
                [('position_ids', 'in', self.job_id.id),
                 ('state', 'in', ('approved', 'done')),
                 ('date_start', '<=', fields.Date.today())]))
            employee.announcement_count = (announcement_ids_general +
                                           announcement_ids_emp +
                                           announcement_ids_dep +
                                           announcement_ids_job)

    def action_open_announcements(self):
        """ Open a view displaying announcements related to the employee. """
        announcement_ids_general = self.env[
            'hr.announcement'].sudo().search(
            [('is_announcement', '=', True),
             ('state', 'in', ('approved', 'done')),
             ('date_start', '<=', fields.Date.today())])
        announcement_ids_emp = self.env['hr.announcement'].sudo().search(
            [('employee_ids', 'in', self.id),
             ('state', 'in', ('approved', 'done')),
             ('date_start', '<=', fields.Date.today())])
        announcement_ids_dep = self.env['hr.announcement'].sudo().search(
            [('department_ids', 'in', self.department_id.id),
             ('state', 'in', ('approved', 'done')),
             ('date_start', '<=', fields.Date.today())])
        announcement_ids_job = self.env['hr.announcement'].sudo().search(
            [('position_ids', 'in', self.job_id.id),
             ('state', 'in', ('approved', 'done')),
             ('date_start', '<=', fields.Date.today())])
        announcement_ids = (announcement_ids_general.ids +
                            announcement_ids_emp.ids +
                            announcement_ids_job.ids + announcement_ids_dep.ids)
        view_id = self.env.ref('hr_reward_warning.hr_announcement_view_form').id
        if announcement_ids:
            if len(announcement_ids) > 1:
                value = {
                    'domain': [('id', 'in', announcement_ids)],
                    'view_mode': 'tree,form',
                    'res_model': 'hr.announcement',
                    'type': 'ir.actions.act_window',
                    'name': _('Announcements'),
                }
            else:
                value = {
                    'view_mode': 'form',
                    'res_model': 'hr.announcement',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Announcements'),
                    'res_id': announcement_ids and announcement_ids[0],
                }
            return value

    def get_leave_balance(self, leave_type_id, balance_date=None):
        self.ensure_one()
        if isinstance(leave_type_id, models.BaseModel):
            leave_type_id = leave_type_id.id
        elif isinstance(leave_type_id, int):
            pass
        elif isinstance(leave_type_id, str):
            leave_type_id = self.env['hr.leave.type'].search([('name', '=', leave_type_id)], limit=1).id

        if not balance_date:
            balance_date = fields.Date.today()

        def duration(date1, date2):
            date1 = fields.Date.from_string(date1)
            date2 = fields.Date.from_string(date2 if date2 else fields.Date.today())
            return (date2 - date1).days + 1

        balance = 0
        leaves = self.env['hr.leave'].search(
            [('employee_id', '=', self.id),
             ('state', '=', 'validate'),
             ('holiday_status_id', '=', leave_type_id),
             ('date_from', '<=', balance_date)]
        )
        for leave in leaves:
            if leave.date_to.date() <= balance_date:
                balance -= leave.number_of_days
            else:
                holiday_days = duration(leave.date_from, leave.date_to)
                affected_days = duration(leave.date_from, balance_date)
                balance += leave.number_of_days * (affected_days / holiday_days)

        allocations = self.env['hr.leave.allocation'].search(
            [('employee_id', '=', self.id),
             ('state', '=', 'validate'),
             ('holiday_status_id', '=', leave_type_id), '|',
             ('period_date_from', '<=', balance_date),
             ('period_date_from', '=', False)]
        )
        for allocation in allocations:
            if not allocation.period_date_to or allocation.period_date_to <= balance_date or allocation.allocation_type == 'accrual':
                balance += allocation.number_of_days
            else:
                from_string = fields.Date.from_string
                to_months = lambda delta: delta.years * 12 + delta.months + delta.days / 30
                holiday_delta = relativedelta(from_string(allocation.period_date_to) + timedelta(days=1),
                                              from_string(allocation.period_date_from))
                affected_delta = relativedelta(from_string(balance_date) + timedelta(days=1),
                                               from_string(allocation.period_date_from))
                balance += allocation.number_of_days * (to_months(affected_delta) / to_months(holiday_delta))

        return round(balance, 2)


class EmployeeStageHistory(models.Model):
    """This is used to show the employee stages history"""
    _name = 'hr.employee.status.history'
    _description = 'Status History'

    start_date = fields.Date(string='Start Date',
                             help="Start date of the status period")

    end_date = fields.Date(string='End Date',
                           help="End date of the status period")

    duration = fields.Integer(compute='_compute_get_duration',
                              string='Duration(days)',
                              help="Duration of the stage")

    state = fields.Selection([('joined', 'Slap On'),
                              ('grounding', 'Grounding'),
                              ('test_period', 'Test Period'),
                              ('employment', 'Employment'),
                              ('notice_period', 'Notice Period'),
                              ('relieved', 'Resigned'),
                              ('terminate', 'Terminated')], string='Stage')

    employee_id = fields.Many2one('hr.employee', help="Stage of the employee", string="Employee")

    @api.depends('start_date', 'end_date')
    def _compute_get_duration(self):
        """This is used to calculate the duration for the stages"""
        for history in self:
            history.duration = 0
            end_date = history.end_date if history.end_date else fields.Date.today()
            if history.start_date:
                duration = fields.Date.from_string(
                    end_date) - fields.Date.from_string(history.start_date)
                history.duration = duration.days

    @api.onchange('state')
    def update_status(self):
        """This is used to update the status of the employee"""
        latest_stage = self.env['hr.employee.status.history'].search(
            [('employee_id', '=', self.employee_id.id)], order='id desc', limit=1)
        if latest_stage:
            self.employee_id.state = latest_stage.state
        else:
            self.employee_id.state = 'joined'


class HrEmployeeFamily(models.Model):
    """Table for keep employee family information"""
    _name = 'hr.employee.family'
    _description = 'HR Employee Family Information'
    _rec_name = 'member_name'

    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  help='Select corresponding Employee', )
    relation_id = fields.Many2one('hr.employee.relation', string="Relation",
                                  help="Relationship with the employee")
    member_name = fields.Char(string='Name', help='Name of the family member')
    member_contact = fields.Char(string='Contact No',
                                 help='Contact No of the family member')
    birth_date = fields.Date(string="DOB",
                             help='Birth date of the family member')
    age = fields.Integer(string="Age", compute="_compute_age")
    on_visa = fields.Boolean(string="On Visa", default=False,
                             help='Is the family member on a Visa?')
    visa_nationality = fields.Many2one('res.country', string="Visa Nationality",
                                       default=lambda self: self.env.user.company_id.country_id,
                                       help='Visa Nationality of the family member')
    visa_no = fields.Char(string="Visa Number",
                          help='Visa Number of the family member')
    visa_issue_date = fields.Date(string="Visa Issue Date",
                                  help='Visa Issue date of the family member')
    visa_expiry_date = fields.Date(string="Visa Expiry Date",
                                   help='Visa Expiry date of the family member')
    visa_expiry_days = fields.Integer(string="Visa Expiry Days", compute="_compute_visa_expiry_days")

    @api.depends('visa_expiry_date')
    def _compute_visa_expiry_days(self):
        for rec in self:
            rec.visa_expiry_days = 0
            if rec.visa_expiry_date:
                rec.visa_expiry_days = (rec.visa_expiry_date - fields.Date.today()).days

    @api.depends('birth_date')
    def _compute_age(self):
        for rec in self:
            rec.age = 0
            if rec.birth_date:
                rec.age = (fields.Date.today() - rec.birth_date).days / 365


class HrEmployeePublic(models.Model):
    """This is used to inherit the public employee model"""
    _inherit = 'hr.employee.public'

    state = fields.Selection(related='employee_id.state',
                             string='Stage',
                             help="Stages of employee")

    late_check_in_count = fields.Integer(
        string="Late Check-In", compute="_compute_late_check_in_count",
        help="Count of employee's late checkin")

    def action_to_open_late_check_in_records(self):
        """
            :return: dictionary defining the action to open the late check-in
            records window.
            :rtype: dict
        """
        return {
            'name': _('Employee Late Check-In'),
            'domain': [('employee_id', '=', self.id)],
            'res_model': 'late.check.in',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'limit': 80}

    def _compute_late_check_in_count(self):
        """Compute the late check-in count"""
        for rec in self:
            rec.late_check_in_count = self.env['late.check.in'].search_count(
                [('employee_id', '=', rec.id)])


class HrEmployeeContact(models.Model):
    """This is used to inherit the contact model"""
    _inherit = 'hr.contract'

    total_wage = fields.Monetary(string="Total Wage", compute='_compute_total_wage')

    @api.onchange('wage', 'hra', 'da', 'meal_allowance', 'travel_allowance', 'medical_allowance', 'other_allowance')
    def _compute_total_wage(self):
        for record in self:
            record.total_wage = record.wage + record.hra + record.da + record.meal_allowance + \
                                record.travel_allowance + record.medical_allowance + record.other_allowance


class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    period_date_from = fields.Date('Period Start Date')
    period_date_to = fields.Date('Period End Date')

    @api.constrains('period_date_from', 'period_date_to')
    def _check_period_date(self):
        for record in self:
            if record.period_date_from and record.period_date_to and record.period_date_from > record.period_date_to:
                raise ValidationError(_('Period Start Date > Period End Date'))
            if record.period_date_from and not record.period_date_to:
                raise ValidationError(_('Period End Date'))
            if not record.period_date_from and record.period_date_to:
                raise ValidationError(_('Period Start Date'))

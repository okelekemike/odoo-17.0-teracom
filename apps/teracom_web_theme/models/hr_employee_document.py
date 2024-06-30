# -*- coding: utf-8 -*-

from datetime import datetime, date, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EmployeeChecklist(models.Model):
    """Create an 'employee_checklist' model to incorporate
    details about document types"""
    _name = 'employee.checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Checklist"
    _order = 'sequence'

    name = fields.Char(string='Document Name', copy=False, required=True,
                       help="Enter Document Name")
    document_type = fields.Selection([('entry', 'Entry Process'),
                                      ('exit', 'Exit Process'),
                                      ('other', 'Other')],
                                     string='Checklist Type', required=True,
                                     help="Select checklist type for document")
    sequence = fields.Integer(string='Sequence', help="Sequence of Checklist")
    entry_obj = fields.Many2many('hr.employee', 'entry_checklist',
                                 'hr_check_rel', 'check_hr_rel',
                                 string="Entry Object")
    exit_obj = fields.Many2many('hr.employee', 'exit_checklist', 'hr_exit_rel',
                                'exit_hr_rel', string="Exit Object")
    entry_obj_plan = fields.Many2many('hr.employee', 'entry_checklist_plan_ds',
                                      'hr_check_rel', 'check_hr_rel',
                                      string="Plan Object")
    exit_obj_plan = fields.Many2many('hr.employee', 'exit_checklist_plan_ids',
                                     'hr_exit_rel', 'exit_hr_rel',
                                     string='Exit Plan Object')


    def name_get(self):
        """Function to obtain the names '_en,' '_ex,' or '_ot'
        for entry, exit, and other."""
        result = []
        for each in self:
            if each.document_type == 'entry':
                name = each.name + '_en'
            elif each.document_type == 'exit':
                name = each.name + '_ex'
            elif each.document_type == 'other':
                name = each.name + '_ot'
            result.append((each.id, name))
        return result


class DocumentType(models.Model):
    """This model add details of document type"""
    _name = 'document.type'
    _description = "Document Type"

    name = fields.Char(string="Name", required=True,
                       help="Name of the document type")


class HrEmployeeDocument(models.Model):
    """Create a new module for retrieving document files, allowing users
     to input details about the documents."""
    _name = 'hr.employee.document'
    _description = 'HR Employee Documents'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_employee_id(self):
        """Get the ID of the currently logged-in employee"""
        if self.env['hr.employee'].id:
            return self.env['hr.employee'].id
        employee_rec = self.env['hr.employee'].search([
            ('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    name = fields.Char(string='Document Number', required=True, copy=False, help="Enter Document Number")
    document_id = fields.Many2one('employee.checklist', string='Document Checklist', required=True,
                                  help="Choose Employee Checklist for Employee Document")
    description = fields.Text(string='Description', copy=False,
                              help="Description for Employee Document")
    expiry_date = fields.Date(string='Expiry Date', copy=False,
                              help="Choose Expiry Date for Employee Document")
    employee_ref_id = fields.Many2one(comodel_name='hr.employee', default=_get_employee_id, copy=False, required=True)
    doc_attachment_ids = fields.Many2many('ir.attachment', 'doc_attach_ids', 'doc_id', 'attach_id3',
                                          string="Attachment", copy=False,
                                          help='You can attach the copy of your document')
    issue_date = fields.Date(string='Issue Date',
                             default=fields.Date.context_today, copy=False,
                             help="Choose Issue Date for Employee Document")
    document_type_id = fields.Many2one(comodel_name='document.type',
                                       string="Document Type",
                                       help="Document type of employee")
    before_days = fields.Integer(string="Notification Days",
                                 help="How many number of days before to get the notification email")
    notification_type = fields.Selection([
        ('single', 'Notification on expiry date'),
        ('multi', 'Notification before few days'),
        ('everyday', 'Everyday till expiry date'),
        ('everyday_after', 'Notification on and after expiry')
    ], string='Notification Type',
        help="Notification on expiry date: You will get notification only on "
             "expiry date. Notification before few days: You will get "
             "notification in 2 days.On expiry date and number of days before "
             "date. Everyday till expiry date: You will get notification from "
             "number of days till the expiry date of the document. Notification"
             " on and after expiry: You will get notification on the expiry "
             "date and continues up to Days. If you didn't select any then you "
             "will get notification before 7 days of document expiry.")

    def mail_reminder(self):
        """Function for scheduling emails to send reminders
        about document expiry notification to employees."""
        date_now = fields.Date.today()
        for record in self.search([]):
            if record.expiry_date:
                if record.notification_type == 'single':
                    if date_now == record.expiry_date:
                        mail_content = ("  Hello  " + record.employee_ref_id.
                                        name + ",<br>Your Document " +
                                        record.name +
                                        " is expiring today, please renew it")
                        main_content = {
                            'subject': _('Document-%s Expired On %s') % (
                                record.name, record.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': record.employee_ref_id.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()
                elif record.notification_type == 'multi':
                    exp_date = fields.Date.from_string(
                        record.expiry_date) - timedelta(days=record.before_days)
                    if date_now == exp_date or date_now == record.expiry_date:
                        mail_content = ("  Hello  " + record.employee_ref_id.
                                        name + ",<br>Your Document " +
                                        record.name + " is going to expire on "
                                        + str(record.expiry_date) +
                                        ". Please renew it before expiry date")
                        main_content = {
                            'subject': _('Document-%s Expiry on %s') % (
                                record.name, record.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': record.employee_ref_id.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()
                elif record.notification_type == 'everyday':
                    exp_date = fields.Date.from_string(
                        record.expiry_date) - timedelta(days=record.before_days)
                    if exp_date <= date_now <= record.expiry_date:
                        mail_content = ("  Hello  " +
                                        record.employee_ref_id.name
                                        + ",<br>Your Document " + record.name +
                                        " is going to expire on " +
                                        str(record.expiry_date) +
                                        ". Please renew it before expiry date")
                        main_content = {
                            'subject': _('Document-%s Expiry on %s') % (
                                record.name, record.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': record.employee_ref_id.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()
                elif record.notification_type == 'everyday_after':
                    exp_date = fields.Date.from_string(
                        record.expiry_date) + timedelta(days=record.before_days)
                    if record.expiry_date <= date_now <= exp_date:
                        mail_content = ("  Hello  " +
                                        record.employee_ref_id.name +
                                        ",<br>Your Document " + record.name +
                                        " is expired on " +
                                        str(record.expiry_date) +
                                        ". Please renew it ")
                        main_content = {
                            'subject': _('Document-%s Expired On %s') % (
                                record.name, record.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': record.employee_ref_id.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()
                else:
                    exp_date = fields.Date.from_string(
                        record.expiry_date) - timedelta(days=7)
                    if date_now == exp_date:
                        mail_content = ("  Hello  " + record.employee_ref_id.
                                        name + ",<br>Your Document " +
                                        record.name + " is going to expire on "
                                        + str(record.expiry_date) +
                                        ". Please renew it before expiry date ")
                        main_content = {
                            'subject': _('Document-%s Expired On %s') % (
                                record.name, record.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': record.employee_ref_id.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()

    @api.onchange('expiry_date')
    def check_expr_date(self):
        """Function to obtain a validation error for expired documents."""
        if self.expiry_date and self.expiry_date < date.today():
            return {
                'warning': {
                    'title': _('Document Expired.'),
                    'message': _("Your Document Is Already Expired.")
                }
            }

    @api.model_create_multi
    def create(self, vals):
        """Supering the create function"""
        result = super().create(vals)
        if result.document_id.document_type == 'entry':
            result.employee_ref.write(
                {'entry_checklist': [(4, result.document_id.id)]})
        if result.document_id.document_type == 'exit':
            result.employee_ref.write(
                {'exit_checklist': [(4, result.document_id.id)]})
        return result

    def unlink(self):
        """Supering the unlink method"""
        for result in self:
            if result.document_id.document_type == 'entry':
                result.employee_ref.write(
                    {'entry_checklist': [(5, result.document_id.id)]})
            if result.document_id.document_type == 'exit':
                result.employee_ref.write(
                    {'exit_checklist': [(5, result.document_id.id)]})
        res = super().unlink()
        return res


class HrEmployee(models.Model):
    """Inherit the 'hr_employee' module to add 'Documents' super button."""
    _inherit = 'hr.employee'

    document_count = fields.Integer(compute='_compute_document_count',
                                    string='# Documents',
                                    help="Get total count of Document for an Employee")

    def _compute_document_count(self):
        """Function to obtain the total count of documents."""
        for rec in self:
            rec.document_count = self.env['hr.employee.document'].search_count(
                [('employee_ref_id', '=', rec.id)])

    def document_view(self):
        """Function to open the 'hr_employee_document' model."""
        self.ensure_one()
        return {
            'name': _('Documents'),
            'domain': [('employee_ref_id', '=', self.id)],
            'res_model': 'hr.employee.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create for New Documents
                        </p>'''),
            'limit': 80,
            'context': {'default_employee_id': self.id}
        }

    @api.depends('exit_checklist')
    def exit_progress(self):
        """This is used to determine the exit status"""
        for each in self:
            total_len = self.env['employee.checklist'].search_count(
                [('document_type', '=', 'exit')])
            entry_len = len(each.exit_checklist)
            if total_len != 0:
                each.exit_progress = (entry_len * 100) / total_len

    @api.depends('entry_checklist')
    def entry_progress(self):
        """This is used to determine the entry status"""
        for each in self:
            total_len = self.env['employee.checklist'].search_count(
                [('document_type', '=', 'entry')])
            entry_len = len(each.entry_checklist)
            if total_len != 0:
                each.entry_progress = (entry_len * 100) / total_len

    entry_checklist = fields.Many2many('employee.checklist', 'entry_obj',
                                       'check_hr_rel', 'hr_check_rel',
                                       string='Entry Process',
                                       domain=[('document_type', '=', 'entry')],
                                       help="Entry Checklist's")
    exit_checklist = fields.Many2many('employee.checklist', 'exit_obj',
                                      'exit_hr_rel', 'hr_exit_rel',
                                      string='Exit Process',
                                      domain=[('document_type', '=', 'exit')],
                                      help="Exit Checklist's")
    entry_progress = fields.Float(compute=entry_progress, string='Entry Progress',
                                  store=True, default=0.0,
                                  help="Percentage of Entry Checklist's")
    exit_progress = fields.Float(compute=exit_progress, string='Exit Progress',
                                 store=True, default=0.0,
                                 help="Percentage of Exit Checklist's")
    maximum_rate = fields.Integer(default=100)
    check_list_enable = fields.Boolean(copy=False)


class HrDocument(models.Model):
    """Store the details of employee documents"""
    _name = 'hr.document'
    _description = 'Documents Template '

    name = fields.Char(string='Document Name', required=True, copy=False,
                       help='You can give your Document name here')
    note = fields.Text(string='Note', copy=False,
                       help="Note for document template")
    attach_ids = fields.Many2many(comodel_name='ir.attachment',
                                  relation='attach_rel_ids', column1='doc_id',
                                  column2='attach_id3', string="Attachment",
                                  help='You can attach the copy of your document',
                                  copy=False)


class IrAttachment(models.Model):
    """Inherit the 'ir_attachment' model to retrieve attached documents."""
    _inherit = 'ir.attachment'

    doc_attach_ids = fields.Many2many('hr.employee.document',
                                      'doc_attachment_ids', 'attach_id3', 'doc_id',
                                      string="Attachment",
                                      help="Choose Employee Document for Attachment")

    attach_rel_ids = fields.Many2many(comodel_name='hr.document',
                                      relation='attach_ids',
                                      column1='attachment_id3',
                                      column2='document_id',
                                      string='Attachment',
                                      help='Attachments.')


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    entry_checklist_plan_ids = fields.Many2many(
        'employee.checklist', 'check_hr_rel', 'hr_check_rel',
        string='Entry Process', domain=[('document_type', '=', 'entry')],
        help="Entry Checklist's")
    exit_checklist_plan_ids = fields.Many2many(
        'employee.checklist', 'exit_hr_rel', 'hr_exit_rel',
        string='Exit Process', domain=[('document_type', '=', 'exit')],
        help="Exit Checklist's")
    check_type_check = fields.Boolean(string="Activity Type Check")
    on_board_type_check = fields.Boolean(string="On-boarding")
    off_board_type_check = fields.Boolean(string="Off-boarding")

    def action_close_dialog(self):
        """
        Function is used for writing checklist values based on
        mail activity of the employee.
        """
        emp_checklist = self.env['hr.employee'].search([('id', '=', self.res_id)])
        emp_checklist.write({
            'entry_checklist': self.entry_checklist_plan_ids if self.entry_checklist_plan_ids else emp_checklist.entry_checklist,
            'exit_checklist': self.exit_checklist_plan_ids if self.exit_checklist_plan_ids else emp_checklist.exit_checklist
        })
        return super().action_close_dialog()


class MailActivityPlan(models.Model):
    _inherit = 'mail.activity.plan'

    def unlink(self):
        """
        Function is used for checking while deleting
        plan which is related to checklist record
        and raise error.

        """
        on_id = self.env.ref('hr.onboarding_plan')
        of_id = self.env.ref('hr.offboarding_plan')
        for recd in self:
            if recd.id == of_id.id or recd.id == on_id.id:
                raise UserError(_("Checklist Record's Can't Be Delete!"))
        return super().unlink()


class MailActivityPlanTemplate(models.Model):
    _inherit = 'mail.activity.plan.template'

    entry_checklist_plan_ids = fields.Many2many(
        'employee.checklist', 'entry_obj_plan', 'check_hr_rel', 'hr_check_rel',
        string='Entry Process', domain=[('document_type', '=', 'entry')])
    exit_checklist_plan_ids = fields.Many2many(
        'employee.checklist', 'exit_obj_plan', 'exit_hr_rel', 'hr_exit_rel',
        string='Exit Process', domain=[('document_type', '=', 'exit')])

    def unlink(self):
        """
        Function is used for while deleting the planing types
        it check if the record is related to checklist and raise
        error.

        """
        check_id = self.env.ref(
            'teracom_web_theme.checklist_activity_type')
        for recd in self:
            if recd.id == check_id.id:
                raise UserError(_("Checklist Record Can't Be Delete!"))
        return super().unlink()


class MailActivitySchedule(models.TransientModel):
    _inherit = 'mail.activity.schedule'

    def action_schedule_plan(self):
        """
        Function is override for appending checklist values
        to the mail activity.

        """
        employee = self.env['hr.employee'].browse(
            self._context.get('active_id'))
        check_type_id = self.env.ref(
            'teracom_web_theme.checklist_activity_type')
        on_id = self.env.ref('hr.onboarding_plan')
        of_id = self.env.ref('hr.offboarding_plan')
        for activity_type in self.plan_id.template_ids:
            responsible = activity_type.responsible_id
            if self.env['hr.employee'].with_user(
                    responsible).check_access_rights('read',
                                                     raise_exception=False):
                self.env['mail.activity'].create({
                    'res_id': self._context.get('active_id'),
                    'res_model_id': employee.env['ir.model']._get(
                        'hr.employee').id,
                    'summary': activity_type.summary,
                    'note': self.note,
                    'activity_type_id': self.activity_type_id.id,
                    'user_id': self.activity_user_id.id,
                    'entry_checklist_plan_ids': activity_type.entry_checklist_plan_ids,
                    'exit_checklist_plan_ids': activity_type.exit_checklist_plan_ids,
                    'check_type_check': True if activity_type.id == check_type_id.id else False,
                    'on_board_type_check': True if self.plan_id.id == on_id.id else False,
                    'off_board_type_check': True if self.plan_id.id == of_id.id else False
                })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'res_id': self._context.get('active_id'),
            'name': self.env['hr.employee'].browse(
                self._context.get('active_id')).display_name,
            'view_mode': 'form',
            'views': [(False, "form")],
        }

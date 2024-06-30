# -*- coding: utf-8 -*-

from datetime import date
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError


class EmployeeVerification(models.Model):
    """Creates the model Employee Verification"""
    _name = 'employee.verification'
    _description = "Employee Verification"

    name = fields.Char(string='ID', readonly=True, copy=False,
                       help="Verification ID")
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  help='Employee for background verification')
    address_id = fields.Many2one(related='employee_id.address_id',
                                 string='Address', readonly=False,
                                 help="Address of the chosen employee")
    assigned_id = fields.Many2one('res.users', string='Assigned By', readonly=True,
                                  default=lambda self: self.env.uid,
                                  help="Assigned Login User")
    agency_id = fields.Many2one('res.partner', string='Verification Agency',
                                domain=[('verification_agent', '=', True)],
                                help='You can choose a Verification Agent')
    resume_ids = fields.Many2many('ir.attachment', string="Resume of Applicant",
                                  help='You can attach the copy of your document',
                                  copy=False)
    description_by_agency = fields.Char(string='Description', readonly=True,
                                        help="Description by agency")
    assigned_date = fields.Date(string="Assigned Date", readonly=True,
                                default=date.today(), help="Record Assigned Date")
    expected_date = fields.Date(string='Expected Date',
                                help='Expected date of completion of background verification')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assign', 'Assigned'),
        ('submit', 'Verification Completed'),
    ], string='Status', default='draft')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help="Company of the current record")
    agency_attachment_ids = fields.Many2many('ir.attachment',
                                             'agency_attachments_rel',
                                             'verification', 'attachment',
                                             string="Agency Attachment",
                                             help='Attachment from the agency',
                                             copy=False, readonly=True)

    def action_assign_statusbar(self):
        """Method action_assign_statusbar will assign the verification
        of the contact to an agency and mail to agency"""
        if self.agency_id:
            if self.address_id or self.resume_ids:
                self.state = 'assign'
                template = self.env.ref('accounting_base_kit.assign_agency_email_template')
                self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
            else:
                raise UserError(
                    _("There should be at least address or resume of the employee."))
        else:
            raise UserError(
                _("Agency is not assigned. Please select one of the Agency."))

    @api.model_create_multi
    def create(self, vals_list):
        """Supering the create method of the model Employee Verification and
        also adding verification_id into the vals for creating the record."""
        for vals in vals_list:
            seq = self.env['ir.sequence'].next_by_code(
                'employee.verification') or '/'
            vals['name'] = seq
        return super(EmployeeVerification, self).create(vals_list)

    def unlink(self):
        """Supering the unlink method of the model Employee Verification to
        raise an error when unlinking the record in model which is not in draft
        state"""
        for record in self:
            if record.state not in 'draft':
                raise UserError(
                    _('You cannot delete the verification created.'))
            super(EmployeeVerification, record).unlink()


class IrAttachment(models.Model):
    """Inherits the model Ir Attachment and extends to change functionality
    of the method check to download the attached file from the user portal."""
    _inherit = 'ir.attachment'

    @api.model
    def check(self, mode, values=None):
        """ Restricts the access to an ir.attachment, according to referred
        mode """
        if self.env.is_superuser():
            return True
        if not (self.env.is_admin() or self.env.user.has_group(
                'base.group_user') or self.env.user.has_group(
            'base.group_portal')):
            raise AccessError(
                _("Sorry, you are not allowed to access this document."))
        model_ids = defaultdict(set)
        if self:
            self.env['ir.attachment'].flush_recordset(
                ['res_model', 'res_id', 'create_uid', 'public', 'res_field'])
            self._cr.execute(
                'SELECT res_model, res_id, create_uid, public, res_field FROM ir_attachment WHERE id IN %s',
                [tuple(self.ids)])
            for res_model, res_id, create_uid, public, res_field in self._cr.fetchall():
                if not self.env.is_system() and res_field:
                    raise AccessError(
                        _("Sorry, you are not allowed to access this document."))
                if public and mode == 'read':
                    continue
                if not (res_model and res_id):
                    continue
                model_ids[res_model].add(res_id)
        if values and values.get('res_model') and values.get('res_id'):
            model_ids[values['res_model']].add(values['res_id'])
        for res_model, res_ids in model_ids.items():
            if res_model not in self.env:
                continue
            if res_model == 'res.users' and len(
                    res_ids) == 1 and self.env.uid == list(res_ids)[0]:
                continue
            records = self.env[res_model].browse(res_ids).exists()
            access_mode = 'write' if mode in ('create', 'unlink') else mode
            records.check_access_rights(access_mode)
            records.check_access_rule(access_mode)


class ResPartner(models.Model):
    """Inherits the model Res Partner to extend and add field"""
    _inherit = 'res.partner'

    verification_agent = fields.Boolean(
        string='Verification Agency',
        help="Mark it if the partner is an Employee Verification Agency Agent")

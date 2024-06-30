# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LateCheckIn(models.Model):
    """Model to store late check-in records"""
    _name = 'late.check.in'
    _description = 'Late Check In'

    name = fields.Char(
        readonly=True, string='Name', help="Reference number of the record")
    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  help='Late employee')
    late_minutes = fields.Integer(string="Late Minutes",
                                  help='The field indicates the number of '
                                       'minutes in which the worker is considered late.')
    date = fields.Date(string="Date", help='Current date')
    penalty_amount = fields.Float(compute="_compute_penalty_amount",
                                  help='Amount needs to be deducted',
                                  string="Amount",)
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('approved', 'Approved'),
                                        ('refused', 'Refused'),
                                        ('deducted', 'Deducted')],
                             string="State", default="draft",
                             help='State of the record')
    attendance_id = fields.Many2one('hr.attendance', string='Attendance',
                                    help='Attendence of the employee')

    @api.model_create_multi
    def create(self, vals_list):
        """Create a sequence for the model"""
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'late.check.in') or '/'
        return super(LateCheckIn, self.sudo()).create(vals_list)

    def _compute_penalty_amount(self):
        """Compute the penalty amount if the employee was late"""
        for rec in self:
            amount = float(self.env['ir.config_parameter'].sudo().get_param(
                'deduction_amount'))
            rec.penalty_amount = amount
            if self.env['ir.config_parameter'].sudo().get_param(
                    'deduction_type') == 'minutes':
                rec.penalty_amount = amount * rec.late_minutes

    def approve(self):
        """Change state to approved when approve button clicks"""
        self.state = 'approved'

    def reject(self):
        """Change state refused when refuse button clicks"""
        self.state = 'refused'

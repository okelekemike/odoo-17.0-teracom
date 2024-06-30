# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrShiftSchedule(models.Model):
    _name = 'hr.shift.schedule'
    _description = 'Employee Shift Schedule'

    start_date = fields.Datetime(string="Date From", required=True, help="Starting date and time for the shift")
    end_date = fields.Datetime(string="Date To", required=True, help="Ending date and time for the shift")
    rel_hr_schedule = fields.Many2one('hr.contract')
    hr_shift = fields.Many2one('resource.calendar', string="Shift", required=True, help="Shift")
    company_id = fields.Many2one('res.company', string='Company', help="Company")

    @api.onchange('start_date', 'end_date')
    def get_department(self):
        """Adding domain to  the hr_shift field"""
        hr_department = None
        if self.start_date:
            hr_department = self.rel_hr_schedule.department_id.id
        return {
            'domain': {
                'hr_shift': [('hr_department', '=', hr_department)]
            }
        }

    def write(self, vals):
        """Overrides the default write method to ensure there are no overlapping
        shift schedules before updating a record.
        This method first checks for any overlapping shift schedules, If no
        overlaps are found, it proceeds to update the record using the parent class's `write` method."""
        self._check_overlap(vals)
        return super(HrShiftSchedule, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """The create method in the HrShift Schedule class overrides the parent
         class's create function to check for overlapping shift schedules before
          creating a new record."""
        for vals in vals_list:
            self._check_overlap(vals)
        return super(HrShiftSchedule, self).create(vals_list)

    def _check_overlap(self, vals):
        """The _check_ove rlap method checks for overlapping shift schedules and
         validates that the start date is before the end date. If an overlap is
         detected or the start date is after the end date, it raises a warning."""
        if vals.get('start_date', False) and vals.get('end_date', False):
            shifts = self.env['hr.shift.schedule'].search([('rel_hr_schedule', '=', vals.get('rel_hr_schedule'))])
            for each in shifts:
                if each != shifts[-1]:
                    if each.end_date >= vals.get('start_date') or each.start_date >= vals.get('start_date'):
                        raise Warning(_('The dates and times may not overlap with one another.'))
            if vals.get('start_date') > vals.get('end_date'):
                raise Warning(_('Start date and time should be less than end date.'))
        return True

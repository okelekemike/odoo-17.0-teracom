# -*- coding: utf-8 -*-

from odoo import fields, models


class EmployeeStage(models.TransientModel):
    """Wizards to set the related user"""
    _name = 'employee.stage'
    _description = "Set Related User"

    related_user_id = fields.Many2one('res.users', string="Related User",
                                      help="Set related user for the employee")

    def set_as_employee(self):
        """This is used to create a related user for the employee in
        employment stage"""
        employee_obj = self.env['hr.employee'].browse(
            self._context.get('employee_id'))
        if self.related_user_id:
            employee_obj.user_id = self.related_user_id
        employee_obj.set_as_employee()

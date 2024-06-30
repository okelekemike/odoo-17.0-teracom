# -*- coding: utf-8 -*-

from random import randint
from odoo import api, fields, models


class ResUsers(models.Model):
    """ Inherited class of res user to override the create function"""
    _inherit = 'res.users'

    employee_id = fields.Many2one('hr.employee',
                                  string='Related Employee',
                                  ondelete='restrict', auto_join=True,
                                  help='Related employee based on the data of the user')

    @api.model_create_multi
    def create(self, vals):
        """Overrides the default 'create' method to create an employee record
        when a new user is created."""
        result = super(ResUsers, self).create(vals)
        result['employee_id'] = self.env['hr.employee'].sudo().create({
            'name': result['name'],
            'user_id': result['id'],
            'partner_id': result['partner_id'],
            'private_street': result['partner_id'].id
        }) if not result['employee_id'] else result['employee_id']
        return result


class HrEmployee(models.Model):
    """Inheriting employee to add employee user"""
    _inherit = 'hr.employee'

    partner_id = fields.Many2one('res.partner',
                                 string='Related Partner',
                                 ondelete='restrict', auto_join=True,
                                 help='Related partner based on the data of the employee')

    def unlink(self):
        if self.partner_id:
            self.partner_id.employee_id = False
            self.partner_id = False
        result = super(HrEmployee, self).unlink()
        return result


class ResPartner(models.Model):
    """The Class inherits the res.partner model for adding the new
    fields and functions"""
    _inherit = 'res.partner'

    employee_id = fields.Many2one('hr.employee',
                                  string='Related Employee',
                                  ondelete='restrict', auto_join=True,
                                  help='Related employee based on the data of the user')

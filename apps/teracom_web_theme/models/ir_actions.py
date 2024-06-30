# -*- coding: utf-8 -*-

from odoo import fields, models


class IrActionsReportXml(models.Model):
    _inherit = 'ir.actions.report'

    default_print_option = fields.Selection(selection=[
        ('print', 'Print'),
        ('download', 'Download'),
        ('open', 'Open')
    ], string='Default Printing Option')

    def _get_readable_fields(self):
        data = super(IrActionsReportXml, self)._get_readable_fields()
        data.add('default_print_option')
        return data

    def report_action(self, docids, data=None, config=True):
        data = super(IrActionsReportXml, self).report_action(docids, data, config)
        data['id'] = self.id
        data['default_print_option'] = self.default_print_option
        return data

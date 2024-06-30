# -*- coding: utf-8 -*-

from odoo import models


class HrPayslipEmployees(models.TransientModel):
    """Extends the standard 'hr.payslip.employees' model to provide
    functionality for calculating and generating payroll slips for selected
    employees.
    Methods:
        - compute_sheet: Calculate and generate payroll slips for the selected
        employees."""
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        """Calculate and generate payroll slips for the selected employees.
        This method calculates and generates payroll slips for the employees
        associated with the current wizard instance. It sets the journal_id
        based on the active_id from the context, and then calls the parent
        class's compute_sheet method."""
        journal_id = False
        if self.env.context.get('active_id'):
            journal_id = self.env['hr.payslip.run'].browse(
                self.env.context.get('active_id')).journal_id.id
        return super(HrPayslipEmployees,
                     self.with_context(journal_id=journal_id)).compute_sheet()

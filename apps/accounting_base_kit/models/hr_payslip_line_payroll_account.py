# -*- coding: utf-8 -*-

from odoo import models


class HrPayslipLine(models.Model):
    """Extends the standard 'hr.payslip.line' model to provide additional
    functionality for accounting.
    Methods:
        - _get_partner_id: Get partner_id of the slip line to use in
        account_move_line."""
    _inherit = 'hr.payslip.line'

    def _get_partner_id(self, credit_account):
        """Get partner_id of slip line to use in account_move_line."""
        # use partner of salary rule or fallback on employee's address
        register_partner_id = self.salary_rule_id.register_id.partner_id
        if credit_account:
            if (register_partner_id or
                    self.salary_rule_id.account_credit_id.account_type in (
                    'asset_receivable', 'liability_payable')):
                return register_partner_id.id
        else:
            if (register_partner_id or
                    self.salary_rule_id.account_debit_id.account_type in (
                    'asset_receivable', 'liability_payable')):
                return register_partner_id.id
        return False

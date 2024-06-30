# -*- coding: utf-8 -*-

from datetime import date, timedelta

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning


class ResCompany(models.Model):
    _inherit = "res.company"

    def _validate_fiscalyear_lock(self, values):
        if values.get('fiscalyear_lock_date'):

            draft_entries = self.env['account.move'].search([
                ('company_id', 'in', self.ids),
                ('state', '=', 'draft'),
                ('date', '<=', values['fiscalyear_lock_date'])])
            if draft_entries:
                error_msg = _('There are still unposted entries in the period you want to lock. You should either post or delete them.')
                action_error = {
                    'view_mode': 'tree',
                    'name': 'Unposted Entries',
                    'res_model': 'account.move',
                    'type': 'ir.actions.act_window',
                    'domain': [('id', 'in', draft_entries.ids)],
                    'search_view_id': [self.env.ref('account.view_account_move_filter').id, 'search'],
                    'views': [[self.env.ref('account.view_move_tree').id, 'list'], [self.env.ref('account.view_move_form').id, 'form']],
                }
                raise RedirectWarning(error_msg, action_error, _('Show unposted entries'))

            unreconciled_statement_lines = self.env['account.bank.statement.line'].search([
                ('company_id', 'in', self.ids),
                ('is_reconciled', '=', False),
                ('date', '<=', values['fiscalyear_lock_date']),
                ('move_id.state', 'in', ('draft', 'posted')),
            ])
            if unreconciled_statement_lines:
                error_msg = _("There are still unreconciled bank statement lines in the period you want to lock."
                            "You should either reconcile or delete them.")
                action_error = {
                    'view_mode': 'tree',
                    'name': 'Unreconciled Transactions',
                    'res_model': 'account.bank.statement.line',
                    'type': 'ir.actions.act_window',
                    'domain': [('id', 'in', unreconciled_statement_lines.ids)],
                    # 'search_view_id': [self.env.ref('account.view_account_move_filter').id, 'search'],
                    'views': [[self.env.ref('accounting_base_kit.view_bank_statement_line_tree').id, 'list']]
                              # [self.env.ref('account.view_move_form').id, 'form']],
                }
                # action_error = self._get_fiscalyear_lock_statement_lines_redirect_action(unreconciled_statement_lines)
                raise RedirectWarning(error_msg, action_error, _('Show Unreconciled Bank Statement Line'))

    # Employee Late Check-in
    deduction_amount = fields.Float(
        help='How much amount need to be deducted if a employee was late',
        string="Deduction Amount",)
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id.id)
    maximum_minutes = fields.Char(
        help="Maximum time limit a employee was considered as late",
        string="Maximum Late Minute")
    late_check_in_after = fields.Char(
        help='When should the late check-in count down starts.',
        string="Late Check-In Starts After",)
    deduction_type = fields.Selection(
        selection=[('minutes', 'Per Minutes'), ('total', 'Per Total')],
        default="minutes", string='Deduction Type',
        help='Type of deduction, (If Per Minutes is chosen then for each '
             'minutes given amount is deducted, if Per Total is chosen then '
             'given amount is deducted from the total salary)')

    city_id = fields.Many2one(
        'res.city', string='City', domain="[('state_id', '=', state_id)]")

    @api.onchange('state_id', 'country_id')
    def _onchange_state(self):
        if not (self.state_id or self.country_id) or (
                self.state_id and self.state_id != self.city_id.state_id) or (
                self.country_id and self.country_id != self.city_id.country_id):
            self.city_id = False

    @api.onchange('city_id')
    def _onchange_city(self):
        if self.city_id:
            self.city = self.city_id.name

    # Account Reconciliation
    reconcile_aggregate = fields.Selection(
        selection=lambda self: self.env["account.journal"]
        ._fields["reconcile_aggregate"]
        .selection
    )

    reconciliation_commit_every = fields.Integer(
        string="How often to commit when performing automatic reconciliation.",
        help="Leave zero to commit only at the end of the process.",
    )


# -*- coding: utf-8 -*-

import time
from collections import defaultdict
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo import tools
from odoo.tools import format_date


class ReportFollowup(models.AbstractModel):
    _name = 'report.accounting_base_kit.report_followup'
    _description = 'Report Followup'

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env['followup.sending.results']
        ids = self.env.context.get('active_ids') or False
        docs = model.browse(ids)
        return {
            'docs': docs,
            'doc_ids': docids,
            'doc_model': model,
            'time': time,
            'ids_to_objects': self._ids_to_objects,
            'getLines': self._lines_get,
            'get_text': self._get_text,
            'data': data and data['form'] or {}}

    def _ids_to_objects(self, ids):
        all_lines = []
        for line in self.env['followup.stat.by.partner'].browse(ids):
            if line not in all_lines:
                all_lines.append(line)
        return all_lines

    def _lines_get(self, stat_by_partner_line):
        return self._lines_get_with_partner(stat_by_partner_line.partner_id,
                                            stat_by_partner_line.company_id.id)

    def _lines_get_with_partner(self, partner, company_id):
        moveline_obj = self.env['account.move.line']
        moveline_ids = moveline_obj.search(
            [('partner_id', '=', partner.id),
             ('account_id.account_type', '=', 'asset_receivable'),
             ('full_reconcile_id', '=', False),
             ('company_id', '=', company_id),
             '|', ('date_maturity', '=', False),
             ('date_maturity', '<=', fields.Date.today())])
        lines_per_currency = defaultdict(list)
        total = 0
        for line in moveline_ids:
            currency = line.currency_id or line.company_id.currency_id
            balance = line.debit - line.credit
            if currency != line.company_id.currency_id:
                balance = line.amount_currency
            line_data = {
                'name': line.move_id.name,
                'ref': line.ref,
                'date': format_date(self.env, line.date),
                'date_maturity': format_date(self.env, line.date_maturity),
                'balance': balance,
                'blocked': line.blocked,
                'currency_id': currency,
            }
            total = total + line_data['balance']
            lines_per_currency[currency].append(line_data)

        return [{'total': total, 'line': lines, 'currency': currency} for
                currency, lines in
                lines_per_currency.items()]

    def _get_text(self, stat_line, followup_id, context=None):
        fp_obj = self.env['followup.followup']
        fp_line = fp_obj.browse(followup_id).followup_line
        if not fp_line:
            raise ValidationError(
                _("The followup plan defined for the current company does not "
                  "have any followup action."))
        default_text = ''
        li_delay = []
        for line in fp_line:
            if not default_text and line.description:
                default_text = line.description
            li_delay.append(line.delay)
        li_delay.sort(reverse=True)
        partner_line_ids = self.env['account.move.line'].search(
            [('partner_id', '=', stat_line.partner_id.id),
             ('full_reconcile_id', '=', False),
             ('company_id', '=', stat_line.company_id.id),
             ('blocked', '=', False),
             ('debit', '!=', False),
             ('account_id.account_type', '=', 'asset_receivable'),
             ('followup_line_id', '!=', False)])

        partner_max_delay = 0
        partner_max_text = ''
        for i in partner_line_ids:
            if i.followup_line_id.delay > partner_max_delay and \
                    i.followup_line_id.description:
                partner_max_delay = i.followup_line_id.delay
                partner_max_text = i.followup_line_id.description
        text = partner_max_delay and partner_max_text or default_text
        if text:
            lang_obj = self.env['res.lang']
            lang_ids = lang_obj.search(
                [('code', '=', stat_line.partner_id.lang)], limit=1)
            date_format = lang_ids and lang_ids.date_format or '%Y-%m-%d'
            text = text % {
                'partner_name': stat_line.partner_id.name,
                'date': time.strftime(date_format),
                'company_name': stat_line.company_id.name,
                'user_signature': self.env.user.signature or '',
            }
        return text


class AccountFollowupStat(models.Model):
    _name = "followup.stat"
    _description = "Follow-up Statistics"
    _rec_name = 'partner_id'
    _order = 'date_move'
    _auto = False

    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    date_move = fields.Date('First move', readonly=True)
    date_move_last = fields.Date('Last move', readonly=True)
    date_followup = fields.Date('Latest followup', readonly=True)
    followup_id = fields.Many2one('followup.lines', 'Follow Ups', readonly=True, ondelete="cascade")
    balance = fields.Float('Balance', readonly=True)
    debit = fields.Float('Debit', readonly=True)
    credit = fields.Float('Credit', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    blocked = fields.Boolean('Blocked', readonly=True)

    @api.model
    def init(self):
        tools.drop_view_if_exists(self._cr, 'followup_stat')
        self._cr.execute("""
            create or replace view followup_stat as (
                SELECT
                    l.id as id,
                    l.partner_id AS partner_id,
                    min(l.date) AS date_move,
                    max(l.date) AS date_move_last,
                    max(l.followup_date) AS date_followup,
                    max(l.followup_line_id) AS followup_id,
                    sum(l.debit) AS debit,
                    sum(l.credit) AS credit,
                    sum(l.debit - l.credit) AS balance,
                    l.company_id AS company_id,
                    l.blocked as blocked
                FROM
                    account_move_line l
                    LEFT JOIN account_account a ON (l.account_id = a.id)
                WHERE
                    a.account_type =  'asset_receivable' AND
                    l.full_reconcile_id is NULL AND
                    l.partner_id IS NOT NULL
                GROUP BY
                    l.id, l.partner_id, l.company_id, l.blocked
            )""")

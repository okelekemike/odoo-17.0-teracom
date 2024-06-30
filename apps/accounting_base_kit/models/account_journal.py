# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.addons.base.models.res_bank import sanitize_account_number


class MultipleInvoice(models.Model):
    """Multiple Invoice Model"""
    _name = "multiple.invoice"
    _description = 'Multiple Invoice'
    _order = "sequence"

    sequence = fields.Integer(string='Sequence No')
    copy_name = fields.Char(string='Invoice Copy Name')
    journal_id = fields.Many2one('account.journal', string="Journal")


class AccountJournal(models.Model):
    """Module inherited for adding the reconcile method in the account journal"""
    _inherit = "account.journal"

    multiple_invoice_ids = fields.One2many('multiple.invoice',
                                           'journal_id',
                                           string='Multiple Invoice')
    multiple_invoice_type = fields.Selection(
        [('text', 'Text'), ('watermark', 'Watermark')], required=True,
        default='text', string="Display Type")
    text_position = fields.Selection([
        ('header', 'Header'),
        ('footer', 'Footer'),
        ('body', 'Document Body')
    ], required=True, default='header', string='Text Position')
    body_text_position = fields.Selection([
        ('tl', 'Top Left'),
        ('tr', 'Top Right'),
        ('bl', 'Bottom Left'),
        ('br', 'Bottom Right'),
    ], default='tl', string='Body Text Position')
    text_align = fields.Selection([
        ('right', 'Right'),
        ('left', 'Left'),
        ('center', 'Center'),
    ], default='right', string='Center Align Text Position')
    layout = fields.Char(string="Layout",
                         related="company_id.external_report_layout_id.key")

    def action_open_reconcile(self):
        """Function to open reconciliation view for bank statements
        belonging to this journal"""
        if self.type in ['bank', 'cash']:
            # Open reconciliation view for bank statements belonging
            # to this journal
            bank_stmt = self.env['account.bank.statement'].search(
                [('journal_id', 'in', self.ids)]).mapped('line_ids')
            return {
                'type': 'ir.actions.client',
                'tag': 'bank_statement_reconciliation_view',
                'context': {'statement_line_ids': bank_stmt.ids,
                            'company_ids': self.mapped('company_id').ids},
            }
        else:
            # Open reconciliation view for customers/suppliers
            action_context = {'show_mode_selector': False,
                              'company_ids': self.mapped('company_id').ids}
            if self.type == 'sale':
                action_context.update({'mode': 'customers'})
            elif self.type == 'purchase':
                action_context.update({'mode': 'suppliers'})
            return {
                'type': 'ir.actions.client',
                'tag': 'manual_reconciliation_view',
                'context': action_context,
            }

    def create_cash_statement(self):
        """for redirecting in to bank statement lines"""
        return {
            'name': _("Statements"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.bank.statement.line',
            'view_mode': 'list,form',
            'context': {'default_journal_id': self.id},
        }

    def action_new_transaction(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "accounting_base_kit.action_bank_statement_line_create"
        )
        action["context"] = {'default_journal_id': self.id}
        return action

    # Account Reconciliation
    reconcile_mode = fields.Selection(
        [("edit", "Edit Move"), ("keep", "Keep Suspense Accounts")],
        default="edit",
        required=True,
    )
    company_currency_id = fields.Many2one(related="company_id.currency_id")
    reconcile_aggregate = fields.Selection(
        [
            ("statement", "Statement"),
            ("day", "Day"),
            ("week", "Week"),
            ("month", "Month"),
        ],
        string="Reconcile Aggregation",
        help="Aggregation to use on reconcile view",
    )

    def get_rainbowman_message(self):
        self.ensure_one()
        if (
                self._get_journal_dashboard_data_batched()[self.id]["number_to_reconcile"]
                > 0
        ):
            return False
        return _("Well done! Everything has been reconciled")

    def _statement_line_import_speeddict(self):
        """This method is designed to be inherited by reconciliation modules.
        These modules can take advantage of this method to pre-fetch data
        that will later be used for many statement lines (to avoid
        searching data for each statement line).
        The goal is to improve performances.
        """
        self.ensure_one()
        speeddict = {"account_number": {}}
        partner_banks = self.env["res.partner.bank"].search_read(
            [("company_id", "in", (False, self.company_id.id))],
            ["acc_number", "partner_id"],
        )
        for partner_bank in partner_banks:
            speeddict["account_number"][partner_bank["acc_number"]] = {
                "partner_id": partner_bank["partner_id"][0],
                "partner_bank_id": partner_bank["id"],
            }
        return speeddict

    def _statement_line_import_update_hook(self, st_line_vals, speeddict):
        """This method is designed to be inherited by reconciliation modules.
        In this method you can:
        - update the partner of the line by writing st_line_vals['partner_id']
        - set an automated counter-part via counterpart_account_id by writing
          st_line_vals['counterpart_account_id']
        - do anythink you want with the statement line
        """
        self.ensure_one()
        if st_line_vals.get("account_number"):
            st_line_vals["account_number"] = self._sanitize_bank_account_number(
                st_line_vals["account_number"]
            )
            if not st_line_vals.get("partner_id") and speeddict["account_number"].get(
                    st_line_vals["account_number"]
            ):
                st_line_vals.update(
                    speeddict["account_number"][st_line_vals["account_number"]]
                )

    def _statement_line_import_update_unique_import_id(
            self, st_line_vals, account_number
    ):
        self.ensure_one()
        if st_line_vals.get("unique_import_id"):
            sanitized_acc_number = self._sanitize_bank_account_number(account_number)
            st_line_vals["unique_import_id"] = (
                    (sanitized_acc_number and sanitized_acc_number + "-" or "")
                    + str(self.id)
                    + "-"
                    + st_line_vals["unique_import_id"]
            )

    @api.model
    def _sanitize_bank_account_number(self, account_number):
        """Hook for extension"""
        return sanitize_account_number(account_number)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        formats_list = self._get_bank_statements_available_import_formats()
        if formats_list:
            res["bank_statements_source"] = "file_import_oca"
        return res

    def _get_bank_statements_available_import_formats(self):
        """Returns a list of strings representing the supported import formats."""
        return []

    def __get_bank_statements_available_sources(self):
        rslt = super().__get_bank_statements_available_sources()
        formats_list = self._get_bank_statements_available_import_formats()
        if formats_list:
            formats_list.sort()
            import_formats_str = ", ".join(formats_list)
            rslt.insert(
                0, ("file_import_oca", _("Import") + "(" + import_formats_str + ")")
            )
        return rslt

    def import_account_statement(self):
        """return action to import bank/cash statements.
        This button should be called only on journals with type =='bank'"""
        action = self.env["ir.actions.actions"]._for_xml_id(
            "accounting_base_kit.account_statement_import_action"
        )
        action["context"] = {"journal_id": self.id}
        return action


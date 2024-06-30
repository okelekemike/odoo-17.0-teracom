# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import  ValidationError, UserError


class AccountRegisterPayments(models.TransientModel):
    """Inherits the account.payment.register model to add the new
     fields and functions"""
    _inherit = "account.payment.register"

    bank_reference = fields.Char(string="Bank Reference", copy=False)
    cheque_reference = fields.Char(string="Cheque Reference", copy=False)
    effective_date = fields.Date('Effective Date',
                                 help='Effective date of PDC', copy=False,
                                 default=False)

    def _prepare_payment_vals(self, invoices):
        """Its prepare the payment values for the invoice and update
         the MultiPayment"""
        res = super(AccountRegisterPayments, self)._prepare_payment_vals(
            invoices)
        # Check payment method is Check or PDC
        check_pdc_ids = self.env['account.payment.method'].search(
            [('code', 'in', ['pdc', 'check_printing'])])
        if self.payment_method_id.id in check_pdc_ids.ids:
            currency_id = self.env['res.currency'].browse(res['currency_id'])
            journal_id = self.env['account.journal'].browse(res['journal_id'])
            # Updating values in case of Multi payments
            res.update({
                'bank_reference': self.bank_reference,
                'cheque_reference': self.cheque_reference,
                'check_manual_sequencing': journal_id.check_manual_sequencing,
                'effective_date': self.effective_date,
                'check_amount_in_words': currency_id.amount_to_text(
                    res['amount']),
            })
        return res

    def _create_payment_vals_from_wizard(self, batch_result):
        """It super the wizard action of the create payment values and update
         the bank and cheque values"""
        res = super(AccountRegisterPayments,
                    self)._create_payment_vals_from_wizard(
            batch_result)
        if self.effective_date:
            res.update({
                'bank_reference': self.bank_reference,
                'cheque_reference': self.cheque_reference,
                'effective_date': self.effective_date,
            })
        return res

    def _create_payment_vals_from_batch(self, batch_result):
        """It super the batch action of the create payment values and update
         the bank and cheque values"""
        res = super(AccountRegisterPayments,
                    self)._create_payment_vals_from_batch(
            batch_result)
        if self.effective_date:
            res.update({
                'bank_reference': self.bank_reference,
                'cheque_reference': self.cheque_reference,
                'effective_date': self.effective_date,
            })
        return res

    def _create_payments(self):
        """USed to create a list of payments and update the bank and
         cheque reference"""
        payments = super(AccountRegisterPayments, self)._create_payments()

        for payment in payments:
            payment.write({
                'bank_reference': self.bank_reference,
                'cheque_reference': self.cheque_reference
            })
        return payments


class AccountPayment(models.Model):
    """"It inherits the account.payment model for adding new fields
     and functions"""
    _inherit = "account.payment"
    _inherits = {'account.move': 'move_id'}

    bank_reference = fields.Char(string="Bank Reference", copy=False)
    cheque_reference = fields.Char(string="Cheque Reference",copy=False)
    effective_date = fields.Date('Effective Date',
                                 help='Effective date of PDC', copy=False,
                                 default=False)

    def open_payment_matching_screen(self):
        """Open reconciliation view for customers/suppliers"""
        move_line_id = False
        for move_line in self.line_ids:
            if move_line.account_id.reconcile:
                move_line_id = move_line.id
                break
        if not self.partner_id:
            raise UserError(_("Payments without a customer can't be matched"))
        action_context = {'company_ids': [self.company_id.id], 'partner_ids': [
            self.partner_id.commercial_partner_id.id]}
        if self.partner_type == 'customer':
            action_context.update({'mode': 'customers'})
        elif self.partner_type == 'supplier':
            action_context.update({'mode': 'suppliers'})
        if move_line_id:
            action_context.update({'move_line_id': move_line_id})
        return {
            'type': 'ir.actions.client',
            'tag': 'manual_reconciliation_view',
            'context': action_context,
        }

    def print_checks(self):
        """ Check that the recordset is valid, set the payments state to
        sent and call print_checks() """
        # Since this method can be called via a client_action_multi, we
        # need to make sure the received records are what we expect
        selfs = self.filtered(lambda r:
                              r.payment_method_id.code
                              in ['check_printing', 'pdc']
                              and r.state != 'reconciled')
        if len(selfs) == 0:
            raise UserError(_(
                "Payments to print as a checks must have 'Check' "
                "or 'PDC' selected as payment method and "
                "not have already been reconciled"))
        if any(payment.journal_id != selfs[0].journal_id for payment in selfs):
            raise UserError(_(
                "In order to print multiple checks at once, they "
                "must belong to the same bank journal."))

        if not selfs[0].journal_id.check_manual_sequencing:
            # The wizard asks for the number printed on the first
            # pre-printed check so payments are attributed the
            # number of the check the'll be printed on.
            last_printed_check = selfs.search([
                ('journal_id', '=', selfs[0].journal_id.id),
                ('check_number', '!=', "0")], order="check_number desc",
                limit=1)
            next_check_number = last_printed_check and int(
                last_printed_check.check_number) + 1 or 1
            return {
                'name': _('Print Pre-numbered Checks'),
                'type': 'ir.actions.act_window',
                'res_model': 'print.prenumbered.checks',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'payment_ids': self.ids,
                    'default_next_check_number': next_check_number,
                }
            }
        else:
            self.filtered(lambda r: r.state == 'draft').post()
            self.write({'state': 'sent'})
            return self.do_print_checks()

    def _prepare_payment_moves(self):
        """ supered function to set effective date """
        res = super(AccountPayment, self)._prepare_payment_moves()
        inbound_pdc_id = self.env.ref(
            'accounting_base_kit.account_payment_method_pdc_in').id
        outbound_pdc_id = self.env.ref(
            'accounting_base_kit.account_payment_method_pdc_out').id
        if self.payment_method_id.id == inbound_pdc_id or \
                self.payment_method_id.id == outbound_pdc_id \
                and self.effective_date:
            res[0]['date'] = self.effective_date
            for line in res[0]['line_ids']:
                line[2]['date_maturity'] = self.effective_date
        return res

    def mark_as_sent(self):
        """Updates the is_move_sent value of the payment model"""
        self.write({'is_move_sent': True})

    def unmark_as_sent(self):
        """Updates the is_move_sent value of the payment model"""
        self.write({'is_move_sent': False})

    def _compute_is_approve_person(self):
        """This function fetches the value of the
        'account_payment_approval.payment_approval' parameter using the
        get_param method and converts to integer, it checks if the current
        user's ID matches the ID stored in the 'approval_user_id'
        parameter. If both conditions are met, it sets the is_approve_person
         field to True"""
        approval = self.env['ir.config_parameter'].sudo().get_param(
            'account_payment_approval.payment_approval')
        approver_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'account_payment_approval.approval_user_id'))
        self.is_approve_person = True if (self.env.user.id == approver_id and
                                          approval) else False

    is_approve_person = fields.Boolean(string='Approving Person',
                                       compute=_compute_is_approve_person,
                                       readonly=True,
                                       help="Enable/disable if approving person.")

    def action_post(self):
        """Overwrites the _post() to validate the payment in the 'approved'
         stage too.
        currently Odoo allows payment posting only in draft stage."""
        validation = self._check_payment_approval()
        if validation:
            if self.state == (
                    'posted', 'cancel', 'waiting_approval', 'rejected'):
                raise UserError(
                    _("Only a draft or approved payment can be posted."))
            if any(inv.state != 'posted' for inv in
                   self.reconciled_invoice_ids):
                raise ValidationError(_("The payment cannot be processed "
                                        "because the invoice is not open!"))
            self.move_id._post(soft=False)

    def _check_payment_approval(self):
        """This function checks the payment approval if payment_amount grater
         than amount,then state changed to waiting_approval """
        self.ensure_one()
        if self.state == "draft":
            first_approval = self.env['ir.config_parameter'].sudo().get_param(
                'account_payment_approval.payment_approval')
            if first_approval:
                amount = float(self.env['ir.config_parameter'].sudo().get_param(
                    'account_payment_approval.approval_amount'))
                payment_currency_id = int(
                    self.env['ir.config_parameter'].sudo().get_param(
                        'account_payment_approval.approval_currency_id'))
                payment_amount = self.amount
                if payment_currency_id:
                    if (self.currency_id and
                            self.currency_id.id != payment_currency_id):
                        currency_id = self.env['res.currency'].browse(
                            payment_currency_id)
                        payment_amount = (self.currency_id._convert(
                            self.amount, currency_id, self.company_id,
                            self.date or fields.Date.today(), round=True))
                if payment_amount > amount:
                    self.write({
                        'state': 'waiting_approval'
                    })
                    return False
        return True

    def approve_transfer(self):
        """This function changes state to approved state if approving person
         approves payment"""
        if self.is_approve_person:
            self.write({
                'state': 'approved'
            })

    def reject_transfer(self):
        """This function changes state to rejected state if approving person
                reject approval"""
        self.write({
            'state': 'rejected'
        })


class AccountPaymentMethod(models.Model):
    """The class inherits the account payment method for supering the
    _get_payment_method_information function"""
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        """Super the function to update the pdc values"""
        res = super()._get_payment_method_information()
        res['pdc'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        return res

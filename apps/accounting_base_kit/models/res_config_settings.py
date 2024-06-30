# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    res_partner_id = fields.Many2one('res.partner', ondelete='set null', string='Default Customer')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    customer_credit_limit = fields.Boolean(string="Customer Credit Limit")

    use_anglo_saxon_accounting = fields.Boolean(string="Use Anglo-Saxon accounting", readonly=False,
                                                related='company_id.anglo_saxon_accounting')

    notice_period = fields.Boolean(string='Notice Period',
                                   help='Enable to configure a notice period'
                                        ' for an employee.')
    no_of_days = fields.Integer(string='Notice Period Days',
                                help='Set the number of days for the notice'
                                     ' period.')

    send_payslip_by_email = fields.Boolean(
        string="Automatic Send Payslip By Mail",
        help="Is needed for automatic send mail")

    loan_approve = fields.Boolean(default=False,
                                  string="Approval from Accounting Department",
                                  help="Loan Approval from account manager")

    loan_concurrent_count = fields.Integer('Loan Concurrency Count', default=1,
                                           config_parameter='accounting_base_kit.loan_concurrent_count',
                                           help="Number of concurrent loans an employee can create. "
                                                "0 means unlimited allowed")

    po_limit = fields.Integer(string='Limit', default=0,
                              config_parameter='accounting_base_kit.po_limit',
                              help='Specify the limit to show')

    po_status = fields.Selection(
        [('all', 'All'),
         ('rfq', 'RFQ'),
         ('purchase_order', 'Purchase Order'),
         ('in_process', 'Under Process')],
        string='Status',
        config_parameter='accounting_base_kit.po_status',
        help='Specify the status of the purchase order')

    so_limit = fields.Integer(string='Limit', default=0,
                              config_parameter='accounting_base_kit.so_limit',
                              help='Specify the limit to show')

    so_status = fields.Selection(
        [('all', 'All'),
         ('rfq', 'Quotation'),
         ('sale_order', 'Sales Order'),
         ('in_process', 'Under Process')],
        string='Status',
        config_parameter='accounting_base_kit.so_status',
        help='Specify the status of the purchase order')

    # Employee Late Check-In
    deduction_amount = fields.Float(
        config_parameter='accounting_base_kit.deduction_amount',
        help='How much amount need to be deducted if a employee was late',
        string="Deduction Amount", )
    maximum_minutes = fields.Char(
        config_parameter='accounting_base_kit.maximum_minutes',
        help="Maximum time limit a employee was considered as late",
        string="Maximum Late Minute")
    late_check_in_after = fields.Char(
        config_parameter='accounting_base_kit.late_check_in_after',
        help='When should the late check-in count down starts.',
        string="Late Check-In Starts After", )
    deduction_type = fields.Selection(
        selection=[('minutes', 'Per Minutes'), ('total', 'Per Total')],
        config_parameter='accounting_base_kit.deduction_type',
        default="minutes", string='Deduction Type',
        help='Type of deduction, (If Per Minutes is chosen then for each '
             'minutes given amount is deducted, if Per Total is chosen then '
             'given amount is deducted from the total salary)')
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id.id)

    generate_payslip = fields.Boolean(string="Generate Payslip",
                                      config_parameter="automatic_payroll.generate_payslip",
                                      help="Automatic generation of payslip "
                                           "batches and payslips (Monthly)")
    option = fields.Selection(
        [('first', 'Month First'),
         ('specific', 'Specific date'),
         ('end', 'Month End'),], string='Option', default='first',
        config_parameter="automatic_payroll.option",
        help='Option to select the date to generate payslips')

    generate_day = fields.Integer(string="Day", default=1,
                                  config_parameter="automatic_payroll.generate_day",
                                  help="payslip generated day in a month")

    digitize_bill = fields.Boolean(
        string="Digitize Bill",
        config_parameter='bill_digitization.digitize_bill',
        help="Enable the button to digitize bills")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        customer_credit_limit = params.get_param('customer_credit_limit',
                                                 default=False)
        res.update(customer_credit_limit=customer_credit_limit)

        send_payslip_by_email = params.get_param('send_payslip_by_email',
                                                 default=False)
        res.update(
            send_payslip_by_email=send_payslip_by_email
        )
        res.update(
            loan_approve=self.env['ir.config_parameter'].sudo().get_param(
                'account.loan_approve')
        )

        get_param = self.env['ir.config_parameter'].sudo().get_param
        res['notice_period'] = get_param('accounting_base_kit.notice_period')
        res['no_of_days'] = int(get_param('accounting_base_kit.no_of_days'))
        res['po_status'] = get_param('accounting_base_kit.po_status')
        res['po_limit'] = int(get_param('accounting_base_kit.po_limit'))
        res['so_status'] = get_param('accounting_base_kit.so_status')
        res['so_limit'] = int(get_param('accounting_base_kit.so_limit'))

        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            "customer_credit_limit",
            self.customer_credit_limit)
        self.env['ir.config_parameter'].sudo().set_param(
            "accounting_base_kit.notice_period", self.notice_period)
        self.env['ir.config_parameter'].sudo().set_param(
            "accounting_base_kit.no_of_days", self.no_of_days)
        self.env['ir.config_parameter'].sudo().set_param(
            "send_payslip_by_email", self.send_payslip_by_email)
        self.env['ir.config_parameter'].sudo().set_param(
            'account.loan_approve', self.loan_approve)
        self.env['ir.config_parameter'].set_param(
            'accounting_base_kit.po_limit', self.po_limit)
        self.env['ir.config_parameter'].set_param(
            'accounting_base_kit.po_status', self.po_status)
        # Employee Late Check-In
        self.env['ir.config_parameter'].sudo().set_param(
            'deduction_amount', self.deduction_amount)
        self.env['ir.config_parameter'].sudo().set_param(
            'maximum_minutes', self.maximum_minutes)
        self.env['ir.config_parameter'].sudo().set_param(
            'late_check_in_after', self.late_check_in_after)
        self.env['ir.config_parameter'].sudo().set_param(
            'deduction_type', self.deduction_type)
        if self.po_limit < 0:
            raise ValidationError("Limit cannot be less than 0")
        if self.so_limit < 0:
            raise ValidationError("Limit cannot be less than 0")
        return res

    module_account_accountant = fields.Boolean(string='Account Accountant', default=True,
                                               help="Is Account Accountant")
    module_l10n_fr_hr_payroll = fields.Boolean(string='French Payroll',
                                               help="Is French Payroll")
    module_l10n_be_hr_payroll = fields.Boolean(string='Belgium Payroll',
                                               help="Is Belgium Payroll")
    module_l10n_in_hr_payroll = fields.Boolean(string='Indian Payroll',
                                               help="Is Indian Payroll")

    # Payment Approvals
    def _get_account_manager_ids(self):
        """This function  gets all the records of 'res.users'  and
        it filters the 'res.users' records to select only those users
        who belong to the 'account.group_account_manager' group."""
        user_ids = self.env['res.users'].search([])
        account_manager_ids = user_ids.filtered(
            lambda x: x.has_group('account.group_account_manager'))
        return [('id', 'in', account_manager_ids.ids)]

    payment_approval = fields.Boolean(string='Payment Approval',
                                      config_parameter='account_payment_'
                                                       'approval.payment_'
                                                       'approval',
                                      help="Enable/disable payment"
                                           " approval to approve for payment "
                                           "if needed.")
    approval_user_id = fields.Many2one('res.users',
                                       string="Payment Approving person",
                                       required=False,
                                       domain=_get_account_manager_ids,
                                       config_parameter='account_payment_'
                                                        'approval.approval_'
                                                        'user_id',
                                       help="Select the payment approving "
                                            "person.")
    approval_amount = fields.Float(
        string='Minimum Approval Amount',
        config_parameter='account_payment_approval.approval_amount',
        help="If amount is 0.00, All the payments go through approval.")

    approval_currency_id = fields.Many2one('res.currency',
                                           string='Approval Currency',
                                           config_parameter='account_payment_'
                                                            'approval.approval_'
                                                            'currency_id',
                                           help="Converts the payment amount"
                                                " to this currency if chosen.")

    #  Digital Signature
    is_show_digital_sign_po = fields.Boolean(
        config_parameter='accounting_base_kit.is_show_digital_sign_po',
        help="Show digital signature for purchase orders.")
    is_enable_options_po = fields.Boolean(
        config_parameter='accounting_base_kit.is_enable_options_po',
        help="Enable options for digital signatures on purchase orders.")
    is_confirm_sign_po = fields.Boolean(
        config_parameter='accounting_base_kit.is_confirm_sign_po',
        help="Require confirmation for digital signatures on purchase orders.")
    is_show_digital_sign_inventory = fields.Boolean(
        config_parameter='accounting_base_kit.is_show_digital_sign_inventory',
        help="Show digital signature for inventory operations.")
    is_enable_options_inventory = fields.Boolean(
        config_parameter='accounting_base_kit.is_enable_options_inventory',
        help="Enable options for digital signatures on inventory operations.")
    sign_applicable = fields.Selection(
        [('picking_operations', 'Picking Operations'),
         ('delivery', 'Delivery Slip'), ('both', 'Both')],
        string="Sign Applicable inside", default="picking_operations",
        config_parameter='accounting_base_kit.sign_applicable',
        help="Define where the digital signature is applicable.")
    is_confirm_sign_inventory = fields.Boolean(
        config_parameter='accounting_base_kit.is_confirm_sign_inventory',
        help="Require confirmation for digital signatures on inventory "
             "operations.")
    is_show_digital_sign_invoice = fields.Boolean(
        config_parameter='accounting_base_kit.is_show_digital_sign_invoice',
        help="Show digital signature for invoices.")
    is_enable_options_invoice = fields.Boolean(
        config_parameter='accounting_base_kit.is_enable_options_invoice',
        help="Enable options for digital signatures on invoices.")
    is_confirm_sign_invoice = fields.Boolean(
        config_parameter='accounting_base_kit.is_confirm_sign_invoice',
        help="Require confirmation for digital signatures on invoices.")
    is_show_digital_sign_bill = fields.Boolean(
        config_parameter='accounting_base_kit.is_show_digital_sign_bill',
        help="Show digital signature for bills.")

    automate_purchase = fields.Boolean(
        string='Confirm RFQ', help="Automate confirmation for RFQ",
        config_parameter='automate_purchase')
    automate_bills = fields.Boolean(
        string='Create Bill', config_parameter="automate_bills",
        help="Create bills for purchase order")
    automate_print_bills = fields.Boolean(
        string='Print Bills', config_parameter="automate_print_bills",
        help="Print bill from corresponding purchase order")
    automate_sale = fields.Boolean(
        string='Confirm Quotation', config_parameter="automate_sale",
        help="Automate confirmation for quotation")
    automate_invoice = fields.Boolean(
        string='Create Invoice', config_parameter="automate_invoice",
        help="Create invoices for sales order")
    automate_validate_invoice = fields.Boolean(
        string='Validate Invoice', config_parameter="automate_validate_invoice",
        help="Automate validation of invoice")
    automate_print_invoices = fields.Boolean(
        string='Print Invoices', config_parameter="automate_print_invoices",
        help="Print invoice from corresponding sales order")

    pos_res_partner_id = fields.Many2one(related='pos_config_id.res_partner_id',
                                         string='Default Customer', readonly=False)

    # Account Reconciliation
    reconcile_aggregate = fields.Selection(
        related="company_id.reconcile_aggregate", readonly=False
    )

    reconciliation_commit_every = fields.Integer(
        related="company_id.reconciliation_commit_every",
        string="How often to commit when performing automatic reconciliation.",
        help="Leave zero to commit only at the end of the process.",
        readonly=False,
    )

    auto_generate_barcode = fields.Boolean(
        string='Auto Generate Product Barcode', default=True,
        help="To automatically generate the product barcode.",
        config_parameter='accounting_base_kit.auto_generate_barcode')

    pro_internal_ref = fields.Boolean(string='Product Internal Ref.',
                                      help="Internal reference of products",
                                      config_parameter='accounting_base_kit.pro_internal_ref')

    auto_generate_internal_ref = fields.Boolean(
        string='Auto Generate Product Internal Ref.',
        help="To auto generate the product internal reference.",
        config_parameter='accounting_base_kit.auto_generate_internal_ref')
    product_name_config = fields.Boolean(string='Product Name Config',
                                         help="Name of the product config",
                                         config_parameter='accounting_base_kit.product_name_config')
    pro_name_digit = fields.Integer(string='Product Name Digit',
                                    help="Number of digit of product name",
                                    config_parameter='accounting_base_kit.pro_name_digit')
    pro_name_separator = fields.Char(string='Product Name Separator',
                                     help="Separator for product name",
                                     config_parameter='accounting_base_kit.pro_name_separator')
    pro_template_config = fields.Boolean(string='Product Attribute Config',
                                         help="To add the product attribute config",
                                         config_parameter='accounting_base_kit.pro_template_config')
    pro_template_digit = fields.Integer(string='Product Attribute Digit',
                                        help="Number of digit of product attribute",
                                        config_parameter='accounting_base_kit.pro_template_digit')
    pro_template_separator = fields.Char(string='Product Attribute Separator',
                                         help="Separator for product attribute",
                                         config_parameter="accounting_base_kit.pro_template_separator")
    pro_categ_config = fields.Boolean(string='Product Category Config',
                                      help="To add product category",
                                      config_parameter="accounting_base_kit.pro_categ_config")
    pro_categ_digit = fields.Integer(string='Product Category Digit',
                                     help="Number of product category digit",
                                     config_parameter='accounting_base_kit.pro_categ_digit')
    pro_categ_separator = fields.Char(string='Product Category Separator',
                                      help="Separator for product category",
                                      config_parameter='accounting_base_kit.pro_categ_separator')


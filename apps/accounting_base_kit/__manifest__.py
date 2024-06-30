# -*- coding: utf-8 -*-

{
    'name': 'Full Accounting Kit Odoo 17 (By Teracom)',
    'version': '17.0.1.20.40',
    'category': 'Accounting',
    'summary': """ 
                Asset and Budget Management,Accounting Reports, PDC, 
                Lock dates, Credit Limit, Follow Ups, Day-Bank-Cash Book Reports.
                """,
    'description': """ 
                The module used to manage the Full Account Features in Odoo 17.
                that can manage the Account Reports,Journals Asset and Budget Management, 
                Accounting Reports, PDC, Lock Dates, Credit Limit, Follow Ups, 
                Day-Bank-Cash Book Reports, Manage your employee Payroll Records
                and other Accounting Features.
                """,
    'author': 'Michael Okeleke, Teracom Consulting',
    'company': 'Teracom Consulting',
    'maintainer': 'Teracom Consulting',
    'website': 'https://www.teracomconsulting.org',
    'depends': ['base', 'account', 'website', 'mrp', 'hr_timesheet', 'account_check_printing', 'payment',
                'product', 'sale', 'point_of_sale', 'analytic', 'base_sparse_field', 'mail', 'hr_attendance',
                'purchase', 'sale_management', 'stock', 'hr_contract', 'hr_holidays', 'l10n_ng', 'resource',
                'hr_gamification', 'survey', 'contacts', 'hr_expense', 'hr_recruitment_survey', 'website_sale',
                'project_todo', 'base_address_extended',],

    'external_dependencies': {
        'python': ['numpy>=1.15', 'numpy-financial<=1.0.0', 'pytesseract', 'xlrd', 'chardet'],
        'deb': ['libatlas-base-dev'],
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        # Budget Management
        'views/account_analytic_account_views.xml',
        'views/account_budget_views.xml',

        # Account Module
        'data/account_financial_report_data.xml',
        'data/cash_flow_data.xml',
        'data/followup_levels.xml',
        'data/multiple_invoice_data.xml',
        'data/recurring_entry_cron.xml',
        'data/account_pdc_data.xml',
        'views/reports_config_view.xml',
        'views/accounting_menu.xml',
        'views/account_group.xml',
        'views/credit_limit_view.xml',
        'views/account_configuration.xml',
        'views/account_followup.xml',
        'views/followup_report.xml',
        'wizard/asset_depreciation_confirmation_wizard_views.xml',
        'wizard/asset_modify_views.xml',
        'views/account_asset_views.xml',
        'views/account_move_views.xml',
        'views/product_template_views.xml',
        'views/multiple_invoice_layout_view.xml',
        'views/multiple_invoice_form.xml',
        'wizard/financial_report.xml',
        'wizard/general_ledger.xml',
        'wizard/partner_ledger.xml',
        'wizard/tax_report.xml',
        'wizard/trial_balance.xml',
        'wizard/aged_partner.xml',
        'wizard/journal_audit.xml',
        'wizard/cash_flow_report.xml',
        'wizard/account_bank_book_wizard_view.xml',
        'wizard/account_cash_book_wizard_view.xml',
        'wizard/account_day_book_wizard_view.xml',
        'report/report_financial.xml',
        'report/general_ledger_report.xml',
        'report/report_journal_audit.xml',
        'report/report_aged_partner.xml',
        'report/report_trial_balance.xml',
        'report/report_tax.xml',
        'report/report_partner_ledger.xml',
        'report/cash_flow_report.xml',
        'report/account_bank_book_view.xml',
        'report/account_cash_book_view.xml',
        'report/account_day_book_view.xml',
        'report/account_asset_report_views.xml',
        'report/report.xml',
        'report/multiple_invoice_layouts.xml',
        'report/multiple_invoice_report.xml',
        'views/recurring_payments_view.xml',
        'wizard/account_lock_date.xml',
        'views/account_payment_view.xml',

        # Centralize your Product Views
        'views/product_menu.xml',

        # Manages Employee Stages
        'wizard/employee_stage_views.xml',

        # Accounting Journal Print
        'report/accounting_print_report_journal_entries_view.xml',
        'report/accounting_print_report_report_journal_entries.xml',

        # Nigeria Localization
        'data/res.country.state.csv',
        'data/res.city.csv',
        'data/res.bank.csv',
        'data/res_country_data.xml',

        # Invoice Details on Product
        'views/product_invoice_link_view.xml',

        # Sale,Purchase Mass Confirm and Cancel
        'views/sale_view.xml',
        'views/purchase_view.xml',

        # Force Availability Button in Delivery
        'views/stock_picking_views.xml',

        # Contact Person in Sale, Purchase and Invoice Orders
        'views/sr_inherited_sale_order.xml',
        'views/sr_inherited_invoice_order.xml',
        'views/sr_inherited_purchase_order.xml',
        'report/sr_inherited_sale_order_report.xml',
        'report/sr_inherited_invoice_order_report.xml',
        'report/sr_inherited_purchase_order_report.xml',

        # Payroll
        'data/hr_payroll_sequence.xml',
        'data/hr_payroll_data.xml',
        'wizard/hr_payslips_employees_views.xml',
        'wizard/payslip_lines_contribution_register_views.xml',
        'report/hr_payroll_report.xml',
        'report/report_contribution_register_templates.xml',
        'report/report_payslip_templates.xml',
        'report/report_payslip_details_templates.xml',
        'views/hr_leave_type_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_salary_rule_views.xml',
        'views/hr_salary_rule_category_views.xml',
        'views/hr_contribution_register_views.xml',
        'views/hr_payroll_structure_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_payslip_line_views.xml',
        'views/hr_payslip_run_views.xml',

        # Payroll Advanced Features
        'data/mail_template_data.xml',
        'wizard/payslip_confirm_views.xml',
        'report/hr_payslip_report_views.xml',

        # Account Loan management
        'data/ir_sequence_data.xml',
        'wizard/account_loan_generate_entries_view.xml',
        'wizard/account_loan_pay_amount_view.xml',
        'wizard/account_loan_increase_amount.xml',
        'wizard/account_loan_post_view.xml',
        'views/account_loan_view.xml',
        'views/account_move_view.xml',
        'views/account_loan_lines_view.xml',

        # Automatically creates employee while creating user
        'views/res_users_views.xml',

        # Manages the loan process of the employees
        'views/hr_loan_views.xml',

        # Adding Advanced Fields In Employee Master
        'views/hr_employee_views.xml',
        'data/hr_employee_relation_data.xml',
        'data/ir_cron_data.xml',

        # Manages the resignation process of the employees
        'views/hr_resignation_views.xml',

        # Salary Advance
        'data/hr_salary_rule_data.xml',
        'views/salary_advance_views.xml',

        # HR Appraisal
        'views/appraisal_templates.xml',
        'views/survey_user_input_views.xml',
        'views/hr_appraisal_views.xml',

        # Digital Signature In Purchase Order, Invoice, Inventory
        'views/digital_signature_views.xml',
        'report/invoice_report_templates.xml',
        'report/purchase_report_templates.xml',
        'report/stock_picking_report_templates.xml',

        # Customer/ Supplier Payment Statement Report
        'views/res_partner_views.xml',
        'report/res_partner_reports.xml',
        'report/res_partner_templates.xml',

        # Amount in Words Invoice, Purchase Order, Sales Order
        'views/amount_in_words_invoice.xml',
        'report/amount_in_words_invoice.xml',

        # Print Barcode in Sales, Invoice, Inventory, and Purchase Order Reports
        'report/inherited_sale_order_report.xml',
        'report/inherited_invoice_order_report.xml',
        'report/inherited_purchase_order_report.xml',
        'report/inherited_delivery_order_report.xml',

        # Employee Purchase Requisition
        'views/employee_purchase_requisition_views.xml',
        'report/employee_purchase_requisition_templates.xml',
        'report/employee_purchase_requisition_report.xml',

        # Inventory Turnover Analysis Report
        'views/fetch_data_views.xml',
        'views/turnover_graph_analysis_views.xml',
        'report/turnover_report_templates.xml',
        'wizard/turnover_report_views.xml',

        # Account Movement, Invoice, Bill and Credit-Note\Refund Line Views
        'views/account_move_line_view.xml',

        # BOM Structure & Cost Report in Excel
        'data/mrp_bom_data.xml',

        # Employee Late Check-In
        'views/late_check_in_views.xml',

        # Employee Announcement
        'views/hr_announcement_views.xml',

        # Master Search
        'views/master_search_view.xml',

        # Purchase and Sale Items Report
        'report/sales_report_view.xml',
        'report/purchase_report_view.xml',

        # Quick Publish\Unpublish Product on Website
        'wizard/product_publish_views.xml',

        # HR Timesheet Calendar View
        'views/hr_timesheet_calendar_view.xml',
        'views/hr_timesheet_report_calender_view.xml',

        # Sale Purchase Order Automated, WhatsApp & Email Integration
        'views/website_templates.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/website_views.xml',
        'views/selection_message_views.xml',
        'wizard/whatsapp_send_message_views.xml',
        'wizard/portal_share_views.xml',

        # Question Duplicator In Survey
        'views/action_question_duplicate.xml',
        'wizard/question_duplicate_views.xml',

        # Dynamic Accounts  Reports
        'views/accounting_report_views.xml',
        'report/trial_balance.xml',
        'report/general_ledger_templates.xml',
        'report/financial_report_template.xml',
        'report/partner_ledger_templates.xml',
        'report/financial_reports_views.xml',
        'report/balance_sheet_report_templates.xml',
        'report/bank_book_templates.xml',
        'report/aged_payable_templates.xml',
        'report/aged_receivable_templates.xml',
        'report/tax_report_templates.xml',

        # Company Scrap Management
        'views/scrap_management_line_views.xml',
        'views/scrap_management_views.xml',
        'views/stock_scrap_views.xml',
        'report/scrap_management_template.xml',
        'report/scrap_management_state_wise_template.xml',
        'report/scrap_management_reports.xml',
        'report/scrap_management_product_wise_template.xml',
        'wizard/scrap_management_report_views.xml',

        # Employee Bonus Management
        'views/employee_bonus_manager.xml',

        # Custom List View
        'report/custom_list_view_templates.xml',
        'report/custom_list_view_reports.xml',

        # Employee Promotion
        'views/employee_promotion_views.xml',
        'report/employee_promotion_report.xml',
        'report/employee_promotion_templates.xml',

        # Product Profit Report
        'report/product_profit_report_templates.xml',
        'report/profit_product_report_views.xml',
        'wizard/profit_product_views.xml',

        # Mass Price Update
        'wizard/mass_price_update_views.xml',

        # Employee Background Verification
        'views/employee_verification_portal_templates.xml',
        'views/employee_verification_views.xml',

        # Sales Contract and Recurring Invoices
        'report/subscription_contract_reports.xml',
        'views/subscription_contracts_views.xml',
        'views/subscription_contracts_templates.xml',
        'report/subscription_contract_templates.xml',

        # Stock Lot Archive
        'views/stock_lot_views.xml',

        # Advanced Cash Flow Statements
        'report/account_wizard_reports.xml',
        'report/account_wizard_templates.xml',
        'views/account_wizard_views.xml',

        # Employee Shift Management
        'views/hr_employee_shift_views.xml',
        'views/hr_employee_contract_views.xml',
        'wizard/hr_generate_shift_views.xml',

        # Employee Manufacturing Timesheet Management
        'views/manufacturing_timesheet.xml',

        # Employee Disciplinary Management
        'data/discipline_category_demo.xml',
        'views/disciplinary_action_views.xml',
        'views/discipline_category_views.xml',

        # Balance Leave Report
        'report/report_balance_leave_views.xml',

        # POS Order Default Customer
        'data/default_customer_data.xml',

        # Employee Pantry Order
        'views/pantry_order_views.xml',
        
        # Freight Management System
        'views/freight_management_system.xml',
        'report/freight_report_templates.xml',
        'wizard/custom_clearance_revision_views.xml',

        # Interest for Overdue Invoice
        'views/account_interest_on_overdue_invoice.xml',

        # Payment Transaction Logs
        'views/payment_transaction.xml',

        # Employee Business Card
        'views/business_card.xml',

        # Stock Location Report
        'views/stock_analysis_by_location_report.xml',

        # Stock Card Report
        'data/stock_card_report.xml',
        'report/stock_card_report.xml',
        'wizard/stock_card_report_wizard_view.xml',

        # Dynamic Product Label Print
        'report/label_layout_templates.xml',
        'views/dynamic_template_views.xml',
        'wizard/product_label_layout_views.xml',

        # Sale Order Invoice Linker
        'wizard/link_invoice_views.xml',

        # Bill Digitization
        'wizard/digitize_bill_views.xml',

        # Partner Trial Balance Report
        'report/partner_trial_balance_view.xml',
        'report/partner_trial_balance_template.xml',
        'report/partner_trial_balance_report.xml',

        # Product Sales Report
        'report/sale_products_report_view.xml',

        # Bank Statement Base
        'views/account_bank_statement.xml',
        'views/account_bank_statement_line.xml',

        # Account Reconcile OCA
        'views/account_reconcile/account_account_reconcile.xml',
        'views/account_reconcile/account_bank_statement_line.xml',
        'views/account_reconcile/account_move_line.xml',
        'views/account_reconcile/account_journal.xml',
        'views/account_reconcile/account_move.xml',
        'views/account_reconcile/account_account.xml',
        'views/account_reconcile/account_bank_statement.xml',

        # Account Mass Reconcile
        'views/account_reconcile/mass_reconcile.xml',
        'views/account_reconcile/mass_reconcile_history_view.xml',

        # Account Import Statement Files
        'wizard/account_statement_import_view.xml',

        # Bank Statement TXT/CSV/XLSX Import
        'data/map_data.xml',
        'views/account_reconcile/account_statement_import_sheet_mapping.xml',
        'views/account_reconcile/account_statement_import.xml',

        # Activity Dashboard and Management
        'views/activity_tag_views.xml',
        'views/activity_dashbord_views.xml',
        'views/mail_activity_views.xml',

        # Customer Follow Up Management
        'wizard/followup_results_view.xml',
        'views/followup_view.xml',
        'report/followup_report.xml',

        # Product Internal Reference Generator
        'data/product_internal_ref_generator.xml',

        # General Views Placement
        'views/res_config_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'accounting_base_kit/static/src/scss/*.scss',
            'accounting_base_kit/static/src/css/stock_card_report.css',
            'accounting_base_kit/static/src/css/whatsapp_icon_website.css',
            'accounting_base_kit/static/src/js/action_manager.js',
            'accounting_base_kit/static/src/js/whatsapp_icon.js',
            'accounting_base_kit/static/src/js/mail_icon.js',
            'accounting_base_kit/static/src/xml/whatsapp_icon_template.xml',
            'accounting_base_kit/static/src/xml/mail_icon_template.xml',

            # Dynamic Accounts  Reports
            'accounting_base_kit/static/src/xml/general_ledger_view.xml',
            'accounting_base_kit/static/src/xml/trial_balance_view.xml',
            'accounting_base_kit/static/src/xml/cash_flow_templates.xml',
            'accounting_base_kit/static/src/xml/bank_flow_templates.xml',
            'accounting_base_kit/static/src/xml/profit_and_loss_templates.xml',
            'accounting_base_kit/static/src/xml/balance_sheet_template.xml',
            'accounting_base_kit/static/src/xml/partner_ledger_view.xml',
            'accounting_base_kit/static/src/xml/aged_payable_report_views.xml',
            'accounting_base_kit/static/src/xml/aged_receivable_report_views.xml',
            'accounting_base_kit/static/src/xml/tax_report_views.xml',
            'accounting_base_kit/static/src/css/accounts_report.css',
            'accounting_base_kit/static/src/js/general_ledger.js',
            'accounting_base_kit/static/src/js/trial_balance.js',
            'accounting_base_kit/static/src/js/cash_flow.js',
            'accounting_base_kit/static/src/js/bank_flow.js',
            'accounting_base_kit/static/src/js/profit_and_loss.js',
            'accounting_base_kit/static/src/js/balance_sheet.js',
            'accounting_base_kit/static/src/js/partner_ledger.js',
            'accounting_base_kit/static/src/js/aged_payable_report.js',
            'accounting_base_kit/static/src/js/aged_receivable_report.js',
            'accounting_base_kit/static/src/js/tax_report.js',

            # Custom List View
            'accounting_base_kit/static/src/js/list_controller.js',
            'accounting_base_kit/static/src/xml/list_controller.xml',

            # Dashboard
            'accounting_base_kit/static/src/webclient/dashboard/*.js',
            'accounting_base_kit/static/src/webclient/dashboard/*.xml',

            # Activity Dashboard and Management
            'accounting_base_kit/static/src/activity_dashboard/css/dashboard.css',
            'accounting_base_kit/static/src/activity_dashboard/css/style.scss',
            'accounting_base_kit/static/src/activity_dashboard/css/material-gauge.css',
            'accounting_base_kit/static/src/activity_dashboard/xml/activity_dashboard_template.xml',
            'accounting_base_kit/static/src/activity_dashboard/js/activity_dashboard.js',

            # WhatsApp Button
            'accounting_base_kit/static/src/webclient/whatsapp_button/*.js',
            'accounting_base_kit/static/src/webclient/whatsapp_button/*.xml',

            # Bill Digitization
            'accounting_base_kit/static/src/webclient/bill_digitization/*.js',
            'accounting_base_kit/static/src/webclient/bill_digitization/*.xml',

            # Account Reconcile OCA
            'accounting_base_kit/static/src/account_reconcile/js/widgets/reconcile_data_widget.esm.js',
            'accounting_base_kit/static/src/account_reconcile/js/widgets/reconcile_chatter_field.esm.js',
            'accounting_base_kit/static/src/account_reconcile/js/widgets/selection_badge_uncheck.esm.js',
            'accounting_base_kit/static/src/account_reconcile/js/widgets/reconcile_move_line_widget.esm.js',
            'accounting_base_kit/static/src/account_reconcile/js/reconcile_move_line/*.esm.js',
            'accounting_base_kit/static/src/account_reconcile/js/reconcile_form/*.esm.js',
            'accounting_base_kit/static/src/account_reconcile/js/reconcile_manual/*.esm.js',
            'accounting_base_kit/static/src/account_reconcile/js/reconcile/*.esm.js',
            'accounting_base_kit/static/src/account_reconcile/xml/reconcile.xml',
            'accounting_base_kit/static/src/account_reconcile/scss/reconcile.scss',
        ],
        'web.assets_frontend': [
            'accounting_base_kit/static/src/css/whatsapp_icon_website.css',
            'accounting_base_kit/static/src/js/whatsapp_web_icon.js',
            'accounting_base_kit/static/src/js/whatsapp_modal.js',
        ],
        'point_of_sale._assets_pos': [
            'accounting_base_kit/static/src/js/pos/EditListPopup.esm.js',
            'accounting_base_kit/static/src/js/pos/ErrorMultiLotBarcodePopup.esm.js',
            'accounting_base_kit/static/src/js/pos/ProductScreen.esm.js',
            'accounting_base_kit/static/src/js/pos/models.esm.js',
            'accounting_base_kit/static/src/xml/pos/LotSelectorPopup.xml',
            'accounting_base_kit/static/src/xml/pos/ErrorMultiLotBarcodePopup.xml',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'post_init_hook': 'post_init_hook',
}


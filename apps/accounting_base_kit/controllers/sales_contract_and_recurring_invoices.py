# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalAccount(CustomerPortal):
    """ Super customer portal and get count of contracts """
    def _prepare_home_portal_values(self, counters):
        """ Prepares values for the home portal """
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id.id
        contract_count = request.env['subscription.contracts'].search([('partner_id', '=', partner)])
        values['contract_count'] = len(contract_count)
        return values


class ContractsController(http.Controller):
    """ Sale contract in customer portal controller """
    @http.route(['/my/contracts'], type='http', auth='user', csrf=False, website=True)
    def portal_my_quotes(self):
        """ Displays Contracts in portal """
        partner = request.env.user.partner_id.id
        values = {'records': request.env['subscription.contracts'].search(
                [('partner_id', '=', partner)]),
        }
        return request.render('accounting_base_kit.tmp_contract_details', values)

    @http.route(['/contracts/<int:contract_id>/'], type='http', auth='user', csrf=False, website=True)
    def portal_manufacture(self, contract_id):
        """ Customer portal subscription contract """
        values = {
            'records': request.env['subscription.contracts'].browse(contract_id),
        }
        return request.render('accounting_base_kit.contract_details', values)

    @http.route(['/report/pdf/<int:contract_id>/'], type='http', auth='user', csrf=False, website=True)
    def action_print_report(self, contract_id):
        """ Print subscription contract report """
        data = {
            'records': request.env['subscription.contracts'].browse(contract_id)
        }
        report = request.env.ref(
            'accounting_base_kit.action_report_subscription_contracts')
        pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'accounting_base_kit.action_report_subscription_contracts', [report.id], data=data)[0]
        pdf_http_headers = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=pdf_http_headers)

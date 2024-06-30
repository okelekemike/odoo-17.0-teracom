# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class SendMessage(http.Controller):
    """ Controller for whatsapp message templates """
    @http.route('/whatsapp_message', type='json', auth='public')
    def whatsapp_message(self, **kwargs):
        """ Whatsapp message templates """
        messages = request.env['selection.message'].sudo().search_read(fields=['name', 'message'])
        return {'messages': messages}

    @http.route('/mobile_number', type='json', auth='public')
    def mobile_number(self, **kwargs):
        """ Mobile number of website """
        mobile_number = request.env['website'].sudo().search_read(fields=['mobile_number'])
        return {'mobile': mobile_number}

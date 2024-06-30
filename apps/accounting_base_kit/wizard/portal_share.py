# -*- coding: utf-8 -*-

import urllib.parse as urllib
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PortalShare(models.TransientModel):
    """ Inheriting 'portal.share' for adding custom fields."""
    _inherit = 'portal.share'

    share_type = fields.Selection([
        ('mail', 'Mail'),
        ('whatsapp', 'Whatsapp')], string="Sharing Method", default="mail")
    mobile_number = fields.Char(string="Mobile number")

    partner_id = fields.Many2one('res.partner',
                                 string="Recipient",
                                 help="Partner")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ Assigns mobile number of the selected partner."""
        self.mobile_number = self.env.context.get('default_mobile') or self.partner_id.mobile or self.partner_id.phone
        # if self.partner_id and not self.mobile_number:
        #     raise UserError(_("No mobile number found in database for partner: ") + str(self.partner_id.name))

    def action_send_whatsapp(self):
        """ This function redirects to the whatsapp web with required
        parameters."""
        if self.note and self.mobile_number:
            if self.res_model == 'sale.order':
                common_message = _('You have been invited to access the following Sale Order.')
            elif self.res_model == 'account.move':
                common_message = _('You have been invited to access the following Invoice.')
            elif self.res_model == 'purchase.order':
                common_message = _('You have been invited to access the following Purchase Order.')
            else:
                common_message = _('You have been invited to access the following Document.')
            message_string = (self.note + '%0a' + common_message + '%0a' +
                              urllib.quote(self.share_link))
            related_record = self.env[self.res_model].search([
                ('id', '=', int(self.res_id))])
            related_record.message_post(body=message_string)
            return {
                'type': 'ir.actions.act_url',
                'url': "https://api.whatsapp.com/send?phone=" +
                       self.mobile_number + "&text=" + message_string,
                'target': 'new',
                'res_id': self.id,
            }

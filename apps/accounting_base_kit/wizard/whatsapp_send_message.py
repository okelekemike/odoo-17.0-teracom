# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from urllib.parse import quote


class WhatsappSendMessage(models.TransientModel):
    """ Wizard for sending whatsapp message."""
    _name = 'whatsapp.send.message'
    _description = 'Whatsapp Send Message'

    partner_id = fields.Many2one('res.partner',
                                 string="Recipient",
                                 help="Partner")
    mobile = fields.Char(string="Contact Number",
                         required=True,
                         help="Contact number of Partner")
    message = fields.Text(string="Message",
                          required=True,
                          help="Message to send")
    image_1920 = fields.Binary(string='Image', help="Image of Partner")
    partner_readonly = fields.Boolean(default=False)
    mobile_readonly = fields.Boolean(default=False)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ Function for fetching the mobile number and image of partner."""
        self.mobile = self.env.context.get('default_mobile') or self.partner_id.mobile or self.partner_id.phone
        if self.partner_id and not self.mobile:
            raise UserError(_("No mobile number found in database for partner: ") + self.partner_id.name)
        self.image_1920 = self.partner_id.image_1920
        self.partner_readonly = True if self.env.context.get('default_partner_id') else False
        self.mobile_readonly = True if self.env.context.get('default_mobile') else False

    def send_message(self):
        """ This function redirects to the whatsapp web with required
        parameters.
        """
        if self.message and self.mobile:
            message_string = quote(self.message.encode("utf-8"))
            message_string = message_string[:(len(message_string) - 3)]
            message_post_content = "WhatsApp Message Sent:\n" + self.mobile + "\n" + self.message
            if self.partner_id:
                self.partner_id.message_post(body=message_post_content)
            return {
                'type': 'ir.actions.act_url',
                'url': "https://api.whatsapp.com/send?phone=" + self.mobile + "&text=" + message_string,
                'target': 'new',
                'res_id': self.id,
            }

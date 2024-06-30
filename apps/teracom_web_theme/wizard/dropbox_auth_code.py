# -*- coding: utf-8 -*-

from werkzeug import urls
from odoo import api, fields, models, _

GOOGLE_AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_ENDPOINT = 'https://accounts.google.com/o/oauth2/token'


class AuthenticationWizard(models.TransientModel):
    """Wizard to handle authentication for backup configuration.
    This wizard allows users to enter the Dropbox authorization code and
    sets up the Dropbox refresh token."""
    _name = 'dropbox.auth.code'
    _description = 'Authentication Code Wizard'

    dropbox_authorization_code = fields.Char(
        string='Dropbox Authorization Code',
        help='The authorization code of dropbox')
    dropbox_auth_url = fields.Char(string='Dropbox Authentication URL',
                                   compute='_compute_dropbox_auth_url',
                                   help='Dropbox authentication URL')

    @api.depends('dropbox_authorization_code')
    def _compute_dropbox_auth_url(self):
        """Compute method to generate the Dropbox authentication URL based on
        the provided authorization code."""
        backup_config = self.env['db.backup.configure'].browse(
            self.env.context.get('active_id'))
        dropbox_auth_url = backup_config.get_dropbox_auth_url()
        for rec in self:
            rec.dropbox_auth_url = dropbox_auth_url

    def action_setup_dropbox_token(self):
        """Action method to set up the Dropbox refresh token using the
        provided authorization code."""
        backup_config = self.env['db.backup.configure'].browse(
            self.env.context.get('active_id'))
        backup_config.hide_active = True
        backup_config.active = True
        backup_config.set_dropbox_refresh_token(self.dropbox_authorization_code)

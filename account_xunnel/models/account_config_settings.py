# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, exceptions, _


def assert_xunnel_token(function):
    """Raises an user error whenever the user
    tries to manual update either providers or invoices
    without having any Xunnel Token registered in its company.
    """
    def wraper(self):
        if not self.company_id.xunnel_token:
            raise exceptions.UserError(_(
                "Your company doesn't have a Xunnel Token "
                "established. Make sure you have saved your"
                " configuration changes before trying manual sync."))
        return function(self)
    return wraper


class AccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    xunnel_last_sync = fields.Date(
        string='Last Sync in Xunnel', related='company_id.xunnel_last_sync')
    xunnel_token = fields.Char(
        related='company_id.xunnel_token',
        help="Key-like text for authentication in controllers.")
    xunnel_testing = fields.Boolean(
        help="Use Xunnel server testing?", related='company_id.xunnel_testing')

    @api.model
    def get_values(self):
        res = super(AccountConfigSettings, self).get_values()
        company = self.company_id
        res.update(
            xunnel_last_sync=company.xunnel_last_sync,
            xunnel_token=company.xunnel_token
        )
        return res

    @api.multi
    def set_values(self):
        super(AccountConfigSettings, self).set_values()
        company = self.company_id
        company.write({
            'xunnel_last_sync': self.xunnel_last_sync,
            'xunnel_token': self.xunnel_token
        })

    @api.multi
    @assert_xunnel_token
    def sync_xunnel_providers(self):
        self.company_id.sync_xunnel_providers()

    @api.multi
    @assert_xunnel_token
    def sync_xunnel_attachments(self):
        self.company_id.sync_xunnel_attachments()

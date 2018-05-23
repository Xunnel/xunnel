# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from json import dumps

import requests
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    xunnel_token = fields.Char()
    xunnel_testing = fields.Boolean()

    @api.multi
    def _xunnel(self, endpoint, payload=None):
        """_xunnel calls xunnel.com and returns it response.
            if is there any an exception. The error message within the API
            response will be raised.
        """
        self.ensure_one()
        base = "https://xunnel.com/"
        if self.xunnel_testing:
            base = "https://ci.xunnel.com/"
        response = requests.post(
            str(base) + endpoint,
            headers={'Xunnel-Token': str(self.xunnel_token)},
            data=dumps(payload) if payload else None)
        return response.json()

    @api.multi
    def cron_get_xunnel_providers(self):
        """Sync all the providers from all companies that have xunnel_provider
        """
        for rec in self.search([('xunnel_token', '!=', False)]):
            rec.sync_xunnel_providers()

    @api.multi
    def sync_xunnel_providers(self):
        """Requests https://wwww.xunnel.com/ to retrive all providers
        related to the current company and check them in the database
        to create them if they're not. After sync journals.
        """
        self.ensure_one()
        providers_response = self._xunnel('get_xunnel_providers')
        if providers_response.get('error'):
            return
        for provider in providers_response.get('response'):
            provider.update(company_id=self.id, provider_type='xunnel')
            online_provider = self.env['account.online.provider'].search([
                ('provider_account_identifier', '=',
                 provider.get('provider_account_identifier'))], limit=1)
            if online_provider:
                online_provider.write(provider)
            else:
                online_provider = online_provider.create(provider)
            online_provider.sync_journals()

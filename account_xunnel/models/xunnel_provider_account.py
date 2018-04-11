# -*- coding: utf-8 -*-
# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class XunnelProviderAccount(models.Model):
    _inherit = 'account.online.provider'

    provider_type = fields.Selection(selection_add=[('xunnel', 'Xunnel')])

    @api.multi
    def _sync_journals(self):
        for account in self._get_journals():
            obj_jor = self.env['account.online.journal']
            journal = obj_jor.search(
                [('online_identifier', '=', account.get('id_account'))])
            vals = {
                'name': account.get('name'),
                'balance': account.get('balance'),
                'account_number': account.get('number'),
                'online_identifier': account.get('id_account'),
                'account_online_provider_id': self.id,
                'last_sync': fields.Datetime.now()
            }
            if journal:
                journal.write(vals)
            else:
                obj_jor.create(vals)

    @api.multi
    def _get_journals(self):
        res = self.company_id._xunnel(
            'get_xunnel_accounts',
            dict(credential_id=self.provider_account_identifier))
        err = res.get('error')
        if err:
            raise UserError(err)
        return res.get('response')

    @api.multi
    def update_credentials(self):
        raise UserError(
            'Updating credentials is not allowed here. '
            'Please go to https://www.xunnel.com/ to achieve that.')

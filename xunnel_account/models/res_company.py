# -*- coding: utf-8 -*-
# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import requests
from json import dumps
from odoo import api, fields, models
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    ciec_key = fields.Char(string="CIEC Key")
    xunnel_last_sync = fields.Date(string='Last Sync in Xunnel')
    xunnel_token = fields.Char()

    @api.model
    def _xunnel(self, endpoint, payload=None):
        """_xunnel calls xunnel.com and returns it response.
            if is there any an exception. The error message within the API
            response will be raised.
        """
        base = self.env['ir.config_parameter'].get_param(
            'xunnel_account.url')
        response = requests.post(
            str(base) + endpoint,
            headers={'Xunnel-Token': str(self.xunnel_token)},
            data=dumps(payload) if payload else None)
        return response.json()

    @api.model
    def _cron_xunnel_sync(self):
        for rec in self.search([]):
            if not rec.ciec_key:
                continue
            credentials = {
                'rfc': rec.vat,
                'password': rec.ciec_key,
            }
            response = rec._xunnel(
                'get_invoices_sat',
                dict(
                    credentials=credentials,
                    last_sync=rec.xunnel_last_sync))
            err = response.get('error')
            if err:
                raise UserError(err)
            files = response.get('response')
            self.env['account.pre.invoice'].each_invoice(files)
            rec.xunnel_last_sync = fields.Date.context_today(self)

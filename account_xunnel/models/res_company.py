# -*- coding: utf-8 -*-
# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
from codecs import BOM_UTF8
from datetime import datetime
from json import dumps
from time import mktime

import requests
from odoo import api, fields, models
from odoo.exceptions import UserError

BOM_UTF8U = BOM_UTF8.decode('UTF-8')


class ResCompany(models.Model):
    _inherit = 'res.company'

    xunnel_last_sync = fields.Date(string='Last Sync in Xunnel')
    xunnel_token = fields.Char()

    @api.multi
    def _xunnel(self, endpoint, payload=None):
        """_xunnel calls xunnel.com and returns it response.
            if is there any an exception. The error message within the API
            response will be raised.
        """
        self.ensure_one()
        base = self.env['ir.config_parameter'].get_param(
            'account_xunnel.url')
        response = requests.post(
            str(base) + endpoint,
            headers={'Xunnel-Token': str(self.xunnel_token)},
            data=dumps(payload) if payload else None)
        return response.json()

    @api.model
    def cron_xunnel_sync(self):
        att_obj = self.env['ir.attachment']
        for rec in self.search([]):
            response = rec._xunnel(
                'get_invoices_sat',
                dict(
                    last_sync=mktime(datetime.strptime(
                        '2009-01-01', '%Y-%m-%d').timetuple())
                ))
            err = response.get('error')
            if err:
                raise UserError(err)
            for item in response.get('response'):
                xml = item[0].lstrip(BOM_UTF8U).encode("UTF-8")
                json = item[1]
                attachment = att_obj.search([
                    ('name', '=', 'Xunnel_' + json['id_attachment'])])
                if not attachment:
                    att_obj.create({
                        'name': 'Xunnel_' + json['id_attachment'],
                        'datas_fname': (
                            'Xunnel_' + json['id_attachment'] + '.xml'),
                        'type': 'binary',
                        'datas': base64.encodestring(xml),
                        'description': str(json),
                        'index_content': xml,
                        'mimetype': 'text/plain',
                    })
            rec.xunnel_last_sync = fields.Date.context_today(self)

    @api.multi
    def cron_get_xunnel_providers(self):
        for rec in self.search([('xunnel_token', '!=', False)]):
            rec.sync_xunnel_providers()

    @api.multi
    def sync_xunnel_providers(self):
        self.ensure_one()
        prov_res = self._xunnel('get_xunnel_providers')
        if prov_res.get('error'):
            return
        for provider in prov_res.get('response'):
            provider.update(company_id=self.id, provider_type='xunnel')
            prov = self.env['account.online.provider'].search([
                ('provider_account_identifier', '=',
                 provider.get('provider_account_identifier'))], limit=1)
            if prov:
                prov.write(provider)
            else:
                prov = prov.create(provider)
            prov.sync_journals()

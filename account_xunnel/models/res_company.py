# -*- coding: utf-8 -*-
# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import requests
from json import dumps
from odoo import api, fields, models
from odoo.exceptions import UserError
from time import mktime
from datetime import datetime


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
            response.get('response')
            rec.xunnel_last_sync = fields.Date.context_today(self)

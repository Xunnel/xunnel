# -*- coding: utf-8 -*-
# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json

from odoo import api, fields, models
from odoo.exceptions import UserError


class XunnelProviderAccount(models.Model):
    _inherit = 'account.online.provider'

    provider_type = fields.Selection(selection_add=[('xunnel', 'Xunnel')])

    @api.multi
    def get_institution(self, search_string):
        response = self.env.user.company_id._xunnel('get_xunnel_sites')
        err = response.get('error')
        if err:
            raise UserError(err)
        ins = []
        institutions = response.get('response')
        for institution in institutions:
            if search_string.lower() in institution[
                    'name'].lower() and institution[
                    'id_site_organization_type'] == '56cf4f5b784806cf028b4568':
                ins.append({'id': institution['id_site'],
                            'name': institution['name'],
                            'status': 'Supported',
                            'countryISOCode': institution['country_code'],
                            'baseUrl': '/',
                            'loginUrl': '/',
                            'type_provider': 'Xunnel'})
        return ins

    @api.multi
    def get_login_form(self, id_site, provider):
        if provider != 'Xunnel':
            return super(XunnelProviderAccount, self).get_login_form(
                id_site, provider)
        response = self.env.user.company_id._xunnel(
            'get_site_info', dict(id_site=id_site))
        err = response.get('error')
        if err:
            raise UserError(err)
        resp_json = response.get('response')
        return {'type': 'ir.actions.client',
                'tag': 'xunnel_online_sync_widget',
                'target': 'new',
                'resp_json': json.loads(resp_json),
                'context': self.env.context,
                }

    @api.multi
    def update_status(self, status, code=0):
        with self.pool.cursor() as cr:
            self = self.with_env(self.env(cr=cr)).write({
                'status': status,
                'status_code': code,
                'last_refresh': fields.Datetime.now()
            })

    @api.multi
    def xunnel_add_update_provider_account(
            self, credentials, resp_json, twofa):
        if 'id_site' not in resp_json:
            return resp_json
        response = self.env.user.company_id._xunnel(
            'register_credentials', dict(
                id_site=resp_json['id_site'],
                credentials=credentials, twofa=twofa))
        err = response.get('error')
        if err:
            raise UserError(err)
        response_o = response.get('response')
        response = json.loads(response_o[1])
        if response_o[0] == 410:
            resp_json.update({
                'action': 'twofa',
                'account_online_provider_id': self.id,
                'twofa': response['twofa'],
                'address': response['address'],
                'params': credentials,
            })
            return resp_json
        provider_account = self.search([
            ('provider_account_identifier', '=', response['id_credential']),
            ('company_id', '=', self.env.user.company_id.id)], limit=1)
        if not provider_account:
            vals = {
                'name': resp_json['institution_name'] or 'Online institution',
                'provider_account_identifier': response['id_credential'],
                'provider_identifier': resp_json['id_site'],
                'status': 'IN_PROGRESS',
                'status_code': 0,
                'message': '',
                'last_refresh': fields.Datetime.now(),
                'provider_type': 'xunnel'}
            with self.pool.cursor() as cr:
                provider_account = self.with_env(self.env(cr=cr)).create(vals)
        provider_account.update_status('SUCCESS')
        account_added = provider_account.xunnel_add_update_account(response)
        return {
            'action': 'success',
            'numberAccountAdded': len(account_added),
        }

    @api.multi
    def xunnel_add_update_account(self, response):
        account_added = self.env['account.online.journal']
        for account in response['accounts']:
            vals = {'balance': account['balance']}
            with self.pool.cursor() as cr:
                account_search = self.env['account.online.journal'].with_env(
                    self.env(cr=cr)).search([
                        ('account_online_provider_id', '=', self.id),
                        ('online_identifier', '=', account['id_account'])],
                        limit=1)
            if not account_search:
                vals.update({
                    'name': account['name'],
                    'account_online_provider_id': self.id,
                    'online_identifier': account['id_account'],
                    'account_number': account['number'],
                    'last_sync': fields.Datetime.now(),
                })
                with self.pool.cursor() as cr:
                    acc = self.env['account.online.journal'].with_env(
                        self.env(cr=cr)).create(vals)
                account_added += acc
            else:
                with self.pool.cursor() as cr:
                    account_search.env['account.online.journal'].with_env(
                        self.env(cr=cr)).write(vals)
        return account_added

    @api.multi
    def manual_sync(self):
        if self.provider_type != 'xunnel':
            return super(XunnelProviderAccount, self).manual_sync()
        self.update_status('SUCCESS')
        transactions = []
        for account in self.account_online_journal_ids.filtered(
                lambda l: l.journal_ids):
            tr = account.retrieve_transactions()
            transactions.append({
                'journal': account.journal_ids[0].name,
                'count': tr,
            })
        resp_json = {'action': 'success', 'transactions': transactions}
        ctx = dict(self._context or {})
        ctx.update({
            'init_call': False,
            'provider_account_identifier': self.id,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'xunnel_online_sync_widget',
            'target': 'new',
            'resp_json': resp_json,
            'context': ctx,
        }

    @api.multi
    def update_credentials(self):
        if self.provider_type != 'xunnel':
            return super(XunnelProviderAccount, self).update_credentials()
        ret_action = self.get_login_form(self.provider_identifier, 'Xunnel')
        ctx = dict(self._context or {})
        ctx.update({
            'update': True,
            'provider_account_identifier': self.id,
        })
        ret_action['context'] = ctx
        return ret_action

    @api.model
    def cron_fetch_online_transactions(self):
        if self.provider_type != 'xunnel':
            return super(
                XunnelProviderAccount, self).cron_fetch_online_transactions()
        self.manual_sync()

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.provider_type == 'xunnel':
                response = self.env.user.company_id._xunnel(
                    'delete_credentials')
                err = response.get('error')
                if err:
                    raise UserError(err)
        super(XunnelProviderAccount, self).unlink()

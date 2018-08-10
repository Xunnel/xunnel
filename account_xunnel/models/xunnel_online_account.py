# Copyright 2017, Vauxoo, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
from datetime import datetime
from time import mktime
from odoo import api, models, _
from odoo.exceptions import UserError


class ProviderAccount(models.Model):
    _inherit = 'account.online.journal'

    @api.multi
    def retrieve_transactions(self, forced_params=None):
        if self.account_online_provider_id.provider_type != 'xunnel':
            return super(ProviderAccount, self).retrieve_transactions()
        params = {
            'id_account': self.online_identifier,
            'id_credential':
                self.account_online_provider_id.provider_account_identifier
        }
        if forced_params is not None:
            params.update(forced_params)
        elif self.last_sync:
            params.update(
                dt_transaction_from=mktime(datetime.strptime(
                    self.last_sync, '%Y-%m-%d').timetuple()))
        resp = self.env.user.company_id._xunnel(
            'get_xunnel_transactions', params)
        err = resp.get('error')
        if err:
            raise UserError(err)
        resp_json = json.loads(resp.get('response'))
        transactions = []
        json_transactions = resp_json['transactions']
        for transaction in json_transactions:
            trans = {
                'id': transaction['id_transaction'],
                'date': datetime.fromtimestamp(
                    int(transaction['dt_transaction'])).strftime('%Y-%m-%d'),
                'description': transaction['description'],
                'amount': transaction['amount'],
                'end_amount': resp_json['balance'],
            }
            if 'meta' in transaction and 'location' in transaction['meta']:
                trans['location'] = transaction['meta']['location']
            transactions.append(trans)
        if not self.journal_ids or not transactions:
            return 0
        journal_id = self.journal_ids[0]
        statement_obj = self.env['account.bank.statement']
        line_statement_obj = self.env['account.bank.statement.line']
        response = statement_obj.online_sync_bank_statement(
            transactions, journal_id)
        statement = statement_obj.search(
            [('journal_id', '=', journal_id.id)],
            order="date desc, id desc", limit=1)
        starting_balance = line_statement_obj.search([
            ('id', 'in', statement.line_ids.ids),
            ('online_identifier', '=', False)], limit=1)
        if starting_balance:
            statement.write({'balance_start': starting_balance.amount})
            starting_balance.unlink()
        last_date = line_statement_obj.search(
            [('id', 'in', statement.line_ids.ids)], limit=1,
            order='date desc').date
        statement.date = last_date
        statement.line_ids.write({
            'note': _('Transaction synchronized from Xunnel')})
        return response

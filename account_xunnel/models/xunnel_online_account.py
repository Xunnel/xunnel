# Copyright 2017, Vauxoo, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
from datetime import datetime
from time import mktime
from odoo import api, models
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
        for transaction in resp_json['transactions']:
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
        if not self.journal_ids:
            return 0
        # Create the bank statement with the transactions
        return self.env['account.bank.statement'].online_sync_bank_statement(
            transactions, self.journal_ids[0])

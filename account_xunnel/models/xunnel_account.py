# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    @api.multi
    def manual_sync(self):
        online_journal = self.account_online_journal_id
        if online_journal.account_online_provider_id.provider_type != 'xunnel':
            return super(AccountJournal, self).manual_sync()
        return online_journal.retrieve_transactions()

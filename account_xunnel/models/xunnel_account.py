# Copyright 2017, Vauxoo, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    online_journal_last_sync = fields.Date(
        "Online account last synchronization",
        related="account_online_journal_id.last_sync",
        track_visibility='always')

    @api.multi
    def manual_sync(self):
        online_journal = self.account_online_journal_id
        if online_journal.account_online_provider_id.provider_type != 'xunnel':
            return super(AccountJournal, self).manual_sync()
        return online_journal.retrieve_transactions()

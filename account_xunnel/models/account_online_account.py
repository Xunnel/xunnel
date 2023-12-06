# Copyright 2017, Vauxoo, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
from datetime import datetime
from time import mktime

from odoo import models
from odoo.exceptions import UserError


class AccountOnlineAccount(models.Model):
    _inherit = "account.online.account"

    def _refresh(self):
        """xunnel does not need to pre download transactions"""
        return True

    def _retrieve_transactions(self, date=None, include_pendings=False):
        self.ensure_one()
        if not self.account_online_link_id.is_xunnel:
            return super()._retrieve_transactions(date, include_pendings)
        resp_json = self._get_transactions()
        transactions = self._prepare_transactions(resp_json).get("transactions", [])
        return {
            "transactions": self._format_transactions(transactions),
            "pendings": [],
        }

    def _get_transactions(self):
        params = {"id_account": self.online_identifier, "id_credential": self.account_online_link_id.client_id}
        if self.last_sync:
            params.update(dt_transaction_from=mktime(self.last_sync.timetuple()))
        resp = self.env.company._xunnel("get_xunnel_transactions", params)
        err = resp.get("error")
        if err:
            raise UserError(err)
        return json.loads(resp.get("response"))

    def _prepare_transactions(self, resp_json):
        json_transactions = resp_json["transactions"]
        if not self.journal_ids or not json_transactions:
            return {}
        journal_id = self.journal_ids[0]
        transactions = {}
        for transaction in json_transactions:
            date = datetime.strptime(transaction["dt_authorization"], "%Y-%m-%d")
            trans = {
                "ref": transaction["reference"],
                "payment_ref": transaction["description"],
                "online_transaction_identifier": transaction["id_transaction"],
                "date": date.date(),
                "amount": transaction["amount"],
                "card_number": transaction["card_number"],
                "journal_id": journal_id.id,
            }
            manual_lines = self.env["account.bank.statement.line"].search(
                [
                    ("journal_id", "=", journal_id.id),
                    ("date", "=", trans["date"]),
                    ("amount", "=", trans["amount"]),
                    ("online_transaction_identifier", "=", False),
                ],
                limit=2,
            )
            if len(manual_lines) == 1:
                manual_lines.online_transaction_identifier = trans["online_transaction_identifier"]
                if manual_lines.name:
                    manual_lines.name += " - " + trans["payment_ref"]
                continue
            if "meta" in transaction and "location" in transaction["meta"]:
                trans["location"] = transaction["meta"]["location"]
            transactions.setdefault("transactions", []).append(trans)
        return transactions

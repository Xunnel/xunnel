from json import dumps

from requests_mock import mock

from odoo import Command
from odoo.tests.common import TransactionCase, tagged

from . import response


@tagged("account_journal")
class TestAccountJournal(TransactionCase):
    def setUp(self):
        super().setUp()
        self.url = "https://xunnel.com/"
        self.company = self.env.user.company_id
        suspense_account = self.env["account.account"].create(
            {
                "account_type": "expense",
                "name": "account xunnel",
                "code": "121050",
                "create_asset": "no",
                "company_id": self.company.id,
            }
        )
        self.company.account_journal_suspense_account_id = suspense_account.id
        self.company.xunnel_token = "test token"
        self.link = self.env["account.online.link"].create(
            {
                "name": "Acme Bank - Normal with Attachments",
                "is_xunnel": True,
                "client_id": "5ad5ad730c212a6a268b45e4",
                "company_id": self.env.user.company_id.id,
            }
        )

        self.account = self.env["account.online.account"].create(
            {
                "name": "ACME Checking",
                "account_online_link_id": self.link.id,
                "account_number": "00000001",
                "last_sync": "1970-01-01",
                "online_identifier": "5a9dcb3d244283f35a8c6e22",
                "balance": 1099,
            }
        )

        self.journal = self.env["account.journal"].create(
            {
                "name": "Demo bank attachments",
                "code": "TESTB",
                "type": "bank",
                "company_id": self.env.user.company_id.id,
                "account_online_account_id": self.account.id,
                "account_online_link_id": self.link.id,
                "bank_statements_source": "online_sync",
            }
        )

    def test_01_has_synchronized_xunnel(self):
        partner = self.env["res.partner"].search([], limit=1)
        self.statement = self.env["account.bank.statement"].create(
            {
                "name": "test_statement",
                "date": "2019-01-01",
                "journal_id": self.journal.id,
                "balance_end_real": 7250.0,
                "line_ids": [
                    Command.create(
                        {
                            "date": "2019-01-01",
                            "payment_ref": "line_1",
                            "partner_id": partner.id,
                            "amount": 1250.0,
                            "online_transaction_identifier": "test",
                            "journal_id": self.journal.id,
                        }
                    ),
                    Command.create(
                        {
                            "date": "2019-01-01",
                            "payment_ref": "line_2",
                            "partner_id": partner.id,
                            "amount": 2000.0,
                            "online_transaction_identifier": "test",
                            "journal_id": self.journal.id,
                        }
                    ),
                    Command.create(
                        {
                            "date": "2019-01-01",
                            "payment_ref": "line_3",
                            "partner_id": partner.id,
                            "amount": 4000.0,
                            "online_transaction_identifier": "test",
                            "journal_id": self.journal.id,
                        }
                    ),
                ],
            }
        )
        self.journal._compute_has_synchronized_xunnel()
        self.assertTrue(self.journal.has_synchronized_xunnel)

    @mock()
    def test_02_retrieve_transactions_last_sync(self, request):
        """Test requesting all transactions from an account and
        how many bank statement were created. Also checks last_sync's refreshed
        """
        self.env["account.bank.statement"].search([("journal_id", "=", self.journal.id)]).unlink()
        request.post(
            "%sget_xunnel_transactions" % self.url,
            text=dumps(dict(response=dumps({"balance": 0, "transactions": response.TRANSACTIONS}))),
        )
        online_journal = self.journal.account_online_link_id
        self.env.user.company_id.xunnel_token = "test token"
        transactions = self.journal.manual_sync()
        self.assertNotEqual(online_journal.last_refresh, False)
        self.assertEqual(transactions, 7)

    @mock()
    def test_03_bad_retrieve_transactions_last_sync(self, request):
        """Test making a bank statement form online journal without
        having assigned an account journal. Also checks last_sync's refreshed
        """
        request.post(
            "%sget_xunnel_transactions" % self.url,
            text=dumps(dict(response=dumps({"balance": 0, "transactions": response.TRANSACTIONS}))),
        )
        online_journal = self.journal.account_online_account_id
        # To test if manual_sync its executed before is assigned to a journal
        online_journal.last_sync = False
        online_journal.journal_ids = False
        statements = online_journal._retrieve_transactions()
        self.assertFalse(online_journal.last_sync)
        self.assertEqual(statements, 0)

    @mock()
    def test_04_link_manual_transactions(self, request):
        """Test to validate if you create statement lines manually, it should
        update that entries to link it with the one updated from xunnel.
        """
        request.post(
            "%sget_xunnel_transactions" % self.url,
            text=dumps(dict(response=dumps({"balance": 0, "transactions": response.TRANSACTIONS}))),
        )
        statement = self.env["account.bank.statement"].create(
            {
                "line_ids": [
                    Command.create(
                        {
                            "name": "Transaction 1",
                            "date": "2014-10-05",
                            "amount": 10,
                            "payment_ref": "test",
                            "journal_id": self.journal.id,
                        }
                    )
                ],
                "date": "2014-10-05",
                "journal_id": self.journal.id,
            }
        )
        line = statement.line_ids
        self.assertFalse(line.online_transaction_identifier)

    @mock()
    def test_05_duplicate_manual_transactions(self, request):
        """Test to validate if you create more than one equal statement line
        manually, it should let that records and create new transactions.
        """
        request.post(
            "%sget_xunnel_transactions" % self.url,
            text=dumps(dict(response=dumps({"balance": 0, "transactions": response.TRANSACTIONS}))),
        )
        statement = self.env["account.bank.statement"].create(
            {
                "name": "online sync",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Transaction 1",
                            "date": "2014-10-05",
                            "amount": 10,
                            "payment_ref": "test",
                            "journal_id": self.journal.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Transaction 2",
                            "date": "2014-10-05",
                            "amount": 10,
                            "payment_ref": "test",
                            "journal_id": self.journal.id,
                        },
                    ),
                ],
                "date": "2014-10-05",
                "journal_id": self.journal.id,
            }
        )
        self.journal.manual_sync()
        lines = statement.line_ids.filtered(lambda l: not l.online_transaction_identifier)
        self.assertEqual(len(lines), 2)

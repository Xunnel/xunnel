from datetime import datetime
from json import dumps
from unittest.mock import Mock, patch

from requests_mock import mock

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from . import response

requests = Mock()


@tagged("account_online_link")
class TestAccountOnlineLink(TransactionCase):
    def setUp(self):
        super().setUp()
        self.url = "https://xunnel.com/"
        self.company = self.env.user.company_id
        self.company.xunnel_token = "test token"
        self.link = self.env["account.online.link"].create(
            {
                "name": "Acme Bank - Normal with Attachments",
                "is_xunnel": True,
                "client_id": "5ad5ad730c212a6a268b45e4",
                "company_id": self.env.user.company_id.id,
            }
        )

    def test_01_update_credentials(self):
        with self.assertRaises(UserError):
            self.link.update_credentials()

    @patch("odoo.addons.account_online_synchronization.models.account_online.AccountOnlineLink._fetch_odoo_fin")
    def test_02_fetch_odoo_fin(self, _fetch_odoo_fin):
        self.link._fetch_odoo_fin(url="test")
        _fetch_odoo_fin.assert_called_once()

    @mock()
    def test_03_get_journals(self, request=None):
        request.post("%sget_xunnel_journals" % self.url, text=dumps(dict(response.ERROR)))
        with self.assertRaises(UserError):
            self.link._get_journals()

    @mock()
    def test_04_fetch_odoo_fin(self, request=None):
        request.post(
            "%sget_xunnel_transactions" % self.url,
            text=dumps(dict(response=dumps({"balance": 0, "transactions": response.TRANSACTIONS}))),
        )
        data = {"account_id": 666}
        online_link = self.env["account.online.link"].search([("client_id", "!=", False)], limit=1)
        expected_transactions = {
            "balance": 0,
            "transactions": [
                {
                    "online_transaction_identifier": "5a9dcb3d244283f35a8c6e26",
                    "amount": 10,
                    "date": datetime(2014, 10, 5, 0, 0),
                    "id": "5a9dcb3d244283f35a8c6e26",
                    "payment_ref": "ACME Checking Transaction 1",
                },
                {
                    "online_transaction_identifier": "5a9dcb3d244283f35a8c6e28",
                    "amount": 10,
                    "date": datetime(2014, 10, 3, 0, 0),
                    "id": "5a9dcb3d244283f35a8c6e28",
                    "payment_ref": "ACME Checking Transaction 2",
                },
                {
                    "online_transaction_identifier": "5a9dcb3d244283f35a8c6e2a",
                    "amount": 10,
                    "date": datetime(2014, 10, 2, 0, 0),
                    "id": "5a9dcb3d244283f35a8c6e2a",
                    "payment_ref": "ACME Checking Transaction 3",
                },
                {
                    "online_transaction_identifier": "5a9dcb3d244283f35a8c6e2c",
                    "amount": 10,
                    "date": datetime(2014, 10, 1, 0, 0),
                    "id": "5a9dcb3d244283f35a8c6e2c",
                    "payment_ref": "ACME Checking Transaction 4",
                },
                {
                    "online_transaction_identifier": "5a9dcb3d244283f35a8c6e2e",
                    "amount": 15,
                    "date": datetime(2014, 5, 1, 0, 0),
                    "id": "5a9dcb3d244283f35a8c6e2e",
                    "payment_ref": "ACME Checking Transaction 5",
                },
                {
                    "online_transaction_identifier": "5a9dcb3d244283f35a8c6e30",
                    "amount": 15,
                    "date": datetime(2014, 5, 1, 0, 0),
                    "id": "5a9dcb3d244283f35a8c6e30",
                    "payment_ref": "ACME Checking Transaction 6",
                },
                {
                    "online_transaction_identifier": "5a9dcb3d244283f35a8c6e31",
                    "amount": 15,
                    "date": datetime(2014, 10, 16, 0, 0),
                    "id": "5a9dcb3d244283f35a8c6e31",
                    "payment_ref": "ACME Checking Transaction 7",
                },
            ],
        }
        transactions = online_link.with_context(xunnel_operation=True)._fetch_odoo_fin(url="test", data=data)
        self.assertEqual(transactions, expected_transactions)

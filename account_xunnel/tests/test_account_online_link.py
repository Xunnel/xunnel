import json
from unittest.mock import Mock, patch

try:
    from requests_mock import mock
except ImportError:
    from .common import failed_requests_mock as mock


from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from . import response

requests = Mock()


@tagged("account_online_link")
class TestAccountOnlineLink(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = "https://xunnel.com/"
        cls.company = cls.env.user.company_id
        cls.company.xunnel_token = "test token"
        cls.link = cls.env["account.online.link"].create(
            {
                "name": "Acme Bank - Normal with Attachments",
                "is_xunnel": True,
                "client_id": "5ad5ad730c212a6a268b45e4",
                "company_id": cls.env.user.company_id.id,
            }
        )

    def test_01_update_credentials(self):
        with self.assertRaises(UserError):
            self.link.action_update_credentials()

    @patch("odoo.addons.account_online_synchronization.models.account_online.AccountOnlineLink._fetch_odoo_fin")
    def test_02_fetch_odoo_fin(self, _fetch_odoo_fin):
        self.link._fetch_odoo_fin(url="test")
        _fetch_odoo_fin.assert_called_once()

    @mock()
    def test_03_get_journals(self, request=None):
        request.post("%sget_xunnel_journals" % self.url, text=json.dumps(dict(response.ERROR)))
        with self.assertRaises(UserError):
            self.link._get_journals()

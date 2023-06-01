from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestResUsers(TransactionCase):
    def setUp(self):
        super().setUp()
        self.url = "https://xunnel.com/"
        self.company = self.env.user.company_id
        self.config_settings = self.env["res.config.settings"].create({})

    def test_01_get_xunnel_token_with_no_company_token(self):
        self.env.company.xunnel_token = ""
        with self.assertRaises(UserError):
            self.env["res.users"].get_xunnel_token()

    @patch("odoo.addons.account_xunnel.models.res_company.ResCompany._xunnel")
    def test_02_get_xunnel_token_with_company_token(self, _xunnel_patch):
        self.env.company.xunnel_token = "test token"
        _xunnel_patch.return_value = {
            "error": "Test Error",
        }
        with self.assertRaises(UserError):
            self.env["res.users"].get_xunnel_token()

    @patch("odoo.addons.account_xunnel.models.res_company.ResCompany._xunnel")
    def test_03_get_xunnel_token_with_company_token_and_response(self, _xunnel_patch):
        self.env.company.xunnel_token = "test token"
        _xunnel_patch.return_value = {
            "response": {
                "token": "Test Token",
            },
        }
        locale = self.env.context.get("lang", "en_US").split("_")[0]
        info = self.env["res.users"].get_xunnel_token()
        self.assertEqual(info, {"locale": locale, "token": "Test Token"})

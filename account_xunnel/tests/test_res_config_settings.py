import json
import os
from unittest.mock import Mock, patch

from requests_mock import mock

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import misc

from . import response

requests = Mock()


@tagged("res_config_settings")
class TestResConfigSettings(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = "https://xunnel.com/"
        cls.company = cls.env.user.company_id
        cls.config_settings = cls.env["res.config.settings"].create({})

    @mock()
    def test_01_sync_xunnel_providers(self, request=None):
        self.company.xunnel_token = False
        with self.assertRaises(UserError):
            self.config_settings.sync_xunnel_providers()

        def _response(request, context):
            data = json.loads(request.text)
            path = "response_journal_%s.json"
            if data.get("account_identifier") == "5ad79e9d0b212a5b608b459a":
                return misc.file_open(os.path.join("account_xunnel", "tests", path % "2")).read()
            return misc.file_open(os.path.join("account_xunnel", "tests", path % "1")).read()

        request.post("%sget_xunnel_providers" % self.url, text=json.dumps({"response": response.PROVIDERS}))
        request.post("%sget_xunnel_journals" % self.url, text=_response)

        self.company.xunnel_token = "test token"

        expected_res = {
            "type": "ir.actions.client",
            "tag": "account_xunnel.SyncrhonizedAccounts",
            "name": "Xunnel response",
            "target": "new",
            "params": {"message": "Success! 2 banks have been synchronized.", "message_class": "success"},
        }

        res = self.config_settings.sync_xunnel_providers()
        self.assertEqual(res, expected_res)

    @patch("odoo.addons.account_xunnel.models.res_company.ResCompany._sync_xunnel_providers")
    def test_02_sync_xunnel_providers_error(self, patch_sync_xunnel_providers):
        patch_sync_xunnel_providers.return_value = False, False
        with self.assertRaises(UserError):
            self.env["res.config.settings"].sync_xunnel_providers()

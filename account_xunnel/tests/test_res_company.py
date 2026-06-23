# Copyright 2017, Vauxoo, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import json
import os
from unittest.mock import Mock

try:
    from requests_mock import mock
except ImportError:
    from .common import failed_requests_mock as mock


from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import misc

from . import response

requests = Mock()


@tagged("res_company")
class TestResCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = "https://xunnel.com/"
        cls.company = cls.env.user.company_id

    @mock()
    def test_01_get_xunnel_response(self, request=None):
        """Test the _xunnel() method, cases:
        Case 1: The _xunnel() method is called from a company without xunnel_token, this should rause an UserError
        Case 2: The _xunnel() method is called from a company with wrong xunnel_token and the response is an error"""
        request.post("%sget_xunnel_providers" % self.url, text=json.dumps({"error": True}))
        company = self.env.user.company_id
        company.xunnel_token = False
        with self.assertRaises(UserError):
            company._xunnel("get_xunnel_providers")

        company.xunnel_token = "test token"
        res = company._xunnel("get_xunnel_providers")
        self.assertTrue(res.get("error"))

    @mock()
    def test_02_sync_xunnel_providers(self, request=None):
        """Test requesting all providers and journals from an user.
        Two providers and 9 journals are returned"""

        def _response(request, context):
            data = json.loads(request.text)
            path = "response_journal_%s.json"
            if data.get("account_identifier") == "5ad79e9d0b212a5b608b459a":
                return misc.file_open(os.path.join("account_xunnel", "tests", path % "2")).read()
            return misc.file_open(os.path.join("account_xunnel", "tests", path % "1")).read()

        request.post("%sget_xunnel_providers" % self.url, text=json.dumps({"response": response.PROVIDERS}))
        request.post("%sget_xunnel_journals" % self.url, text=_response)
        old_links = len(self.env["account.online.link"].search([]))
        old_journals = len(self.env["account.online.account"].search([]))
        self.assertEqual(old_links, 1)
        self.assertEqual(old_journals, 1)
        self.company.xunnel_token = "test token"
        self.company._sync_xunnel_providers()
        new_links = len(self.env["account.online.link"].search([]))
        new_journals = len(self.env["account.online.account"].search([]))
        self.assertEqual(new_links, 2)
        self.assertEqual(new_journals, 9)

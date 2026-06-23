# Copyright 2017, Vauxoo, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from json import dumps
from unittest.mock import Mock

try:
    from requests_mock import mock
except ImportError:
    from .common import failed_requests_mock as mock


from odoo.tests.common import TransactionCase, tagged

from . import webhook_responses

requests = Mock()


@tagged("webhooks")
class TestWebhooks(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.user.company_id
        self.env.user.company_id.xunnel_token = "test token"
        self.url = "https://xunnel.com/"

    @mock()
    def test_01_sync_account_data(self, request=None):
        request.post("%sget_xunnel_providers" % self.url, text=dumps(webhook_responses.GET_XUNNEL_PROVIDERS))
        request.post("%sget_xunnel_journals" % self.url, text=dumps(webhook_responses.GET_XUNNEL_JOURNALS))
        request.post("%sget_xunnel_transactions" % self.url, text=dumps(webhook_responses.GET_XUNNEL_TRANSACTIONS))
        account_id = "5b2d85a00b212a1f1c8b456d"
        link_obj = self.env["account.online.link"]
        providers_old_count = link_obj.search_count([("company_id", "=", self.company.id)])
        self.assertEqual(providers_old_count, 1)
        self.company._sync_xunnel_providers(account_id)
        providers_new_count = link_obj.search_count([("company_id", "=", self.company.id)])
        self.assertEqual(providers_new_count, 3)
        provider = link_obj.search([("client_id", "=", account_id), ("company_id", "=", self.company.id)])
        journals = len(provider.account_online_account_ids)
        self.assertEqual(journals, 6)

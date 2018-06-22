# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os
from json import dumps, loads

from odoo.tests.common import TransactionCase
from requests_mock import mock

from . import response


class TestXunnelAccount(TransactionCase):

    def setUp(self):
        super(TestXunnelAccount, self).setUp()
        self.company = self.env['res.company'].browse(
            self.ref('base.main_company'))
        self.url = "https://ci.xunnel.com/"

    @mock()
    def test_01_sync_account_data(self, request):
        providers_old_count = self.env['account.online.provider'].search_count(
            [('company_id', '=', self.company_id)])
        request.post(
            '%sget_xunnel_providers/' % self.url,
            text=dumps({'response': [{
                'name': 'Acme Bank-Normal',
                'provider_account_identifier': '5b2d52940b212a18128b456c',
                'provider_identifier': '56cf5728784806f72b8b4568'
            }]}))
        self.assertEqual(providers_old_count, 0)
        self.company.sync_providers()
        providers_new_count = self.env['account.online.provider'].search_count(
            [('company_id', '=', self.company_id)])
        self.assertEqual(providers_new_count, 1)

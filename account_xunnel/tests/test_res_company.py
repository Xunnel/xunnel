from odoo.tests.common import TransactionCase
from requests_mock import mock
from json import dumps
from datetime import datetime
from . import response


class TestXunnelAccount(TransactionCase):

    def setUp(self):
        super(TestXunnelAccount, self).setUp()
        self.url = self.env['ir.config_parameter'].get_param(
            'account_xunnel.url')
        self.company = self.env['res.company'].browse(
            self.ref('base.main_company'))

    # @mock()
    def test_01_sync_xunnel_attachments(self):
        """Test requesting all transactions from an account and
        making a bank statement. Also checks last_sync's refreshed
        """
        # request.post(
        #     '%sget_invoices_sat' % self.url,
        #     text=dumps(dict(response=response.response)))
        old_sync = datetime.strptime('1970-01-01', '%Y-%m-%d')
        self.company.xunnel_last_sync = old_sync
        self.company.sync_xunnel_attachments()
        self.assertTrue(old_sync < self.xunnel_last_sync)


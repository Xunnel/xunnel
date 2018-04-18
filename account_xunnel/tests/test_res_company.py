from odoo.tests.common import TransactionCase
from datetime import datetime
from odoo.exceptions import UserError
from json import dumps, loads
from requests_mock import mock
from . import response


class TestXunnelAccount(TransactionCase):

    def setUp(self):
        super(TestXunnelAccount, self).setUp()
        self.url = self.env['ir.config_parameter'].get_param(
            'account_xunnel.url')
        self.company = self.env['res.company'].browse(
            self.ref('base.main_company'))

    @mock()
    def test_01_sync_xunnel_attachments(self, request=None):
        """Test requesting all transactions from an account and
        making a bank statement. Also checks last_sync's refreshed.
        """
        attachments_response = open(
            "./account_xunnel/tests/response_attachments.json").read()
        request.post(
            '%sget_invoices_sat' % self.url,
            text=attachments_response)
        old_sync = datetime.strptime('1970-01-01', '%Y-%m-%d')
        self.company.xunnel_last_sync = old_sync
        self.company.sync_xunnel_attachments()
        last_sync = datetime.strptime(
            self.company.xunnel_last_sync, '%Y-%m-%d')
        self.assertTrue(old_sync < last_sync)

    @mock()
    def test_02_sync_xunnel_attachments(self, request):
        """Test a bad requesting transactions. Also checks
        last_sync is not refreshed. Six attachments are returned
        but 3 of those are already in the database and must not be overwritten.
        """
        request.post(
            '%sget_invoices_sat' % self.url,
            text=dumps({"error": "Expected error for testing"}))

        attachments = self.env['ir.attachment']
        inital_attachments = attachments.search_count([])
        old_sync = '1970-01-01'
        self.company.xunnel_last_sync = old_sync
        with self.assertRaisesRegexp(UserError, 'Expected error for testing'):
            self.company.sync_xunnel_attachments()
            final_attachments = attachments.search_count([])
            self.assertEquals(final_attachments - inital_attachments, 3)
        self.assertEquals(old_sync, self.company.xunnel_last_sync)

    @mock()
    def test_03_sync_xunnel_providers(self, request=None):
        """Test requesting all providers and journals from an user.
        Two providers and 9 providers are returned but one of each is
        already in the database and must not be overwritten.
        """
        def _response(request, context):
            data = loads(request.text)
            path = './account_xunnel/tests/response_journal_%s.json'
            if data.get('account_identifier') == '5ad79e9d0b212a5b608b459a':
                return open(path % '2').read()
            return open(path % '1').read()

        request.post(
            '%sget_xunnel_providers' % self.url,
            text=dumps(dict(
                response=response.PROVIDERS)))
        request.post(
            '%sget_xunnel_journals' % self.url,
            text=_response)

        old_providers = len(self.env['account.online.provider'].search([]))
        old_journals = len(self.env['account.online.journal'].search([]))
        self.company.sync_xunnel_providers()
        new_providers = len(self.env['account.online.provider'].search([]))
        new_journals = len(self.env['account.online.journal'].search([]))
        self.assertEquals(new_providers - old_providers, 1)
        self.assertEquals(new_journals - old_journals, 8)

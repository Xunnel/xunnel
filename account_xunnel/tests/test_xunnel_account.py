from odoo.tests.common import TransactionCase
from requests_mock import mock
from json import dumps
from . import response


class TestXunnelAccount(TransactionCase):

    def setUp(self):
        super(TestXunnelAccount, self).setUp()
        self.url = self.env[
            'ir.config_parameter'].get_param('account_xunnel.url')

    @mock()
    def test_01_retrieve_transactions_last_sync(self, request):
        """Test requesting all transactions from an account and
        how many bank statement were created. Also checks last_sync's refreshed
        """
        id_journal = self.ref('account_xunnel.account_journal_attachments')
        for stm in self.env['account.bank.statement'].search(
                [('journal_id', '=', id_journal)]):
            stm.unlink()
        request.post(
            '%sget_xunnel_transactions' % self.url,
            text=dumps(dict(response=dumps({
                'balance': 0,
                'transactions': response.TRANSACTIONS}))))
        journal = self.env['account.journal'].browse(id_journal)
        online_journal = journal.account_online_journal_id
        statements = journal.manual_sync()
        self.assertNotEquals(online_journal.last_sync, False)
        self.assertEquals(statements, 7)

    @mock()
    def test_02_bad_retrieve_transactions_last_sync(self, request):
        """Test making a bank statement form online journal without
        having assigned an account journal. Also checks last_sync's refreshed
        """
        request.post(
            '%sget_xunnel_transactions' % self.url,
            text=dumps(dict(response=dumps({
                'balance': 0,
                'transactions': response.TRANSACTIONS}))))
        id_journal = self.ref('account_xunnel.online_journal_attachments')
        online_journal = self.env['account.online.journal'].browse(id_journal)
        # To test if manual_sync its executed before is assigned to a journal
        online_journal.last_sync = False
        online_journal.journal_ids = False
        statements = online_journal.retrieve_transactions()
        self.assertFalse(online_journal.last_sync)
        self.assertEquals(statements, 0)

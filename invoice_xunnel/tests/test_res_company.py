# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os
import time as time_module
from json import dumps

try:
    from requests_mock import mock
except ImportError:
    from odoo.addons.account_xunnel.tests.common import failed_requests_mock as mock


from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tools import misc


class TestXunnelAccount(TransactionCase):
    def setUp(self):
        super().setUp()
        self.url = "https://xunnel.com/"
        self.company = self.env["res.company"].browse(self.ref("base.main_company"))
        self.company.xunnel_token = "test"

    @mock()
    def test_01_sync_xunnel_documents(self, request=None):
        """Test requesting all transactions from an account and
        making a bank statement. Also checks last_sync's refreshed.
        """
        documents_response = misc.file_open(os.path.join("invoice_xunnel", "tests", "response_documents.json")).read()
        request.post("%sget_invoices_sat" % self.url, text=documents_response)
        old_sync = fields.Date.to_date("2018-01-01")
        self.company.xunnel_last_sync = old_sync
        self.company.vat = "MXGODE561231GR8"
        self.company._sync_xunnel_documents()
        last_sync = self.company.xunnel_last_sync
        self.assertTrue(old_sync < last_sync)
        self.company.vat = False

    @mock()
    def test_02_sync_xunnel_documents(self, request):
        """Test a bad requesting transactions. Also checks
        last_sync is not refreshed. Six documents are returned
        but 3 of those are already in the database and must not be overwritten.
        """
        request.post("%sget_invoices_sat" % self.url, text=dumps({"error": "Expected error for testing"}))

        documents = self.env["documents.document"]
        inital_documents = documents.search_count([])
        old_sync = "1970-01-01"
        self.company.xunnel_last_sync = old_sync
        self.company.vat = "MXGODE561231GR8"
        with self.assertRaisesRegex(UserError, "Expected error for testing"):
            self.company._sync_xunnel_documents()
        final_documents = documents.search_count([])
        self.assertEqual(final_documents - inital_documents, 0)
        self.assertEqual(old_sync, fields.Date.to_string(self.company.xunnel_last_sync))

    def test_03_date_to_epoch_ignores_server_timezone(self):
        """The epoch for a given date must not depend on the `TZ` the
        server process happens to run under (see MR 216, note_844798):
        a UTC server must produce the same instant as a Mexico_City one.
        """
        date_to = fields.Date.to_date("2026-02-01")
        original_tz = os.environ.get("TZ")
        try:
            os.environ["TZ"] = "UTC"
            time_module.tzset()
            epoch_utc = self.company._date_to_epoch(date_to)

            os.environ["TZ"] = "America/Mexico_City"
            time_module.tzset()
            epoch_mexico_city = self.company._date_to_epoch(date_to)
        finally:
            if original_tz is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = original_tz
            time_module.tzset()

        self.assertEqual(epoch_utc, epoch_mexico_city)

    @mock()
    def test_04_sync_xunnel_documents_with_end_date(self, request=None):
        self.company.xunnel_last_sync = fields.Date.to_date("2018-01-01")
        self.company.vat = "MXGODE561231GR8"
        date_to = fields.Date.to_date("2018-08-31")
        request.post("%sget_invoices_sat" % self.url, text=dumps({"response": []}))

        result = self.company._sync_xunnel_documents(date_to=date_to)

        payload = request.request_history[-1].json()
        # Literal epochs, not `self.company._date_to_epoch(...)`: computing the
        # expectation from the same helper the production code calls would make
        # this an identity check that passes for any implementation of the
        # helper, right or wrong (see MR 216, note_846357).
        self.assertEqual(payload["last_sync"], 1514786400.0)  # 2018-01-01 00:00 Mexico City
        self.assertEqual(payload["last_sync_to"], 1535691600.0)  # 2018-08-31 00:00 Mexico City
        self.assertEqual(result, {"created": [], "failed": 0})

    @mock()
    def test_05_sync_xunnel_documents_without_end_date(self, request=None):
        self.company.xunnel_last_sync = fields.Date.to_date("2018-01-01")
        self.company.vat = "MXGODE561231GR8"
        request.post("%sget_invoices_sat" % self.url, text=dumps({"response": []}))

        self.company._sync_xunnel_documents()

        payload = request.request_history[-1].json()
        self.assertNotIn("last_sync_to", payload)

import base64

from odoo.tests.common import HttpCase, tagged

from odoo.addons.invoice_xunnel.controllers.main import BinaryXunnel
from odoo.addons.website.tools import MockRequest


@tagged("controllers_main")
class TestControllersMain(HttpCase):
    def test_01_content_common(self):
        """Check that when a XML is going to be shown in the Documents iframe this is
        modified correctly to render its content"""
        xunnel_datas_invoice = base64.b64encode(
            bytes('<?xml version="1.0" encoding="UTF-8"?></SOAP-ENV:Env>', "utf-8")
        )
        self.folder_a = self.env["documents.folder"].create(
            {
                "name": "folder A",
            }
        )
        self.document_xunnel = self.env["documents.document"].create(
            {
                "datas": xunnel_datas_invoice,
                "name": "file.txt",
                "mimetype": "application/xml",
                "folder_id": self.folder_a.id,
                "xunnel_document": True,
            }
        )
        with MockRequest(self.env):
            res = BinaryXunnel().content_common(
                model="documents.document",
                id=self.document_xunnel.id,
                mimetype="application/xml",
            )
            self.assertEqual(res.status_code, 200, "Response should be Ok (200)")

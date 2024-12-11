import base64

from odoo.tests import HttpCase, tagged

from odoo.addons.invoice_xunnel.controllers.main import BinaryXunnel
from odoo.addons.website.tools import MockRequest


@tagged("controllers_main")
class TestControllersMain(HttpCase):
    def setUp(self):
        super().setUp()
        self.xunnel_datas_invoice = base64.b64encode(
            bytes('<?xml version="1.0" encoding="UTF-8"?></SOAP-ENV:Env>', "utf-8")
        )
        self.folder_a = self.env["documents.document"].create(
            {
                "name": "Folder A",
                "type": "folder",
                "access_internal": "edit",
                "access_via_link": "none",
                "owner_id": self.env.user.id,
            }
        )
        self.document_xunnel = self.env["documents.document"].create(
            {
                "datas": self.xunnel_datas_invoice,
                "name": "file.txt",
                "mimetype": "application/xml",
                "folder_id": self.folder_a.id,
                "xunnel_document": True,
            }
        )

    def test_01_content_common(self):
        """Check that when a XML is going to be shown in the Documents iframe this is
        modified correctly to render its content
        """
        access_token = "my_test_token"
        with MockRequest(self.env) as request:
            request.httprequest.args = {"access_token": access_token}
            res = BinaryXunnel().content_common(
                model="documents.document",
                id=self.document_xunnel.id,
                mimetype="application/xml",
            )
            self.assertEqual(res.status_code, 200, "Response should be Ok (200)")

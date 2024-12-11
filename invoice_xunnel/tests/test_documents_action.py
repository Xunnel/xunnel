import base64
import json

from odoo.tests import TransactionCase

TEXT_CONTENT = "Test Content"
TEXT_DATAS = base64.b64encode(TEXT_CONTENT.encode("utf-8"))


class TestDocumentsServerAction(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.folder_a = cls.env["documents.document"].create(
            {
                "type": "folder",
                "name": "folder A",
                "owner_id": cls.env.user.id,
                "access_internal": "edit",
                "access_via_link": "none",
            }
        )
        cls.document = cls.env["documents.document"].create(
            {
                "datas": TEXT_DATAS,
                "name": "file.xml",
                "mimetype": "text/xml",
                "folder_id": cls.folder_a.id,
                "xunnel_document": False,
            }
        )

    def test_01_create_record_without_document(self):
        res = self.document._server_action_create_record()
        self.assertIsNone(res)  # No return value expected

    def test_02_create_record(self):
        res = self.document.create_record([self.document])

        res_context = res["context"]
        decoded_files = json.loads(res_context["file_names"])
        for file in decoded_files:
            file["text"] = base64.b64decode(file["text"]).decode("utf-8")
        res_context["file_names"] = json.dumps(decoded_files)

        expected_files = [{"name": "file.xml", "text": TEXT_CONTENT}]
        expected_res = {
            "type": "ir.actions.act_window",
            "res_model": "attach.xmls.wizard",
            "target": "new",
            "views": [[False, "form"]],
            "context": {
                "file_names": json.dumps(expected_files),
                "autofill_enable": True,
                "l10n_mx_edi_invoice_type": "in",
            },
        }

        self.assertEqual(res, expected_res)

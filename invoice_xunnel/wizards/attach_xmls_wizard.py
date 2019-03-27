
from odoo import models, api


class AttachXmlsWizard(models.TransientModel):
    _inherit = 'attach.xmls.wizard'

    @api.model
    def check_xml(self, files, account_id=False):
        response = super().check_xml(files=files, account_id=account_id)
        if not self.env.context.get('autofill_enable'):
            return response
        attachment_obj = self.env['ir.attachment']
        tag_id = self.env.ref('invoice_xunnel.with_invoice')
        for invoice in response.get('invoices'):
            attachment = attachment_obj.search(
                [('res_id', '=', invoice.id),
                 ('res_model', '=', 'account.invoice')], limit=1)
            if not attachment:
                continue
            attachment.write({
                'tag_ids': [(6, None, tag_id.ids)]
            })
        return response

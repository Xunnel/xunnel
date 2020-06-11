
from odoo import models, fields, _


class DocumentsWizard(models.TransientModel):
    _name = 'xunnel.documents.wizard'
    _description = 'Xunnel documents sync'

    company_id = fields.Many2one(
        'res.company', required=True,
        default=lambda self: self.env.user.company_id)
    date_from = fields.Date(
        related='company_id.xunnel_last_sync',
        readonly=False)
    message = fields.Char(help="Used to show the synchronization status.")

    def synchronize_documents(self):
        """Synchronize attachments from Xunnel. After it,
        opens a new `xunnel.attachments.wizard` instance with
        the message corresponding to the synchronization status.

        If there was downloaded attachments, it also shows a button
        to redirect to those attachments.
        """
        result = self.company_id._sync_xunnel_attachments()
        failed = result.get('failed')
        message = _("%s xml have been downloaded.") % result.get('created', '0')
        if failed:
            message += _(" Also %s files have failed at the conversion.") % failed
        action = self.env.ref('invoice_xunnel.action_product_confirm_wizard').read()[0]
        action['context'] = {'default_message': message}
        return action

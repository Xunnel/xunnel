
from odoo import models, fields


class DocumentsWizard(models.TransientModel):
    _name = 'xunnel.documents.wizard'
    _description = 'Xunnel documents sync'

    company_id = fields.Many2one(
        'res.company', required=True,
        default=lambda self: self.env.user.company_id)
    date_from = fields.Date(
        related='company_id.xunnel_last_sync',
        readonly=False)

    def synchronize_documents(self):
        return self.company_id.get_xml_sync_action()

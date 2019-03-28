
from odoo import models, fields, api
from lxml import etree, objectify
import base64
import logging

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    emitter_partner_id = fields.Many2one(
        'res.partner',
        compute="_compute_emitter_partner_id",
        required=True,
        string="emitter")
    xunnel_attachment = fields.Boolean()
    invoice_total_amount = fields.Float(
        compute="_compute_emitter_partner_id")

    @api.multi
    @api.depends('datas')
    def _compute_emitter_partner_id(self):
        for rec in self:
            if not rec.xunnel_attachment:
                continue
            xml = rec.get_xml_object(rec.datas)
            if not xml:
                return
            rfc = xml.Emisor.get('Rfc', '').upper()
            partner = self.env['res.partner'].search([
                ('vat', '=', rfc), '|',
                ('supplier', '=', True), ('customer', '=', True)
            ], limit=1)
            rec.emitter_partner_id = partner.id,
            rec.invoice_total_amount = xml.get('Total')

    @api.multi
    def get_xml_object(self, xml):
        try:
            if isinstance(xml, bytes):
                xml = xml.decode()
            xml_str = base64.b64decode(xml.replace(
                'data:text/xml;base64,', ''))
            xml = objectify.fromstring(xml_str)
        except (AttributeError, SyntaxError):
            xml = False
        return xml

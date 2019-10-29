from datetime import datetime
import base64
import logging
from lxml import objectify

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    emitter_partner_id = fields.Many2one(
        'res.partner',
        compute="_compute_emitter_partner_id",
        string="Emitter",
        help="In case this is a CFDI file, stores emitter's name.",
        store=True)
    xunnel_attachment = fields.Boolean(
        help="Specify if this is a XUNNEL attachment.")
    invoice_total_amount = fields.Float(
        compute="_compute_emitter_partner_id",
        help="In case this is a CFDI file, stores invoice's total amount.",
        store=True)
    stamp_date = fields.Datetime(
        compute="_compute_emitter_partner_id",
        help="In case this is a CFDI file, stores invoice's stamp date.",
        store=True)

    @api.multi
    @api.depends('datas')
    def _compute_emitter_partner_id(self):
        attachments = self.filtered(
            lambda rec: rec.xunnel_attachment and rec.datas_fname and
            rec.datas_fname.lower().endswith('xml'))
        for rec in attachments:
            xml = rec.get_xml_object(rec.datas)
            if xml is None:
                return
            rfc = xml.Emisor.get('Rfc', '').upper()
            partner = self.env['res.partner'].search([
                ('vat', '=', rfc), '|',
                ('supplier', '=', True), ('customer', '=', True)
            ], limit=1)
            stamp_date = xml.Complemento.xpath(
                'tfd:TimbreFiscalDigital[1]',
                namespaces={
                    'tfd':
                    'http://www.sat.gob.mx/TimbreFiscalDigital'})[0].get(
                        'FechaTimbrado')

            rec.emitter_partner_id = partner.id
            rec.invoice_total_amount = xml.get('Total')
            rec.stamp_date = datetime.strptime(stamp_date, "%Y-%m-%dT%H:%M:%S")

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

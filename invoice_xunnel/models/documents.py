from datetime import datetime
import base64
import json
import logging
from lxml import objectify

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Document(models.Model):
    _inherit = 'documents.document'

    emitter_partner_id = fields.Many2one(
        'res.partner',
        compute="_compute_emitter_partner_id",
        string="Emitter",
        help="In case this is a CFDI file, stores emitter's name.",
        store=True)
    xunnel_document = fields.Boolean(
        help="Specify if this is a XUNNEL document.")
    invoice_total_amount = fields.Float(
        string='Total Amount',
        compute="_compute_emitter_partner_id",
        help="In case this is a CFDI file, stores invoice's total amount.",
        store=True)
    stamp_date = fields.Datetime(
        compute="_compute_emitter_partner_id",
        help="In case this is a CFDI file, stores invoice's stamp date.",
        store=True)
    product_list = fields.Text(
        compute="_compute_product_list",
        string='Products',
        help="In case this is a CFDI file, show invoice's product list",
        store=True,
    )
    just_downloaded = fields.Boolean(
        compute="_compute_just_downloaded",
        search="_search_just_downloaded", store=False,
        help="""Used to identify the just donwloaded attachments.
 To evaluate if an attachment was just downloaded, we need to
 check the current context.""")

    def _compute_just_downloaded(self):
        downloaded_ids = self._context.get('downloaded_invoice', [])
        for rec in self:
            rec.just_downloaded = rec.id in downloaded_ids

    def _search_just_downloaded(self, operator, value):
        operator = 'in' if value else 'not int'
        return [('id', operator, self._context.get('downloaded_invoice', []))]

    @api.depends('datas')
    def _compute_emitter_partner_id(self):
        documents = self.filtered(
            lambda rec: rec.xunnel_document and rec.attachment_id and
            rec.attachment_id.description and
            'emitter' in rec.attachment_id.description)
        for rec in documents:
            xml = rec.get_xml_object(rec.datas)
            if xml is None:
                return
            rfc = xml.Emisor.get('Rfc', '').upper()
            partner = self.env['res.partner'].search([
                ('vat', '=', rfc)], limit=1)
            stamp_date = xml.Complemento.xpath(
                'tfd:TimbreFiscalDigital[1]',
                namespaces={
                    'tfd':
                    'http://www.sat.gob.mx/TimbreFiscalDigital'})[0].get(
                        'FechaTimbrado')

            rec.emitter_partner_id = partner.id
            rec.invoice_total_amount = xml.get('Total')
            rec.stamp_date = datetime.strptime(stamp_date, "%Y-%m-%dT%H:%M:%S")

    @api.depends('datas')
    def _compute_product_list(self):
        documents = self.filtered(
            lambda rec: rec.xunnel_document and rec.attachment_id)
        for rec in documents:
            xml = rec.get_xml_object(rec.datas)
            if xml is None:
                continue
            product_list = []
            for concepto in xml.Conceptos.iter(
                    '{http://www.sat.gob.mx/cfd/3}Concepto'):
                product_list += [concepto.get('Descripcion')]
            rec.product_list = json.dumps(product_list)

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

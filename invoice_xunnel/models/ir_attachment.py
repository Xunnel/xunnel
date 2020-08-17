# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import logging
import json
import requests

from datetime import datetime
from lxml import objectify
from odoo import api, models, fields, tools
from odoo.addons.l10n_mx_edi.models.account_invoice import CFDI_SAT_QR_STATE
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_repr

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

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

    @api.model
    def create(self, values):
        if 'datas' in values and self._validate_xml(values['datas']):
            description = self._create_description(values['datas'])
            values.update(description)
        return super().create(values)

    @api.multi
    def write(self, values):
        no_mx_rec = self
        for rec in self:
            datas = values['datas'] if 'datas' in values else rec.datas
            if (('description' in values or 'datas' in values) and
                    self._validate_xml(datas)):
                description = self._create_description(datas)
                rec_values = values.copy()
                rec_values.update(description)
                super(IrAttachment, rec).write(rec_values)
                no_mx_rec -= rec
            elif ('datas' in values and rec.mimetype == 'application/xml' and
                    not self._validate_xml(datas)):
                rec_values = values.copy()
                rec_values.update({
                    'description': False,
                    'mimetype': self._compute_mimetype({'datas': datas})
                })
                super(IrAttachment, rec).write(rec_values)
                no_mx_rec -= rec
        return super(IrAttachment, no_mx_rec).write(values)

    @api.model
    def _validate_xml(self, datas):
        if not datas:
            return False
        data_file = base64.b64decode(datas)
        try:
            objectify.fromstring(data_file)
        except (SyntaxError, ValueError):
            return False
        return True

    @api.model
    def _create_description(self, datas):
        """Process XML file to get description.
        Args:
            datas (binary): attachment in base64.
        Returns:
            dict: procesed description dict or empty dict.
        """
        xml_str = base64.b64decode(datas)
        try:
            xml_obj = objectify.fromstring(xml_str)
        except (SyntaxError, ValueError) as err:
            _logger.error(str(err))
            return {}
        if (xml_obj.get('Version') != '3.3' or
                xml_obj.get('TipoDeComprobante') != 'I'):
            return {}
        partner = self.env['res.partner'].search([
            ('vat', '=ilike', xml_obj.Emisor.get('Rfc'))], limit=1)
        if not partner:
            wizard_attachment = self.env['xunnel.attach.xmls.wizard']
            wizard_attachment.create_partner(datas, '')
        return {
            'description': json.dumps(
                self._prepare_description_attachment(xml_obj),
                ensure_ascii=False),
            'mimetype': 'application/xml',
        }

    @api.model
    def _prepare_description_attachment(self, xml):
        # TODO: Check if we can avoid use enterprise.
        cfdi = self.env['account.invoice'].l10n_mx_edi_get_tfd_etree(xml)
        data = {
            'date': xml.get('Fecha', ' ').replace('T', ' '),
            'number': xml.get('Folio', ''),
            'name': xml.Emisor.get('Nombre', ' '),
            'emitter_vat': xml.Emisor.get('Rfc', ' '),
            'subtotal': float(xml.get('SubTotal', '0.0')),
            'tax': 0.0,
            'tax_retention': 0.0,
            'currency': xml.get('Moneda', ''),
            'total': float(xml.get('Total')),
            'uuid': cfdi.get('UUID') if cfdi is not None else ' ',
        }
        if hasattr(xml, 'Impuestos'):
            data.update({
                'tax': float(xml.Impuestos.get(
                    'TotalImpuestosTrasladados', '0.0')),
                'tax_retention': float(xml.Impuestos.get(
                    'TotalImpuestosRetenidos', '0.0')),
            })
        return data

    sat_status = fields.Selection(
        selection=[
            ('none', 'State not defined'),
            ('undefined', 'Not Synced Yet'),
            ('not_found', 'Not Found'),
            ('cancelled', 'Cancelled'),
            ('valid', 'Valid'),
        ],
        default='undefined',
        compute='_compute_sat_status',
        help='Refers to the status of the invoice inside the SAT system.',
        store=True)
    emitter_partner_id = fields.Many2one(
        'res.partner',
        compute="_compute_emitter_partner_id",
        string="Emitter",
        help="In case this is a CFDI file, stores emitter's name.",
        store=True)
    xunnel_attachment = fields.Boolean(
        help="Specify if this is a XUNNEL attachment.")
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
        compute="_compute_emitter_partner_id",
        string='Products',
        help="In case this is a CFDI file, show invoice's product list",
    )
    related_cfdi = fields.Text(
        compute="_compute_emitter_partner_id",
        string='Related CFDI',
        help="Related CFDI of the XML file",
    )

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
            product_list = []
            for concepto in xml.Conceptos.iter(
                    '{http://www.sat.gob.mx/cfd/3}Concepto'):
                product_list.append(concepto.get('Descripcion'))
            rec.product_list = json.dumps(product_list)
            try:
                related_uuid = []
                for related in xml.CfdiRelacionados.iter(
                        '{http://www.sat.gob.mx/cfd/3}CfdiRelacionado'):
                    related_uuid.append(related.get('UUID'))
                    rec.related_cfdi = json.dumps(related_uuid)
            except AttributeError:
                rec.related_cfdi = None

    @api.depends('datas')
    def _compute_sat_status(self):
        for rec in self.filtered(
                lambda r: r.xunnel_attachment and r.url != 'nocompute'):
            xml = rec.get_xml_object(rec.datas)
            if not xml:
                return
            rec.sat_status = self.l10n_mx_edi_update_sat_status_xml(xml)

    def l10n_mx_edi_update_sat_status_xml(self, xml):
        """Check SAT WS to make sure the invoice is valid.
        inv: dict containing values to check SAT WS correctly.
        """
        template = """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="http://tempuri.org/"
xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Consulta>
         <ns0:expresionImpresa>${data}</ns0:expresionImpresa>
      </ns0:Consulta>
   </ns1:Body>
</SOAP-ENV:Envelope>"""
        supplier_rfc = xml.Emisor.get('Rfc', '').upper()
        customer_rfc = xml.Receptor.get('Rfc', '').upper()
        amount = float(xml.get('Total', 0.0))
        uuid = xml.get('UUID', '')
        currency = self.env['res.currency'].search([
            ('name', '=', xml.get('Moneda', 'MXN'))
        ])
        precision = currency.decimal_places if currency else 0
        tfd = self.env['account.invoice'].l10n_mx_edi_get_tfd_etree(xml)
        uuid = tfd.get('UUID', '')
        total = float_repr(amount, precision_digits=precision)
        params = '?re=%s&amp;rr=%s&amp;tt=%s&amp;id=%s' % (
            tools.html_escape(tools.html_escape(supplier_rfc or '')),
            tools.html_escape(tools.html_escape(customer_rfc or '')),
            total or 0.0, uuid or '')
        soap_env = template.format(data=params)
        try:
            soap_xml = requests.post(
                'https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc?wsdl',
                data=soap_env,
                timeout=20,
                headers={
                    'SOAPAction': 'http://tempuri.org/IConsultaCFDIService/Consulta',
                    'Content-Type': 'text/xml; charset=utf-8'
                })
            response = objectify.fromstring(soap_xml.text)
            status = response.xpath('//a:Estado', namespaces={
                'a': 'http://schemas.datacontract.org/2004/07/Sat.Cfdi.Negocio.ConsultaCfdi.Servicio'
            })
        except Exception as e:
            raise ValidationError(str(e))
        return CFDI_SAT_QR_STATE.get(status[0] if status else '', 'none')

    @api.multi
    def get_xml_object(self, xml):
        try:
            if isinstance(xml, bytes):
                xml = xml.decode()
            xml_str = base64.b64decode(xml.replace(
                'data:text/xml;base64,', ''))
            xml = objectify.fromstring(xml_str)
        except (AttributeError, SyntaxError):
            xml = None
        return xml

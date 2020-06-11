# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
# pylint: disable=too-complex

import base64

from lxml import etree, objectify

from odoo import _, api, fields, models
from odoo.tools.float_utils import float_is_zero
from odoo.tools import float_round
from odoo.exceptions import UserError

TYPE_CFDI22_TO_CFDI33 = {
    'ingreso': 'I',
    'egreso': 'E',
    'traslado': 'T',
    'nomina': 'N',
    'pago': 'P',
}


class AttachXmlsWizard(models.TransientModel):
    _name = 'xunnel.attach.xmls.wizard'

    @api.model
    def _default_journal(self):
        type_inv = 'in_invoice' if self._context.get(
            'l10n_mx_edi_invoice_type') == 'in' else 'out_invoice'
        return self.env['account.invoice'].with_context(
            type=type_inv)._default_journal()

    @api.model
    def _get_journal_domain(self):
        type_inv = 'purchase' if self._context.get(
            'l10n_mx_edi_invoice_type') == 'in' else 'sale'
        return [('type', '=', type_inv)]

    dragndrop = fields.Char()
    account_id = fields.Many2one(
        'account.account',
        help='Optional field to define the account that will be used in all '
        'the lines of the invoice.\nIf the field is not set, the wizard will '
        'take the account by default.')
    journal_id = fields.Many2one(
        'account.journal', required=True,
        default=_default_journal,
        domain=_get_journal_domain,
        help='This journal will be used in the invoices generated with this '
        'wizard.')
    omit_cfdi_related = fields.Boolean(
        help='Use this option when the CFDI attached do not have a CFDI '
        'related and is a Refund (Only as exception)')

    toggle_mode = fields.Boolean(
        string="Load from attachments",
        help="Check this in order to load xml from attachments")

    attachment_ids = fields.Many2many('ir.attachment')

    @api.multi
    def load_attachments(self):
        self.ensure_one()
        files = {'%s %s' % (i.id, i.datas_fname):
                 i.datas for i in self.attachment_ids}
        res = self.with_context(
            account_id=self.account_id.id, journal_id=self.journal_id.id,
            omit_cfdi_related=self.omit_cfdi_related).check_xml(files)
        if res['wrongfiles']:
            message = ''
            for key, msg in res['wrongfiles'].items():
                msg.pop('xml64')
                message += '%s issues with: {%s}\n' % (key, msg)
                raise UserError(
                    _("Resolve following issues:\n %s") % (message))
        invoice_ids = [
            res['invoices'][i]['invoice_id'] for i in res['invoices']]
        action = self.env.ref('account.action_invoice_tree2').read()[0]
        if len(invoice_ids) > 1:
            action['domain'] = [('id', 'in', invoice_ids)]
        elif len(invoice_ids) == 1:
            action['views'] = [
                (self.env.ref('account.invoice_supplier_form').id, 'form')]
            action['res_id'] = invoice_ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @staticmethod
    def _xml2capitalize(xml):
        """Receive 1 lxml etree object and change all attrib to Capitalize.
        """
        def recursive_lxml(element):
            for attrib, value in element.attrib.items():
                new_attrib = "%s%s" % (attrib[0].upper(), attrib[1:])
                element.attrib.update({new_attrib: value})

            for child in element.getchildren():
                child = recursive_lxml(child)
            return element
        return recursive_lxml(xml)

    @staticmethod
    def _l10n_mx_edi_convert_cfdi32_to_cfdi33(xml):
        """Convert a xml from cfdi32 to cfdi33
        :param xml: The xml 32 in lxml.objectify object
        :return: A xml 33 in lxml.objectify object
        """
        if xml.get('version', None) != '3.2':
            return xml
        # TODO: Process negative taxes "Retenciones" node
        # TODO: Process payment term
        xml = AttachXmlsWizard._xml2capitalize(xml)
        xml.attrib.update({
            'TipoDeComprobante': TYPE_CFDI22_TO_CFDI33[
                xml.attrib['TipoDeComprobante']],
            'Version': '3.3',
            # By default creates Payment Complement since that the imported
            # invoices are most imported for this propose if it is not the case
            # then modified manually from odoo.
            'MetodoPago': 'PPD',
        })
        return xml

    @staticmethod
    def collect_taxes(taxes_xml):
        """ Get tax data of the Impuesto node of the xml and return
        dictionary with taxes datas
        :param taxes_xml: Impuesto node of xml
        :type taxes_xml: etree
        :return: A list with the taxes data
        :rtype: list
        """
        taxes = []
        tax_codes = {'001': 'ISR', '002': 'IVA', '003': 'IEPS'}
        for rec in taxes_xml:
            tax_xml = rec.get('Impuesto', '')
            tax_xml = tax_codes.get(tax_xml, tax_xml)
            amount_xml = float(rec.get('Importe', '0.0'))
            rate_xml = float_round(
                float(rec.get('TasaOCuota', '0.0')) * 100, 4)
            if 'Retenciones' in rec.getparent().tag:
                tax_xml = tax_xml
                amount_xml = amount_xml * -1
                rate_xml = rate_xml * -1

            taxes.append({'rate': rate_xml, 'tax': tax_xml,
                          'amount': amount_xml})
        return taxes

    def get_impuestos(self, xml):
        if not hasattr(xml, 'Impuestos'):
            return {}
        taxes_list = {'wrong_taxes': [], 'taxes_ids': {}, 'withno_account': []}
        taxes = []
        company = self._context.get('force_company_id')
        company = company if company else self.env.user.company_id.id
        for index, rec in enumerate(xml.Conceptos.Concepto):
            if not hasattr(rec, 'Impuestos'):
                continue
            taxes_list['taxes_ids'][index] = []
            taxes_xml = rec.Impuestos
            if hasattr(taxes_xml, 'Traslados'):
                taxes = self.collect_taxes(taxes_xml.Traslados.Traslado)
            if hasattr(taxes_xml, 'Retenciones'):
                taxes += self.collect_taxes(taxes_xml.Retenciones.Retencion)

            for tax in taxes:
                tax_group_id = self.env['account.tax.group'].search(
                    [('name', 'ilike', tax['tax'])])
                domain = [('tax_group_id', 'in', tax_group_id.ids),
                          ('type_tax_use', '=', 'purchase'),
                          ('company_id', '=', company),
                          ]
                if -10.67 <= tax['rate'] <= -10.66:
                    domain.append(('amount', '<=', -10.66))
                    domain.append(('amount', '>=', -10.67))
                else:
                    domain.append(('amount', '=', tax['rate']))

                name = '%s(%s%%)' % (tax['tax'], tax['rate'])

                tax_get = self.env['account.tax'].search(domain, limit=1)

                if not tax_group_id or not tax_get:
                    taxes_list['wrong_taxes'].append(name)
                    continue
                if not tax_get.account_id.id:
                    taxes_list['withno_account'].append(
                        name if name else tax['tax'])
                else:
                    tax['id'] = tax_get.id
                    tax['account'] = tax_get.account_id.id
                    tax['name'] = name if name else tax['tax']
                    taxes_list['taxes_ids'][index].append(tax)
        return taxes_list

    def get_local_taxes(self, xml):
        if not hasattr(xml, 'Complemento'):
            return {}
        local_taxes = xml.Complemento.xpath(
            'implocal:ImpuestosLocales',
            namespaces={'implocal': 'http://www.sat.gob.mx/implocal'})
        taxes_list = {
            'wrong_taxes': [], 'withno_account': [], 'taxes': []}
        if not local_taxes:
            return taxes_list
        local_taxes = local_taxes[0]
        tax_obj = self.env['account.tax']
        if hasattr(local_taxes, 'RetencionesLocales'):
            for local_ret in local_taxes.RetencionesLocales:
                name = local_ret.get('ImpLocRetenido')
                tasa = float(local_ret.get('TasadeRetencion')) * -1
                tax = tax_obj.search([
                    '&',
                    ('type_tax_use', '=', 'purchase'),
                    '|',
                    ('name', '=', name),
                    ('amount', '=', tasa)], limit=1)
                if not tax and name not in self.get_taxes_to_omit():
                    taxes_list['wrong_taxes'].append(name)
                    continue
                elif tax and not tax.account_id:
                    taxes_list['withno_account'].append(name)
                    continue
                taxes_list['taxes'].append((0, 0, {
                    'tax_id': tax.id,
                    'account_id': tax.account_id.id,
                    'name': name,
                    'amount': float(local_ret.get('Importe')) * -1,
                    'for_expenses': not bool(tax),
                }))
        if hasattr(local_taxes, 'TrasladosLocales'):
            for local_tras in local_taxes.TrasladosLocales:
                name = local_tras.get('ImpLocTrasladado')
                tasa = float(local_tras.get('TasadeTraslado'))
                tax = tax_obj.search([
                    '&',
                    ('type_tax_use', '=', 'purchase'),
                    '|',
                    ('name', '=', name),
                    ('amount', '=', tasa)], limit=1)
                if not tax and name not in self.get_taxes_to_omit():
                    taxes_list['wrong_taxes'].append(name)
                    continue
                elif tax and not tax.account_id:
                    taxes_list['withno_account'].append(name)
                    continue
                taxes_list['taxes'].append((0, 0, {
                    'tax_id': tax.id,
                    'account_id': tax.account_id.id,
                    'name': name,
                    'amount': float(local_tras.get('Importe')),
                    'for_expenses': not bool(tax),
                }))

        return taxes_list

    def get_xml_folio(self, xml):
        return '%s%s' % (xml.get('Serie', ''), xml.get('Folio', ''))

    def validate_documents(self, key, xml, account_id):
        """ Validate the incoming or outcoming document before create or
        attach the xml to invoice
        :param key: Name of the document that is being validated
        :type key: str
        :param xml: xml file with the datas of purchase
        :type xml: etree
        :param account_id: The account by default that must be used in the
            lines of the invoice if this is created
        :type account_id: int
        :return: Result of the validation of the CFDI and the invoices created.
        :rtype: dict
        """
        wrongfiles = {}
        invoices = {}
        inv_obj = self.env['account.invoice']
        currency_obj = self.env['res.currency']
        inv = inv_obj
        inv_id = False
        xml_str = etree.tostring(xml, pretty_print=True, encoding='UTF-8')
        xml_vat_emitter, xml_vat_receiver, xml_amount, xml_currency, version,\
            xml_name_supplier, xml_type_of_document, xml_uuid, xml_folio,\
            xml_taxes = self._get_xml_data(xml)
        xml_related_uuid = related_invoice = False
        partner_domain = [('vat', '=', xml_vat_emitter)]
        partner_obj = self.env['res.partner'].sudo()
        currency_obj = self.env['res.currency'].sudo()
        currency_field = 'property_purchase_currency_id' in partner_obj._fields
        if currency_field:
            currency_id = currency_obj.search(
                [('name', '=', xml_currency)], limit=1)
            partner_domain.append(
                ('property_purchase_currency_id', '=', currency_id.id))
        exist_supplier = self._get_partner_cfdi(partner_domain)
        if not exist_supplier and currency_field:
            partner_domain.pop()
            exist_supplier = self._get_partner_cfdi(partner_domain)
        domain = [
            '|', ('partner_id', 'child_of', exist_supplier.id),
            ('partner_id', '=', exist_supplier.id)]
        invoice = xml_folio
        if xml_folio:
            domain.append(('reference', '=ilike', xml_folio))
        else:
            domain.append(('amount_total', '>=', xml_amount - 1))
            domain.append(('amount_total', '<=', xml_amount + 1))
            domain.append(('l10n_mx_edi_cfdi_name', '=', False))
        invoice = inv_obj.search(domain, limit=1)
        exist_reference = invoice if invoice and xml_uuid != invoice.l10n_mx_edi_cfdi_uuid else False  # noqa
        if exist_reference and not exist_reference.l10n_mx_edi_cfdi_uuid:
            inv = exist_reference
            inv_id = inv.id
            exist_reference = False
        xml_status = inv.l10n_mx_edi_sat_status
        company = self._context.get('force_company_id')
        company = self.env['res.company'].browse(
            company) if company else self.env.user.company_id
        inv_vat_receiver = (company.vat or '').upper()
        inv_vat_emitter = (
            inv and inv.commercial_partner_id.vat or '').upper()
        inv_amount = inv.amount_total
        diff = inv.journal_id.l10n_mx_edi_amount_authorized_diff or 1
        inv_folio = inv.reference or ''
        domain = [('l10n_mx_edi_cfdi_name', '!=', False)]
        if exist_supplier:
            domain += [('partner_id', 'child_of', exist_supplier.id)]
        if xml_type_of_document == 'I':
            domain += [('type', '=', 'in_invoice')]
        if xml_type_of_document == 'E':
            domain += [('type', '=', 'in_refund')]
        uuid_dupli = xml_uuid in inv_obj.search(domain).mapped(
            'l10n_mx_edi_cfdi_uuid')
        mxns = ['mxp', 'mxn', 'pesos', 'peso mexicano', 'pesos mexicanos']
        xml_currency = 'MXN' if xml_currency.lower(
        ) in mxns else xml_currency

        exist_currency = currency_obj.search(
            ['|', ('name', '=', xml_currency),
             ('currency_unit_label', '=ilike', xml_currency)], limit=1)

        xml_related_uuid = False
        if xml_type_of_document == 'E' and hasattr(xml, 'CfdiRelacionados'):
            xml_related_uuid = xml.CfdiRelacionados.CfdiRelacionado.get('UUID')
            related_invoice = xml_related_uuid in inv_obj.search([
                ('l10n_mx_edi_cfdi_name', '!=', False),
                ('type', '=', 'in_invoice')]).mapped('l10n_mx_edi_cfdi_uuid')
        omit_cfdi_related = self._context.get('omit_cfdi_related')
        force_save = False
        if self.env.user.has_group('invoice_xunnel.allow_force_invoice_generation'):
            force_save = self._context.get('force_save')
        errors = [
            (not xml_uuid, {'signed': True}),
            (xml_status == 'cancelled', {'cancel': True}),
            ((xml_uuid and uuid_dupli), {'uuid_duplicate': xml_uuid}),
            ((inv_vat_receiver != xml_vat_receiver),
             {'rfc': (xml_vat_receiver, inv_vat_receiver)}),
            ((not inv_id and exist_reference),
             {'reference': (xml_name_supplier, xml_folio)}),
            (version != '3.3', {'version': True}),
            ((not inv_id and not exist_supplier),
             {'supplier': xml_name_supplier}),
            ((not inv_id and xml_currency and not exist_currency),
             {'currency': xml_currency}),
            ((not inv_id and xml_taxes.get('wrong_taxes', False)),
             {'taxes': xml_taxes.get('wrong_taxes', False)}),
            ((not inv_id and xml_taxes.get('withno_account', False)),
             {'taxes_wn_accounts': xml_taxes.get(
                 'withno_account', False)}),
            ((inv_id and inv_folio != xml_folio),
             {'folio': (xml_folio, inv_folio)}),
            ((inv_id and inv_vat_emitter != xml_vat_emitter), {
                'rfc_supplier': (xml_vat_emitter, inv_vat_emitter)}),
            ((inv_id and abs(round(float(inv_amount) - xml_amount, 2)) > diff),
             {'amount': (xml_amount, inv_amount)}),
            ((xml_related_uuid and not related_invoice and not force_save),
             {'invoice_not_found': xml_related_uuid}),
            ((not omit_cfdi_related and xml_type_of_document == 'E' and
              not xml_related_uuid), {'no_xml_related_uuid': True}),
        ]
        msg = {}
        for error in errors:
            if error[0]:
                msg.update(error[1])
        if msg:
            msg.update({'xml64': True})
            wrongfiles.update({key: msg})
            return {'wrongfiles': wrongfiles, 'invoices': invoices}

        if not inv_id:
            invoice_status = self.with_context(key=key).create_invoice(
                xml, exist_supplier, exist_currency,
                xml_taxes.get('taxes_ids', {}), account_id)

            if invoice_status['key'] is False:
                del invoice_status['key']
                invoice_status.update({'xml64': True})
                wrongfiles.update({key: invoice_status})
                return {'wrongfiles': wrongfiles, 'invoices': invoices}

            del invoice_status['key']
            invoices.update({key: invoice_status})
            return {'wrongfiles': wrongfiles, 'invoices': invoices}

        inv.l10n_mx_edi_cfdi = xml_str.decode('UTF-8')
        if self.toggle_mode:
            attach_id, attach_name = key.split(' ')
            inv.link_xml_attachment(attach_name, int(attach_id))
        else:
            inv.generate_xml_attachment()
        inv.reference = '%s|%s' % (xml_folio, xml_uuid.split('-')[0])
        inv.l10n_mx_edi_update_sat_status()
        invoices.update({key: {'invoice_id': inv.id}})
        if not float_is_zero(float(inv.amount_total) - xml_amount,
                             precision_digits=0):
            inv.message_post(
                body=_('The XML attached total amount is different to '
                       'the total amount in this invoice. The XML total '
                       'amount is %s') % xml_amount)
        return {'wrongfiles': wrongfiles, 'invoices': invoices}

    @api.model
    def _get_xml_data(self, xml):
        """Return data from XML"""
        inv_obj = self.env['account.invoice']
        vat_emitter = xml.Emisor.get('Rfc', '').upper()
        vat_receiver = xml.Receptor.get('Rfc', '').upper()
        amount = float(xml.get('Total', 0.0))
        currency = xml.get('Moneda', 'MXN')
        version = xml.get('Version', xml.get('version'))
        name_supplier = xml.Emisor.get('Nombre', '')
        document_type = xml.get('TipoDeComprobante', False)
        tfd = inv_obj.l10n_mx_edi_get_tfd_etree(xml)
        uuid = False if tfd is None else tfd.get('UUID', '')
        folio = self.get_xml_folio(xml)
        taxes = self.get_impuestos(xml)
        local_taxes = self.get_local_taxes(xml)
        taxes['wrong_taxes'] = taxes.get(
            'wrong_taxes', []) + local_taxes.get('wrong_taxes', [])
        taxes['withno_account'] = taxes.get(
            'withno_account', []) + local_taxes.get('withno_account', [])
        return vat_emitter, vat_receiver, amount, currency, version,\
            name_supplier, document_type, uuid, folio, taxes

    @api.model
    def check_xml(self, files, account_id=False):
        """ Validate that attributes in the xml before create invoice
        or attach xml in it
        :param files: dictionary of CFDIs in b64
        :type files: dict
        param account_id: The account by default that must be used in the
        lines of the invoice if this is created
        :type account_id: int
        :return: the Result of the CFDI validation
        :rtype: dict
        """
        if not isinstance(files, dict):
            raise UserError(_("Something went wrong. The parameter for XML "
                              "files must be a dictionary."))
        wrongfiles = {}
        invoices = {}
        outgoing_docs = {}
        account_id = account_id or self._context.get('account_id', False)
        for key, xml64 in files.items():
            try:
                if isinstance(xml64, bytes):
                    xml64 = xml64.decode()
                xml_str = base64.b64decode(xml64.replace(
                    'data:text/xml;base64,', ''))
                # Fix the CFDIs emitted by the SAT
                xml_str = xml_str.replace(
                    b'xmlns:schemaLocation', b'xsi:schemaLocation')
                xml = objectify.fromstring(xml_str)
            except (AttributeError, SyntaxError) as exce:
                wrongfiles.update({key: {
                    'xml64': xml64, 'where': 'CheckXML',
                    'error': [exce.__class__.__name__, str(exce)]}})
                continue
            xml = self._l10n_mx_edi_convert_cfdi32_to_cfdi33(xml)
            if xml.get('TipoDeComprobante', False) == 'E':
                outgoing_docs.update({key: {'xml': xml, 'xml64': xml64}})
                continue
            elif xml.get('TipoDeComprobante', False) != 'I':
                wrongfiles.update({key: {'cfdi_type': True, 'xml64': xml64}})
                continue
            # Check the incoming documents
            validated_documents = self.validate_documents(key, xml, account_id)
            wrongfiles.update(validated_documents.get('wrongfiles'))
            if wrongfiles.get(key, False) and \
                    wrongfiles[key].get('xml64', False):
                wrongfiles[key]['xml64'] = xml64
            invoices.update(validated_documents.get('invoices'))
        # Check the outgoing documents
        for key, value in outgoing_docs.items():
            xml64 = value.get('xml64')
            xml = value.get('xml')
            xml = self._l10n_mx_edi_convert_cfdi32_to_cfdi33(xml)
            validated_documents = self.validate_documents(key, xml, account_id)
            wrongfiles.update(validated_documents.get('wrongfiles'))
            if wrongfiles.get(key, False) and \
                    wrongfiles[key].get('xml64', False):
                wrongfiles[key]['xml64'] = xml64
            invoices.update(validated_documents.get('invoices'))
        return {'wrongfiles': wrongfiles,
                'invoices': invoices}

    def get_default_analytic(self, product, supplier):
        try:
            analytic_default = self.env['account.analytic.default']
        except BaseException:
            return False
        default_analytic = (
            analytic_default.account_get(
                product.id, supplier.id, self.env.user.id,
                fields.Date.today()) or False)
        return default_analytic

    @api.multi
    def create_invoice(
            self, xml, supplier, currency_id, taxes, account_id=False):
        """ Create supplier invoice from xml file
        :param xml: xml file with the datas of purchase
        :type xml: etree
        :param supplier: supplier partner
        :type supplier: res.partner
        :param currency_id: payment currency of the purchase
        :type currency_id: res.currency
        :param taxes: Datas of taxes
        :type taxes: list
        :param account_id: The account by default that must be used in the
            lines, if this is defined will to use this.
        :type account_id: int
        :return: the Result of the invoice creation
        :rtype: dict
        """
        inv_obj = self.env['account.invoice']
        line_obj = self.env['account.invoice.line']
        prod_obj = self.env['product.product']
        prod_supplier_obj = self.env['product.supplierinfo']
        sat_code_obj = self.env['l10n_mx_edi.product.sat.code']

        xml_type_doc = xml.get('TipoDeComprobante', False)
        type_invoice = 'in_invoice' if xml_type_doc == 'I' else 'in_refund'
        company = self._context.get('force_company_id')
        company = self.env['res.company'].browse(
            company) if company else self.env.user.company_id
        journal = self._context.get('journal_id', False)
        journal = self.env['account.journal'].browse(
            journal) if journal else inv_obj.with_context(
                type=type_invoice, company_id=company.id)._default_journal()
        uom_obj = uom_obj = self.env['product.uom']
        account_id = account_id or line_obj.with_context({
            'journal_id': journal.id, 'type': 'in_invoice'})._default_account()
        invoice_line_ids = []
        msg = (_('Some products are not found in the system, and the account '
                 'that is used like default is not configured in the journal, '
                 'please set default account in the journal '
                 '%s to create the invoice.') % journal.name)

        date_inv = xml.get('Fecha', '').split('T')
        for index, rec in enumerate(xml.Conceptos.Concepto):
            name = rec.get('Descripcion', '')
            no_id = rec.get('NoIdentificacion', name)
            product_code = rec.get('ClaveProdServ', '')
            uom = rec.get('Unidad', '')
            uom_code = rec.get('ClaveUnidad', '')
            qty = rec.get('Cantidad', '')
            price = rec.get('ValorUnitario', '')
            amount = float(rec.get('Importe', '0.0'))
            supplierinfo_id = prod_supplier_obj.search([
                ('name', '=', supplier.id),
                '|', ('product_name', '=ilike', name),
                ('product_code', '=ilike', no_id)], limit=1)
            product_id = supplierinfo_id.product_tmpl_id.product_variant_id
            product_id = product_id or prod_obj.search([
                '|', ('default_code', '=ilike', no_id),
                ('name', '=ilike', name)], limit=1)
            account_id = (
                account_id or product_id.property_account_expense_id.id or
                product_id.categ_id.property_account_expense_categ_id.id)

            if not account_id:
                return {
                    'key': False, 'where': 'CreateInvoice',
                    'error': [
                        _('Account to set in the lines not found.<br/>'), msg]}

            discount = 0.0
            if rec.get('Descuento') and amount:
                discount = (float(rec.get('Descuento', '0.0')) / amount) * 100

            domain_uom = [('name', '=ilike', uom)]
            line_taxes = [tax['id'] for tax in taxes.get(index, [])]
            code_sat = sat_code_obj.search([('code', '=', uom_code)], limit=1)
            domain_uom = [('l10n_mx_edi_code_sat_id', '=', code_sat.id)]
            uom_id = uom_obj.with_context(
                lang='es_MX').search(domain_uom, limit=1)
            restaurant_category_id = self.env.ref(
                'invoice_xunnel.restaurant_bills')
            tax = taxes.get(index)[0] if taxes.get(index, []) else {}
            if product_code in self._get_fuel_codes() or (
                    restaurant_category_id in supplier.category_id and tax):
                qty = 1.0
                price = tax.get('amount') / (tax.get('rate') / 100)
                invoice_line_ids.append((0, 0, {
                    'account_id': account_id,
                    'name':  _('Non Deductible') if
                    restaurant_category_id in supplier.category_id else
                    _('FUEL - IEPS'),
                    'quantity': qty,
                    'uom_id': uom_id.id,
                    'price_unit': float(rec.get('Importe', 0)) - price,
                }))
            default_analytic = self.get_default_analytic(product_id, supplier)
            invoice_line_ids.append((0, 0, {
                'product_id': product_id.id,
                'account_id': account_id,
                'account_analytic_id':
                default_analytic.analytic_id.id if default_analytic else False,
                'name': name,
                'quantity': float(qty),
                'uom_id': uom_id.id,
                'invoice_line_tax_ids': [(6, 0, line_taxes)],
                'price_unit': float(price),
                'discount': discount,
            }))

        xml_str = etree.tostring(xml, pretty_print=True, encoding='UTF-8')
        xml_tfd = inv_obj.l10n_mx_edi_get_tfd_etree(xml)
        uuid = False if xml_tfd is None else xml_tfd.get('UUID', '')
        invoice_id = inv_obj.create({
            'partner_id': supplier.id,
            'reference': '%s|%s' % (
                self.get_xml_folio(xml),
                uuid.split('-')[0]),
            'date_invoice': date_inv[0],
            'currency_id': (currency_id.id or company.currency_id.id),
            'invoice_line_ids': invoice_line_ids,
            'type': type_invoice,
            'l10n_mx_edi_time_invoice': date_inv[1],
            'journal_id': journal.id,
            'company_id': company.id,
        })

        local_taxes = self.get_local_taxes(xml).get('taxes', [])
        if local_taxes:
            invoice_id.write({
                'tax_line_ids': [_tax for _tax in local_taxes if not _tax[-1].get(
                    'for_expenses')],
            })
            invoice_id.write({
                'invoice_line_ids': [(0, 0, {
                    'account_id': account_id,
                    'name': _tax[-1]['name'],
                    'quantity': 1,
                    'price_unit': _tax[-1]['amount'],
                }) for _tax in local_taxes if _tax[-1].get('for_expenses')],
            })
        if xml.get('version') == '3.2':
            # Global tax used for each line since that a manual tax line
            # won't have base amount assigned.
            tax_path = '//cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado'
            tax_obj = self.env['account.tax']
            for global_tax in xml.xpath(tax_path, namespaces=xml.nsmap):
                tax_name = global_tax.attrib.get('impuesto')
                tax_percent = float(global_tax.attrib.get('tasa'))
                tax_group_id = self.env['account.tax.group'].search(
                    [('name', 'ilike', tax_name)])
                tax_domain = [
                    ('type_tax_use', '=', 'purchase'),
                    ('company_id', '=', company.id),
                    ('tax_group_id', 'in', tax_group_id.ids),
                    ('amount_type', '=', 'percent'),
                    ('amount', '=', tax_percent),
                ]
                tax = tax_obj.search(tax_domain, limit=1)
                if not tax:
                    return {
                        'key': False,
                        'taxes': ['%s(%s%%)' % (tax_name, tax_percent)],
                    }
                invoice_id.invoice_line_ids.write({
                    'invoice_line_tax_ids': [(4, tax.id)]})

            # Global discount used for each line
            # Decimal rounding wrong values could be imported will fix manually
            discount_amount = float(xml.attrib.get('Descuento', 0))
            sub_total_amount = float(xml.attrib.get('subTotal', 0))
            if discount_amount and sub_total_amount:
                percent = discount_amount * 100 / sub_total_amount
                invoice_id.invoice_line_ids.write({'discount': percent})

        invoice_id.l10n_mx_edi_cfdi = xml_str.decode('UTF-8')
        if self.toggle_mode:
            key = self.env.context['key'] or ''
            attach_id, attach_name = key.split(' ')
            invoice_id.link_xml_attachment(attach_name, int(attach_id))
        else:
            invoice_id.generate_xml_attachment()
        if xml_type_doc == 'E' and hasattr(xml, 'CfdiRelacionados'):
            xml_related_uuid = xml.CfdiRelacionados.CfdiRelacionado.get('UUID')
            invoice_id._set_cfdi_origin('01', [xml_related_uuid])
            related_invoices = inv_obj.search([
                ('partner_id', '=', supplier.id), ('type', '=', 'in_invoice')])
            related_invoices = related_invoices.filtered(
                lambda inv: inv.l10n_mx_edi_cfdi_uuid == xml_related_uuid)
            related_invoices.write({
                'refund_invoice_ids': [(4, invoice_id.id, 0)]
            })
        invoice_id.l10n_mx_edi_update_sat_status()
        invoice_id.compute_taxes()
        return {'key': True, 'invoice_id': invoice_id.id}

    @api.model
    def create_partner(self, xml64, key):
        """ It creates the supplier dictionary, getting data from the XML
        Receives an xml decode to read and returns a dictionary with data """
        # Default Mexico because only in Mexico are emitted CFDIs
        try:
            if isinstance(xml64, bytes):
                xml64 = xml64.decode()
            xml_str = base64.b64decode(xml64.replace(
                'data:text/xml;base64,', ''))
            # Fix the CFDIs emitted by the SAT
            xml_str = xml_str.replace(
                b'xmlns:schemaLocation', b'xsi:schemaLocation')
            xml = objectify.fromstring(xml_str)
        except BaseException as exce:
            return {
                key: False, 'xml64': xml64, 'where': 'CreatePartner',
                'error': [exce.__class__.__name__, str(exce)]}

        xml = self._l10n_mx_edi_convert_cfdi32_to_cfdi33(xml)
        rfc_emitter = xml.Emisor.get('Rfc', False)
        name = xml.Emisor.get('Nombre', rfc_emitter)
        xml_currency = xml.get('Moneda', 'MXN')

        # check if the partner exist from a previos invoice creation
        partner_domain = ['|', ('name', '=', name), ('vat', '=', rfc_emitter)]
        partner_obj = self.env['res.partner'].sudo()
        currency_obj = self.env['res.currency'].sudo()
        currency_field = 'property_purchase_currency_id' in partner_obj._fields
        if currency_field:
            currency_id = currency_obj.search(
                [('name', '=', xml_currency)], limit=1)
            partner_domain.append(
                ('property_purchase_currency_id', '=', currency_id.id))
        partner = self._get_partner_cfdi(partner_domain)
        if not partner and currency_field:
            partner_domain.pop()
            partner = self._get_partner_cfdi(partner_domain)

        if partner:
            return partner

        partner = self.env['res.partner'].create({
            'name': name,
            'company_type': 'company',
            'vat': rfc_emitter,
            'country_id': self.env.ref('base.mx').id,
            'supplier': True,
            'customer': False,
        })
        msg = _('This partner was created when invoice %s%s was added from '
                'a XML file. Please verify that the datas of partner are '
                'correct.') % (xml.get('Serie', ''), xml.get('Folio', ''))
        partner.message_post(subject=_('Info'), body=msg)
        return partner

    @api.model
    def _get_fuel_codes(self):
        """Return the codes that could be used in FUEL"""
        return [str(r) for r in range(15101500, 15101513)]

    @api.multi
    def get_taxes_to_omit(self):
        """Some taxes are not found in the system, but is correct, because that
        taxes should be adds in the invoice like expenses.
        To make dynamic this, could be add an system parameter with the name:
            l10n_mx_taxes_for_expense, and un the value set the taxes name,
        and if are many taxes, split the names by ','"""
        taxes = self.env['ir.config_parameter'].sudo().get_param(
            'l10n_mx_taxes_for_expense', '')
        return taxes.split(',')

    @api.multi
    def _get_partner_cfdi(self, domain):
        """Consider in the search the next order:
            - Is supplier
            - Is company
            - Any record with the same VAT received."""
        partner = self.env['res.partner']
        domain.append(('supplier', '=', True))
        domain.append(('is_company', '=', True))
        cfdi_partner = partner.search(domain, limit=1)
        if not cfdi_partner:
            domain.pop()
            cfdi_partner = partner.search(domain, limit=1)
        if not cfdi_partner:
            domain.pop()
            cfdi_partner = partner.search(domain, limit=1)
        return cfdi_partner

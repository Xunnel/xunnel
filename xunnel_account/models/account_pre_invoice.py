# -*- coding: utf-8 -*-
# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from __future__ import division

import base64
import unicodedata
from codecs import BOM_UTF8

from lxml import objectify

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

BOM_UTF8U = BOM_UTF8.decode('UTF-8')


class AccountPreInvoice(models.Model):
    _name = 'account.pre.invoice'

    @api.one
    @api.depends(
        'invoice_line_ids.price_subtotal', 'tax_line_ids.amount',
        'currency_id', 'company_id', 'date_invoice', 'type')
    def _compute_amount(self):
        self.amount_untaxed = sum(
            line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(line.amount for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax

    name = fields.Char(readonly=True)
    partner_id = fields.Many2one(
        'res.partner', required=True, string='Vendor', readonly=True,
        domain=[('supplier', '=', True)])
    reference = fields.Char(string='Vendor Reference', readonly=True)
    date_invoice = fields.Date(
        string='Bill Date', default=fields.Date.today, readonly=True)
    invoice_line_ids = fields.One2many(
        'account.pre.invoice.line', 'invoice_id', string='Invoice Lines',
        readonly=True, states={'check': [('readonly', False)]})
    company_id = fields.Many2one(
        'res.company', string='Company', change_default=True, required=True,
        default=lambda self: self.env[
            'res.company']._company_default_get('account.invoice'))
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        readonly=True, states={'check': [('readonly', False)]})
    type = fields.Char()
    tax_line_ids = fields.One2many(
        'account.pre.invoice.tax', 'invoice_id', string='Tax Lines',
        readonly=True, states={'check': [('readonly', False)]})
    amount_untaxed = fields.Monetary(
        string='Untaxed Amount', readonly=True, compute='_compute_amount')
    amount_tax = fields.Monetary(
        string='Tax', readonly=True, compute='_compute_amount')
    amount_total = fields.Monetary(
        string='Total', readonly=True, compute='_compute_amount')
    message_wrong_data = fields.Html(readonly=True)
    state = fields.Selection(
        [('pending', 'Pending'), ('check', 'To Check'), ('done', 'Done')],
        string='Status', index=True, readonly=True, default='pending',
        copy=False)
    account_invoice_id = fields.Many2one(
        'account.invoice',
        string='Invoice',
    )

    def button_account_invoice(self):
        return {
            'name': 'Invoice',
            'view_id': self.env.ref(
                'account.invoice_form').id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'res_model': 'account.invoice',
            'res_id': self.account_invoice_id.id,
            'type': 'ir.actions.act_window'
        }

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        """ Get taxes from invoice lines """
        rets_and_news = [(0, 0, {
            'name': ret.name,
            'account_id': ret.account_id.id if ret.account_id else False,
            'amount': ret.amount,
            'xml_invoice': ret.xml_invoice,
        }) for ret in self.tax_line_ids if 'Retencion(' in ret.name or not
            ret.xml_invoice]
        group_taxes = {}
        for inv_line in self.invoice_line_ids:
            for tax_line in inv_line.invoice_line_tax_ids:
                if tax_line.name not in group_taxes.keys():
                    group_taxes[tax_line.name] = {

                        'account_id': tax_line.account_id.id,
                        'importe': 0.0,
                    }
                group_taxes[tax_line.name]['importe'] += (
                    (inv_line.price_unit * inv_line.quantity) *
                    (tax_line.amount / 100))
        tax_line_obj = []
        for tax_name, tval in group_taxes.items():
            tax_line_obj.append((0, 0, {
                'name': tax_name,
                'account_id': tval['account_id'],
                'amount': tval['importe'],
                'xml_invoice': True,
            }))
        self.tax_line_ids = tax_line_obj + rets_and_news

    # ----------------------------------------------------------------------- #

    @staticmethod
    def get_cfdi_catalogs(witch):
        """ Returns the cfdi catalogs and attributes """
        catalogs = {}
        if 'attr' in witch:
            catalogs['attr'] = {
                'descuento': {'3.2': 'descuento', '3.3': 'Descuento'},
                'rfc': {'3.2': 'rfc', '3.3': 'Rfc'},
                'fecha': {'3.2': 'fecha', '3.3': 'Fecha'},
                'folio': {'3.2': 'folio', '3.3': 'Folio'},
                'subTotal': {'3.2': 'subTotal', '3.3': 'SubTotal'},
                'total': {'3.2': 'total', '3.3': 'Total'},
                'impuesto': {'3.2': 'impuesto', '3.3': 'Impuesto'},
                'tasa': {'3.2': 'tasa', '3.3': 'TasaOCuota'},
                'importe': {'3.2': 'importe', '3.3': 'Importe'},
                'descripcion': {'3.2': 'descripcion', '3.3': 'Descripcion'},
                'unidad': {'3.2': 'unidad', '3.3': 'Unidad'},
                'cantidad': {'3.2': 'cantidad', '3.3': 'Cantidad'},
                'nombre': {'3.2': 'nombre', '3.3': 'Nombre'},
                'valorUnitario': {
                    '3.2': 'valorUnitario', '3.3': 'ValorUnitario'},
                'tipoDeComprobante': {
                    '3.2': 'tipoDeComprobante', '3.3': 'TipoDeComprobante'},
            }
        if 'tax-catalog' in witch:
            catalogs['tax-catalog'] = {
                '001': 'ISR', '002': 'IVA', '003': 'IEPS'}
        if 'mxns' in witch:
            catalogs['mxns'] = [
                'mxp', 'mxn', 'mn', 'pesos', 'peso mexicano', 'pesos mexicanos'
            ]
        if 'tcomp' in witch:
            catalogs['tcomp'] = {
                'ingreso': {'3.2': 'ingreso', '3.3': 'I'},
                'egreso': {'3.2': 'egreso', '3.3': 'E'},
                'traslado': {'3.2': 'traslado', '3.3': 'T'},
                'nomina': {'3.3': 'N'},
                'pago': {'3.3': 'P'},
            }
        return [catalogs[ele] for ele in witch] if len(
            catalogs) > 1 else catalogs.values()[0]

    @staticmethod
    def delete_accent(string):
        """ It delete accents in words. Receives an utf-8 unicode string and
        returns a string with no accents."""
        if isinstance(string, str):
            string = unicode(string)
        return ''.join((c for c in unicodedata.normalize(
            'NFD', string) if unicodedata.category(c) != 'Mn'))

    @api.multi
    def get_ids_search(self, model, vfields, val):
        """ It searches all records but just gets name and id from records.
        Receives the model where it searches the records, the fields that
        it shows, and the value name that will be searched. """
        objects = self.env[model].search([]).read(vfields)
        object_ids = []
        xml_val = self.delete_accent(val).lower()
        for obbject in objects:
            db_val = self.delete_accent(obbject[
                'name']).lower().replace('(s)', '').replace('(es)', '')
            if xml_val == db_val:
                object_ids.append(obbject['id'])
        return self.env[model].browse(object_ids)

    @staticmethod
    def l10n_mx_edi_get_tfd_etree(cfdi):
        """ Get the TimbreFiscalDigital node from the cfdi.
        :param objectify cfdi: The cfdi as etree
        Returns: objectify: the TimbreFiscalDigital node """  # noqa
        if not hasattr(cfdi, 'Complemento'):
            return {}
        attribute = 'tfd:TimbreFiscalDigital[1]'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else {}

    @staticmethod
    def get_tax_name(impuesto, tasa):
        """ It returns the tax name """
        if not tasa:
            return 'Retencion(%s)' % impuesto
        tasa_split = tasa.split('.')
        get_tasa = (
            str(int(tasa_split[0])) if len(tasa_split) == 1 or
            float('.' + tasa_split[1]) <= 0.0 else
            str(float('.'.join(tasa_split))))
        return '{0}({1}%)'.format(impuesto.upper(), get_tasa)

    @api.multi
    def get_group_taxes(self, ver, xmltaxes):
        """ It gets a group taxes dict """
        taxes = {}
        attr, taxcatalog = self.get_cfdi_catalogs(['attr', 'tax-catalog'])
        for rec in xmltaxes:
            impuesto = rec.get(attr['impuesto'][ver])
            tasa = rec.get(attr['tasa'][ver], False)
            if ver == '3.3':
                tasa = str(float(tasa) * 100) if tasa else tasa
            tax_name = self.get_tax_name(
                impuesto if ver == '3.2' else taxcatalog[impuesto], tasa)
            if tax_name not in taxes.keys():
                taxes[tax_name] = {
                    'tasa': tasa,
                    'impuesto': impuesto if ver == '3.2' else taxcatalog[
                        impuesto],
                    'importe': 0.0,
                }
            taxes[tax_name]['importe'] += float(rec.get(attr['importe'][ver]))
        return taxes

    @api.multi
    def get_taxes(self, ver, ttype, impuestos):
        """ It gets the correct and the wrong taxes list of the xml. """
        taxes = {'wrong': [], 'ids': {}}
        conditioner = '=' if ttype == 'xfr' else '!='
        for tax, tval in self.get_group_taxes(ver, impuestos).items():
            tax_group_id = [rec.id for rec in self.env[
                'account.tax.group'].search([('name', '=ilike', tval[
                    'impuesto'])])]
            tax_get = self.env['account.tax'].search([
                ('tax_group_id', 'in', tax_group_id),
                ('amount', conditioner, float(tval['tasa']) if tval[
                    'tasa'] else False),
                ('type_tax_use', '=', 'purchase')
            ])
            exist_tax = len(tax_group_id) == 0 or len(tax_get) == 0
            if ttype == 'ret':
                index = len([key for key in taxes['ids'].keys(
                ) if not str(key).isdigit()])
                ret_dict = {'Ret:' + str(index): {
                    'name': tax,
                    'account_id': False if exist_tax else tax_get[
                        0].account_id.id,
                    'amount': tval['importe'] * -1}}
            if exist_tax:
                taxes['wrong'].append(tax)
                if ttype == 'ret':
                    taxes['ids'].update(ret_dict)
            else:
                if ttype == 'xfr':
                    taxes['ids'][tax_get[0].id] = tax
                else:
                    taxes['ids'].update(ret_dict)
        return [taxes['wrong'], taxes['ids']]

    # ----------------------------------------------------------------------- #

    @api.multi
    def each_invoice(self, files):
        """ Checks if the xml file was already created as an invoice,
        and return the data for the status message of the invoices
        created and not created. """
        attr = self.get_cfdi_catalogs(['attr'])
        for_message = {'omited': 0, 'except': 0, 'correct': 0, 'wrong': 0}
        uuids = [att.name.replace('.xml', '') for att in self.env[
            'ir.attachment'].search([('res_model', 'in', [
                'account.pre.invoice'])])]
        for xml_file in files:
            try:
                xml = objectify.fromstring(xml_file.encode('utf-8'))
                ver = xml.get('version', False) or xml.get('Version', False)
                uuid = self.l10n_mx_edi_get_tfd_etree(xml).get('UUID', '')
                if (xml.Emisor.get(attr['rfc'][
                        ver], False) != self.env.user.company_id.vat and
                        uuid not in uuids):
                    inv = self.handle_invoice_data(
                        xml_file, xml, ver, uuid)
                    if inv.state == 'pending':
                        for_message['correct'] += 1
                    elif inv.state == 'check':
                        for_message['wrong'] += 1
                    uuids.append(uuid)
                else:
                    for_message['omited'] += 1
            except (SyntaxError, ValueError):
                for_message['except'] += 1
        return for_message

    @api.multi
    def handle_invoice_data(self, xmlstr, xml, ver, uuid):
        """ It handle the xml data to create an invoice """
        pre_data = self.check_xml_data(xml, ver)
        invoice_data = self.get_invoice_data(xml, ver, {
            'xfrs_ids': pre_data['xfrs_ids'],
            'wrongdata_msg_keys': pre_data['wrongdata_msg'].keys()})
        inv_to_review = self.create_invoice(xml, ver, pre_data, invoice_data)
        invoice = self.review_invoice(xml, ver, pre_data, inv_to_review)
        self.create_xml_attachment(invoice.id, xmlstr, uuid)
        return invoice

    @api.multi
    def check_xml_data(self, xml, ver):
        """ Checks the xml data before create the invoice, and returns the
        correct message to each error. """
        wrongdata_msg = {}
        attr, mxns = self.get_cfdi_catalogs(['attr', 'mxns'])
        supplier = self.env['res.partner'].search([
            '&', ('vat', '=', xml.Emisor.get(attr['rfc'][ver], '')),
            '|', ('supplier', '=', True), ('customer', '=', True)])
        if supplier:
            supplier.write({'supplier': True})
        else:
            supplier = [self.env['res.partner'].create_partner(xml, ver, attr)]

        xml_currency = (('MXN' if xml.get('Moneda', '').lower(
        ) in mxns else xml.get('Moneda', '')) if xml.get(
            'Moneda', False) else supplier[
                0].property_product_pricelist.currency_id.name or 'USD'
        ) if supplier else 'USD'
        currency_id = self.env['res.currency'].search(
            [('name', '=', xml_currency)])
        if currency_id == 0:
            wrongdata_msg['currency'] = _(
                'The XML Currency %s was not found or is disabled.') % (
                    xml_currency)

        taxes = {
            'wrong_xfrs': [], 'wrong_rets': [], 'xfrs_ids': {}, 'rets_ids': {}}
        if 'Traslados' in xml.Impuestos.__dict__.keys():
            taxes['wrong_xfrs'], taxes['xfrs_ids'] = self.get_taxes(
                ver, 'xfr', xml.Impuestos.Traslados.Traslado)
        if taxes['wrong_xfrs']:
            wrongdata_msg['xfrs'] = _(
                'Some transfers(taxes) do not exist for purchases: %s.') % (
                    ', '.join(taxes['wrong_xfrs']))

        if 'Retenciones' in xml.Impuestos.__dict__.keys():
            taxes['wrong_rets'], taxes['rets_ids'] = self.get_taxes(
                ver, 'ret', xml.Impuestos.Retenciones.Retencion)
        if taxes['wrong_rets']:
            wrongdata_msg['rets'] = _(
                'Some retentions(taxes) do not exist for purchases: %s. '
                'Put accounts manually.') % (', '.join([tax.replace(
                    'Retencion(', '').replace(')', '') for tax in taxes[
                        'wrong_rets']]))

        return {
            'wrongdata_msg': wrongdata_msg, 'supplier': supplier,
            'currency_id': currency_id, 'xfrs_ids': taxes['xfrs_ids'],
            'rets_ids': taxes['rets_ids']}

    @api.multi
    def get_taxes_per_line_33(self, lines, pre_data, tax_in_line, line_index):
        """ If the xml version is 3.3, get the taxes for each invoice line. """
        imps = []
        taxcatalog = self.get_cfdi_catalogs(['tax-catalog'])
        xfers_ids = {tax: tid for tid, tax in pre_data['xfrs_ids'].items()}
        for imp in lines:
            tax_name = self.get_tax_name(taxcatalog[imp.get(
                'Impuesto')], str(float(imp.get(
                    'TasaOCuota')) * 100))
            if tax_name in xfers_ids.keys():
                imps.append(xfers_ids[tax_name])
            else:
                if tax_name not in tax_in_line.keys():
                    tax_in_line[tax_name] = []
                tax_in_line[tax_name].append(line_index)
        dict_line = {'invoice_line_tax_ids': [(6, 0, imps)]}
        if 'xfrs' in pre_data['wrongdata_msg_keys']:
            dict_line.update({'index': line_index})
        return {'dict': dict_line, 'tax_in_line': tax_in_line}

    @api.multi
    def get_invoice_data(self, xml, ver, pre_data):
        """ It gets the xml data to create the invoice. """
        attr = self.get_cfdi_catalogs(['attr'])
        date_inv = xml.get(attr['fecha'][ver], False)
        invoice_line_ids = []
        line_index = 1
        tax_in_line = {}
        for rec in xml.Conceptos.Concepto:
            product_id = self.env['product.product'].search(
                [('name', 'ilike', rec.get(attr['descripcion'][ver]))])
            uom_id = self.get_ids_search(
                'product.uom', ['name'],
                unicode(rec.get(attr['unidad'][ver], ''), 'utf-8'))
            if ver == '3.3':
                discount_aux = (rec.get('Descuento', 0.0) * 100)
                discount = float(discount_aux) / float(rec.get('Importe'))
            else:
                discount = 0.0
            invoice_line = {
                'product_id': (
                    product_id[0].id if product_id else False),
                'name': rec.get(attr['descripcion'][ver]),
                'quantity': float(rec.get(attr['cantidad'][ver])),
                'uom_id': uom_id[0].id if uom_id else self.env[
                    'product.uom'].search([('name', 'in', [
                        'Unit(s)', 'Unidad(es)'])])[0].id,
                'price_unit': float(rec.get(attr['valorUnitario'][ver])),
                'discount': discount,
                'xml_invoice': True,
            }
            if ver == '3.3':
                if 'Traslados' in rec.Impuestos.__dict__.keys():
                    taxes_33 = self.get_taxes_per_line_33(
                        rec.Impuestos.Traslados.Traslado, pre_data,
                        tax_in_line, line_index)
                    invoice_line.update(taxes_33['dict'])
                    tax_in_line = taxes_33['tax_in_line']
                line_index += 1
            else:
                invoice_line['invoice_line_tax_ids'] = [
                    (6, 0, pre_data['xfrs_ids'].keys())]
            invoice_line_ids.append((0, 0, invoice_line))
        if 'descuento' in xml.keys():
            price_unit = float(xml.get(attr['descuento'][ver]))
            invoice_line_ids.append((0, 0, {
                'name': 'Descuento',
                'price_unit': price_unit * -1 if price_unit > 0.0 else 0.0,
                'quantity': 0.0, 'xml_invoice': True,
            }))

        return {
            'idate': date_inv, 'tax_in_line': tax_in_line,
            'ilines': invoice_line_ids}

    @staticmethod
    def create_header_msg(subtotal, total):
        """ Creates header wrong message """
        return _(
            '<p>The Amount Subtotal must be: <span style="font-weight:500;'
            'text-decoration:underline;">%s</span> and Total: <span'
            ' style="font-weight:500;text-decoration:underline;">%s'
            '</span></p><b>Supplier Invoice has wrong data:</b><br>') % (
                subtotal, total)

    @api.multi
    def create_invoice(self, xml, ver, pdata, idata):
        """ It create the invoice with all the data obtained from the xml.
        But if have errors it create a draft invoice in another model with
        all the errors found. """
        attr, tcomp = self.get_cfdi_catalogs(['attr', 'tcomp'])
        reference = xml.get(attr['folio'][ver], '')
        dict_invoice = {
            'name': pdata['supplier'][0].name + (
                ' - ' if reference else '') + reference,
            'partner_id':
                pdata['supplier'][0].id if pdata['supplier'] else False,
            'reference': xml.get(attr['folio'][ver], ''),
            'date_invoice': (
                idata['idate'][:idata['idate'].find('T')] if idata[
                    'idate'] else idata['idate']),
            'currency_id':
                pdata['currency_id'][0].id if pdata['currency_id'] else (
                    self.env.user.company_id.currency_id.id),
            'invoice_line_ids': idata['ilines'],
            'type': 'in_invoice' if xml.get(attr['tipoDeComprobante'][
                ver]) == tcomp['ingreso'][ver] else 'in_refund',
            'state': 'check' if pdata['wrongdata_msg'] else 'pending'
        }
        if pdata['wrongdata_msg']:
            header_msg = self.create_header_msg(xml.get(
                attr['subTotal'][ver]), xml.get(attr['total'][ver]))
            if 'xfrs' in pdata['wrongdata_msg'].keys() and ver == '3.3':
                items = idata['tax_in_line'].items()
                pdata['wrongdata_msg']['xfrs'] += (
                    '<ul><li>%s</li></ul>' % ('; '.join([_(
                        '<b>%s</b> in invoice line: %s') % (tax, ', '.join([
                            str(x) for x in indexs
                        ])) for tax, indexs in items])))
            dict_invoice.update({'message_wrong_data': (
                header_msg + '<ul><li>%s</li></ul>') % ('</li><li>'.join(
                    pdata['wrongdata_msg'].values()))})
        invoice = self.create(dict_invoice)
        invoice._onchange_invoice_line_ids()
        invoice.write({'tax_line_ids': [
            (0, 0, ret) for ret in pdata['rets_ids'].values()]})
        invoice.tax_line_ids.write({'xml_invoice': True})
        return invoice

    @api.model
    def review_invoice(self, xml, ver, pdata, invoice):
        """ Reviews taxes repeated and wrong totals """
        attr = self.get_cfdi_catalogs(['attr'])
        total_xml = float(xml.get(attr['total'][ver]))
        if (not (invoice.amount_total + .05 > total_xml and
                 invoice.amount_total - .05 < total_xml)):
            if not invoice.message_wrong_data:
                header_msg = self.create_header_msg(
                    xml.get(attr['subTotal'][ver]), xml.get(attr['total'][ver])
                )
            else:
                header_msg = invoice.message_wrong_data
            invoice.write({
                'message_wrong_data': header_msg + _(
                    '<ul><li>Totals do not match</li></ul>'),
                'state': 'check'})
        return invoice

    @api.multi
    def create_xml_attachment(self, inv_id, xmlstr, xmlname):
        """ It creates the attachment file for the invoices creted. """
        self.env['ir.attachment'].create({
            'type': 'binary',
            'res_id': inv_id,
            'res_model': 'account.pre.invoice',
            'mimetype': 'application/xml',
            'datas_fname': xmlname + '.xml',
            'datas': base64.b64encode(xmlstr.encode('utf-8')),
            'name': xmlname + '.xml',
            'description': 'SAT XML',
        })

    # ----------------------------------------------------------------------- #

    @api.multi
    def get_data_validate_invoice(self):
        """ It gets the first data to obtain the xml and wrong invoice data """
        xml_attach = self.env['ir.attachment'].search([
            ('res_model', '=', self._name), ('res_id', '=', self.id),
            ('description', '=', 'SAT XML')])
        xml = objectify.fromstring(
            base64.decodestring(xml_attach[0].datas).lstrip(BOM_UTF8))
        ver = xml.get('version', False) or xml.get('Version', False)
        return [xml, ver]

    @api.multi
    def validate_invoice(self):
        """ It checks if the xml and wrong invoice matches and raises
        the erros. """
        attr, mxns, taxcatalog = self.get_cfdi_catalogs(
            ['attr', 'mxns', 'tax-catalog'])
        xml, ver = self.get_data_validate_invoice()
        error_msg = []
        currency = ('MXN' if xml.get('Moneda', '').lower(
        ) in mxns else xml.get('Moneda', '')) if xml.get(
            'Moneda', False) else 'USD'
        if self.currency_id.name != currency:
            error_msg.append(_('✘ The currency must be %s') % (currency))

        taxes = []
        if 'Traslados' in xml.Impuestos.__dict__.keys():
            for tax in xml.Impuestos.Traslados.Traslado:
                impuesto = tax.get(attr['impuesto'][ver])
                tasa = tax.get(attr['tasa'][ver], False)
                if ver == '3.3':
                    tasa = str(float(tasa) * 100) if tasa else tasa
                taxes.append(self.get_tax_name(
                    impuesto if ver == '3.2' else taxcatalog[impuesto], tasa))

        recordtaxes = [tax.name for tax in self.tax_line_ids]
        if any([tax for tax in taxes if tax not in recordtaxes]):
            error_msg.append(_(
                '✘ There are some transfer taxes with out adding: %s') % (
                    ', '.join(taxes)))

        accounts = [tax.account_id.id for tax in self.tax_line_ids]
        if not all(accounts):
            error_msg.append(_(
                '✘ There are undefined accounts on the tax lines'))

        total_xml = float(xml.get(attr['total'][ver]))
        if not (self.amount_total + .05 > total_xml and
                self.amount_total - .05 < total_xml):
            error_msg.append(_('✘ Totals do not match'))

        if any(error_msg):
            raise ValidationError(_(
                'There are some errors:\n%s') % '\n'.join(error_msg))
        self.write({
            'message_wrong_data': False,
            'state': 'pending',
        })

# -*- coding: utf-8 -*-
# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import sys
import imp
from xml.etree import ElementTree

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

imp.reload(sys)
# sys.setdefaultencoding('utf-8')


class AccountPreInvoiceWizard(models.TransientModel):
    _name = 'account.pre.invoice.wizard'

    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True,
        domain="[('type', '=', 'purchase')]")
    account_analytic_id = fields.Many2one(
        'account.analytic.account', 'Analytic Account')
    account_id = fields.Many2one(
        'account.account',
        string='Account',
    )
    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag', string='Analytic Tags')
    invisible_account = fields.Boolean(string='Account')
    invisible_account_analytic = fields.Boolean(
        string='Account Analytic',
    )
    invisible_account_analytic_tag = fields.Boolean(
        string='Analytic Tags',
    )

    @api.model
    def prepare_invoice_lines(self, items):
        lines = []
        for line in items:
            lines.append((0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'uom_id': line.uom_id.id,
                'invoice_line_tax_ids': [
                    (6, 0, line.invoice_line_tax_ids.ids)],
                'name': line.name,
                'account_id': (
                    line.account_id.id if line.account_id.id
                    else self.account_id.id),
                'account_analytic_id':
                    (line.account_analytic_id.id if line.account_analytic_id.id
                        else self.account_analytic_id.id),
                'analytic_tag_ids':
                    [(6, 0, (line.analytic_tag_ids.ids if
                     line.analytic_tag_ids.ids
                     else self.analytic_tag_ids.ids))],
            }))
        return lines

    @api.multi
    def create_invoices(self):
        obj_invoice = self.env['account.invoice']
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(
            self._context.get('active_ids'))
        invoices = []
        tag = '{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital'
        for record in records:
            if record.state != 'pending':
                raise ValidationError(
                    _('The pre-invoice has a pending validation or is already '
                      'linked to an invoice. Please check!'))
            fpos = record.partner_id.property_account_position_id
            xfile = self.env['ir.attachment'].search([
                ('res_model', '=', 'account.pre.invoice'),
                ('res_id', '=', record.id)])
            xml_str = base64.decodestring(xfile.datas)
            xml = ElementTree.fromstring(xml_str)
            url = '{http://www.sat.gob.mx/cfd/3}Complemento'
            complement_root = [e for e in xml if e.tag == url][0]
            complement_tag = [e for e in complement_root if e.tag == tag][0]
            invoice_id = obj_invoice.create({
                'partner_id': record.partner_id.id,
                'fiscal_position_id': fpos.id,
                'reference': record.reference,
                'journal_id': self.journal_id.id,
                'currency_id': record.currency_id.id,
                'account_id': fpos.map_account(
                    record.partner_id.property_account_payable_id).id,
                'type': 'in_invoice',
                'date_invoice': record.date_invoice,
                'invoice_line_ids': [
                    line for line in self.prepare_invoice_lines(
                        record.invoice_line_ids)],
                'date_stamped': complement_tag.get(
                    'FechaTimbrado', '').replace('T', ' '),
                'cfdi_uuid': complement_tag.get('UUID', ''),
                'xml_signed': ElementTree.tostring(xml, 'UTF-8'),
                'pre_invoice_linked': record.id,
            })
            invoice_id.action_invoice_open()
            invoices.append(invoice_id.id)
            record.invoice_id = invoice_id.id
            record.state = 'done'
            xfile.write({
                'res_model': 'account.invoice',
                'res_id': invoice_id.id,
            })
        return {
            'name': _('Invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'domain': [('id', 'in', invoices)],
            'type': 'ir.actions.act_window',
            'context': {
                'create': False,
                'delete': False
            }
        }

    @api.model
    def default_get(self, fields_aux):
        res = super(AccountPreInvoiceWizard, self).default_get(
            fields_aux)
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(
            self._context.get('active_ids'))
        map_rec = records.mapped('invoice_line_ids')
        account_ids = [
            e for e in map_rec if not e.account_id]
        account_analytic_ids = [
            e for e in map_rec if not e.account_analytic_id]
        account_analytic_tag_ids = [
            e for e in map_rec if not e.analytic_tag_ids]
        if account_ids:
            res['invisible_account'] = True
        if account_analytic_ids:
            res['invisible_account_analytic'] = True
        if account_analytic_tag_ids:
            res['invisible_account_analytic_tag'] = True
        return res

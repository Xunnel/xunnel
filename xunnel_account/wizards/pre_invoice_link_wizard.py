# -*- coding: utf-8 -*-
# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
from xml.etree import ElementTree
from odoo import api, fields, models, _


class PreInvoiceLinkWizard(models.TransientModel):
    _name = 'pre.invoice.link.wizard'

    uuid_pre_invoice = fields.Many2one(
        'ir.attachment', string='Pre Invoice UUID', domain=[], required=True)
    pre_invoice_data = fields.Html(default=False, readonly=True)

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(PreInvoiceLinkWizard, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'form':
            invoice = self.env[self._context.get('active_model')].search([
                ('id', '=', self._context.get('active_id'))])
            domain = {
                'partner': ('partner_id', '=', invoice.partner_id.id),
                'reference': ('reference', '=', invoice.reference),
                'subtotal': ('amount_untaxed', '=', invoice.amount_untaxed),
                'total': ('amount_total', '=', invoice.amount_total),
            }
            pre_invoices = self.env['account.pre.invoice'].search(
                domain.values())
            if not any(pre_invoices):
                del domain['reference']
                pre_invoices = self.env['account.pre.invoice'].search(
                    domain.values())
            uuids = self.env['ir.attachment'].search([
                ('res_model', '=', 'account.pre.invoice'),
                ('res_id', 'in', [
                    pre_invs.id for pre_invs in pre_invoices])])
            res['fields']['uuid_pre_invoice']['domain'] = [('id', 'in', [
                uuid.id for uuid in uuids])]
        return res

    @api.onchange('uuid_pre_invoice')
    def onchange_pre_invoice_data(self):
        self.pre_invoice_data = False
        if self.uuid_pre_invoice:
            pre_invoice = self.env['account.pre.invoice'].search(
                [('id', '=', self.uuid_pre_invoice.res_id)])
            self.pre_invoice_data = _(
                '<p><b>Name: </b>%s</p><p><b>Reference: </b>%s</p>') % (
                    pre_invoice.name, pre_invoice.reference)

    @api.multi
    def link_pre_invoice(self):
        invoice = self.env[self._context.get('active_model')].search([
            ('id', '=', self._context.get('active_id'))])
        tag = '{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital'
        attach = self.env['ir.attachment'].search(
            [('id', '=', self.uuid_pre_invoice.id)])
        xml_str = base64.decodestring(attach.datas)
        xml = ElementTree.fromstring(xml_str)
        url = '{http://www.sat.gob.mx/cfd/3}Complemento'
        complement_root = [x for x in xml if x.tag == url][0]
        complement_tag = [t for t in complement_root if t.tag == tag][0]
        invoice.write({
            'pre_invoice_linked': self.uuid_pre_invoice.res_id,
            'date_stamped': complement_tag.get(
                'FechaTimbrado', '').replace('T', ' '),
            'cfdi_uuid': complement_tag.get('UUID', ''),
            'xml_signed': ElementTree.tostring(xml, 'UTF-8'),
            'pre_invoices_found_msg': False,
        })
        self.env['account.pre.invoice'].browse(
            self.uuid_pre_invoice.res_id).write({
                'state': 'done',
                'account_invoice_id': self._context.get('active_id')})
        attach.write({'res_model': 'account.invoice', 'res_id': invoice.id})

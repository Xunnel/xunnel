# -*- coding: utf-8 -*-
# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    pre_invoice_linked = fields.Many2one(
        'account.pre.invoice', string='Pre Invoice Linked', readonly=True)
    pre_invoices_found_msg = fields.Char(readonly=True)

    @api.multi
    def check_pre_invoices(self):
        domain = {
            'partner': ('partner_id', '=', self.partner_id.id),
            'reference': ('reference', '=', self.reference),
        }

        def filter_by_total_untaxed(objs):
            return [pre_inv.id for pre_inv in objs if
                    pre_inv.amount_total == self.amount_total and
                    pre_inv.amount_untaxed == self.amount_untaxed]

        pre_inv_objs = self.env['account.pre.invoice'].search(domain.values())
        pre_invoices = filter_by_total_untaxed(pre_inv_objs)
        if not any(pre_invoices):
            del domain['reference']
            pre_inv_objs = self.env['account.pre.invoice'].search(
                domain.values())
            pre_invoices = filter_by_total_untaxed(pre_inv_objs)
        if any(pre_invoices):
            self.pre_invoices_found_msg = _(
                'There are XML attachments in pre invoices that match with '
                'this bill. Press "Link Inovice" to check them.')

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        self.check_pre_invoices()
        return res

    @api.multi
    def unlink_invoice(self):
        attach = self.env['ir.attachment'].search(
            [('res_id', '=', self.id), ('res_model', '=', 'account.invoice')])
        attach.write({'res_id': self.pre_invoice_linked,
                      'res_model': 'account.pre.invoice'})
        self.pre_invoice_linked.write({
            'state': 'pending', 'account_invoice_id': False})
        self.write({
            'pre_invoice_linked': False, 'date_stamped': False,
            'cfdi_uuid': False, 'xml_signed': False,
        })
        self.check_pre_invoices()

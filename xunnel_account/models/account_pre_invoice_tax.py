# -*- coding: utf-8 -*-
# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class AccountPreInvoiceTax(models.Model):
    _name = 'account.pre.invoice.tax'

    invoice_id = fields.Many2one(
        'account.pre.invoice', string='Invoice', ondelete='cascade',
        index=True)
    name = fields.Char(string='Tax Description', required=True)
    account_id = fields.Many2one(
        'account.account', string='Tax Account', domain=[
            ('deprecated', '=', False)])
    amount = fields.Float(default=0.0)
    xml_invoice = fields.Boolean(readonly=True, default=False)

    @api.multi
    def unlink(self):
        """ Avoid user delete tax from original xml """
        taxes_name = ['%s/%s' % (tax.name, tax.xml_invoice) for
                      tax in self.invoice_id.tax_line_ids if tax.xml_invoice]
        this_inv = '%s/%s' % (self.name, self.xml_invoice)
        if not self.xml_invoice or taxes_name.count(this_inv) > 1:
            super(AccountPreInvoiceTax, self).unlink()

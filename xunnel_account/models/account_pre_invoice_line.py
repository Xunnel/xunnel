# -*- coding: utf-8 -*-
# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class AccountPreInvoiceLine(models.Model):
    _name = 'account.pre.invoice.line'

    @api.one
    @api.depends(
        'price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id',
        'invoice_id.company_id', 'invoice_id.date_invoice')
    def _compute_price(self):
        """ It calculates the total with discounts and taxes. """
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(
                price, currency, self.quantity, product=self.product_id,
                partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes[
            'total_excluded'] if taxes else self.quantity * price
        if (self.invoice_id.currency_id and self.invoice_id.company_id and
                self.invoice_id.currency_id !=
                self.invoice_id.company_id.currency_id):
            price_subtotal_signed = self.invoice_id.currency_id.with_context(
                date=self.invoice_id.date_invoice).compute(
                    price_subtotal_signed,
                    self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign

    index = fields.Integer(readonly=True, string="N°")
    invoice_id = fields.Many2one(
        'account.pre.invoice', string='Invoice Reference',
        ondelete='cascade', index=True)
    company_id = fields.Many2one(
        'res.company', string='Company', related='invoice_id.company_id',
        store=True, readonly=True, related_sudo=False)
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Text(required=True)
    account_id = fields.Many2one(
        'account.account', string='Account', help="The income or expense "
        "account related to the selected product.", domain=[
            ('deprecated', '=', False)])
    account_analytic_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag', string='Analytic Tags')
    quantity = fields.Float(required=True, default=1.0)
    discount = fields.Float(
        string='Discount (%)', digits=dp.get_precision('Discount'),
        default=0.0)
    uom_id = fields.Many2one(
        'product.uom', string='Unit of Measure', ondelete='set null',
        index=True)
    price_unit = fields.Float(
        string='Unit Price', required=True, default=0.0)
    invoice_line_tax_ids = fields.Many2many(
        'account.tax', 'account_pre_invoice_line_tax', 'invoice_line_id',
        'tax_id', string='Taxes', domain=[
            ('type_tax_use', '!=', 'none'), '|',
            ('active', '=', False), ('active', '=', True)])
    price_subtotal = fields.Float(
        string='Amount', readonly=True, default=0.0, compute='_compute_price')
    price_subtotal_signed = fields.Float(
        string='Amount Signed', currency_field='company_currency_id',
        readonly=True, compute='_compute_price',
        help="Total amount in the currency of the company, negative"
        "for credit notes.")
    xml_invoice = fields.Boolean(readonly=True, default=False)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.invoice_id:
            return
        if not self.xml_invoice:
            part = self.invoice_id.partner_id
            if not part:
                warning = {
                    'title': _('Warning!'),
                    'message': _('You must first select a partner!')}
                return {'warning': warning}
            if not self.product_id:
                self.price_unit = 0.0
            else:
                self.uom_id = self.product_id.uom_po_id
                if part.lang:
                    product = self.product_id.with_context(lang=part.lang)
                else:
                    product = self.product_id

                account_id = (
                    product.property_account_expense_id or
                    product.categ_id.property_account_expense_categ_id or
                    False)
                self.account_id = account_id.id
                self.name = product.partner_ref
                if product.description_purchase:
                    self.name += '\n' + product.description_purchase
                elif product.description_sale:
                    self.name += '\n' + product.description_sale

                if (not self.uom_id or product.uom_id.category_id.id !=
                        self.uom_id.category_id.id):
                    self.uom_id = product.uom_id.id
                self.price_unit = product.standard_price

    @api.multi
    def unlink(self):
        """ Avoid user delete lines from original xml """
        if self.xml_invoice:
            self.invoice_id.invoice_line_id = [4, self.id]
        else:
            super(AccountPreInvoiceLine, self).unlink()

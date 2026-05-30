# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends('product_id', 'product_uom_id', 'move_id.pricelist_id')
    def _compute_price_unit(self):
        sale_lines = self.filtered('sale_line_ids')
        pricelist_lines = self.filtered(lambda line: line._use_invoice_pricelist_price())
        other_lines = self - sale_lines - pricelist_lines
        if other_lines:
            super(AccountMoveLine, other_lines)._compute_price_unit()
        for line in sale_lines:
            line.price_unit = line._get_price_unit_from_sale_line()
        for line in pricelist_lines:
            line.price_unit = line._get_price_from_invoice_pricelist(
                move=line.move_id,
                product=line.product_id,
                quantity=line.quantity or 1.0,
                uom=line.product_uom_id or line.product_id.uom_id,
            )

    def _get_price_unit_from_sale_line(self):
        self.ensure_one()
        sale_line = self.sale_line_ids[:1]
        return sale_line.price_unit if sale_line else self.price_unit

    def _use_invoice_pricelist_price(self):
        self.ensure_one()
        force = self.env.context.get('force_invoice_pricelist_price')
        return bool(
            self.move_id
            and self.move_id._use_invoice_pricelist()
            and self.display_type == 'product'
            and self.product_id
            and not self.sale_line_ids
            and (force or not self.is_imported)
        )

    @api.model
    def _get_price_from_invoice_pricelist(self, move, product, quantity=1.0, uom=None):
        pricelist = move.pricelist_id
        date = move.invoice_date or move.date or fields.Date.context_today(move)
        uom = uom or product.uom_id
        currency = move.currency_id or pricelist.currency_id or move.company_id.currency_id

        price = pricelist._get_product_price(
            product=product,
            quantity=quantity or 1.0,
            uom=uom,
            date=date,
            currency=currency,
        )

        product_taxes = product.taxes_id._filter_taxes_by_company(move.company_id)
        if product_taxes:
            price = product._get_tax_included_unit_price_from_price(
                price,
                product_taxes=product_taxes,
                fiscal_position=move.fiscal_position_id,
            )
        return price

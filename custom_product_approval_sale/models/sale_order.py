# -*- coding: utf-8 -*-
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('product_id')
    def _check_product_approved(self):
        for line in self:
            if line.product_id:
                line.product_id._ensure_approved_for_use()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        # Defense in depth: also block at confirmation time, in case a
        # line was created in a way that bypassed the line-level check
        # (e.g. bulk import, or the product was un-approved again after
        # being added to a still-draft quotation).
        for order in self:
            order.order_line.mapped('product_id')._ensure_approved_for_use()
        return super().action_confirm()

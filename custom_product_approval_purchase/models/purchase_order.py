# -*- coding: utf-8 -*-
from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.constrains('product_id')
    def _check_product_approved(self):
        for line in self:
            if line.product_id:
                line.product_id._ensure_approved_for_use()


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        # Defense in depth: also block at confirmation time.
        for order in self:
            order.order_line.mapped('product_id')._ensure_approved_for_use()
        return super().button_confirm()

# -*- coding: utf-8 -*-
from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.constrains('product_id')
    def _check_product_approved(self):
        for move in self:
            if move.product_id:
                move.product_id._ensure_approved_for_use()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        # Defense in depth: also block at validation time.
        for picking in self:
            picking.move_ids.mapped('product_id')._ensure_approved_for_use()
        return super().button_validate()

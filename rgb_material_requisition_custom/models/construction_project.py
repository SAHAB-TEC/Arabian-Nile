# -*- coding: utf-8 -*-
from odoo import fields, models


class ConstructionProject(models.Model):
    _inherit = "construction.project"

    # sale_project_stock.button_validate always reads this field on picking.project_id.
    # After switching project_id to construction.project, the attribute must exist
    # even when empty, otherwise every picking validation crashes.
    reinvoiced_sale_order_id = fields.Many2one(
        "sale.order",
        string="Reinvoiced Sales Order",
        copy=False,
        index=True,
        help="Technical compatibility with Odoo sale_project_stock. "
             "Not used by construction workflows.",
    )

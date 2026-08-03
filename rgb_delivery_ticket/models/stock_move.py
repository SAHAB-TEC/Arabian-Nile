# -*- coding: utf-8 -*-
from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    delivery_ticket_note = fields.Char(
        string="Ticket Notes",
        help="Notes printed on the Delivery Ticket line.",
    )

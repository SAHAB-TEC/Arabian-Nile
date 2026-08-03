# -*- coding: utf-8 -*-
from odoo import fields, models


class RequisitionRequestType(models.Model):
    _inherit = "requisition.request.type"

    ticket_status_color = fields.Selection(
        selection=[
            ("yellow", "Yellow"),
            ("orange", "Orange"),
            ("green", "Green"),
        ],
        string="Delivery Ticket Status Color",
        help="Color shown on the Delivery Ticket status circles (filled from the request).",
    )

# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_engineer = fields.Boolean(
        string="Is Engineer",
        default=False,
        index=True,
        help="Mark contacts who are engineers for attendance sheets and vendor bills.",
    )

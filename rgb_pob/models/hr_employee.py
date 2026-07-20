# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    pob_travel_eligible = fields.Boolean(
        string="Available for Oil Site Travel",
        default=False,
        help="If enabled, this employee can be selected on POB travel permits.",
        tracking=True,
    )

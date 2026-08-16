# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    daily_rate = fields.Monetary(
        related="contract_id.daily_rate",
        string="Daily Rate",
        readonly=False,
        currency_field="currency_id",
        help="Daily attendance rate from the employee current contract.",
    )

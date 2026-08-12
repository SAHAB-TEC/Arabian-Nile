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
    daily_rate = fields.Monetary(
        string="Daily Rate",
        currency_field="currency_id",
        help="Daily attendance rate used to compute monthly net salary.",
    )
    engineer_salary_line_ids = fields.One2many(
        "rgb.engineer.salary.line",
        "partner_id",
        string="Monthly Salaries",
    )

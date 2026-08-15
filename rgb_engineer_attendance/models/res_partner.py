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
    # Kept for migration / fallback; UI lives on hr.contract.
    daily_rate = fields.Monetary(
        string="Daily Rate",
        currency_field="currency_id",
        help="Deprecated on contact: use Daily Rate on the employee contract.",
    )
    engineer_salary_line_ids = fields.One2many(
        "rgb.engineer.salary.line",
        "partner_id",
        string="Monthly Salaries",
    )

    def write(self, vals):
        res = super().write(vals)
        if any(key in vals for key in ("is_engineer", "is_contractor")):
            contracts = self.env["hr.contract"].search([
                ("employee_id.work_contact_id", "in", self.ids),
            ])
            contracts._rgb_sync_wage_from_last_basic()
        return res

    def _rgb_get_daily_rate(self, company=None):
        """Daily rate from the engineer active contract, else partner fallback."""
        self.ensure_one()
        contract = self.env["hr.contract"]._rgb_get_engineer_contract(self, company=company)
        if contract and contract.daily_rate:
            return contract.daily_rate
        return self.daily_rate or 0.0

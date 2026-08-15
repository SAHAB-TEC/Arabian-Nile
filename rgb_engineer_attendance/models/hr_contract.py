# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    daily_rate = fields.Monetary(
        string="Daily Rate",
        currency_field="currency_id",
        help="Daily attendance rate used to compute monthly net salary.",
    )
    engineer_partner_id = fields.Many2one(
        related="employee_id.work_contact_id",
        string="Engineer Contact",
        store=True,
        index=True,
    )
    engineer_salary_line_ids = fields.One2many(
        related="employee_id.work_contact_id.engineer_salary_line_ids",
        string="Monthly Salaries",
        readonly=True,
    )
    last_basic_salary = fields.Monetary(
        string="Last Basic Salary",
        currency_field="currency_id",
        compute="_compute_last_salaries",
        store=True,
        help="Basic salary from the most recent monthly salary line.",
    )
    last_net_salary = fields.Monetary(
        string="Last Net Salary",
        currency_field="currency_id",
        compute="_compute_last_salaries",
        store=True,
        help="Net salary from the most recent monthly salary line.",
    )

    @api.depends(
        "engineer_salary_line_ids",
        "engineer_salary_line_ids.basic_salary",
        "engineer_salary_line_ids.net_salary",
        "engineer_salary_line_ids.year",
        "engineer_salary_line_ids.month",
    )
    def _compute_last_salaries(self):
        for contract in self:
            lines = contract.engineer_salary_line_ids.sorted(
                key=lambda line: (line.year or 0, int(line.month or 0), line.id),
                reverse=True,
            )
            last = lines[:1]
            contract.last_basic_salary = last.basic_salary if last else 0.0
            contract.last_net_salary = last.net_salary if last else 0.0

    @api.model
    def _rgb_contracts_for_engineer(self, partner, company=None):
        """Return contracts linked to the engineer partner via employee work contact."""
        if not partner:
            return self.browse()
        domain = [("employee_id.work_contact_id", "=", partner.id)]
        if company:
            domain.append(("company_id", "=", company.id))
        return self.search(domain)

    @api.model
    def _rgb_get_engineer_contract(self, partner, company=None):
        """Active/open contract for an engineer partner, else latest contract."""
        contracts = self._rgb_contracts_for_engineer(partner, company=company)
        if not contracts:
            return self.browse()
        open_contracts = contracts.filtered(lambda c: c.state == "open")
        if open_contracts:
            return open_contracts.sorted("date_start", reverse=True)[:1]
        return contracts.sorted(
            key=lambda c: (c.date_start or fields.Date.to_date("1970-01-01"), c.id),
            reverse=True,
        )[:1]

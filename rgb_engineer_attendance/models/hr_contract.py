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

    def write(self, vals):
        res = super().write(vals)
        if any(key in vals for key in ("last_basic_salary", "employee_id", "engineer_partner_id", "wage_type")):
            self._rgb_sync_wage_from_last_basic()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        contracts = super().create(vals_list)
        contracts._rgb_sync_wage_from_last_basic()
        return contracts

    @api.onchange("last_basic_salary", "employee_id", "engineer_partner_id", "wage_type")
    def _onchange_rgb_wage_from_last_basic(self):
        for contract in self:
            contract._rgb_apply_wage_from_last_basic_in_memory()

    def _rgb_related_partner(self):
        """Contact linked to the employee (work contact)."""
        self.ensure_one()
        return self.engineer_partner_id or self.employee_id.work_contact_id

    def _rgb_should_sync_wage_from_partner(self):
        """True when related contact is Engineer or Contractor."""
        self.ensure_one()
        partner = self._rgb_related_partner()
        if not partner:
            return False
        is_engineer = bool(getattr(partner, "is_engineer", False))
        is_contractor = bool(getattr(partner, "is_contractor", False))
        return is_engineer or is_contractor

    def _rgb_wage_field_name(self):
        """Field shown/used as contract wage (hourly_wage or wage)."""
        self.ensure_one()
        if hasattr(self, "_get_contract_wage_field"):
            return self._get_contract_wage_field() or "wage"
        if getattr(self, "wage_type", None) == "hourly":
            return "hourly_wage"
        return "wage"

    def _rgb_apply_wage_from_last_basic_in_memory(self):
        self.ensure_one()
        if self._rgb_should_sync_wage_from_partner() and self.last_basic_salary > 0:
            self[self._rgb_wage_field_name()] = self.last_basic_salary

    def _rgb_sync_wage_from_last_basic(self):
        """Set wage/hourly_wage = last_basic_salary for engineer/contractor contacts."""
        if self.env.context.get("rgb_skip_wage_sync"):
            return
        for contract in self:
            if not contract._rgb_should_sync_wage_from_partner():
                continue
            if not contract.last_basic_salary or contract.last_basic_salary <= 0:
                continue
            wage_field = contract._rgb_wage_field_name()
            current = contract[wage_field] or 0.0
            if current != contract.last_basic_salary:
                contract.with_context(rgb_skip_wage_sync=True).write({
                    wage_field: contract.last_basic_salary,
                })

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

# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    # Job titles allowed to sync wage from last_basic_salary.
    _RGB_WAGE_SYNC_JOB_KEYWORDS = ("عامل", "سائق", "worker", "driver")

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
        if any(key in vals for key in ("last_basic_salary", "job_id", "employee_id")):
            self._rgb_sync_wage_from_last_basic()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        contracts = super().create(vals_list)
        contracts._rgb_sync_wage_from_last_basic()
        return contracts

    @api.onchange("job_id", "last_basic_salary", "employee_id")
    def _onchange_rgb_wage_from_last_basic(self):
        for contract in self:
            if contract._rgb_is_worker_or_driver() and contract.last_basic_salary > 0:
                contract.wage = contract.last_basic_salary

    def _rgb_is_worker_or_driver(self):
        """True when contract/employee job is Worker (عامل) or Driver (سائق)."""
        self.ensure_one()
        job = self.job_id or self.employee_id.job_id
        if not job:
            return False
        name = (job.name or "").strip().lower()
        return any(keyword.lower() in name for keyword in self._RGB_WAGE_SYNC_JOB_KEYWORDS)

    def _rgb_sync_wage_from_last_basic(self):
        """Set wage = last_basic_salary for worker/driver contracts only."""
        if self.env.context.get("rgb_skip_wage_sync"):
            return
        for contract in self:
            if not contract._rgb_is_worker_or_driver():
                continue
            if contract.last_basic_salary > 0 and contract.wage != contract.last_basic_salary:
                contract.with_context(rgb_skip_wage_sync=True).write({
                    "wage": contract.last_basic_salary,
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

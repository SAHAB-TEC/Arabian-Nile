# -*- coding: utf-8 -*-
import calendar

from odoo import api, fields, models, _
from odoo.tools import float_round


class RgbEngineerSalaryLine(models.Model):
    _name = "rgb.engineer.salary.line"
    _description = "Engineer Monthly Salary"
    _order = "year desc, month desc, id desc"

    partner_id = fields.Many2one(
        "res.partner",
        string="Engineer",
        required=True,
        ondelete="cascade",
        index=True,
        domain="[('is_engineer', '=', True)]",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    month = fields.Selection(
        selection=[
            ("1", "January"),
            ("2", "February"),
            ("3", "March"),
            ("4", "April"),
            ("5", "May"),
            ("6", "June"),
            ("7", "July"),
            ("8", "August"),
            ("9", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ],
        string="Month",
        required=True,
        index=True,
    )
    year = fields.Integer(string="Year", required=True, index=True)
    month_name = fields.Char(string="Month Name", compute="_compute_month_name", store=True)
    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")
    days_count = fields.Integer(string="Attendance Days", readonly=True)
    daily_rate = fields.Monetary(
        string="Daily Rate",
        currency_field="currency_id",
        readonly=True,
    )
    net_salary = fields.Monetary(
        string="Net Salary",
        currency_field="currency_id",
        readonly=True,
        help="Sum of attendance days across all sheets in this month × daily rate.",
    )
    basic_salary = fields.Monetary(
        string="Basic Salary",
        currency_field="currency_id",
        readonly=True,
        help="Computed from monthly net salary using Libyan payroll reverse formulas.",
    )
    attendance_sheet_ids = fields.Many2many(
        "rgb.attendance.sheet",
        "rgb_salary_line_attendance_rel",
        "salary_line_id",
        "sheet_id",
        string="Attendance Sheets",
        readonly=True,
    )

    _sql_constraints = [
        (
            "uniq_partner_month_year_company",
            "unique(partner_id, month, year, company_id)",
            "A salary line already exists for this engineer and month.",
        ),
    ]

    @api.depends("month", "year")
    def _compute_month_name(self):
        month_names = dict(self._fields["month"].selection)
        for line in self:
            if line.month and line.year:
                line.month_name = f"{month_names.get(line.month, '')} {line.year}"
            else:
                line.month_name = ""

    # Reverse net → basic constants from customer workbook (ODOO.xlsx, Sheet2!D17).
    _NET_BASIC_TIER1_MAX = 937.33
    _NET_BASIC_TIER1_DIVISOR = 0.7547861875
    _NET_BASIC_TIER2_MAX = 11479.41
    _NET_BASIC_TIER2_OFFSET = 50.25
    _NET_BASIC_TIER2_DIVISOR = 0.714322375
    _NET_BASIC_TIER3_OFFSET = 2752.592
    _NET_BASIC_TIER3_DIVISOR = 0.8895

    @api.model
    def _compute_basic_salary_from_net(self, net_salary):
        """Reverse-calculate basic salary from monthly net salary.

        Applied on the aggregated monthly net (days × daily rate), not per day.
        Formulas match the customer payroll workbook reverse brackets.
        """
        net = net_salary or 0.0
        if net <= 0:
            return 0.0
        if net <= self._NET_BASIC_TIER1_MAX:
            basic = net / self._NET_BASIC_TIER1_DIVISOR
        elif net <= self._NET_BASIC_TIER2_MAX:
            basic = (net - self._NET_BASIC_TIER2_OFFSET) / self._NET_BASIC_TIER2_DIVISOR
        else:
            basic = (net + self._NET_BASIC_TIER3_OFFSET) / self._NET_BASIC_TIER3_DIVISOR
        return float_round(basic, precision_digits=2)

    @api.model
    def sync_from_attendance(self, engineer, month, year, company=None):
        """Rebuild/update one monthly salary line from all sheets of the engineer."""
        if not engineer or not month or not year:
            return self.browse()
        company = company or self.env.company
        Sheet = self.env["rgb.attendance.sheet"]
        sheets = Sheet.search([
            ("engineer_id", "=", engineer.id),
            ("month", "=", month),
            ("year", "=", int(year)),
            ("company_id", "=", company.id),
            ("state", "!=", "cancel"),
        ])
        # Aggregate only generated (submitted+) sheets, plus any still in the
        # current generate transaction already flipped to to_approve.
        sheets = sheets.filtered(lambda s: s.state in ("to_approve", "approved", "invoiced"))
        line = self.search([
            ("partner_id", "=", engineer.id),
            ("month", "=", month),
            ("year", "=", int(year)),
            ("company_id", "=", company.id),
        ], limit=1)

        if not sheets:
            if line:
                line.unlink()
            self._rgb_refresh_contract_last_salaries(engineer, company=company)
            return self.browse()

        days_count = sum(sheets.mapped("days_count"))
        daily_rate = engineer._rgb_get_daily_rate(company=company)
        net_salary = days_count * daily_rate
        basic_salary = self._compute_basic_salary_from_net(net_salary)

        date_start, date_end = self._attendance_date_bounds(sheets, month, year)
        vals = {
            "partner_id": engineer.id,
            "company_id": company.id,
            "currency_id": engineer.currency_id.id or company.currency_id.id,
            "month": month,
            "year": int(year),
            "date_start": date_start,
            "date_end": date_end,
            "days_count": days_count,
            "daily_rate": daily_rate,
            "net_salary": net_salary,
            "basic_salary": basic_salary,
            "attendance_sheet_ids": [(6, 0, sheets.ids)],
        }
        if line:
            line.write(vals)
        else:
            line = self.create(vals)
        self._rgb_refresh_contract_last_salaries(engineer, company=company)
        return line

    @api.model
    def _rgb_refresh_contract_last_salaries(self, engineer, company=None):
        """Recompute last basic/net on contracts linked to this engineer."""
        contracts = self.env["hr.contract"]._rgb_contracts_for_engineer(
            engineer, company=company
        )
        if contracts:
            contracts._compute_last_salaries()
            contracts._rgb_sync_wage_from_last_basic()

    @api.model
    def _attendance_date_bounds(self, sheets, month, year):
        """First/last marked attendance day across aggregated sheets."""
        month_i = int(month)
        year_i = int(year)
        days_in_month = calendar.monthrange(year_i, month_i)[1]
        marked = []
        for sheet in sheets:
            for day in range(1, days_in_month + 1):
                if getattr(sheet, f"day_{day}", False):
                    marked.append(day)
        if not marked:
            return (
                fields.Date.to_date(f"{year_i:04d}-{month_i:02d}-01"),
                fields.Date.to_date(f"{year_i:04d}-{month_i:02d}-{days_in_month:02d}"),
            )
        return (
            fields.Date.to_date(f"{year_i:04d}-{month_i:02d}-{min(marked):02d}"),
            fields.Date.to_date(f"{year_i:04d}-{month_i:02d}-{max(marked):02d}"),
        )

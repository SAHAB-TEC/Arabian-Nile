# -*- coding: utf-8 -*-
import calendar

from odoo import api, fields, models, _


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
        help="Computed from net salary using Libyan payroll brackets (pending client formulas).",
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

    @api.model
    def _compute_basic_salary_from_net(self, net_salary):
        """Compute basic salary from net salary using Libyan payroll brackets.

        TODO(client-formulas): Replace this stub when the customer provides the
        exact reverse-calculation formulas for the three net-salary brackets:
          - net < 1000
          - 1000 <= net <= 16000
          - net > 16000
        Example shared by customer: Daily/Net amount 900 → Basic 1192.33
        (first bracket). Until then basic_salary stays 0.0.
        """
        # TODO(client-formulas): implement bracket formulas from customer.
        return 0.0

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
            return self.browse()

        days_count = sum(sheets.mapped("days_count"))
        daily_rate = engineer.daily_rate or 0.0
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
            return line
        return self.create(vals)

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

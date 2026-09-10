# -*- coding: utf-8 -*-
import calendar

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class RgbAttendanceSheet(models.Model):
    _name = "rgb.attendance.sheet"
    _description = "Engineer Attendance Sheet"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "year desc, month desc, id desc"

    _engineer_domain = "[('is_engineer', '=', True)]"
    _client_company_domain = "[('is_company', '=', True), ('is_engineer', '=', False)]"
    _ATTENDANCE_DAY_TYPE = [
        ("r", "R"),
        ("t", "T"),
    ]

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
        tracking=True,
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        tracking=True,
        domain="[('company_id', '=', company_id)]",
        required=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("to_approve", "To Approve"),
            ("approved", "Approved"),
            ("invoiced", "Invoiced"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    engineer_id = fields.Many2one(
        "res.partner",
        string="Engineer",
        required=True,
        domain=_engineer_domain,
        tracking=True,
        check_company=True,
    )
    partner_company_id = fields.Many2one(
        "res.partner",
        string="Client Company",
        required=True,
        domain=_client_company_domain,
        tracking=True,
        help="Client / operator company.",
    )
    well_id = fields.Many2one(
        "workover.well",
        string="Well",
        tracking=True,
        domain="['|', ('rig_id', '=', rig_id), ('rig_id', '=', False)]",
    )
    rig_id = fields.Many2one(
        "workover.rig",
        string="Rig",
        tracking=True,
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
        default=lambda self: str(fields.Date.context_today(self).month),
        tracking=True,
    )
    year = fields.Integer(
        string="Year",
        required=True,
        default=lambda self: fields.Date.context_today(self).year,
        tracking=True,
    )
    period_label = fields.Char(compute="_compute_period_label", store=True)
    days_in_month = fields.Integer(compute="_compute_days_in_month")
    days_count = fields.Integer(
        string="Number of Days",
        compute="_compute_days_count",
        store=True,
        tracking=True,
    )
    approver_id = fields.Many2one(
        "res.users",
        string="Approved By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    approval_date = fields.Datetime(readonly=True, copy=False, tracking=True)

    day_1 = fields.Boolean(string="1")
    day_2 = fields.Boolean(string="2")
    day_3 = fields.Boolean(string="3")
    day_4 = fields.Boolean(string="4")
    day_5 = fields.Boolean(string="5")
    day_6 = fields.Boolean(string="6")
    day_7 = fields.Boolean(string="7")
    day_8 = fields.Boolean(string="8")
    day_9 = fields.Boolean(string="9")
    day_10 = fields.Boolean(string="10")
    day_11 = fields.Boolean(string="11")
    day_12 = fields.Boolean(string="12")
    day_13 = fields.Boolean(string="13")
    day_14 = fields.Boolean(string="14")
    day_15 = fields.Boolean(string="15")
    day_16 = fields.Boolean(string="16")
    day_17 = fields.Boolean(string="17")
    day_18 = fields.Boolean(string="18")
    day_19 = fields.Boolean(string="19")
    day_20 = fields.Boolean(string="20")
    day_21 = fields.Boolean(string="21")
    day_22 = fields.Boolean(string="22")
    day_23 = fields.Boolean(string="23")
    day_24 = fields.Boolean(string="24")
    day_25 = fields.Boolean(string="25")
    day_26 = fields.Boolean(string="26")
    day_27 = fields.Boolean(string="27")
    day_28 = fields.Boolean(string="28")
    day_29 = fields.Boolean(string="29")
    day_30 = fields.Boolean(string="30")
    day_31 = fields.Boolean(string="31")
    day_1_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="1 Type")
    day_2_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="2 Type")
    day_3_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="3 Type")
    day_4_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="4 Type")
    day_5_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="5 Type")
    day_6_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="6 Type")
    day_7_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="7 Type")
    day_8_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="8 Type")
    day_9_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="9 Type")
    day_10_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="10 Type")
    day_11_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="11 Type")
    day_12_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="12 Type")
    day_13_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="13 Type")
    day_14_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="14 Type")
    day_15_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="15 Type")
    day_16_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="16 Type")
    day_17_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="17 Type")
    day_18_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="18 Type")
    day_19_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="19 Type")
    day_20_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="20 Type")
    day_21_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="21 Type")
    day_22_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="22 Type")
    day_23_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="23 Type")
    day_24_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="24 Type")
    day_25_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="25 Type")
    day_26_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="26 Type")
    day_27_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="27 Type")
    day_28_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="28 Type")
    day_29_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="29 Type")
    day_30_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="30 Type")
    day_31_type = fields.Selection(_ATTENDANCE_DAY_TYPE, string="31 Type")

    @api.onchange(
        "day_1", "day_2", "day_3", "day_4", "day_5", "day_6", "day_7", "day_8", "day_9", "day_10",
        "day_11", "day_12", "day_13", "day_14", "day_15", "day_16", "day_17", "day_18", "day_19", "day_20",
        "day_21", "day_22", "day_23", "day_24", "day_25", "day_26", "day_27", "day_28", "day_29", "day_30", "day_31",
    )
    def _onchange_attendance_days(self):
        for day in range(1, 32):
            if not self[f"day_{day}"]:
                self[f"day_{day}_type"] = False

    @api.constrains(
        "month", "year", "days_in_month",
        "day_1", "day_2", "day_3", "day_4", "day_5", "day_6", "day_7", "day_8", "day_9", "day_10",
        "day_11", "day_12", "day_13", "day_14", "day_15", "day_16", "day_17", "day_18", "day_19", "day_20",
        "day_21", "day_22", "day_23", "day_24", "day_25", "day_26", "day_27", "day_28", "day_29", "day_30", "day_31",
        "day_1_type", "day_2_type", "day_3_type", "day_4_type", "day_5_type", "day_6_type", "day_7_type", "day_8_type",
        "day_9_type", "day_10_type", "day_11_type", "day_12_type", "day_13_type", "day_14_type", "day_15_type",
        "day_16_type", "day_17_type", "day_18_type", "day_19_type", "day_20_type", "day_21_type", "day_22_type",
        "day_23_type", "day_24_type", "day_25_type", "day_26_type", "day_27_type", "day_28_type", "day_29_type",
        "day_30_type", "day_31_type",
    )
    def _check_day_types(self):
        for sheet in self:
            for day in range(1, sheet.days_in_month + 1):
                if getattr(sheet, f"day_{day}") and not getattr(sheet, f"day_{day}_type"):
                    raise ValidationError(
                        _("Select attendance type (R or T) for day %(day)s.", day=day)
                    )

    @api.depends("month", "year")
    def _compute_period_label(self):
        month_names = dict(self._fields["month"].selection)
        for sheet in self:
            if sheet.month and sheet.year:
                sheet.period_label = f"{month_names.get(sheet.month, '')} {sheet.year}"
            else:
                sheet.period_label = ""

    @api.depends("month", "year")
    def _compute_days_in_month(self):
        for sheet in self:
            if sheet.month and sheet.year:
                sheet.days_in_month = calendar.monthrange(int(sheet.year), int(sheet.month))[1]
            else:
                sheet.days_in_month = 31

    @api.depends(
        "month", "year", "days_in_month",
        "day_1", "day_2", "day_3", "day_4", "day_5", "day_6", "day_7", "day_8", "day_9", "day_10",
        "day_11", "day_12", "day_13", "day_14", "day_15", "day_16", "day_17", "day_18", "day_19", "day_20",
        "day_21", "day_22", "day_23", "day_24", "day_25", "day_26", "day_27", "day_28", "day_29", "day_30", "day_31",
    )
    def _compute_days_count(self):
        for sheet in self:
            total = 0
            for day in range(1, sheet.days_in_month + 1):
                if getattr(sheet, f"day_{day}", False):
                    total += 1
            sheet.days_count = total

    @api.onchange("well_id")
    def _onchange_well_id(self):
        if self.well_id and self.well_id.rig_id:
            self.rig_id = self.well_id.rig_id

    @api.onchange("rig_id")
    def _onchange_rig_id(self):
        if self.well_id and self.well_id.rig_id and self.well_id.rig_id != self.rig_id:
            self.well_id = False

    @api.constrains("engineer_id")
    def _check_engineer_partner(self):
        for sheet in self:
            if sheet.engineer_id and not sheet.engineer_id.is_engineer:
                raise ValidationError(
                    _("%(partner)s is not marked as an engineer.", partner=sheet.engineer_id.display_name)
                )

    @api.constrains("engineer_id", "partner_company_id", "well_id", "rig_id", "month", "year")
    def _check_unique_period(self):
        for sheet in self:
            duplicate = self.search([
                ("id", "!=", sheet.id),
                ("engineer_id", "=", sheet.engineer_id.id),
                ("partner_company_id", "=", sheet.partner_company_id.id),
                ("well_id", "=", sheet.well_id.id),
                ("rig_id", "=", sheet.rig_id.id),
                ("month", "=", sheet.month),
                ("year", "=", sheet.year),
                ("state", "!=", "cancel"),
            ], limit=1)
            if duplicate:
                raise ValidationError(
                    _("An attendance sheet already exists for this engineer, company, well, rig and period (%(period)s).")
                    % {"period": sheet.period_label}
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("rgb.attendance.sheet") or _("New")
        return super().create(vals_list)

    def write(self, vals):
        allowed_after_submit = {"state", "approver_id", "approval_date", "message_main_attachment_id"}
        if not self.env.user.has_group("rgb_engineer_attendance.group_rgb_attendance_manager"):
            for sheet in self:
                if sheet.state != "draft" and set(vals) - allowed_after_submit:
                    raise UserError(_("You cannot modify an attendance sheet after it has been submitted."))
        return super().write(vals)

    def _check_editable(self):
        self.ensure_one()
        if self.state not in ("draft",):
            raise UserError(_("Only draft attendance sheets can be edited."))

    def action_submit(self):
        """Submit for approval (Generate / Confirm) and sync monthly salary."""
        for sheet in self:
            sheet._check_editable()
            if sheet.days_count <= 0:
                raise UserError(_("Select at least one attendance day before submitting."))
            if not sheet.engineer_id._rgb_get_daily_rate(company=sheet.company_id):
                raise UserError(_(
                    "Set a Daily Rate on the employee contract of %(engineer)s before generating.",
                    engineer=sheet.engineer_id.display_name,
                ))
            sheet._check_day_types()
            sheet.state = "to_approve"
            sheet.message_post(body=_("Attendance sheet submitted for approval (%(days)s days).") % {"days": sheet.days_count})
            sheet._sync_engineer_monthly_salary()
            approvers = self.env.ref("rgb_engineer_attendance.group_rgb_attendance_approver").users
            for user in approvers:
                sheet.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=user.id,
                    summary=_("Approve attendance sheet %s") % sheet.name,
                    note=_("Please review and approve attendance for %(engineer)s — %(days)s days.") % {
                        "engineer": sheet.engineer_id.display_name,
                        "days": sheet.days_count,
                    },
                )
        return True

    def _sync_engineer_monthly_salary(self):
        """Aggregate all sheets for the same engineer + month into one salary line."""
        SalaryLine = self.env["rgb.engineer.salary.line"]
        for sheet in self:
            SalaryLine.sync_from_attendance(
                sheet.engineer_id,
                sheet.month,
                sheet.year,
                company=sheet.company_id,
            )
    def action_approve(self):
        if not self.env.user.has_group("rgb_engineer_attendance.group_rgb_attendance_approver"):
            raise UserError(_("You are not allowed to approve attendance sheets."))
        for sheet in self.filtered(lambda s: s.state == "to_approve"):
            sheet.write({
                "state": "approved",
                "approver_id": self.env.uid,
                "approval_date": fields.Datetime.now(),
            })
            sheet.activity_ids.filtered(
                lambda act: act.summary and "Approve attendance" in (act.summary or "")
            ).action_done()
            sheet.message_post(body=_("Attendance approved by %s.") % self.env.user.display_name)
        return True

    def action_cancel(self):
        for sheet in self:
            sheet.state = "cancel"
            sheet._sync_engineer_monthly_salary()
        return True

    def action_reset_draft(self):
        manager = self.env.user.has_group("rgb_engineer_attendance.group_rgb_attendance_manager")
        if not manager:
            raise UserError(_("Only attendance managers can reset to draft."))
        self.write({"state": "draft", "approver_id": False, "approval_date": False})
        return True

    def _get_day_values(self):
        """Return list of booleans for each calendar day (for reports)."""
        self.ensure_one()
        return [bool(getattr(self, f"day_{day}", False)) for day in range(1, 32)]

    def _get_day_type_values(self):
        """Return list of type codes (r/t/False) for each calendar day (for reports)."""
        self.ensure_one()
        return [getattr(self, f"day_{day}_type", False) for day in range(1, 32)]

    def _get_day_display(self, day):
        """Return display label for a day cell (e.g. R, T, or empty)."""
        self.ensure_one()
        if not getattr(self, f"day_{day}", False):
            return ""
        day_type = getattr(self, f"day_{day}_type", False)
        return dict(self._ATTENDANCE_DAY_TYPE).get(day_type, "")

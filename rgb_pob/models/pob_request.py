# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class PobRequest(models.Model):
    _name = "pob.request"
    _description = "POB Travel Permit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, id desc"
    _rec_name = "name"

    name = fields.Char(
        string="Serial Number",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        tracking=True,
        domain="[('pob_travel_eligible', '=', True)]",
        index=True,
    )
    department_id = fields.Many2one(
        related="employee_id.department_id",
        store=True,
        readonly=True,
    )
    job_id = fields.Many2one(
        related="employee_id.job_id",
        store=True,
        readonly=True,
    )
    well_id = fields.Many2one(
        "pob.well",
        string="Well",
        required=True,
        tracking=True,
        index=True,
    )
    rig_id = fields.Many2one(
        "pob.rig",
        string="Rig / Location",
        required=True,
        tracking=True,
        domain="[('well_id', '=', well_id)]",
        index=True,
    )
    duration_days = fields.Integer(
        string="Duration (Days)",
        required=True,
        default=15,
        tracking=True,
    )
    date_start = fields.Date(
        string="Start Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    date_end = fields.Date(
        string="Expected End Date",
        compute="_compute_date_end",
        store=True,
        tracking=True,
    )
    approved_extension_days = fields.Integer(
        string="Approved Extension Days",
        compute="_compute_approved_extension_days",
        store=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("pending_operations", "Pending Operations"),
            ("pending_hse_rig", "Pending HSE / Rig"),
            ("active_onboard", "Active / Onboard"),
            ("under_extension", "Under Extension"),
            ("expired_closed", "Expired / Closed"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
        index=True,
    )
    alert_date = fields.Date(
        string="Alert Date",
        compute="_compute_alert_date",
        store=True,
    )
    alert_sent = fields.Boolean(string="Expiry Alert Sent", default=False, copy=False)
    alert_level = fields.Selection(
        selection=[
            ("ok", "OK"),
            ("warning", "Warning (≤4 days)"),
            ("critical", "Critical (≤1 day)"),
            ("expired", "Expired"),
        ],
        string="Alert Level",
        compute="_compute_alert_level",
        store=True,
    )
    days_remaining = fields.Integer(
        string="Days Remaining",
        compute="_compute_alert_level",
        store=True,
    )
    extension_ids = fields.One2many(
        "pob.extension",
        "request_id",
        string="Extensions",
    )
    extension_count = fields.Integer(compute="_compute_extension_count")
    notes = fields.Text(string="Notes")
    rejection_reason = fields.Text(string="Rejection Reason", copy=False)
    is_locked = fields.Boolean(
        compute="_compute_is_locked",
        help="Technical: basic fields locked after draft / during extension.",
    )

    @api.depends("extension_ids", "extension_ids.state", "extension_ids.extension_days")
    def _compute_approved_extension_days(self):
        for record in self:
            record.approved_extension_days = sum(
                record.extension_ids.filtered(lambda e: e.state == "approved").mapped(
                    "extension_days"
                )
            )

    @api.depends("date_start", "duration_days", "approved_extension_days")
    def _compute_date_end(self):
        for record in self:
            if record.date_start and record.duration_days:
                total_days = record.duration_days + (record.approved_extension_days or 0)
                # Inclusive duration: start + (days - 1)
                record.date_end = record.date_start + relativedelta(days=max(total_days - 1, 0))
            else:
                record.date_end = False

    @api.depends("date_end")
    def _compute_alert_date(self):
        for record in self:
            record.alert_date = (
                record.date_end - relativedelta(days=4) if record.date_end else False
            )

    @api.depends("date_end", "state")
    def _compute_alert_level(self):
        today = fields.Date.context_today(self)
        for record in self:
            if not record.date_end:
                record.alert_level = "ok"
                record.days_remaining = 0
                continue
            remaining = (record.date_end - today).days
            record.days_remaining = remaining
            if record.state == "expired_closed" or remaining < 0:
                record.alert_level = "expired"
            elif remaining <= 1 and record.state in ("active_onboard", "under_extension"):
                record.alert_level = "critical"
            elif remaining <= 4 and record.state in ("active_onboard", "under_extension"):
                record.alert_level = "warning"
            else:
                record.alert_level = "ok"

    def _compute_extension_count(self):
        for record in self:
            record.extension_count = len(record.extension_ids)

    @api.depends("state")
    def _compute_is_locked(self):
        for record in self:
            record.is_locked = record.state not in ("draft",)

    @api.onchange("well_id")
    def _onchange_well_id(self):
        if self.rig_id and self.rig_id.well_id != self.well_id:
            self.rig_id = False

    @api.constrains("duration_days")
    def _check_duration_days(self):
        for record in self:
            if record.duration_days < 1:
                raise ValidationError(_("Duration must be at least 1 day."))

    @api.constrains("employee_id")
    def _check_employee_eligible(self):
        for record in self:
            if record.employee_id and not record.employee_id.pob_travel_eligible:
                raise ValidationError(
                    _(
                        "Employee '%(employee)s' is not marked as available for oil site travel.",
                        employee=record.employee_id.display_name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("pob.request") or _("New")
                )
        return super().create(vals_list)

    def write(self, vals):
        locked_fields = {
            "employee_id",
            "well_id",
            "rig_id",
            "duration_days",
            "date_start",
            "name",
        }
        if locked_fields & set(vals):
            for record in self:
                if record.state != "draft" and not self.env.context.get("pob_force_write"):
                    raise UserError(
                        _(
                            "Basic POB fields can only be edited while the permit is in Draft."
                        )
                    )
        # Reset alert flag when end date effectively changes via extensions
        if "alert_sent" not in vals and any(
            f in vals for f in ("duration_days", "date_start")
        ):
            vals = dict(vals, alert_sent=False)
        return super().write(vals)

    # -------------------------------------------------------------------------
    # Approval workflow
    # -------------------------------------------------------------------------
    def action_submit(self):
        for record in self:
            if record.state != "draft":
                raise UserError(_("Only draft permits can be submitted."))
            record._validate_required_fields()
            record.state = "pending_operations"
            record._notify_group(
                "rgb_pob.group_pob_operations",
                summary=_("POB Operations Approval"),
                note=_(
                    "Please approve Operations stage for POB %(name)s (%(employee)s).",
                    name=record.name,
                    employee=record.employee_id.display_name,
                ),
                mail_template_xmlid="rgb_pob.mail_template_pob_operations_approval",
                activity_type_xmlid="rgb_pob.mail_activity_pob_approval",
            )
            record.message_post(body=_("Submitted for Operations approval."))
        return True

    def action_approve_operations(self):
        for record in self:
            if record.state != "pending_operations":
                raise UserError(_("Only permits pending Operations can be approved here."))
            record._check_group("rgb_pob.group_pob_operations")
            record._done_activities()
            record.state = "pending_hse_rig"
            record._notify_group(
                "rgb_pob.group_pob_hse",
                summary=_("POB HSE / Rig Approval"),
                note=_(
                    "Please approve HSE / Rig stage for POB %(name)s (%(employee)s).",
                    name=record.name,
                    employee=record.employee_id.display_name,
                ),
                mail_template_xmlid="rgb_pob.mail_template_pob_hse_approval",
                activity_type_xmlid="rgb_pob.mail_activity_pob_approval",
            )
            record.message_post(body=_("Approved by Operations. Waiting for HSE / Rig."))
        return True

    def action_approve_hse(self):
        for record in self:
            if record.state != "pending_hse_rig":
                raise UserError(_("Only permits pending HSE / Rig can be approved here."))
            record._check_group("rgb_pob.group_pob_hse")
            record._done_activities()
            record.with_context(pob_force_write=True).write(
                {
                    "state": "active_onboard",
                    "alert_sent": False,
                }
            )
            record.message_post(
                body=_("Approved by HSE / Rig. Permit is now Active / Onboard.")
            )
        return True

    def action_reject(self):
        for record in self:
            if record.state not in ("pending_operations", "pending_hse_rig"):
                raise UserError(_("Only pending permits can be rejected."))
            record._done_activities()
            record.write(
                {
                    "state": "draft",
                    "rejection_reason": record.rejection_reason
                    or _("Rejected and returned to Draft."),
                }
            )
            record.message_post(
                body=_(
                    "Rejected and returned to Draft.%(reason)s",
                    reason=(
                        ("\n" + record.rejection_reason) if record.rejection_reason else ""
                    ),
                )
            )
        return True

    def action_reset_draft(self):
        for record in self:
            if record.state == "expired_closed":
                raise UserError(_("Expired / Closed permits cannot be reset."))
            if record.state == "under_extension":
                raise UserError(_("Cancel or resolve the extension before resetting."))
            record._done_activities()
            record.state = "draft"
            record.message_post(body=_("Reset to Draft."))
        return True

    def action_open_extension_wizard(self):
        self.ensure_one()
        if self.state != "active_onboard":
            raise UserError(_("Extensions can only be requested for Active / Onboard permits."))
        if not (
            self.env.user.has_group("rgb_pob.group_pob_manager")
            or self.env.user.has_group("rgb_pob.group_pob_supervisor")
        ):
            raise UserError(_("You are not allowed to request a POB extension."))
        return {
            "name": _("Request Extension"),
            "type": "ir.actions.act_window",
            "res_model": "pob.extension.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_request_id": self.id,
            },
        }

    def action_view_extensions(self):
        self.ensure_one()
        return {
            "name": _("Extensions"),
            "type": "ir.actions.act_window",
            "res_model": "pob.extension",
            "view_mode": "list,form",
            "domain": [("request_id", "=", self.id)],
            "context": {"default_request_id": self.id},
        }

    def action_approve_pending_extension(self):
        self.ensure_one()
        pending = self.extension_ids.filtered(lambda e: e.state == "pending")
        if not pending:
            raise UserError(_("No pending extension to approve."))
        pending[:1].action_approve()
        return True

    def action_reject_pending_extension(self):
        self.ensure_one()
        pending = self.extension_ids.filtered(lambda e: e.state == "pending")
        if not pending:
            raise UserError(_("No pending extension to reject."))
        pending[:1].action_reject()
        return True

    # -------------------------------------------------------------------------
    # Extension helpers
    # -------------------------------------------------------------------------
    def _create_extension_request(self, extension_days, reason):
        self.ensure_one()
        if self.state != "active_onboard":
            raise UserError(_("Extensions can only be requested for Active / Onboard permits."))
        if extension_days < 1:
            raise ValidationError(_("Additional days must be at least 1."))
        if not reason:
            raise ValidationError(_("Extension reason is required."))
        if self.extension_ids.filtered(lambda e: e.state == "pending"):
            raise UserError(_("There is already a pending extension for this permit."))

        extension = self.env["pob.extension"].create(
            {
                "request_id": self.id,
                "extension_days": extension_days,
                "reason": reason,
                "state": "pending",
            }
        )
        self.state = "under_extension"
        self._notify_group(
            "rgb_pob.group_pob_operations",
            summary=_("POB Extension Approval"),
            note=_(
                "Extension of %(days)s day(s) requested for POB %(name)s.\nReason: %(reason)s",
                days=extension_days,
                name=self.name,
                reason=reason,
            ),
            mail_template_xmlid="rgb_pob.mail_template_pob_extension_approval",
            activity_type_xmlid="rgb_pob.mail_activity_pob_extension",
        )
        self.message_post(
            body=_(
                "Extension requested: +%(days)s day(s). Reason: %(reason)s",
                days=extension_days,
                reason=reason,
            )
        )
        return extension

    def _approve_extension(self, extension):
        self.ensure_one()
        self._check_group("rgb_pob.group_pob_operations")
        extension.write(
            {
                "state": "approved",
                "approved_by_id": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )
        self._done_activities()
        # Recompute date_end / alert_date via approved_extension_days; reset alert
        self.with_context(pob_force_write=True).write(
            {
                "state": "active_onboard",
                "alert_sent": False,
            }
        )
        self.message_post(
            body=_(
                "Extension of +%(days)s day(s) approved by %(user)s. New end date: %(date_end)s.",
                days=extension.extension_days,
                user=self.env.user.display_name,
                date_end=self.date_end,
            )
        )

    def _reject_extension(self, extension, reason=False):
        self.ensure_one()
        self._check_group("rgb_pob.group_pob_operations")
        extension.write(
            {
                "state": "rejected",
                "rejected_by_id": self.env.user.id,
                "rejection_date": fields.Datetime.now(),
                "rejection_reason": reason or _("Rejected"),
            }
        )
        self._done_activities()
        self.state = "active_onboard"
        self.message_post(
            body=_(
                "Extension of +%(days)s day(s) rejected by %(user)s.",
                days=extension.extension_days,
                user=self.env.user.display_name,
            )
        )

    # -------------------------------------------------------------------------
    # Cron / alerts
    # -------------------------------------------------------------------------
    @api.model
    def _cron_pob_alerts(self):
        today = fields.Date.context_today(self)
        # Expiry close
        to_close = self.search(
            [
                ("state", "=", "active_onboard"),
                ("date_end", "<", today),
            ]
        )
        for record in to_close:
            record.with_context(pob_force_write=True).write({"state": "expired_closed"})
            record.message_post(body=_("Automatically closed: stay period expired."))

        # 4-day alert
        to_alert = self.search(
            [
                ("state", "=", "active_onboard"),
                ("alert_sent", "=", False),
                ("alert_date", "!=", False),
                ("alert_date", "<=", today),
                ("date_end", ">=", today),
            ]
        )
        for record in to_alert:
            record._send_expiry_alert()
            record.alert_sent = True

    def _send_expiry_alert(self):
        self.ensure_one()
        note = _(
            "POB %(name)s for %(employee)s expires on %(date_end)s (%(days)s day(s) remaining).",
            name=self.name,
            employee=self.employee_id.display_name,
            date_end=self.date_end,
            days=self.days_remaining,
        )
        self._notify_group(
            "rgb_pob.group_pob_operations",
            summary=_("POB Expiry Alert"),
            note=note,
            mail_template_xmlid="rgb_pob.mail_template_pob_expiry_alert",
            activity_type_xmlid="rgb_pob.mail_activity_pob_alert",
            also_manager=True,
        )
        self.message_post(body=_("Expiry alert sent (4 days before end date)."))

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _validate_required_fields(self):
        self.ensure_one()
        if not self.employee_id or not self.well_id or not self.rig_id:
            raise UserError(_("Employee, Well and Rig are required before submitting."))
        if not self.duration_days or not self.date_start:
            raise UserError(_("Duration and Start Date are required before submitting."))

    def _check_group(self, xmlid):
        if not self.env.user.has_group(xmlid) and not self.env.user.has_group(
            "rgb_pob.group_pob_manager"
        ):
            raise UserError(_("You do not have the required POB approval rights."))

    def _done_activities(self):
        activities = self.activity_ids.filtered(
            lambda a: a.activity_type_id
            in (
                self.env.ref("rgb_pob.mail_activity_pob_approval", raise_if_not_found=False),
                self.env.ref("rgb_pob.mail_activity_pob_extension", raise_if_not_found=False),
                self.env.ref("rgb_pob.mail_activity_pob_alert", raise_if_not_found=False),
            )
        )
        activities.action_feedback(feedback=_("Processed"))

    def _get_users_in_group(self, xmlid):
        group = self.env.ref(xmlid, raise_if_not_found=False)
        if not group:
            return self.env["res.users"]
        return group.users.filtered(lambda u: u.active and not u.share)

    def _notify_group(
        self,
        group_xmlid,
        summary,
        note,
        mail_template_xmlid=False,
        activity_type_xmlid=False,
        also_manager=False,
    ):
        self.ensure_one()
        users = self._get_users_in_group(group_xmlid)
        if also_manager:
            users |= self._get_users_in_group("rgb_pob.group_pob_manager")
        users = users - self.env.user

        activity_type = (
            self.env.ref(activity_type_xmlid, raise_if_not_found=False)
            if activity_type_xmlid
            else False
        )
        for user in users:
            if activity_type:
                self.activity_schedule(
                    activity_type_id=activity_type.id,
                    summary=summary,
                    note=note,
                    user_id=user.id,
                )
            # In-app notification
            if user.partner_id:
                self.env["bus.bus"]._sendone(
                    user.partner_id,
                    "simple_notification",
                    {
                        "title": summary,
                        "message": note,
                        "type": "warning",
                        "sticky": False,
                    },
                )
            # Email
            if mail_template_xmlid and user.email:
                template = self.env.ref(mail_template_xmlid, raise_if_not_found=False)
                if template:
                    template.send_mail(
                        self.id,
                        force_send=False,
                        email_values={"email_to": user.email_formatted},
                    )

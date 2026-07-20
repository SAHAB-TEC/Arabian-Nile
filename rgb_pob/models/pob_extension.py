# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PobExtension(models.Model):
    _name = "pob.extension"
    _description = "POB Extension Request"
    _order = "create_date desc, id desc"
    _rec_name = "display_name"

    request_id = fields.Many2one(
        "pob.request",
        string="POB Request",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="request_id.company_id",
        store=True,
        index=True,
    )
    extension_days = fields.Integer(string="Additional Days", required=True)
    reason = fields.Text(string="Reason", required=True)
    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        default="pending",
        required=True,
        copy=False,
    )
    requested_by_id = fields.Many2one(
        "res.users",
        string="Requested By",
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
    )
    request_date = fields.Datetime(
        string="Request Date",
        default=fields.Datetime.now,
        required=True,
        readonly=True,
    )
    approved_by_id = fields.Many2one("res.users", string="Approved By", readonly=True, copy=False)
    approval_date = fields.Datetime(string="Approval Date", readonly=True, copy=False)
    rejected_by_id = fields.Many2one("res.users", string="Rejected By", readonly=True, copy=False)
    rejection_date = fields.Datetime(string="Rejection Date", readonly=True, copy=False)
    rejection_reason = fields.Text(string="Rejection Reason", copy=False)
    display_name = fields.Char(compute="_compute_display_name")

    @api.depends("request_id.name", "extension_days", "state")
    def _compute_display_name(self):
        for record in self:
            record.display_name = _(
                "%(request)s (+%(days)s days) [%(state)s]",
                request=record.request_id.name or _("New"),
                days=record.extension_days or 0,
                state=dict(record._fields["state"].selection).get(record.state, record.state),
            )

    def action_approve(self):
        for record in self:
            if record.state != "pending":
                raise UserError(_("Only pending extensions can be approved."))
            record.request_id._approve_extension(record)
        return True

    def action_reject(self):
        for record in self:
            if record.state != "pending":
                raise UserError(_("Only pending extensions can be rejected."))
            record.request_id._reject_extension(record)
        return True

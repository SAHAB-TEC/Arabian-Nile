# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class PobExtensionWizard(models.TransientModel):
    _name = "pob.extension.wizard"
    _description = "POB Extension Request Wizard"

    request_id = fields.Many2one(
        "pob.request",
        string="POB Request",
        required=True,
        readonly=True,
    )
    employee_id = fields.Many2one(
        related="request_id.employee_id",
        readonly=True,
    )
    date_end = fields.Date(
        related="request_id.date_end",
        readonly=True,
        string="Current End Date",
    )
    extension_days = fields.Integer(
        string="Additional Days",
        required=True,
        default=7,
    )
    reason = fields.Text(string="Reason for Extension", required=True)

    def action_confirm(self):
        self.ensure_one()
        if self.extension_days < 1:
            raise UserError(_("Additional days must be at least 1."))
        if not (self.reason or "").strip():
            raise UserError(_("Please provide a reason for the extension."))
        self.request_id._create_extension_request(
            extension_days=self.extension_days,
            reason=self.reason.strip(),
        )
        return {"type": "ir.actions.act_window_close"}

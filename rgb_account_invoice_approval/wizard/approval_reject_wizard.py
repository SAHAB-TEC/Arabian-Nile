# -*- coding: utf-8 -*-
from odoo import fields, models, _


class RgbInvoiceApprovalRejectWizard(models.TransientModel):
    _name = 'rgb.invoice.approval.reject.wizard'
    _description = 'Reject Invoice Approval'

    move_id = fields.Many2one(
        'account.move',
        string='Invoice',
        required=True,
        readonly=True,
    )
    note = fields.Text(
        string='Rejection Reason',
    )

    def action_confirm_reject(self):
        self.ensure_one()
        self.move_id.action_reject_invoice(note=self.note)
        return {'type': 'ir.actions.act_window_close'}

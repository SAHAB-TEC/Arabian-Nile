# -*- coding: utf-8 -*-
from odoo import models, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        moves = self.line_ids.move_id
        for move in moves.filtered(lambda m: m.is_purchase_document(include_receipts=True)):
            project = move.construction_project_id
            if project and move.partner_id:
                self.env['rgb.ncr']._raise_if_frozen(
                    project.id,
                    move.partner_id.id,
                    document_label=_('vendor bill payment'),
                )
        return super().action_create_payments()

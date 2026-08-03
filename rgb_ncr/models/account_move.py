# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    construction_project_id = fields.Many2one(
        'construction.project',
        string='Construction Project',
        index=True,
        tracking=True,
        copy=False,
    )
    ncr_financial_freeze = fields.Boolean(
        string='NCR Financial Freeze',
        compute='_compute_ncr_financial_freeze',
    )

    @api.depends('construction_project_id', 'partner_id', 'move_type')
    def _compute_ncr_financial_freeze(self):
        Ncr = self.env['rgb.ncr']
        for move in self:
            if (
                move.move_type in ('in_invoice', 'in_refund')
                and move.construction_project_id
                and move.partner_id
            ):
                move.ncr_financial_freeze = bool(Ncr._get_active_freeze(
                    move.construction_project_id.id,
                    move.partner_id.id,
                ))
            else:
                move.ncr_financial_freeze = False

    def action_post(self):
        for move in self.filtered(lambda m: m.is_purchase_document(include_receipts=True)):
            project = move.construction_project_id
            if not project and move.invoice_origin:
                po = self.env['purchase.order'].search([
                    ('name', '=', move.invoice_origin),
                    ('construction_project_id', '!=', False),
                ], limit=1)
                if po:
                    move.construction_project_id = po.construction_project_id
                    project = po.construction_project_id
            if project and move.partner_id:
                self.env['rgb.ncr']._raise_if_frozen(
                    project.id,
                    move.partner_id.id,
                    document_label=_('vendor bill posting'),
                )
        return super().action_post()

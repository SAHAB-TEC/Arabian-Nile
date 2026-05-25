# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    contract_id = fields.Many2one(
        'rgb.contract',
        string='Contract',
        index=True,
        tracking=True,
    )
    contract_type = fields.Selection(
        related='contract_id.contract_type',
        store=True,
        readonly=True,
    )

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if not self.contract_id:
            return
        contract = self.contract_id
        if contract.partner_id:
            self.partner_id = contract.partner_id
        if contract.currency_id:
            self.currency_id = contract.currency_id
        if contract.contract_type == 'sale_contract' and contract.price_list_id:
            self._onchange_partner_id()
        self._apply_contract_analytic_on_lines()

    def _apply_contract_analytic_on_lines(self):
        distribution = self.contract_id._get_analytic_distribution() if self.contract_id else {}
        if not distribution:
            return
        for line in self.invoice_line_ids:
            line.analytic_distribution = distribution

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves.filtered('contract_id')._apply_contract_analytic_on_lines()
        return moves

    def write(self, vals):
        res = super().write(vals)
        if vals.get('contract_id') or vals.get('invoice_line_ids'):
            self.filtered('contract_id')._apply_contract_analytic_on_lines()
        return res

    def action_post(self):
        for move in self.filtered('contract_id'):
            contract = move.contract_id
            if not contract._has_insurance_pdf():
                raise UserError(
                    _('Cannot post invoice: upload insurance documents on contract %s first.')
                    % contract.name
                )
            contract._check_invoice_contract_limit(move.amount_total)
        res = super().action_post()
        for move in self.filtered('contract_id'):
            move.contract_id.message_post(
                body=_('Invoice %s posted (amount: %s).') % (move.name, move.amount_total),
            )
        return res

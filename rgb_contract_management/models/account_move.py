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
    contract_code = fields.Char(
        string='Contract Code',
        related='contract_id.contract_code',
        store=True,
        readonly=True,
    )
    dollar_percentage = fields.Float(
        string='USD %',
        help='Percentage of the invoice amount payable in USD.',
    )
    libya_dinar_percentage = fields.Float(
        string='LYD %',
        help='Percentage of the invoice amount payable in LYD.',
    )
    usd_amount = fields.Float(
        string='USD Amount',
        compute='_compute_usd_lyd_amount',
        help='Invoice amount share in USD based on USD %.',
    )
    lyd_amount = fields.Float(
        string='LYD Amount',
        compute='_compute_usd_lyd_amount',
        help='Invoice amount share in LYD based on LYD %.',
    )

    @api.depends('amount_total', 'dollar_percentage', 'libya_dinar_percentage', 'currency_id', 'date', 'invoice_date')
    def _compute_usd_lyd_amount(self):
        usd_currency = self.env.ref('base.USD', raise_if_not_found=False)
        lyd_currency = self.env.ref('base.LYD', raise_if_not_found=False)
        for move in self:
            move.usd_amount = 0.0
            move.lyd_amount = 0.0
            if not move.amount_total or not move.currency_id:
                continue
            conv_date = move.invoice_date or move.date or fields.Date.context_today(move)
            if usd_currency:
                total_usd = move.currency_id._convert(
                    move.amount_total,
                    usd_currency,
                    move.company_id,
                    conv_date,
                )
                move.usd_amount = total_usd * (move.dollar_percentage or 0.0) / 100.0
            if lyd_currency:
                total_lyd = move.currency_id._convert(
                    move.amount_total,
                    lyd_currency,
                    move.company_id,
                    conv_date,
                )
                move.lyd_amount = total_lyd * (move.libya_dinar_percentage or 0.0) / 100.0

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        contract_id = vals.get('contract_id') or self.env.context.get('default_contract_id')
        if contract_id:
            contract = self.env['rgb.contract'].browse(contract_id)
            if 'dollar_percentage' in fields_list and 'dollar_percentage' not in vals:
                vals['dollar_percentage'] = contract.dollar_percentage
            if 'libya_dinar_percentage' in fields_list and 'libya_dinar_percentage' not in vals:
                vals['libya_dinar_percentage'] = contract.libya_dinar_percentage
        return vals

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
        self.dollar_percentage = contract.dollar_percentage
        self.libya_dinar_percentage = contract.libya_dinar_percentage
        self._apply_contract_analytic_on_lines()
        self._apply_contract_invoice_template_fields()

    def _apply_contract_analytic_on_lines(self):
        distribution = self.contract_id._get_analytic_distribution() if self.contract_id else {}
        if not distribution:
            return
        for line in self.invoice_line_ids:
            line.analytic_distribution = distribution

    def _apply_contract_invoice_template_fields(self):
        """Hook for account_invoice_templates; no-op when that module is not installed."""
        return

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('contract_id') and 'dollar_percentage' not in vals:
                contract = self.env['rgb.contract'].browse(vals['contract_id'])
                vals.setdefault('dollar_percentage', contract.dollar_percentage)
                vals.setdefault('libya_dinar_percentage', contract.libya_dinar_percentage)
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

# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


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
        help='Deprecated: migrated to Payment Currency Split.',
    )
    libya_dinar_percentage = fields.Float(
        string='LYD %',
        help='Deprecated: migrated to Payment Currency Split.',
    )
    usd_amount = fields.Float(
        string='USD Amount',
        compute='_compute_legacy_currency_split_fields',
        store=True,
    )
    lyd_amount = fields.Float(
        string='LYD Amount',
        compute='_compute_legacy_currency_split_fields',
        store=True,
    )
    currency_split_ids = fields.One2many(
        'rgb.account.move.currency.split',
        'move_id',
        string='Payment Currency Split',
        copy=True,
    )
    currency_split_percentage_total = fields.Float(
        string='Split Total (%)',
        compute='_compute_currency_split_percentage_total',
        digits=(16, 4),
    )

    @api.constrains('currency_split_ids')
    def _check_currency_split_total(self):
        for move in self:
            if not move.currency_split_ids:
                continue
            total = sum(move.currency_split_ids.mapped('percentage'))
            if abs(total - 100.0) > 0.0001:
                raise ValidationError(_(
                    'Payment currency split must total 100%% (current total: %(total).2f%%).',
                    total=total,
                ))
            currency_ids = move.currency_split_ids.mapped('currency_id')
            if len(currency_ids) != len(set(currency_ids.ids)):
                raise ValidationError(_(
                    'Each currency can appear only once in the payment split.',
                ))

    @api.depends('currency_split_ids.percentage')
    def _compute_currency_split_percentage_total(self):
        for move in self:
            move.currency_split_percentage_total = sum(
                move.currency_split_ids.mapped('percentage')
            )

    @api.depends(
        'currency_split_ids',
        'currency_split_ids.amount',
        'currency_split_ids.currency_id',
    )
    def _compute_legacy_currency_split_fields(self):
        usd_currency = self.env.ref('base.USD', raise_if_not_found=False)
        lyd_currency = self.env.ref('base.LYD', raise_if_not_found=False)
        for move in self:
            move.usd_amount = 0.0
            move.lyd_amount = 0.0
            for line in move.currency_split_ids:
                if usd_currency and line.currency_id == usd_currency:
                    move.usd_amount = line.amount
                if lyd_currency and line.currency_id == lyd_currency:
                    move.lyd_amount = line.amount

    def _apply_contract_currency_split(self):
        for move in self:
            if not move.contract_id or not move.contract_id.currency_split_ids:
                move.currency_split_ids = [(5, 0, 0)]
                continue
            move.currency_split_ids = [(5, 0, 0)] + move.contract_id._prepare_currency_split_commands()

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        contract_id = vals.get('contract_id') or self.env.context.get('default_contract_id')
        if contract_id:
            contract = self.env['rgb.contract'].browse(contract_id)
            if contract.currency_split_ids and 'currency_split_ids' in fields_list:
                vals['currency_split_ids'] = contract._prepare_currency_split_commands()
        return vals

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if not self.contract_id:
            self.currency_split_ids = [(5, 0, 0)]
            return
        contract = self.contract_id
        if contract.partner_id:
            self.partner_id = contract.partner_id
        if contract.currency_id:
            self.currency_id = contract.currency_id
        if contract.contract_type == 'sale_contract' and contract.price_list_id:
            self._onchange_partner_id()
        self._apply_contract_currency_split()
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
            if vals.get('contract_id') and 'currency_split_ids' not in vals:
                contract = self.env['rgb.contract'].browse(vals['contract_id'])
                if contract.currency_split_ids:
                    vals['currency_split_ids'] = contract._prepare_currency_split_commands()
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

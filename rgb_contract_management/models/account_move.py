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
        string='Contract No',
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
    )
    lyd_amount = fields.Float(
        string='LYD Amount',
        compute='_compute_legacy_currency_split_fields',
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
        for move in self.filtered(lambda m: m.exists() and m.currency_split_ids):
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
        'currency_split_ids.percentage',
        'currency_split_ids.currency_id',
        'amount_total',
        'currency_id',
        'invoice_date',
        'date',
        'company_id',
    )
    def _compute_legacy_currency_split_fields(self):
        usd_currency = self.env.ref('base.USD', raise_if_not_found=False)
        lyd_currency = self.env.ref('base.LYD', raise_if_not_found=False)
        for move in self:
            move.usd_amount = 0.0
            move.lyd_amount = 0.0
            if not move.currency_split_ids or not move.amount_total or not move.currency_id:
                continue
            conv_date = move.invoice_date or move.date or fields.Date.context_today(move)
            for line in move.currency_split_ids:
                if not line.currency_id:
                    continue
                converted_total = move.currency_id._convert(
                    move.amount_total,
                    line.currency_id,
                    move.company_id,
                    conv_date,
                )
                amount = converted_total * (line.percentage or 0.0) / 100.0
                if usd_currency and line.currency_id == usd_currency:
                    move.usd_amount = amount
                if lyd_currency and line.currency_id == lyd_currency:
                    move.lyd_amount = amount

    def unlink(self):
        split_ids = self.mapped('currency_split_ids').ids
        if split_ids:
            self.env['rgb.account.move.currency.split'].browse(split_ids).unlink()
        return super().unlink()

    def _apply_contract_currency_split(self, force=False):
        for move in self:
            if not move.contract_id or not move.contract_id.currency_split_ids:
                if force:
                    move.currency_split_ids = [(5, 0, 0)]
                continue
            if move.currency_split_ids and not force:
                continue
            move.currency_split_ids = [
                (5, 0, 0),
            ] + move.contract_id._prepare_currency_split_commands()

    def _apply_contract_invoice_lines(self, force=False):
        """Copy contract lines to the invoice only when empty or contract changed."""
        for move in self:
            if not move.contract_id or not move.contract_id.contract_line_ids:
                if force:
                    move.invoice_line_ids = [(5, 0, 0)]
                continue
            if move.invoice_line_ids and not force:
                continue
            move.invoice_line_ids = [
                (5, 0, 0),
            ] + move.contract_id._prepare_invoice_line_commands()

    def _contract_id_changed(self):
        self.ensure_one()
        return bool(
            self._origin.contract_id
            and self._origin.contract_id != self.contract_id
        )

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        contract_id = vals.get('contract_id') or self.env.context.get('default_contract_id')
        if not contract_id:
            return vals
        contract = self.env['rgb.contract'].browse(contract_id)
        if contract.currency_split_ids and 'currency_split_ids' in fields_list:
            if not vals.get('currency_split_ids'):
                vals['currency_split_ids'] = contract._prepare_currency_split_commands()
        if contract.contract_line_ids and 'invoice_line_ids' in fields_list:
            if not vals.get('invoice_line_ids'):
                vals['invoice_line_ids'] = contract._prepare_invoice_line_commands()
        return vals

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if not self.contract_id:
            self.currency_split_ids = [(5, 0, 0)]
            self.invoice_line_ids = [(5, 0, 0)]
            return
        contract = self.contract_id
        if contract.partner_id:
            self.partner_id = contract.partner_id
        if contract.currency_id:
            self.currency_id = contract.currency_id
        if contract.contract_type == 'sale_contract' and contract.price_list_id:
            self._onchange_partner_id()

        contract_changed = self._contract_id_changed()
        if contract_changed or not self.currency_split_ids:
            self._apply_contract_currency_split(force=True)
        if contract_changed or not self.invoice_line_ids:
            self._apply_contract_invoice_lines(force=True)

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
        # Contract lines and currency splits are loaded from default_get / web_save
        # only. Injecting them here duplicates records on create + write.
        moves = super().create(vals_list)
        contract_moves = moves.filtered(lambda m: m.contract_id and m.invoice_line_ids)
        contract_moves._apply_contract_analytic_on_lines()
        contract_moves.mapped('contract_id')._clear_staging_invoice_lines()
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

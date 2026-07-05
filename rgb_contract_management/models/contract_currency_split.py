# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RgbContractCurrencySplit(models.Model):
    _name = 'rgb.contract.currency.split'
    _description = 'Contract Payment Currency Split'
    _order = 'sequence, id'

    contract_id = fields.Many2one(
        'rgb.contract',
        string='Contract',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
    )
    percentage = fields.Float(
        string='Percentage (%)',
        digits=(16, 4),
        required=True,
    )
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        compute='_compute_amount',
        store=True,
    )

    @api.depends(
        'percentage',
        'currency_id',
        'contract_id.contract_value_currency',
        'contract_id.currency_id',
        'contract_id.date_start',
        'contract_id.company_id',
    )
    def _compute_amount(self):
        for line in self:
            line.amount = 0.0
            contract = line.contract_id
            if (
                not contract
                or not contract.contract_value_currency
                or not contract.currency_id
                or not line.currency_id
            ):
                continue
            conv_date = contract.date_start or fields.Date.context_today(line)
            company = contract.company_id or line.env.company
            converted_total = contract.currency_id._convert(
                contract.contract_value_currency,
                line.currency_id,
                company,
                conv_date,
            )
            line.amount = converted_total * (line.percentage or 0.0) / 100.0

    @api.constrains('currency_id', 'contract_id')
    def _check_unique_currency(self):
        for line in self:
            if not line.contract_id or not line.currency_id:
                continue
            duplicate = self.search([
                ('contract_id', '=', line.contract_id.id),
                ('currency_id', '=', line.currency_id.id),
                ('id', '!=', line.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    'Currency %(currency)s is already used in the payment split for this contract.',
                    currency=line.currency_id.display_name,
                ))

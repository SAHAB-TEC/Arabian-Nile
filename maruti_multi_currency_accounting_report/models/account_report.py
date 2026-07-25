# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import AccessError

import datetime

NUMBER_FIGURE_TYPES = ('float', 'integer', 'monetary', 'percentage')

# Columns that must keep the original transaction / account currency amount.
# Only debit / credit / balance (and similar monetary totals) are converted.
AMOUNT_CURRENCY_LABELS = frozenset({
    'amount_currency',
})


class AccountReport(models.Model):
    _inherit = 'account.report'

    def _init_options_currencies(self, options, previous_options=None):
        previous_options = previous_options or {}
        currency_id_list = [
            {'id': currency.id, 'name': _(currency.name)}
            for currency in self.env['res.currency'].search([])
        ]
        options['currencies'] = currency_id_list

        currency_id = previous_options.get('currencies_selected')
        old_currency_name = previous_options.get('currencies_selected_name')

        if currency_id:
            options['currencies_selected_name'] = self.env['res.currency'].browse(currency_id).name
        elif old_currency_name:
            options['currencies_selected_name'] = old_currency_name
        else:
            options['currencies_selected_name'] = self.env.company.currency_id.name

    def _get_report_display_currency(self, options):
        """Currency selected in the report filter (fallback: company currency)."""
        options = options or {}
        name = options.get('currencies_selected_name')
        if name:
            currency = self.env['res.currency'].search([('name', '=', name)], limit=1)
            if currency:
                return currency
        return self.env.company.currency_id

    def _build_column_dict(
            self, col_value, col_data,
            options=None, currency=False, digits=1,
            column_expression=None, has_sublines=False,
            report_line_id=None,
    ):
        # Empty column
        if col_value is None and col_data is None:
            return {}

        col_data = col_data or {}
        column_expression = column_expression or self.env['account.report.expression']
        options = options or {}

        blank_if_zero = column_expression.blank_if_zero or col_data.get('blank_if_zero', False)
        figure_type = column_expression.figure_type or col_data.get('figure_type', 'string')
        expression_label = col_data.get('expression_label')

        # Convert monetary totals to the selected report currency.
        # NEVER convert amount_currency — it must stay in the original currency.
        if (
            isinstance(col_value, (int, float))
            and figure_type == 'monetary'
            and expression_label not in AMOUNT_CURRENCY_LABELS
        ):
            date_to = (options.get('date') or {}).get('date_to')
            date_obj = (
                datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
                if date_to else fields.Date.context_today(self)
            )
            company_currency = self.env.company.currency_id
            to_currency = self._get_report_display_currency(options)
            if company_currency and to_currency and company_currency != to_currency:
                col_value = company_currency._convert(
                    col_value, to_currency, self.env.company, date_obj,
                )
            currency = to_currency
        # amount_currency: keep col_value and the currency passed by the report engine

        format_params = {}
        if figure_type == 'monetary' and currency:
            format_params['currency_id'] = currency.id
        elif figure_type in ('float', 'percentage'):
            format_params['digits'] = digits

        col_group_key = col_data.get('column_group_key')

        return {
            'auditable': col_value is not None
                         and column_expression.auditable
                         and not options['column_groups'][col_group_key]['forced_options'].get('compute_budget'),
            'blank_if_zero': blank_if_zero,
            'column_group_key': col_group_key,
            'currency': currency.id if currency else None,
            'currency_symbol': self.env.company.currency_id.symbol if options.get('multi_currency') else None,
            'digits': digits,
            'expression_label': expression_label,
            'figure_type': figure_type,
            'green_on_positive': column_expression.green_on_positive,
            'has_sublines': has_sublines,
            'is_zero': col_value is None or (
                isinstance(col_value, (int, float))
                and figure_type in NUMBER_FIGURE_TYPES
                and self._is_value_zero(col_value, figure_type, format_params)
            ),
            'no_format': col_value,
            'format_params': format_params,
            'report_line_id': report_line_id,
            'sortable': col_data.get('sortable', False),
            'comparison_mode': col_data.get('comparison_mode'),
        }

    def _init_options_rounding_unit(self, options, previous_options=None):
        previous_options = previous_options or {}
        default = 'decimals'
        options['rounding_unit'] = previous_options.get('rounding_unit', default)
        currency_obj = self._get_report_display_currency(options)
        options['rounding_unit_names'] = self._get_rounding_unit_names(currency_obj)

    def _get_rounding_unit_names(self, currency_obj):
        if currency_obj:
            currency_symbol = currency_obj.symbol
        else:
            currency_symbol = self.env.company.currency_id.symbol

        rounding_unit_names = [
            ('decimals', '.%s' % currency_symbol),
            ('units', '%s' % currency_symbol),
            ('thousands', 'K%s' % currency_symbol),
            ('millions', 'M%s' % currency_symbol),
        ]

        if self.env.company.currency_id == self.env.ref('base.INR'):
            rounding_unit_names.insert(3, ('lakhs', 'L%s' % currency_symbol))

        return dict(rounding_unit_names)

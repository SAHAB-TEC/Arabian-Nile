
from odoo import models, _,api
from odoo.exceptions import AccessError

import datetime

NUMBER_FIGURE_TYPES = ('float', 'integer', 'monetary', 'percentage')

class AccountReport(models.Model):
    _inherit = 'account.report'
    

    #Override base method
    def _init_options_currencies(self, options, previous_options=None):
        currency_id = self.env['res.currency'].search([])
        currency_id_list = []
        for currency in currency_id:
            currency_dict = {
                'id':currency.id,
                'name':_(currency.name)
            }
            currency_id_list.append(currency_dict)
             
        options['currencies'] = currency_id_list
        currency_id = previous_options.get('currencies_selected', None)
        old_currency_id = previous_options.get('currencies_selected_name', None)
        
        if currency_id:
            options['currencies_selected_name'] = self.env['res.currency'].browse(currency_id).name
        elif old_currency_id:
            options['currencies_selected_name'] = old_currency_id
        else:    
            options['currencies_selected_name'] = self.env.company.currency_id.name
    
    
    #Override base method
    
    def _build_column_dict(
            self, col_value, col_data,
            options=None, currency=False, digits=1,
            column_expression=None, has_sublines=False,
            report_line_id=None,
    ):
        # Empty column
        if col_value is None and col_data is None:
            return {}

        date_obj = datetime.datetime.strptime(options['date']['date_to'],'%Y-%m-%d').date()
        currency_id = self.env.company.currency_id
        amount = col_value
        to_currency = self.env['res.currency'].search([('name','=',options['currencies_selected_name'])])
        
        if isinstance(amount, (int, float)):
            converted_amount = currency_id._convert(amount,to_currency,date=date_obj)
            col_value = converted_amount
            currency = to_currency
            
        col_data = col_data or {}
        column_expression = column_expression or self.env['account.report.expression']
        options = options or {}

        blank_if_zero = column_expression.blank_if_zero or col_data.get('blank_if_zero', False)
        figure_type = column_expression.figure_type or col_data.get('figure_type', 'string')

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
            'expression_label': col_data.get('expression_label'),
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
        
    
    #Override base method
    def _init_options_rounding_unit(self, options, previous_options=None):
        default = 'decimals'

        if previous_options:
            options['rounding_unit'] = previous_options.get('rounding_unit', default)
        else:
            options['rounding_unit'] = default

        currency_id = previous_options.get('currencies_selected', None)
        old_currency_id = previous_options.get('currencies_selected_name', None)
        
        if currency_id:
            currency_obj = self.env['res.currency'].browse(currency_id)
        elif old_currency_id:
            currency_obj = self.env['res.currency'].search([('name','=',old_currency_id)])
        else:    
            currency_obj = self.env.company.currency_id
         
        options['rounding_unit_names'] = self._get_rounding_unit_names(currency_obj)
        

    #Override base method
    def _get_rounding_unit_names(self,currency_obj):
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

        # We want to add 'lakhs' for Indian Rupee
        if (self.env.company.currency_id == self.env.ref('base.INR')):
            # We want it between 'thousands' and 'millions'
            rounding_unit_names.insert(3, ('lakhs', 'L%s' % currency_symbol))

        return dict(rounding_unit_names)
    
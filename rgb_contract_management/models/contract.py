# -*- coding: utf-8 -*-
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class RgbContract(models.Model):
    _name = 'rgb.contract'
    _description = 'Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc, id desc'

    # ── Identification ──
    name = fields.Char(
        string='Contract Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )
    contract_code = fields.Char(
        string='Contract Code',
        tracking=True,
        copy=False,
        help='Manual unique contract code shown on linked invoice prints.',
    )
    contract_type = fields.Selection(
        selection=[
            ('purchase_contract', 'Purchase / Contractor Contract'),
            ('sale_contract', 'Sale / Customer Contract'),
        ],
        string='Contract Type',
        required=True,
        default='purchase_contract',
        tracking=True,
    )
    contract_business_type = fields.Selection(
        selection=[
            ('supply', 'Supply Only'),
            ('supply_install', 'Supply & Installation'),
            ('construction', 'Construction'),
            ('rental', 'Equipment Rental / Service'),
        ],
        string='Business Type',
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Contractor / Customer',
        required=True,
        tracking=True,
        check_company=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('under_approval', 'Under Approval'),
            ('approved', 'Approved'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
            ('expired', 'Expired'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        copy=False,
    )

    # ── Dates & duration ──
    date_start = fields.Date(string='Start Date', tracking=True)
    date_end = fields.Date(string='End Date', tracking=True)
    service_duration_days = fields.Integer(string='Service Duration (Days)', tracking=True, compute='_compute_service_duration_days', store=True)

    remaining_days = fields.Integer(
        string='Remaining Days',
        compute='_compute_remaining_days',
        store=True,
    )

    # ── Amounts & currencies ──
    currency_id = fields.Many2one(
        'res.currency',
        string='Contract Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        tracking=True,
    )
    contract_value_currency = fields.Monetary(
        string='Contract Value',
        currency_field='currency_id',
        tracking=True,
    )
    lyd_currency_id = fields.Many2one(
        'res.currency',
        string='LYD Currency',
        compute='_compute_lyd_currency_id',
        store=True,
        readonly=False,
    )
    contract_value_lyd = fields.Monetary(
        string='Contract Value (LYD)',
        currency_field='lyd_currency_id',
        tracking=True,
        compute='_compute_contract_value_lyd',
        store=True,
        readonly=False,
    )
    @api.depends('contract_value_currency', 'exchange_rate')
    def _compute_contract_value_lyd(self):
        for contract in self:
            contract.contract_value_lyd = contract.contract_value_currency * (contract.exchange_rate or 0.0)
    
    exchange_rate = fields.Float(
        string='Exchange Rate',
        digits=(16, 6),
        help='Contract exchange rate (e.g. 1 USD = X LYD).',
        compute='_compute_exchange_rate',
        store=True,
        readonly=True,
    )
    @api.depends('currency_id')
    def _compute_exchange_rate(self):
        for contract in self:
            contract.exchange_rate = contract.currency_id.rate if contract.currency_id else 1.0
            
    payment_terms_text = fields.Html(string='Payment Terms')
    price_list_id = fields.Many2one(
        'product.pricelist',
        string='Pricelist',
        check_company=True,
    )
    allow_over_contract_value = fields.Boolean(
        string='Allow Invoicing Over Contract Value',
        help='If unchecked, total posted invoices cannot exceed the contract value.',
    )
    contract_amendment_percent = fields.Float(
        string='Amendment Limit (%)',
        default=10.0,
        help='Maximum contract value change allowed (increase or decrease).',
    )
    dollar_percentage = fields.Float(
        string='USD %',
        tracking=True,
        help='Percentage of the invoice amount payable in USD.',
    )
    libya_dinar_percentage = fields.Float(
        string='LYD %',
        tracking=True,
        help='Percentage of the invoice amount payable in LYD.',
    )
    usd_amount = fields.Float(
        string='USD Amount',
        compute='_compute_usd_lyd_amount',
        help='Contract value share in USD based on USD %.',
    )
    lyd_amount = fields.Float(
        string='LYD Amount',
        compute='_compute_usd_lyd_amount',
        help='Contract value share in LYD based on LYD %.',
    )

    # ── Accounting & responsibility ──
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        check_company=True,
        tracking=True,
    )
    responsible_user_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user,
        tracking=True,
    )
    approval_user_id = fields.Many2one(
        'res.users',
        string='Approval Responsible',
        tracking=True,
    )

    # ── Insurance & attachments ──
    insurance_type_ids = fields.Many2many(
        'rgb.contract.insurance.type',
        'rgb_contract_insurance_type_rel',
        'contract_id',
        'insurance_type_id',
        string='Insurance Types',
    )
    insurance_attachment_ids = fields.Many2many(
        'ir.attachment',
        'rgb_contract_insurance_attachment_rel',
        'contract_id',
        'attachment_id',
        string='Insurance Documents',
    )
    performance_guarantee_attachment_ids = fields.Many2many(
        'ir.attachment',
        'rgb_contract_performance_attachment_rel',
        'contract_id',
        'attachment_id',
        string='Performance Guarantee Documents',
    )
    performance_guarantee_expiry_date = fields.Date(
        string='Performance Guarantee Expiry',
        tracking=True,
    )
    bank_guarantee_status = fields.Selection(
        selection=[
            ('sent', 'Correspondence Sent'),
            ('received', 'Received'),
        ],
        string='Bank Guarantee Status',
        tracking=True,
    )
    bank_guarantee_attachment_ids = fields.Many2many(
        'ir.attachment',
        'rgb_contract_bank_attachment_rel',
        'contract_id',
        'attachment_id',
        string='Bank Guarantee Documents',
    )
    bank_guarantee_value = fields.Monetary(
        string='Bank Guarantee Value',
        currency_field='currency_id',
    )

    # ── Payment & penalties ──
    advance_payment_percent = fields.Float(string='Advance Payment (%)', digits=(16, 4))
    delay_penalty_daily_rate = fields.Float(
        string='Daily Delay Penalty Rate (%)',
        digits=(16, 4),
        help='Percentage of contract value charged per delayed day.',
    )
    delay_penalty_max_percent = fields.Float(
        string='Max Delay Penalty (%)',
        digits=(16, 4),
        default=5.0,
    )
    agreed_execution_date = fields.Date(string='Agreed Execution Date')
    actual_execution_date = fields.Date(string='Actual Execution Date')
    delay_penalty_amount = fields.Monetary(
        string='Delay Penalty Amount',
        currency_field='currency_id',
        compute='_compute_delay_penalty_amount',
        store=True,
    )
    payment_condition_ids = fields.One2many(
        'rgb.contract.payment.condition',
        'contract_id',
        string='Payment Conditions',
    )

    # ── Invoices ──
    invoice_ids = fields.One2many(
        'account.move',
        'contract_id',
        string='Invoices',
        domain=[('move_type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'))],
    )
    invoice_count = fields.Integer(compute='_compute_invoice_count', string='Invoice Count')
    total_invoiced_amount = fields.Monetary(
        string='Total Invoiced',
        currency_field='currency_id',
        compute='_compute_invoice_amounts',
        store=True,
    )
    paid_invoice_amount = fields.Monetary(
        string='Paid Amount',
        currency_field='currency_id',
        compute='_compute_invoice_amounts',
        store=True,
    )
    unpaid_invoice_amount = fields.Monetary(
        string='Unpaid Amount',
        currency_field='currency_id',
        compute='_compute_invoice_amounts',
        store=True,
    )
    paid_percent_currency = fields.Float(
        string='Paid % (Contract Currency)',
        compute='_compute_invoice_amounts',
        digits=(16, 2),
    )
    paid_percent_lyd = fields.Float(
        string='Paid % (LYD)',
        compute='_compute_invoice_amounts',
        digits=(16, 2),
    )

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Contract number must be unique.'),
    ]

    @api.constrains('contract_code')
    def _check_contract_code_unique(self):
        for contract in self.filtered('contract_code'):
            code = contract.contract_code.strip()
            if not code:
                continue
            duplicate = self.search([
                ('contract_code', '=', code),
                ('id', '!=', contract.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    'Contract code "%(code)s" is already used on contract %(contract)s.',
                    code=code,
                    contract=duplicate.name,
                ))

    # ── Computes ──

    @api.depends('company_id')
    def _compute_lyd_currency_id(self):
        lyd = self.env['res.currency'].search([('name', '=', 'LYD')], limit=1)
        for contract in self:
            contract.lyd_currency_id = lyd.id if lyd else contract.currency_id.id

    @api.depends(
        'contract_value_currency',
        'currency_id',
        'dollar_percentage',
        'libya_dinar_percentage',
        'date_start',
        'company_id',
    )
    def _compute_usd_lyd_amount(self):
        usd_currency = self.env.ref('base.USD', raise_if_not_found=False)
        lyd_currency = self.env.ref('base.LYD', raise_if_not_found=False)
        for contract in self:
            contract.usd_amount = 0.0
            contract.lyd_amount = 0.0
            if not contract.contract_value_currency or not contract.currency_id:
                continue
            conv_date = contract.date_start or fields.Date.context_today(contract)
            company = contract.company_id or self.env.company
            if usd_currency:
                total_usd = contract.currency_id._convert(
                    contract.contract_value_currency,
                    usd_currency,
                    company,
                    conv_date,
                )
                contract.usd_amount = total_usd * (contract.dollar_percentage or 0.0) / 100.0
            if lyd_currency:
                total_lyd = contract.currency_id._convert(
                    contract.contract_value_currency,
                    lyd_currency,
                    company,
                    conv_date,
                )
                contract.lyd_amount = total_lyd * (contract.libya_dinar_percentage or 0.0) / 100.0

    @api.depends('date_end', 'date_start', 'service_duration_days', 'state')
    def _compute_remaining_days(self):
        today = fields.Date.context_today(self)
        for contract in self:
            end = contract.date_end
            if not end and contract.date_start and contract.service_duration_days:
                from datetime import timedelta
                end = contract.date_start + timedelta(days=contract.service_duration_days)
            if end:
                contract.remaining_days = (end - today).days
            else:
                contract.remaining_days = 0

    @api.depends('date_start', 'date_end')
    def _compute_service_duration_days(self):
        for contract in self:
            if contract.date_start and contract.date_end:
                contract.service_duration_days = (contract.date_end - contract.date_start).days
            else:
                contract.service_duration_days = 0

    @api.depends(
        'agreed_execution_date',
        'actual_execution_date',
        'delay_penalty_daily_rate',
        'delay_penalty_max_percent',
        'contract_value_currency',
    )
    def _compute_delay_penalty_amount(self):
        for contract in self:
            penalty = 0.0
            if (
                contract.agreed_execution_date
                and contract.actual_execution_date
                and contract.actual_execution_date > contract.agreed_execution_date
                and contract.contract_value_currency
            ):
                delay_days = (contract.actual_execution_date - contract.agreed_execution_date).days
                daily = contract.contract_value_currency * (contract.delay_penalty_daily_rate or 0.0) / 100.0
                penalty = delay_days * daily
                max_penalty = contract.contract_value_currency * (contract.delay_penalty_max_percent or 0.0) / 100.0
                if max_penalty:
                    penalty = min(penalty, max_penalty)
            contract.delay_penalty_amount = penalty

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for contract in self:
            contract.invoice_count = len(contract.invoice_ids)

    @api.depends(
        'invoice_ids',
        'invoice_ids.amount_total',
        'invoice_ids.amount_residual',
        'invoice_ids.state',
        'contract_value_currency',
        'contract_value_lyd',
    )
    def _compute_invoice_amounts(self):
        for contract in self:
            invoices = contract.invoice_ids.filtered(lambda m: m.state == 'posted')
            contract.total_invoiced_amount = sum(invoices.mapped('amount_total'))
            contract.paid_invoice_amount = sum(
                inv.amount_total - inv.amount_residual for inv in invoices
            )
            contract.unpaid_invoice_amount = sum(invoices.mapped('amount_residual'))
            if contract.contract_value_currency:
                contract.paid_percent_currency = (
                    contract.paid_invoice_amount / contract.contract_value_currency * 100.0
                )
            else:
                contract.paid_percent_currency = 0.0
            if contract.contract_value_lyd:
                contract.paid_percent_lyd = (
                    contract.paid_invoice_amount / contract.contract_value_lyd * 100.0
                )
            else:
                contract.paid_percent_lyd = 0.0

    # ── Constraints ──

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for contract in self:
            if contract.date_start and contract.date_end and contract.date_start > contract.date_end:
                raise ValidationError(_('End date must be after start date.'))

    # ── CRUD ──

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('rgb.contract') or _('New')
            if vals.get('contract_code'):
                vals['contract_code'] = vals['contract_code'].strip()
        contracts = super().create(vals_list)
        contracts._link_attachments()
        return contracts

    def write(self, vals):
        if vals.get('contract_code'):
            vals['contract_code'] = vals['contract_code'].strip()
        res = super().write(vals)
        if any(k in vals for k in (
            'insurance_attachment_ids',
            'performance_guarantee_attachment_ids',
            'bank_guarantee_attachment_ids',
        )):
            self._link_attachments()
        return res

    def _link_attachments(self):
        for contract in self:
            attachments = (
                contract.insurance_attachment_ids
                | contract.performance_guarantee_attachment_ids
                | contract.bank_guarantee_attachment_ids
            )
            attachments.filtered(
                lambda a: a.res_model != 'rgb.contract' or a.res_id != contract.id
            ).write({'res_model': 'rgb.contract', 'res_id': contract.id})

    # ── Business helpers ──

    def _has_insurance_pdf(self):
        self.ensure_one()
        return bool(self.insurance_attachment_ids.filtered(
            lambda a: (a.mimetype or '').lower() == 'application/pdf'
            or (a.name or '').lower().endswith('.pdf')
        ))

    def _check_insurance_for_activation(self):
        for contract in self:
            if not contract._has_insurance_pdf():
                raise UserError(
                    _('Cannot proceed: upload at least one insurance document (PDF) for contract %s.')
                    % contract.name
                )

    def _check_invoice_contract_limit(self, invoice_amount=0.0):
        self.ensure_one()
        if self.allow_over_contract_value or not self.contract_value_currency:
            return
        projected = self.total_invoiced_amount + invoice_amount
        max_value = self.contract_value_currency * (1 + (self.contract_amendment_percent or 0) / 100.0)
        if projected > max_value:
            raise UserError(
                _('Total invoiced amount (%(total)s) would exceed the contract limit (%(limit)s).')
                % {'total': projected, 'limit': max_value}
            )

    def _is_approver(self):
        self.ensure_one()
        user = self.env.user
        return (
            user.has_group('rgb_contract_management.group_contract_manager')
            or user == self.approval_user_id
            or user.has_group('rgb_contract_management.group_contract_approver')
        )

    def _send_approval_request(self):
        template = self.env.ref(
            'rgb_contract_management.mail_template_contract_approval',
            raise_if_not_found=False,
        )
        for contract in self:
            if not contract.approval_user_id:
                continue
            if template:
                template.send_mail(contract.id, force_send=False)
            contract.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=contract.approval_user_id.id,
                summary=_('Contract approval required: %s') % contract.name,
            )

    # ── Workflow actions ──

    def action_confirm(self):
        for contract in self.filtered(lambda c: c.state == 'draft'):
            if not contract.approval_user_id:
                raise UserError(_('Set an approval responsible before confirming the contract.'))
            contract.write({'state': 'under_approval'})
            contract.message_post(body=_('Contract submitted for approval.'))
            contract._send_approval_request()
        return True

    def action_approve(self):
        for contract in self.filtered(lambda c: c.state == 'under_approval'):
            if not contract._is_approver():
                raise UserError(_('You are not allowed to approve this contract.'))
            contract.write({'state': 'approved'})
            contract.message_post(body=_('Contract approved.'))
        return True

    def action_set_in_progress(self):
        for contract in self.filtered(lambda c: c.state == 'approved'):
            contract._check_insurance_for_activation()
            contract.write({'state': 'in_progress'})
            contract.message_post(body=_('Contract set to in progress.'))
        return True

    def action_done(self):
        self.filtered(lambda c: c.state == 'in_progress').write({'state': 'done'})
        return True

    def action_cancel(self):
        cancellable = self.filtered(lambda c: c.state not in ('done', 'cancelled'))
        cancellable.write({'state': 'cancelled'})
        return True

    def action_reset_to_draft(self):
        self.filtered(lambda c: c.state in ('under_approval', 'cancelled')).write({'state': 'draft'})
        return True

    def action_expire(self):
        self.filtered(lambda c: c.state not in ('done', 'cancelled')).write({'state': 'expired'})
        return True

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': _('Contract Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': self._prepare_invoice_context(),
        }

    def action_create_invoice(self):
        self.ensure_one()
        self._check_insurance_for_activation()
        return {
            'name': _('Create Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'target': 'current',
            'context': self._prepare_invoice_context(),
        }

    def _get_analytic_distribution(self):
        self.ensure_one()
        if self.analytic_account_id:
            return {str(self.analytic_account_id.id): 100}
        return {}

    def _prepare_invoice_context(self):
        """Default values passed when opening/creating invoices from this contract."""
        self.ensure_one()
        move_type = 'in_invoice' if self.contract_type == 'purchase_contract' else 'out_invoice'
        return {
            'default_contract_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_move_type': move_type,
            'default_currency_id': self.currency_id.id,
            'default_invoice_date': fields.Date.context_today(self),
            'default_analytic_distribution': self._get_analytic_distribution(),
            'default_dollar_percentage': self.dollar_percentage,
            'default_libya_dinar_percentage': self.libya_dinar_percentage,
        }

    @api.onchange('contract_type')
    def _onchange_contract_type(self):
        if self.contract_type == 'sale_contract':
            self.partner_id = False
        elif self.contract_type == 'purchase_contract':
            self.partner_id = False

    @api.onchange('partner_id', 'contract_type')
    def _onchange_partner_pricelist(self):
        if self.contract_type == 'sale_contract' and self.partner_id:
            self.price_list_id = self.partner_id.property_product_pricelist

    @api.model
    def _cron_performance_guarantee_reminder(self):
        """Daily: remind 60 days before performance guarantee expiry."""
        today = fields.Date.context_today(self)
        from datetime import timedelta
        target = today + timedelta(days=60)
        contracts = self.search([
            ('performance_guarantee_expiry_date', '=', target),
            ('state', 'in', ('approved', 'in_progress')),
        ])
        template = self.env.ref(
            'rgb_contract_management.mail_template_guarantee_expiry',
            raise_if_not_found=False,
        )
        for contract in contracts:
            if template:
                template.send_mail(contract.id, force_send=False)
            user = contract.responsible_user_id or contract.approval_user_id
            if user:
                contract.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=user.id,
                    summary=_('Performance guarantee expires in 60 days: %s') % contract.name,
                    date_deadline=contract.performance_guarantee_expiry_date,
                )

    @api.model
    def _cron_contract_expiry_reminder(self):
        today = fields.Date.context_today(self)
        from datetime import timedelta
        target = today + timedelta(days=30)
        contracts = self.search([
            ('date_end', '=', target),
            ('state', 'in', ('approved', 'in_progress')),
        ])
        template = self.env.ref(
            'rgb_contract_management.mail_template_contract_expiry',
            raise_if_not_found=False,
        )
        for contract in contracts:
            if template:
                template.send_mail(contract.id, force_send=False)

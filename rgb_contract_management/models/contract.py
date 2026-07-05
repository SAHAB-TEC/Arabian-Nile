# -*- coding: utf-8 -*-
import logging
from datetime import date, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


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
        string='Client Reference Number',
        tracking=True,
        copy=False,
        index=True,
        help='Unique client reference number shown on linked invoice prints.',
    )
    contract_name = fields.Char(
        string='Contract Name',
        tracking=True,
        copy=False,
    )
    contract_type = fields.Selection(
        selection=[
            ('purchase_contract', 'Expenses Contract'),
            ('sale_contract', 'Income Contract'),
        ],
        string='Contract Type',
        required=True,
        default='purchase_contract',
        tracking=True,
    )
    contract_business_type_id = fields.Many2one(
        'rgb.contract.business.type',
        string='Business Type',
        tracking=True,
        ondelete='restrict',
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
    exchange_rate = fields.Float(
        string='Exchange Rate',
        digits=(16, 6),
        default=1.0,
        tracking=True,
        help='Multiplier to LYD: Contract Value (LYD) = Contract Value × Exchange Rate '
             '(e.g. rate 5 → 6,000 becomes 30,000 LYD).',
    )
    contract_value_lyd = fields.Monetary(
        string='Contract Value (LYD)',
        currency_field='lyd_currency_id',
        tracking=True,
        compute='_compute_contract_value_lyd',
        store=True,
        readonly=True,
    )

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
        help='Deprecated: migrated to Payment Currency Split. Kept for upgrade migration.',
    )
    libya_dinar_percentage = fields.Float(
        string='LYD %',
        help='Deprecated: migrated to Payment Currency Split. Kept for upgrade migration.',
    )
    usd_amount = fields.Float(
        string='USD Amount',
        compute='_compute_legacy_currency_split_fields',
        store=True,
        help='Contract value share in USD from payment currency split.',
    )
    lyd_amount = fields.Float(
        string='LYD Amount',
        compute='_compute_legacy_currency_split_fields',
        store=True,
        help='Contract value share in LYD from payment currency split.',
    )
    currency_split_ids = fields.One2many(
        'rgb.contract.currency.split',
        'contract_id',
        string='Payment Currency Split',
        copy=True,
    )
    currency_split_percentage_total = fields.Float(
        string='Split Total (%)',
        compute='_compute_currency_split_percentage_total',
        digits=(16, 4),
    )
    contract_line_ids = fields.One2many(
        'rgb.contract.line',
        'contract_id',
        string='Invoice Lines',
        copy=True,
    )
    contract_lines_total = fields.Monetary(
        string='Lines Total',
        currency_field='currency_id',
        compute='_compute_contract_lines_total',
        store=True,
    )
    tax_type_use = fields.Selection(
        selection=[
            ('sale', 'Sales'),
            ('purchase', 'Purchases'),
        ],
        compute='_compute_tax_type_use',
        store=True,
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

    @api.constrains('contract_code', 'company_id')
    def _check_contract_code_unique(self):
        for contract in self.filtered('contract_code'):
            code = contract.contract_code.strip()
            if not code:
                continue
            code_key = code.lower()
            duplicates = self.search([
                ('id', '!=', contract.id),
                ('company_id', '=', contract.company_id.id),
                ('contract_code', '!=', False),
            ])
            for duplicate in duplicates:
                if (duplicate.contract_code or '').strip().lower() == code_key:
                    raise ValidationError(_(
                        'Client reference number "%(code)s" is already used on contract %(contract)s.',
                        code=code,
                        contract=duplicate.name,
                    ))

    @api.model
    def _deduplicate_contract_codes_for_unique_index(self):
        """Rename duplicate client references so the unique index can be created."""
        self.env.cr.execute("""
            WITH ranked AS (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY company_id, lower(btrim(contract_code))
                           ORDER BY id
                       ) AS rn
                FROM rgb_contract
                WHERE contract_code IS NOT NULL AND btrim(contract_code) <> ''
            )
            UPDATE rgb_contract c
            SET contract_code = btrim(c.contract_code) || '-' || c.id::text
            FROM ranked r
            WHERE c.id = r.id AND r.rn > 1
            RETURNING c.id, c.contract_code
        """)
        renamed = self.env.cr.fetchall()
        if renamed:
            _logger.warning(
                'Renamed %s duplicate rgb.contract client reference(s) before '
                'creating unique index: %s',
                len(renamed),
                renamed,
            )

    @api.model
    def init(self):
        super().init()
        cr = self.env.cr
        cr.execute("DROP INDEX IF EXISTS rgb_contract_client_ref_unique_ci")
        self._deduplicate_contract_codes_for_unique_index()
        cr.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS rgb_contract_client_ref_unique_ci
            ON rgb_contract (company_id, lower(btrim(contract_code)))
            WHERE contract_code IS NOT NULL AND btrim(contract_code) <> ''
        """)

    # ── Computes ──

    @api.depends('company_id')
    def _compute_lyd_currency_id(self):
        lyd = self.env['res.currency'].search([('name', '=', 'LYD')], limit=1)
        for contract in self:
            contract.lyd_currency_id = lyd.id if lyd else contract.currency_id.id

    def _get_suggested_exchange_rate(self):
        """Default rate from Odoo (contract currency → LYD at start date). User may override."""
        self.ensure_one()
        lyd_currency = self.env.ref('base.LYD', raise_if_not_found=False)
        if not self.currency_id or not lyd_currency or self.currency_id == lyd_currency:
            return 1.0
        conv_date = self.date_start or fields.Date.context_today(self)
        company = self.company_id or self.env.company
        return self.env['res.currency']._get_conversion_rate(
            self.currency_id,
            lyd_currency,
            company,
            conv_date,
        )

    @api.onchange('currency_id', 'date_start', 'company_id')
    def _onchange_currency_exchange_rate(self):
        self.exchange_rate = self._get_suggested_exchange_rate()

    @api.depends('contract_value_currency', 'exchange_rate')
    def _compute_contract_value_lyd(self):
        for contract in self:
            contract.contract_value_lyd = contract.contract_value_currency * (contract.exchange_rate or 0.0)

    @api.constrains('currency_split_ids')
    def _check_currency_split_total(self):
        usd = self.env.ref('base.USD', raise_if_not_found=False)
        lyd = self.env.ref('base.LYD', raise_if_not_found=False)
        for contract in self:
            if not contract.currency_split_ids:
                continue
            total = sum(contract.currency_split_ids.mapped('percentage'))
            if abs(total - 100.0) > 0.0001:
                raise ValidationError(_(
                    'Payment currency split must total 100%% (current total: %(total).2f%%).',
                    total=total,
                ))
            currency_ids = contract.currency_split_ids.mapped('currency_id')
            if len(currency_ids) != len(set(currency_ids.ids)):
                raise ValidationError(_(
                    'Each currency can appear only once in the payment split.',
                ))

    @api.depends('currency_split_ids.percentage')
    def _compute_currency_split_percentage_total(self):
        for contract in self:
            contract.currency_split_percentage_total = sum(
                contract.currency_split_ids.mapped('percentage')
            )

    @api.depends('contract_type')
    def _compute_tax_type_use(self):
        for contract in self:
            contract.tax_type_use = (
                'sale' if contract.contract_type == 'sale_contract' else 'purchase'
            )

    @api.depends('contract_line_ids.price_subtotal')
    def _compute_contract_lines_total(self):
        for contract in self:
            contract.contract_lines_total = sum(contract.contract_line_ids.mapped('price_subtotal'))

    @api.depends(
        'currency_split_ids',
        'currency_split_ids.percentage',
        'currency_split_ids.amount',
        'currency_split_ids.currency_id',
    )
    def _compute_legacy_currency_split_fields(self):
        usd_currency = self.env.ref('base.USD', raise_if_not_found=False)
        lyd_currency = self.env.ref('base.LYD', raise_if_not_found=False)
        for contract in self:
            contract.usd_amount = 0.0
            contract.lyd_amount = 0.0
            for line in contract.currency_split_ids:
                if usd_currency and line.currency_id == usd_currency:
                    contract.usd_amount = line.amount
                if lyd_currency and line.currency_id == lyd_currency:
                    contract.lyd_amount = line.amount

    def _prepare_currency_split_commands(self):
        """Return One2many commands to copy payment split lines to an invoice."""
        self.ensure_one()
        return [
            (0, 0, {
                'sequence': line.sequence,
                'currency_id': line.currency_id.id,
                'percentage': line.percentage,
            })
            for line in self.currency_split_ids
        ]

    def _prepare_invoice_line_commands(self):
        """Return One2many commands to copy contract lines to an invoice."""
        self.ensure_one()
        return [
            (0, 0, line._prepare_invoice_line_vals())
            for line in self.contract_line_ids
        ]

    def _clear_staging_invoice_lines(self):
        """Empty contract invoice lines after they were copied to an invoice."""
        for contract in self:
            if not contract.contract_line_ids:
                continue
            contract.contract_line_ids.unlink()
            contract.message_post(
                body=_(
                    'Invoice lines were cleared after creating an invoice. '
                    'Add new lines to prepare the next invoice.',
                ),
            )

    def _get_expiry_notification_users(self):
        self.ensure_one()
        group = self.env.ref(
            'rgb_contract_management.group_contract_expiry_notification',
            raise_if_not_found=False,
        )
        users = group.users.filtered('active') if group else self.env['res.users']
        if not users:
            users = (self.responsible_user_id | self.approval_user_id).filtered('active')
        return users

    def _notify_expiry_group(self, template_xmlid, summary, chatter_body, date_deadline):
        self.ensure_one()
        users = self._get_expiry_notification_users()
        if not users:
            return
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        for user in users:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary=summary,
                date_deadline=date_deadline,
            )
        emails = ','.join(filter(None, users.mapped('email')))
        if template and emails:
            template.send_mail(
                self.id,
                force_send=False,
                email_values={'email_to': emails},
            )
        self.message_post(
            body=chatter_body,
            partner_ids=users.partner_id.ids,
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

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
        context = {
            'default_contract_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_move_type': move_type,
            'default_currency_id': self.currency_id.id,
            'default_invoice_date': fields.Date.context_today(self),
            'default_analytic_distribution': self._get_analytic_distribution(),
        }
        if self.contract_line_ids:
            context['default_invoice_line_ids'] = self._prepare_invoice_line_commands()
        return context

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
    def _cron_performance_guarantee_group_reminder(self):
        """Daily: notify group 10 days before performance guarantee expiry."""
        today = fields.Date.context_today(self)
        target = today + timedelta(days=10)
        contracts = self.search([
            ('performance_guarantee_expiry_date', '=', target),
            ('state', 'in', ('approved', 'in_progress')),
        ])
        for contract in contracts:
            contract._notify_expiry_group(
                'rgb_contract_management.mail_template_performance_guarantee_group_expiry',
                summary=_('Performance guarantee expires in 10 days: %s') % contract.name,
                chatter_body=_(
                    'Performance guarantee expiry reminder: guarantee for this contract '
                    'expires on %(date)s (10 days remaining).',
                    date=contract.performance_guarantee_expiry_date,
                ),
                date_deadline=contract.performance_guarantee_expiry_date,
            )

    @api.model
    def _cron_performance_guarantee_reminder(self):
        """Daily: remind 60 days before performance guarantee expiry."""
        today = fields.Date.context_today(self)
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
        """Daily: notify group 10 days before contract end date."""
        today = fields.Date.context_today(self)
        target = today + timedelta(days=10)
        contracts = self.search([
            ('date_end', '=', target),
            ('state', 'in', ('approved', 'in_progress')),
        ])
        for contract in contracts:
            contract._notify_expiry_group(
                'rgb_contract_management.mail_template_contract_expiry',
                summary=_('Contract expires in 10 days: %s') % contract.name,
                chatter_body=_(
                    'Contract expiry reminder: this contract ends on %(date)s '
                    '(10 days remaining).',
                    date=contract.date_end,
                ),
                date_deadline=contract.date_end,
            )

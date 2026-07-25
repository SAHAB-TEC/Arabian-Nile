# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, AccessError


CUSTOMER_MOVE_TYPES = frozenset({'out_invoice', 'out_refund'})
VENDOR_MOVE_TYPES = frozenset({'in_invoice', 'in_refund'})
APPROVAL_MOVE_TYPES = CUSTOMER_MOVE_TYPES | VENDOR_MOVE_TYPES
WAITING_STATES = frozenset({'waiting_department', 'waiting_final'})
LOCKED_STATES = frozenset({'waiting_department', 'waiting_final', 'approved'})
FINANCIAL_LOCK_FIELDS = frozenset({
    'invoice_line_ids', 'line_ids', 'partner_id', 'currency_id',
    'invoice_payment_term_id', 'invoice_date', 'invoice_date_due',
    'fiscal_position_id', 'journal_id', 'company_id', 'move_type',
    'competent_department_id',
})


class AccountMove(models.Model):
    _inherit = 'account.move'

    approval_required = fields.Boolean(
        string='Approval Required',
        compute='_compute_approval_stored',
        store=True,
    )
    approval_state = fields.Selection(
        selection=[
            ('not_required', 'Not Required'),
            ('to_submit', 'Finance Draft'),
            ('waiting_department', 'Department Review'),
            ('waiting_final', 'Final Review'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Approval Status',
        default='not_required',
        tracking=True,
        copy=False,
        index=True,
    )
    competent_department_id = fields.Many2one(
        'rgb.invoice.approval.stage',
        string='Competent Department',
        domain="[('stage_role', '=', 'department'), ('active', '=', True), ('company_id', '=', company_id)]",
        tracking=True,
        copy=True,
        index=True,
        help='Department that must review this invoice before final finance review.',
    )
    approval_line_ids = fields.One2many(
        'rgb.invoice.approval.line',
        'move_id',
        string='Approval Path',
        copy=False,
    )
    current_approval_user_id = fields.Many2one(
        'res.users',
        string='Current Approver',
        compute='_compute_approval_stored',
        store=True,
    )
    current_approval_group_id = fields.Many2one(
        'res.groups',
        string='Current Approver Group',
        compute='_compute_approval_stored',
        store=True,
        index=True,
    )
    current_approval_stage = fields.Char(
        string='Current Stage',
        compute='_compute_approval_display',
    )
    approval_progress = fields.Char(
        string='Approval Progress',
        compute='_compute_approval_display',
    )
    can_current_user_approve = fields.Boolean(
        compute='_compute_can_current_user_approve',
    )
    is_financial_locked = fields.Boolean(
        string='Financial Data Locked',
        compute='_compute_is_financial_locked',
    )
    submit_button_label = fields.Char(
        string='Submit Label',
        compute='_compute_submit_button_label',
    )
    department_approver_user_id = fields.Many2one(
        'res.users',
        string='Department Approver',
        readonly=True,
        copy=False,
        tracking=True,
        help='User from the competent department who approved the invoice.',
    )

    def _get_approval_invoice_type(self):
        self.ensure_one()
        if self.move_type in CUSTOMER_MOVE_TYPES:
            return 'customer'
        if self.move_type in VENDOR_MOVE_TYPES:
            return 'vendor'
        return False

    @api.model
    def _stage_type_domain(self, invoice_type):
        return ['|', ('invoice_type', '=', 'both'), ('invoice_type', '=', invoice_type)]

    @api.model
    def _get_department_stages(self, company):
        return self.env['rgb.invoice.approval.stage'].search([
            ('company_id', '=', company.id),
            ('stage_role', '=', 'department'),
            ('active', '=', True),
        ], order='sequence, id')

    @api.model
    def _get_finance_final_stage(self, company, invoice_type=False):
        domain = [
            ('company_id', '=', company.id),
            ('stage_role', '=', 'finance_final'),
            ('active', '=', True),
        ]
        if invoice_type:
            domain += self._stage_type_domain(invoice_type)
        return self.env['rgb.invoice.approval.stage'].search(domain, limit=1)

    def _approval_is_required_for_move(self):
        self.ensure_one()
        invoice_type = self._get_approval_invoice_type()
        if not invoice_type or self.state != 'draft':
            return False
        return bool(
            self._get_department_stages(self.company_id)
            and self._get_finance_final_stage(self.company_id, invoice_type)
        )

    def _refresh_approval_requirement(self):
        for move in self.filtered(lambda m: m.move_type in APPROVAL_MOVE_TYPES):
            if move.state != 'draft':
                continue
            if move.approval_state in WAITING_STATES | {'approved'}:
                continue
            if move._approval_is_required_for_move():
                if move.approval_state in ('not_required', 'rejected'):
                    move.approval_state = 'to_submit'
            else:
                move.approval_state = 'not_required'
                move.approval_line_ids.sudo().unlink()

    def _user_in_group(self, group):
        return bool(group) and group in self.env.user.groups_id

    def _is_approval_manager(self):
        return self.env.user.has_group(
            'rgb_account_invoice_approval.group_invoice_approval_manager'
        )

    def _is_finance_user(self):
        return self.env.user.has_group('account.group_account_invoice')

    @api.depends(
        'move_type', 'company_id', 'state',
        'approval_line_ids', 'approval_line_ids.state',
        'approval_line_ids.group_id', 'approval_line_ids.user_id',
        'approval_state',
    )
    def _compute_approval_stored(self):
        for move in self:
            invoice_type = move._get_approval_invoice_type()
            departments = move._get_department_stages(move.company_id)
            finance_final = move._get_finance_final_stage(move.company_id, invoice_type)
            move.approval_required = (
                bool(departments and finance_final)
                and move.move_type in APPROVAL_MOVE_TYPES
                and move.state == 'draft'
            )
            pending_line = move.approval_line_ids.filtered(
                lambda line: line.state == 'pending'
            )[:1]
            move.current_approval_user_id = pending_line.user_id
            move.current_approval_group_id = pending_line.group_id

    @api.depends(
        'approval_line_ids', 'approval_line_ids.state',
        'approval_line_ids.stage_name', 'competent_department_id',
        'approval_state',
    )
    def _compute_approval_display(self):
        for move in self:
            pending_line = move.approval_line_ids.filtered(
                lambda line: line.state == 'pending'
            )[:1]
            if move.approval_state == 'waiting_department' and move.competent_department_id:
                move.current_approval_stage = _(
                    '%(dept)s Review',
                    dept=move.competent_department_id.name,
                )
            elif pending_line:
                move.current_approval_stage = pending_line.stage_name
            elif move.approval_state == 'to_submit':
                move.current_approval_stage = _('Finance Draft')
            elif move.approval_state == 'waiting_final':
                move.current_approval_stage = _('Final Review')
            elif move.approval_state == 'approved':
                move.current_approval_stage = _('Approved')
            elif move.approval_state == 'rejected':
                move.current_approval_stage = _('Rejected')
            else:
                move.current_approval_stage = ''
            approved_count = len(move.approval_line_ids.filtered(
                lambda line: line.state == 'approved'
            ))
            total_count = len(move.approval_line_ids)
            move.approval_progress = (
                f'{approved_count}/{total_count}' if total_count else ''
            )

    @api.depends(
        'current_approval_group_id', 'current_approval_user_id',
        'approval_state',
    )
    def _compute_can_current_user_approve(self):
        user = self.env.user
        is_manager = self._is_approval_manager()
        for move in self:
            if move.approval_state not in WAITING_STATES:
                move.can_current_user_approve = False
                continue
            if is_manager:
                move.can_current_user_approve = True
                continue
            if move.current_approval_group_id:
                move.can_current_user_approve = move._user_in_group(
                    move.current_approval_group_id
                )
            else:
                move.can_current_user_approve = move.current_approval_user_id == user

    @api.depends('approval_state')
    def _compute_is_financial_locked(self):
        for move in self:
            move.is_financial_locked = move.approval_state in LOCKED_STATES

    @api.depends('competent_department_id', 'competent_department_id.name')
    def _compute_submit_button_label(self):
        for move in self:
            if move.competent_department_id:
                move.submit_button_label = _(
                    'Send for Approval (%(dept)s)',
                    dept=move.competent_department_id.name,
                )
            else:
                move.submit_button_label = _('Send for Approval')

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves._refresh_approval_requirement()
        return moves

    def write(self, vals):
        if not self.env.su and not self._is_approval_manager():
            locked = self.filtered(lambda m: m.approval_state in LOCKED_STATES)
            if locked and FINANCIAL_LOCK_FIELDS.intersection(vals):
                raise UserError(_(
                    'Financial data is locked after the invoice left Finance. '
                    'You can only use Reject / Approve / Recall, or add chatter notes.'
                ))
        res = super().write(vals)
        if {'move_type', 'company_id', 'state'} & set(vals):
            self._refresh_approval_requirement()
        return res

    def _check_approval_before_post(self):
        for move in self.filtered(lambda m: m.move_type in APPROVAL_MOVE_TYPES):
            if not move.approval_required:
                continue
            if move.approval_state == 'approved':
                continue
            if move.approval_state in (
                'to_submit', 'waiting_department', 'waiting_final', 'rejected',
            ):
                raise UserError(_(
                    'Invoice %(invoice)s cannot be confirmed until department and '
                    'final finance approval are completed.',
                    invoice=move.display_name,
                ))

    def action_post(self):
        self._check_approval_before_post()
        return super().action_post()

    def action_submit_for_approval(self):
        self._check_can_submit_for_approval()
        for move in self:
            move._build_approval_lines()
            move.write({
                'approval_state': 'waiting_department',
                'department_approver_user_id': False,
            })
            move.message_post(
                body=_(
                    'Invoice submitted for approval to department "%(dept)s".',
                    dept=move.competent_department_id.name,
                ),
                subtype_xmlid='mail.mt_note',
            )
            move._notify_current_approvers()
        return True

    def _check_can_submit_for_approval(self):
        for move in self:
            if move.state != 'draft':
                raise UserError(_('Only draft invoices can be submitted for approval.'))
            if not move.approval_required:
                raise UserError(_('No approval workflow is configured for this invoice type.'))
            if not move.competent_department_id:
                raise UserError(_('Please select the Competent Department before submitting.'))
            if move.approval_state not in ('to_submit', 'rejected'):
                raise UserError(_('This invoice is already in the approval workflow.'))

    def _build_approval_lines(self):
        self.ensure_one()
        department = self.competent_department_id
        if not department or department.stage_role != 'department':
            raise UserError(_('Please select a valid Competent Department.'))
        finance_final = self._get_finance_final_stage(
            self.company_id, self._get_approval_invoice_type(),
        )
        if not finance_final:
            raise UserError(_('No Finance Final Review stage is configured.'))

        Line = self.env['rgb.invoice.approval.line'].sudo()
        self.approval_line_ids.sudo().unlink()
        Line.create({
            'move_id': self.id,
            'stage_id': department.id,
            'stage_name': _('%(dept)s Review', dept=department.name),
            'stage_role': 'department',
            'sequence': 10,
            'group_id': department.group_id.id,
            'user_id': department.user_id.id if department.user_id else False,
            'state': 'pending',
        })
        Line.create({
            'move_id': self.id,
            'stage_id': finance_final.id,
            'stage_name': finance_final.name or _('Final Review'),
            'stage_role': 'finance_final',
            'sequence': 20,
            'group_id': finance_final.group_id.id,
            'user_id': finance_final.user_id.id if finance_final.user_id else False,
            'state': 'waiting',
        })

    def action_approve_invoice(self):
        self._check_can_approve()
        for move in self:
            move_sudo = move.sudo()
            pending = move_sudo.approval_line_ids.filtered(
                lambda line: line.state == 'pending'
            )[:1]
            if not pending:
                raise UserError(_('No pending approval stage found.'))
            pending.write({
                'state': 'approved',
                'approved_by': self.env.user.id,
                'approved_date': fields.Datetime.now(),
            })
            move_sudo._done_approval_activities(pending)

            if pending.stage_role == 'department':
                move_sudo.department_approver_user_id = self.env.user.id

            next_line = move_sudo.approval_line_ids.filtered(
                lambda line: line.state == 'waiting'
            ).sorted('sequence')[:1]
            if next_line:
                next_line.write({'state': 'pending'})
                next_state = (
                    'waiting_final'
                    if next_line.stage_role == 'finance_final'
                    else 'waiting_department'
                )
                move_sudo.approval_state = next_state
                move_sudo.message_post(
                    body=_(
                        'Approved by %(user)s at stage "%(stage)s". '
                        'Next: %(next_stage)s.',
                        user=self.env.user.name,
                        stage=pending.stage_name,
                        next_stage=next_line.stage_name,
                    ),
                    subtype_xmlid='mail.mt_note',
                    author_id=self.env.user.partner_id.id,
                )
                move_sudo._notify_current_approvers()
            else:
                move_sudo.approval_state = 'approved'
                move_sudo.message_post(
                    body=_(
                        'Final approval completed by %(user)s. '
                        'Invoice can now be confirmed.',
                        user=self.env.user.name,
                    ),
                    subtype_xmlid='mail.mt_note',
                    author_id=self.env.user.partner_id.id,
                )
        return True

    def _check_can_approve(self):
        is_manager = self._is_approval_manager()
        for move in self:
            if move.approval_state not in WAITING_STATES:
                raise UserError(_('This invoice is not waiting for approval.'))
            if is_manager:
                continue
            if move.current_approval_group_id:
                if not move._user_in_group(move.current_approval_group_id):
                    raise AccessError(_(
                        'You are not allowed to approve this stage '
                        '(required group: %(group)s).',
                        group=move.current_approval_group_id.display_name,
                    ))
            elif move.current_approval_user_id != self.env.user:
                raise AccessError(_('You are not the current approver for this invoice.'))

    def action_open_reject_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Invoice'),
            'res_model': 'rgb.invoice.approval.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_move_id': self.id},
        }

    def action_reject_invoice(self, note=False):
        self._check_can_approve()
        for move in self:
            move_sudo = move.sudo()
            pending = move_sudo.approval_line_ids.filtered(
                lambda line: line.state == 'pending'
            )[:1]
            if pending:
                pending.write({
                    'state': 'rejected',
                    'approved_by': self.env.user.id,
                    'approved_date': fields.Datetime.now(),
                    'note': note or '',
                })
                move_sudo._done_approval_activities(pending)
            move_sudo.approval_line_ids.filtered(
                lambda line: line.state == 'waiting'
            ).write({'state': 'skipped'})
            move_sudo.write({
                'approval_state': 'rejected',
                'department_approver_user_id': False,
            })
            body = _('Invoice rejected by %(user)s.', user=self.env.user.name)
            if note:
                body += '<br/>%s' % note
            move_sudo.message_post(
                body=body,
                subtype_xmlid='mail.mt_comment',
                author_id=self.env.user.partner_id.id,
            )
        return True

    def action_recall_approval(self):
        if not (self._is_finance_user() or self._is_approval_manager()):
            raise AccessError(_('Only Finance users can recall invoices.'))
        for move in self:
            if move.state != 'draft':
                raise UserError(_('Only draft invoices can be recalled.'))
            if move.approval_state not in WAITING_STATES | {'approved', 'rejected'}:
                raise UserError(_('This invoice cannot be recalled in its current state.'))
            move._done_all_approval_activities()
            move.approval_line_ids.sudo().unlink()
            move.write({
                'approval_state': (
                    'to_submit' if move._approval_is_required_for_move() else 'not_required'
                ),
                'department_approver_user_id': False,
            })
            move.message_post(
                body=_('Invoice recalled to Finance Draft by %(user)s.', user=self.env.user.name),
                subtype_xmlid='mail.mt_note',
            )
        return True

    def action_reset_approval(self):
        if not self._is_approval_manager():
            raise AccessError(_('Only approval managers can reset the workflow.'))
        return self.action_recall_approval()

    def _get_pending_approver_users(self):
        """Users allowed to act on the pending stage (permission / cleanup scope)."""
        self.ensure_one()
        pending = self.approval_line_ids.filtered(lambda line: line.state == 'pending')[:1]
        if not pending:
            return self.env['res.users']
        users = self.env['res.users']
        if pending.group_id:
            users |= pending.group_id.users.filtered(lambda u: u.active and not u.share)
        if pending.user_id:
            users |= pending.user_id
        if pending.stage_role == 'finance_final' and not users:
            finance_group = self.env.ref('account.group_account_invoice')
            users |= finance_group.users.filtered(lambda u: u.active and not u.share)
        return users

    def _get_notification_users(self):
        """
        Recipients for email / activity / inbox.

        Department: users of the department group (usually few).
        Finance final: do NOT notify every Invoicing user — only the optional stage
        user, else the invoice salesperson / creator (if internal).
        Any finance user can still approve via group permission.
        """
        self.ensure_one()
        pending = self.approval_line_ids.filtered(lambda line: line.state == 'pending')[:1]
        if not pending:
            return self.env['res.users']

        if pending.user_id and pending.user_id.active and not pending.user_id.share:
            return pending.user_id

        if pending.stage_role == 'finance_final':
            for candidate in (self.invoice_user_id, self.create_uid):
                if candidate and candidate.active and not candidate.share:
                    return candidate
            return self.env['res.users']

        if pending.group_id:
            return pending.group_id.users.filtered(lambda u: u.active and not u.share)
        return self.env['res.users']

    def _cleanup_open_approval_activities(self):
        """Remove duplicate / stale approval To-Dos before creating new ones."""
        self.ensure_one()
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        activities = self.sudo().activity_ids.filtered(
            lambda act: act.activity_type_id == activity_type
            and act.summary
            and act.summary.startswith('Invoice approval:')
        )
        if activities:
            activities.unlink()

    def _notify_current_approvers(self):
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        for move in self.sudo():
            recipients = move._get_notification_users()
            summary = _('Invoice approval: %(invoice)s — %(stage)s') % {
                'invoice': move.name or move.ref or move.id,
                'stage': move.current_approval_stage,
            }
            body = _(
                'Your approval is required for invoice %(invoice)s at stage "%(stage)s".',
                invoice=move.display_name,
                stage=move.current_approval_stage,
            )

            # Always clear previous approval activities to avoid duplicates
            move._cleanup_open_approval_activities()

            # One chatter note (not one email log per user)
            move.message_post(
                body=body,
                subject=summary,
                subtype_xmlid='mail.mt_note',
            )

            if not recipients:
                continue

            # Inbox: one call for all partners
            move.message_notify(
                partner_ids=recipients.mapped('partner_id').ids,
                body=body,
                subject=summary,
            )

            # Activities: one To-Do per recipient only
            for user in recipients:
                move.activity_schedule(
                    activity_type_id=activity_type.id,
                    user_id=user.id,
                    summary=summary,
                )

            # Emails: one mail.mail (no per-user chatter spam from template.send_mail)
            emails = [email for email in recipients.mapped('email') if email]
            if emails:
                self.env['mail.mail'].sudo().create({
                    'subject': summary,
                    'body_html': '<p>%s</p>' % body,
                    'email_to': ','.join(emails),
                    'auto_delete': True,
                })

    def _done_approval_activities(self, pending_line):
        self.ensure_one()
        # Complete all open approval To-Dos on this invoice (not only current group)
        self._cleanup_open_approval_activities()

    def _done_all_approval_activities(self):
        self.ensure_one()
        self._cleanup_open_approval_activities()

    @api.model
    def _cron_remind_pending_approvals(self):
        pending_moves = self.search([
            ('approval_state', 'in', list(WAITING_STATES)),
            ('state', '=', 'draft'),
        ])
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        for move in pending_moves:
            recipients = move._get_notification_users()
            overdue = move.activity_ids.filtered(
                lambda act: act.activity_type_id == activity_type
                and act.user_id in recipients
                and act.date_deadline
                and act.date_deadline < fields.Date.today()
            )
            if overdue:
                move._notify_current_approvers()

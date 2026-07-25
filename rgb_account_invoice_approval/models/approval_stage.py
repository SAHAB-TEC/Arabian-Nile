# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RgbInvoiceApprovalStage(models.Model):
    _name = 'rgb.invoice.approval.stage'
    _description = 'Invoice Approval Stage / Department'
    _order = 'stage_role, sequence, id'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        help='Department or stage label shown on the invoice.',
    )
    code = fields.Char(
        string='Code',
        index=True,
        help='Technical code, e.g. it, operations, marketing.',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    stage_role = fields.Selection(
        selection=[
            ('department', 'Department Review'),
            ('finance_final', 'Finance Final Review'),
        ],
        string='Role',
        required=True,
        default='department',
        index=True,
    )
    invoice_type = fields.Selection(
        selection=[
            ('customer', 'Customer Invoices'),
            ('vendor', 'Vendor Bills'),
            ('both', 'Customer & Vendor'),
        ],
        string='Invoice Type',
        required=True,
        default='both',
        index=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    group_id = fields.Many2one(
        'res.groups',
        string='Approver Group',
        required=True,
        help='Odoo security group allowed to approve at this stage.',
    )
    user_id = fields.Many2one(
        'res.users',
        string='Optional Approver',
        domain="[('share', '=', False)]",
        help='Optional. Group membership is used for approvals.',
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            'sequence_positive',
            'CHECK(sequence >= 0)',
            'Sequence must be zero or positive.',
        ),
    ]

    @api.constrains('stage_role', 'company_id', 'active')
    def _check_one_finance_final(self):
        for stage in self.filtered(
            lambda s: s.stage_role == 'finance_final' and s.active
        ):
            duplicates = self.search_count([
                ('id', '!=', stage.id),
                ('company_id', '=', stage.company_id.id),
                ('stage_role', '=', 'finance_final'),
                ('active', '=', True),
            ])
            if duplicates:
                raise ValidationError(
                    'Only one active Finance Final Review stage is allowed per company.'
                )

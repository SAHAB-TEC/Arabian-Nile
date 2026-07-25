# -*- coding: utf-8 -*-
from odoo import fields, models


class RgbInvoiceApprovalLine(models.Model):
    _name = 'rgb.invoice.approval.line'
    _description = 'Invoice Approval Line'
    _order = 'move_id, sequence, id'

    move_id = fields.Many2one(
        'account.move',
        string='Invoice',
        required=True,
        ondelete='cascade',
        index=True,
    )
    stage_id = fields.Many2one(
        'rgb.invoice.approval.stage',
        string='Stage Config',
        ondelete='set null',
    )
    stage_name = fields.Char(
        string='Stage',
        required=True,
    )
    stage_role = fields.Selection(
        selection=[
            ('department', 'Department Review'),
            ('finance_final', 'Finance Final Review'),
        ],
        string='Role',
        index=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    group_id = fields.Many2one(
        'res.groups',
        string='Approver Group',
        index=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Approver',
        index=True,
    )
    state = fields.Selection(
        selection=[
            ('waiting', 'Waiting'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('skipped', 'Skipped'),
        ],
        string='Status',
        default='waiting',
        required=True,
        index=True,
    )
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
    )
    approved_date = fields.Datetime(
        string='Approval Date',
        readonly=True,
    )
    note = fields.Text(
        string='Note',
        readonly=True,
    )
    company_id = fields.Many2one(
        related='move_id.company_id',
        store=True,
        readonly=True,
    )

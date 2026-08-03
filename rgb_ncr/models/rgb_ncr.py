# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class RgbNcr(models.Model):
    _name = 'rgb.ncr'
    _description = 'Non-Conformance Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='NCR Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    date = fields.Date(
        string='Discovery Date',
        default=fields.Date.context_today,
        tracking=True,
    )

    # Linking / governance
    project_id = fields.Many2one(
        'construction.project',
        string='Project',
        required=True,
        tracking=True,
        index=True,
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        related='project_id.analytic_account_id',
        store=True,
        readonly=True,
    )
    sub_project_id = fields.Many2one(
        'construction.sub.project',
        string='Sub Project',
        domain="[('project_id', '=', project_id)]",
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Contractor / Vendor',
        required=True,
        tracking=True,
        domain="[('supplier_rank', '>', 0)]",
        index=True,
    )
    work_order_id = fields.Many2one(
        'construction.work.order',
        string='Work Order',
        domain="[('project_id', '=', project_id)]",
        tracking=True,
    )

    # Technical / geographic
    defect_description = fields.Text(string='Defect Description', required=True)
    latitude = fields.Float(string='Latitude', digits=(16, 6))
    longitude = fields.Float(string='Longitude', digits=(16, 6))

    # Corrective
    root_cause = fields.Selection(
        selection=[
            ('technician_skill', 'ضعف كفاءة الفني'),
            ('nonconforming_material', 'مواد غير مطابقة'),
            ('worn_equipment', 'معدات متهالكة'),
            ('bad_weather', 'ظروف جوية سيئة'),
        ],
        string='Root Cause',
        tracking=True,
    )
    corrective_action = fields.Text(string='Corrective Action')

    # Attachments
    before_image_ids = fields.One2many(
        'rgb.ncr.image',
        'ncr_id',
        string='Before Images',
        domain=[('image_type', '=', 'before')],
        context={'default_image_type': 'before'},
    )
    after_image_ids = fields.One2many(
        'rgb.ncr.image',
        'ncr_id',
        string='After Images',
        domain=[('image_type', '=', 'after')],
        context={'default_image_type': 'after'},
    )
    ndt_report = fields.Binary(string='NDT / X-Ray Report', attachment=True)
    ndt_report_filename = fields.Char(string='NDT Report Filename')

    state = fields.Selection(
        selection=[
            ('open', 'Open'),
            ('under_review', 'Under Review'),
            ('closed', 'Closed'),
        ],
        string='Status',
        default='open',
        required=True,
        tracking=True,
        copy=False,
        index=True,
    )
    financial_freeze = fields.Boolean(
        string='Financial Freeze',
        compute='_compute_financial_freeze',
        store=True,
        help='When active, contractor invoices and RA billings for this project are blocked.',
    )
    after_images_editable = fields.Boolean(compute='_compute_after_images_editable')

    @api.depends('state')
    def _compute_financial_freeze(self):
        for rec in self:
            rec.financial_freeze = rec.state in ('open', 'under_review')

    @api.depends('state')
    def _compute_after_images_editable(self):
        for rec in self:
            rec.after_images_editable = rec.state == 'under_review'

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.sub_project_id and self.sub_project_id.project_id != self.project_id:
            self.sub_project_id = False
        if self.work_order_id and self.work_order_id.project_id != self.project_id:
            self.work_order_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) in (_('New'), 'New', False):
                vals['name'] = self.env['ir.sequence'].next_by_code('rgb.ncr') or _('New')
            vals.setdefault('state', 'open')
        records = super().create(vals_list)
        for rec in records.filtered(lambda n: n.state in ('open', 'under_review')):
            rec._post_freeze_message(frozen=True)
        return records

    def write(self, vals):
        previous = {rec.id: rec.state for rec in self}
        res = super().write(vals)
        if 'state' in vals:
            for rec in self:
                old_state = previous.get(rec.id)
                if old_state == vals['state']:
                    continue
                if vals['state'] in ('open', 'under_review') and old_state == 'closed':
                    rec._post_freeze_message(frozen=True)
                elif vals['state'] == 'closed' and old_state in ('open', 'under_review'):
                    if not rec._has_other_active_freeze():
                        rec._post_freeze_message(frozen=False)
        return res

    def _has_other_active_freeze(self):
        self.ensure_one()
        return bool(self.search_count([
            ('id', '!=', self.id),
            ('project_id', '=', self.project_id.id),
            ('partner_id', '=', self.partner_id.id),
            ('state', 'in', ('open', 'under_review')),
        ]))

    def _post_freeze_message(self, frozen=True):
        self.ensure_one()
        if frozen:
            body = _(
                'Financial freeze activated for contractor %(partner)s on project %(project)s.',
                partner=self.partner_id.display_name,
                project=self.project_id.display_name,
            )
        else:
            body = _(
                'Financial freeze released for contractor %(partner)s on project %(project)s.',
                partner=self.partner_id.display_name,
                project=self.project_id.display_name,
            )
        self.message_post(body=body)

    @api.model
    def _get_active_freeze(self, project_id, partner_id):
        if not project_id or not partner_id:
            return self.browse()
        return self.search([
            ('project_id', '=', project_id),
            ('partner_id', '=', partner_id),
            ('state', 'in', ('open', 'under_review')),
        ], limit=1)

    @api.model
    def _raise_if_frozen(self, project_id, partner_id, document_label=None):
        ncr = self._get_active_freeze(project_id, partner_id)
        if not ncr:
            return
        label = document_label or _('this document')
        raise UserError(_(
            'Financial freeze is active due to open NCR %(ncr)s.\n'
            'Contractor: %(partner)s\n'
            'Project: %(project)s\n'
            'You cannot process %(document)s until the NCR is approved and closed.',
            ncr=ncr.name,
            partner=ncr.partner_id.display_name,
            project=ncr.project_id.display_name,
            document=label,
        ))

    def action_set_under_review(self):
        for rec in self:
            if rec.state != 'open':
                raise UserError(_('Only open NCRs can move to Under Review.'))
        self.write({'state': 'under_review'})

    def action_approve_close(self):
        for rec in self:
            if rec.state != 'under_review':
                raise UserError(_('Only NCRs under review can be approved and closed.'))
            if not rec.after_image_ids:
                raise UserError(_(
                    'Upload after-repair images before approving and closing NCR %s.'
                ) % rec.name)
        self.write({'state': 'closed'})

    def action_reopen(self):
        for rec in self:
            if rec.state != 'closed':
                raise UserError(_('Only closed NCRs can be reopened.'))
        self.write({'state': 'open'})


class RgbNcrImage(models.Model):
    _name = 'rgb.ncr.image'
    _description = 'NCR Image'
    _order = 'id'

    ncr_id = fields.Many2one('rgb.ncr', string='NCR', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Description')
    image = fields.Binary(string='Image', required=True, attachment=True)
    image_filename = fields.Char(string='Filename')
    image_type = fields.Selection(
        selection=[
            ('before', 'Before'),
            ('after', 'After'),
        ],
        string='Type',
        required=True,
        default='before',
    )

    @api.constrains('ncr_id', 'image_type')
    def _check_after_images_state(self):
        for rec in self.filtered(lambda i: i.image_type == 'after'):
            if rec.ncr_id.state == 'open':
                raise ValidationError(_(
                    'After-repair images can only be added when the NCR is Under Review.'
                ))

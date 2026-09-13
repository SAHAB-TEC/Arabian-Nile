# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression

APPROVAL_ACTIVITY_XMLID = 'mail.mail_activity_data_todo'


class ProductTemplate(models.Model):
    # Safely add mail.thread / mail.activity.mixin to product.template.
    # Odoo merges _inherit lists on the same model name, so this is safe
    # even if product.template already inherits one of these mixins.
    _name = 'product.template'
    _inherit = ['product.template', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('approved', 'Approved'),
        ],
        string='Approval Status',
        default='draft',
        copy=False,
        tracking=True,
        help='A newly created product starts as Draft and must be '
             'approved by an authorized user before it can be freely '
             'selected in Sales, Purchase or Inventory operations.',
    )

    created_by_user_id = fields.Many2one(
        'res.users',
        string='Created By',
        readonly=True,
        copy=False,
    )
    created_on_date = fields.Datetime(
        string='Created On',
        readonly=True,
        copy=False,
    )
    approved_by_user_id = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        copy=False,
    )
    approved_on_date = fields.Datetime(
        string='Approved On',
        readonly=True,
        copy=False,
    )

    can_approve = fields.Boolean(
        string='Can Current User Approve',
        compute='_compute_can_approve',
        help='Technical field used to show/hide the Approve button for '
             'the currently logged-in user.',
    )

    @api.depends('state')
    def _compute_can_approve(self):
        is_approver = self.env.user.has_product_approval_rights
        for product in self:
            product.can_approve = is_approver and product.state == 'draft'

    # ------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault('created_by_user_id', self.env.user.id)
            vals.setdefault('created_on_date', fields.Datetime.now())
        products = super().create(vals_list)
        for product in products:
            if product.state == 'draft':
                product._notify_approvers()
        return products

    # ------------------------------------------------------------
    # Business logic
    # ------------------------------------------------------------
    def _notify_approvers(self):
        """Schedule a To-Do activity for every user allowed to approve
        products, asking them to review this newly created product."""
        self.ensure_one()
        approvers = self.env['res.users'].sudo().search(
            [('has_product_approval_rights', '=', True)]
        )
        if not approvers:
            return
        activity_type = self.env.ref(APPROVAL_ACTIVITY_XMLID, raise_if_not_found=False)
        for approver in approvers:
            self.activity_schedule(
                activity_type_id=activity_type.id if activity_type else False,
                summary=_('New product requires approval'),
                note=_(
                    'The product "%(name)s" was created by %(creator)s and '
                    'is waiting for your approval.',
                    name=self.display_name,
                    creator=self.created_by_user_id.name or self.env.user.name,
                ),
                user_id=approver.id,
            )

    def action_approve(self):
        """Approve the product: only allowed for users flagged with
        has_product_approval_rights, and only from the draft state."""
        for product in self:
            if not self.env.user.has_product_approval_rights:
                raise UserError(_(
                    "You are not authorized to approve products. "
                    "Please contact your administrator."
                ))
            if product.state != 'draft':
                raise UserError(_(
                    "Only products in the Draft state can be approved."
                ))
            product.write({
                'state': 'approved',
                'approved_by_user_id': self.env.user.id,
                'approved_on_date': fields.Datetime.now(),
            })
            product._done_approval_activities()
        return True

    def _done_approval_activities(self):
        """Mark all pending activities for this product as done."""
        self.ensure_one()
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'product.template'),
            ('res_id', '=', self.id),
        ])
        if activities:
            activities.action_feedback(feedback=_('Product approved.'))

    def action_open_approval_info(self):
        """Smart button action: open a small popup with the audit trail."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Approval Info'),
            'res_model': 'product.template',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref(
                'custom_product_approval.view_product_template_approval_info_form'
            ).id,
            'target': 'new',
        }

    # ------------------------------------------------------------
    # Restrict draft products from standard selection widgets
    # (Sales, Purchase, Inventory, ...) without adding a hard
    # dependency on those modules: any Many2one field pointing to
    # product.template / product.product uses name_search to build
    # its drop-down, so filtering it here is enough to keep
    # unapproved products out of those operations while still
    # letting approvers manage them from the Products menu.
    # ------------------------------------------------------------
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = list(args or [])
        bypass = (
            self.env.context.get('show_draft_products')
            or self.env.user.has_product_approval_rights
            or self.env.user.has_group('base.group_system')
        )
        if not bypass:
            args = expression.AND([args, [('state', '=', 'approved')]])
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

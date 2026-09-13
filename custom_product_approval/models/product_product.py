# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.osv import expression


class ProductProduct(models.Model):
    """Order lines in Sales, Purchase and Inventory pick a product.product
    record (the variant), not a product.template directly, so the same
    active-based hiding and name_search safety net are mirrored here."""
    _inherit = 'product.product'

    # NOTE: product.product's own form view (product_normal_form_view)
    # inherits its arch from product.template's form view (Odoo's
    # _inherits delegation copies the arch, but NOT the Python methods,
    # across the two models). That means the Approve button and the
    # Approval Info smart button we added on product.template also
    # render on the Product Variant form, bound to product.product.
    # These two delegate methods make sure clicking them from a
    # variant record works exactly like clicking them from the
    # template record.
    def action_approve(self):
        return self.mapped('product_tmpl_id').action_approve()

    def action_open_approval_info(self):
        self.ensure_one()
        return self.product_tmpl_id.action_open_approval_info()

    def write(self, vals):
        # Mirror product.template's guard: a variant can't be manually
        # unarchived unless its template has actually been approved.
        # The template's own write() cascades 'active' down to variants
        # with the from_action_approve context flag already set, so
        # that legitimate path is unaffected.
        if vals.get('active') and not self.env.context.get('from_action_approve'):
            for variant in self:
                if variant.product_tmpl_id.state != 'approved':
                    raise UserError(_(
                        "This variant's product is still Draft. Approve "
                        "the product template first."
                    ))
        return super().write(vals)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = list(args or [])
        bypass = (
            self.env.context.get('show_draft_products')
            or self.env.user.has_product_approval_rights
            or self.env.user.has_group('base.group_system')
        )
        model = self
        if bypass:
            model = self.with_context(active_test=False)
        else:
            args = expression.AND([args, [('product_tmpl_id.state', '=', 'approved')]])
        return super(ProductProduct, model).name_search(name=name, args=args, operator=operator, limit=limit)


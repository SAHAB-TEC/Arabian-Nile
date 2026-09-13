# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.osv import expression


class ProductProduct(models.Model):
    """Order lines in Sales, Purchase and Inventory pick a product.product
    record (the variant), not a product.template directly. Mirroring the
    name_search restriction here keeps Draft products out of those
    operations as well, without requiring sale/purchase/stock as
    dependencies of this module."""
    _inherit = 'product.product'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = list(args or [])
        bypass = (
            self.env.context.get('show_draft_products')
            or self.env.user.has_product_approval_rights
            or self.env.user.has_group('base.group_system')
        )
        if not bypass:
            args = expression.AND([args, [('product_tmpl_id.state', '=', 'approved')]])
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

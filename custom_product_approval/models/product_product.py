# -*- coding: utf-8 -*-
from odoo import models


class ProductProduct(models.Model):
    """product.product's own form view (product_normal_form_view) inherits
    its arch from product.template's form view - Odoo's _inherits
    delegation copies the arch, but NOT the Python methods, across the
    two models. That means the Approve button and the Approval Info
    smart button added on product.template also render on the Product
    Variant form, bound to product.product. These delegate methods make
    sure clicking them from a variant record works exactly like
    clicking them from the template record."""
    _inherit = 'product.product'

    def action_approve(self):
        return self.mapped('product_tmpl_id').action_approve()

    def action_open_approval_info(self):
        self.ensure_one()
        return self.product_tmpl_id.action_open_approval_info()

    def _ensure_approved_for_use(self):
        """Delegate to product.template - order lines / stock moves
        reference product.product (the variant), so bridge modules call
        this on a product.product recordset."""
        self.mapped('product_tmpl_id')._ensure_approved_for_use()

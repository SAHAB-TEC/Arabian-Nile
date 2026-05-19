# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    rgb_abarios_name = fields.Char(
        related='product_tmpl_id.rgb_abarios_name',
        string='ABARIOS Name',
        readonly=False,
        store=True,
    )
    rgb_unit_size = fields.Char(
        related='product_tmpl_id.rgb_unit_size',
        string='Unit Size',
        readonly=False,
        store=True,
    )
    rgb_unit_packing = fields.Char(
        related='product_tmpl_id.rgb_unit_packing',
        string='Unit Packing',
        readonly=False,
        store=True,
    )

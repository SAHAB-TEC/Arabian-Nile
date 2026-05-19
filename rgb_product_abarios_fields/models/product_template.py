# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    rgb_abarios_name = fields.Char(
        string='ABARIOS Name',
        tracking=True,
    )
    rgb_unit_size = fields.Char(
        string='Unit Size',
        tracking=True,
    )
    rgb_unit_packing = fields.Char(
        string='Unit Packing',
        tracking=True,
    )

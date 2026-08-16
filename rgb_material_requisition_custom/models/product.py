# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    rgb_analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        company_dependent=True,
        index=True,
        help="Product analytic account used together with the Material Requisition "
             "analytic account on inventory transfer journal entries.",
    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    rgb_analytic_account_id = fields.Many2one(
        related="product_tmpl_id.rgb_analytic_account_id",
        string="Analytic Account",
        readonly=False,
    )

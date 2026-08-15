# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.osv import expression


class AccountAnalyticPlan(models.Model):
    _inherit = "account.analytic.plan"

    rgb_invisible = fields.Boolean(
        string="Invisible",
        default=False,
        index=True,
        help="If checked, this analytic plan cannot be searched or selected "
             "in any other screen or transaction.",
    )

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        domain = list(domain or [])
        if not self.env.context.get("rgb_show_invisible_analytic"):
            domain = expression.AND([
                domain,
                [("rgb_invisible", "=", False)],
            ])
        return super()._search(domain, offset=offset, limit=limit, order=order)

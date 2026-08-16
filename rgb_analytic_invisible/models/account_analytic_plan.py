# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError
from odoo.osv import expression

from .rgb_invisible_utils import rgb_domain_resolves_ids


class AccountAnalyticPlan(models.Model):
    _inherit = "account.analytic.plan"

    rgb_invisible = fields.Boolean(
        string="Invisible",
        default=False,
        index=True,
        help="If checked, this analytic plan cannot be searched or selected "
             "in any other screen or transaction.",
    )

    def write(self, vals):
        if "rgb_invisible" in vals and not self.env.user.has_group(
            "rgb_analytic_invisible.group_analytic_invisible_manager"
        ):
            raise AccessError(_("You are not allowed to change the Invisible flag."))
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get("rgb_invisible") for vals in vals_list) and not self.env.user.has_group(
            "rgb_analytic_invisible.group_analytic_invisible_manager"
        ):
            raise AccessError(_("You are not allowed to set the Invisible flag."))
        return super().create(vals_list)

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        domain = list(domain or [])
        if (
            not self.env.context.get("rgb_show_invisible_analytic")
            and not rgb_domain_resolves_ids(domain)
        ):
            domain = expression.AND([
                domain,
                [("rgb_invisible", "=", False)],
            ])
        return super()._search(domain, offset=offset, limit=limit, order=order)

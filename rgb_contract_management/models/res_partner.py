# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_contractor = fields.Boolean(
        string='Is Contractor',
        help='When checked, this partner appears in contractor lists for purchase contracts.',
    )

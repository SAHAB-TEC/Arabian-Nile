# -*- coding: utf-8 -*-
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    has_product_approval_rights = fields.Boolean(
        string='Can Approve Products',
        default=False,
        help='If checked, this user is notified when a new product is '
             'created and is allowed to approve it.',
    )

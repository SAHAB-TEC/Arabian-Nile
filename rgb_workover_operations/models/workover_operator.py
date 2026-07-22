# -*- coding: utf-8 -*-
from odoo import fields, models


class WorkoverOperator(models.Model):
    _name = 'workover.operator'
    _description = 'Workover Operator'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)

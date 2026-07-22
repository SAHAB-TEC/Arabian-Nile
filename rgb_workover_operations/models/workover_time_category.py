# -*- coding: utf-8 -*-
from odoo import fields, models


class WorkoverTimeCategory(models.Model):
    _name = 'workover.time.category'
    _description = 'Workover Time Breakdown Category'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)
    summary_column = fields.Selection(
        selection=[
            ('full_ops', 'Full Ops Hrs'),
            ('standby_wcrew', 'Stand-By W/Crew'),
            ('standby_wocrew', 'Stand-By W-O/Crew'),
            ('full_repair', 'Full Repair Rate'),
            ('zero_rate', 'Zero Rate'),
            ('force_majeure', 'Force Majeure'),
            ('rd_ru_rmtime', 'R/D, R/U & R/MTime'),
            ('none', 'Not in Summary'),
        ],
        string='Summary Column',
        default='none',
        required=True,
    )
    active = fields.Boolean(default=True)

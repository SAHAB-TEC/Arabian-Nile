# -*- coding: utf-8 -*-
from odoo import fields, models


class WorkoverRig(models.Model):
    _name = 'workover.rig'
    _description = 'Workover Rig'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    code = fields.Char(string='Rig Code')
    active = fields.Boolean(default=True)
    well_ids = fields.One2many('workover.well', 'rig_id', string='Wells')

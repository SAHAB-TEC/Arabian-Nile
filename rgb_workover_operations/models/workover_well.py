# -*- coding: utf-8 -*-
from odoo import fields, models


class WorkoverWell(models.Model):
    _name = 'workover.well'
    _description = 'Workover Well'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    rig_id = fields.Many2one('workover.rig', string='Rig', ondelete='restrict')
    location = fields.Char()
    active = fields.Boolean(default=True)

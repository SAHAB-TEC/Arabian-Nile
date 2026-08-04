# -*- coding: utf-8 -*-
from odoo import fields, models


class ConstructionProject(models.Model):
    _inherit = 'construction.project'

    risk_ids = fields.One2many(
        'rgb.project.risk',
        'project_id',
        string='Risk Register',
    )
    risk_count = fields.Integer(string='Risks', compute='_compute_risk_count')

    def _compute_risk_count(self):
        Risk = self.env['rgb.project.risk']
        for project in self:
            project.risk_count = Risk.search_count([('project_id', '=', project.id)])

# -*- coding: utf-8 -*-
from odoo import fields, models, _


class ConstructionProject(models.Model):
    _inherit = 'construction.project'

    ncr_ids = fields.One2many('rgb.ncr', 'project_id', string='NCR Reports')
    ncr_count = fields.Integer(string='NCR Count', compute='_compute_ncr_count')
    ncr_open_count = fields.Integer(string='Open NCR Count', compute='_compute_ncr_count')

    def _compute_ncr_count(self):
        Ncr = self.env['rgb.ncr']
        for project in self:
            project.ncr_count = Ncr.search_count([('project_id', '=', project.id)])
            project.ncr_open_count = Ncr.search_count([
                ('project_id', '=', project.id),
                ('state', 'in', ('open', 'under_review')),
            ])

    def action_view_ncr(self):
        self.ensure_one()
        return {
            'name': _('NCR Reports'),
            'type': 'ir.actions.act_window',
            'res_model': 'rgb.ncr',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
            },
        }

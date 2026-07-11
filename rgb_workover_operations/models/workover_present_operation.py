# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round


class WorkoverPresentOperationLine(models.Model):
    _name = 'workover.present.operation.line'
    _description = 'Present Operation Line'
    _order = 'sequence, id'

    report_id = fields.Many2one(
        'workover.daily.report',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    time_from = fields.Float(string='From')
    time_to = fields.Float(string='To')
    type_category_id = fields.Many2one(
        'workover.time.category',
        string='Type',
    )
    operation_type = fields.Char(string='Type', default='')
    description = fields.Text(string='Description')

    @api.onchange('type_category_id')
    def _onchange_type_category_id(self):
        if self.type_category_id:
            self.operation_type = self.type_category_id.name

    def _get_duration_hours(self):
        self.ensure_one()
        if self.time_from is False and self.time_to is False:
            return 0.0
        duration = (self.time_to or 0.0) - (self.time_from or 0.0)
        if duration < 0:
            duration += 24.0
        return float_round(max(duration, 0.0), precision_digits=2)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('type_category_id') and not vals.get('operation_type'):
                category = self.env['workover.time.category'].browse(vals['type_category_id'])
                vals['operation_type'] = category.name
        lines = super().create(vals_list)
        lines.mapped('report_id')._sync_time_breakdown_from_present_ops()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('skip_time_breakdown_sync'):
            trigger_fields = {
                'time_from', 'time_to', 'type_category_id',
                'operation_type', 'report_id',
            }
            if trigger_fields.intersection(vals):
                self.mapped('report_id')._sync_time_breakdown_from_present_ops()
        return res

    def unlink(self):
        reports = self.mapped('report_id')
        res = super().unlink()
        reports._sync_time_breakdown_from_present_ops()
        return res


class WorkoverTimeBreakdownLine(models.Model):
    _name = 'workover.time.breakdown.line'
    _description = 'Time Breakdown Line'
    _order = 'sequence, id'

    report_id = fields.Many2one(
        'workover.daily.report',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    category_id = fields.Many2one(
        'workover.time.category',
        string='Category',
        required=True,
    )
    hours = fields.Float(string='Hours', digits=(16, 2), readonly=True)

    @api.constrains('hours')
    def _check_hours(self):
        for line in self:
            if line.hours < 0:
                raise ValidationError(_('Hours cannot be negative.'))

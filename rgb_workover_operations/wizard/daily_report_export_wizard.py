# -*- coding: utf-8 -*-
from collections import OrderedDict

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .excel_report_helper import build_daily_workbook, encode_xlsx


class WorkoverDailyReportExportWizard(models.TransientModel):
    _name = 'workover.daily.report.export.wizard'
    _description = 'Export Daily Operation Reports'

    date_from = fields.Date(string='From', required=True)
    date_to = fields.Date(string='To', required=True)
    rig_id = fields.Many2one('workover.rig', string='Rig')
    well_id = fields.Many2one('workover.well', string='Well')
    operator_id = fields.Many2one('workover.operator', string='Operator')
    state = fields.Selection(
        selection=[('confirmed', 'Confirmed Only'), ('all', 'All States')],
        default='confirmed',
        required=True,
    )
    xlsx_file = fields.Binary(readonly=True)
    xlsx_filename = fields.Char(readonly=True)

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        today = fields.Date.context_today(self)
        vals.setdefault('date_from', today.replace(day=1))
        vals.setdefault('date_to', today)
        return vals

    def _get_reports(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_('The start date must be before or equal to the end date.'))
        domain = [
            ('report_date', '>=', self.date_from),
            ('report_date', '<=', self.date_to),
        ]
        if self.state == 'confirmed':
            domain.append(('state', '=', 'confirmed'))
        if self.rig_id:
            domain.append(('rig_id', '=', self.rig_id.id))
        if self.well_id:
            domain.append(('well_id', '=', self.well_id.id))
        if self.operator_id:
            domain.append(('operator_id', '=', self.operator_id.id))
        reports = self.env['workover.daily.report'].search(
            domain, order='report_date, report_number, id',
        )
        if not reports:
            raise UserError(_('No daily reports found for the selected filters.'))
        return reports

    def action_export_xlsx(self):
        self.ensure_one()
        reports = self._get_reports()
        content = build_daily_workbook(reports, self.env.company.name)
        filename = 'daily_operations_%s_%s.xlsx' % (self.date_from, self.date_to)
        return encode_xlsx(content, self, filename)

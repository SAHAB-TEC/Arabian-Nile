# -*- coding: utf-8 -*-
from collections import OrderedDict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date

from .excel_report_helper import build_summary_workbook, encode_xlsx


class WorkoverSummaryReportExportWizard(models.TransientModel):
    _name = 'workover.summary.report.export.wizard'
    _description = 'Export Workover Summary Report'

    date_from = fields.Date(string='From', required=True)
    date_to = fields.Date(string='To', required=True)
    rig_id = fields.Many2one('workover.rig', string='Rig')
    well_id = fields.Many2one('workover.well', string='Well')
    operator_id = fields.Many2one('workover.operator', string='Operator')
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
            ('state', '=', 'confirmed'),
            ('report_date', '>=', self.date_from),
            ('report_date', '<=', self.date_to),
        ]
        if self.rig_id:
            domain.append(('rig_id', '=', self.rig_id.id))
        if self.well_id:
            domain.append(('well_id', '=', self.well_id.id))
        if self.operator_id:
            domain.append(('operator_id', '=', self.operator_id.id))
        reports = self.env['workover.daily.report'].search(
            domain, order='well_id, report_date, id',
        )
        if not reports:
            raise UserError(_('No confirmed daily reports found for the selected filters.'))
        return reports

    def action_export_xlsx(self):
        self.ensure_one()
        reports = self._get_reports()
        well_map = OrderedDict()
        for report in reports:
            well_map.setdefault(report.well_id, self.env['workover.daily.report'])
            well_map[report.well_id] |= report

        first = reports[0]
        operator_name = self.operator_id.name if self.operator_id else (
            first.operator_id.name if first.operator_id else ''
        )
        rig_name = self.rig_id.name if self.rig_id else (
            first.rig_id.name if first.rig_id else ''
        )
        lang = self.env.user.lang or 'en_US'
        month_label = format_date(
            self.env, self.date_from, date_format='MMMM-yyyy', lang_code=lang,
        ).upper()

        content = build_summary_workbook(
            well_map, operator_name, rig_name, month_label, self.env.company.name,
        )
        filename = 'workover_summary_%s_%s.xlsx' % (self.date_from, self.date_to)
        return encode_xlsx(content, self, filename)

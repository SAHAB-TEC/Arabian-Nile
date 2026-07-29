# -*- coding: utf-8 -*-
import base64
from collections import OrderedDict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class WorkoverRigSummary(models.Model):
    _name = 'workover.rig.summary'
    _description = 'Rig Summary Report'
    _order = 'date_from desc, id desc'

    name = fields.Char(
        string='Report Name',
        required=True,
        help='Manual name to identify this saved summary report.',
    )
    date_from = fields.Date(
        string='Summary From',
        required=True,
        default=lambda self: fields.Date.context_today(self).replace(day=1),
    )
    date_to = fields.Date(
        string='Summary To',
        required=True,
        default=fields.Date.context_today,
    )
    rig_id = fields.Many2one(
        'workover.rig',
        string='Rig',
        required=True,
    )
    operator_id = fields.Many2one(
        'workover.operator',
        string='Operator',
    )
    well_id = fields.Many2one(
        'workover.well',
        string='Well',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    report_ids = fields.Many2many(
        'workover.daily.report',
        compute='_compute_report_ids',
        string='Summary Lines',
    )
    total_full_ops = fields.Float(
        string='Full Ops Hrs',
        compute='_compute_totals',
    )
    total_standby_wcrew = fields.Float(
        string='Stand-By W/Crew',
        compute='_compute_totals',
    )
    total_standby_wocrew = fields.Float(
        string='Stand-By W-O/Crew',
        compute='_compute_totals',
    )
    total_full_repair = fields.Float(
        string='Full Repair Rate',
        compute='_compute_totals',
    )
    total_zero_rate = fields.Float(
        string='Zero Rate',
        compute='_compute_totals',
    )
    total_force_majeure = fields.Float(
        string='Force Majeure',
        compute='_compute_totals',
    )
    total_rd_ru_rmtime = fields.Float(
        string='R/D, R/U & R/MTime',
        compute='_compute_totals',
    )
    total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_totals',
    )

    def _get_date_range(self):
        self.ensure_one()
        date_from = self.date_from
        date_to = self.date_to
        if date_from and date_to and date_from > date_to:
            date_from, date_to = date_to, date_from
        return date_from, date_to

    @api.depends('date_from', 'date_to', 'rig_id', 'operator_id', 'well_id', 'company_id')
    def _compute_report_ids(self):
        Report = self.env['workover.daily.report']
        for summary in self:
            if not summary.rig_id or not summary.date_from or not summary.date_to:
                summary.report_ids = False
                continue
            date_from, date_to = summary._get_date_range()
            domain = [
                ('rig_id', '=', summary.rig_id.id),
                ('report_date', '>=', date_from),
                ('report_date', '<=', date_to),
                ('state', '=', 'confirmed'),
                ('company_id', '=', summary.company_id.id),
            ]
            if summary.operator_id:
                domain.append(('operator_id', '=', summary.operator_id.id))
            if summary.well_id:
                domain.append(('well_id', '=', summary.well_id.id))
            summary.report_ids = Report.search(
                domain, order='well_id, report_date, id',
            )

    @api.depends(
        'report_ids',
        'report_ids.summary_full_ops',
        'report_ids.summary_standby_wcrew',
        'report_ids.summary_standby_wocrew',
        'report_ids.summary_full_repair',
        'report_ids.summary_zero_rate',
        'report_ids.summary_force_majeure',
        'report_ids.summary_rd_ru_rmtime',
        'report_ids.summary_total_hours',
    )
    def _compute_totals(self):
        for summary in self:
            reports = summary.report_ids
            summary.total_full_ops = sum(reports.mapped('summary_full_ops'))
            summary.total_standby_wcrew = sum(reports.mapped('summary_standby_wcrew'))
            summary.total_standby_wocrew = sum(reports.mapped('summary_standby_wocrew'))
            summary.total_full_repair = sum(reports.mapped('summary_full_repair'))
            summary.total_zero_rate = sum(reports.mapped('summary_zero_rate'))
            summary.total_force_majeure = sum(reports.mapped('summary_force_majeure'))
            summary.total_rd_ru_rmtime = sum(reports.mapped('summary_rd_ru_rmtime'))
            summary.total_hours = sum(reports.mapped('summary_total_hours'))

    def _ensure_reports(self):
        self.ensure_one()
        if not self.rig_id:
            raise UserError(_('Please select a Rig.'))
        if not self.report_ids:
            raise UserError(_('No confirmed daily reports found for the selected filters.'))
        return self.report_ids

    def action_export_xlsx(self):
        self.ensure_one()
        from odoo.addons.rgb_workover_operations.wizard.excel_report_helper import (
            build_summary_workbook,
        )
        reports = self._ensure_reports()
        date_from, date_to = self._get_date_range()
        well_map = OrderedDict()
        for report in reports:
            well_map.setdefault(report.well_id, self.env['workover.daily.report'])
            well_map[report.well_id] |= report

        lang = self.env.user.lang or 'en_US'
        month_label = format_date(
            self.env, date_from, date_format='MMMM-yyyy', lang_code=lang,
        ).upper()
        content = build_summary_workbook(
            well_map,
            self.operator_id.name if self.operator_id else (
                reports[0].operator_id.name if reports[0].operator_id else ''
            ),
            self.rig_id.name or '',
            month_label,
            self.company_id.name,
        )
        safe_name = (self.name or 'rig_summary').replace(' ', '_')
        filename = '%s_%s_%s.xlsx' % (safe_name, date_from, date_to)
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(content),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def action_print_pdf(self):
        self.ensure_one()
        self._ensure_reports()
        return self.env.ref(
            'rgb_workover_operations.action_report_workover_rig_summary_record'
        ).report_action(self)

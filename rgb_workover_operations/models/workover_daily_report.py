# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round

_BREAKDOWN_CATEGORY_CODES = (
    'operation', 'rig_move', 'standby_wcrew', 'down_time',
    'shut_down', 'repair', 'standby_wocrew', 'zero_rate', 'force_majeure',
)


class WorkoverDailyReport(models.Model):
    _name = 'workover.daily.report'
    _description = 'Workover Daily Operation Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'report_date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
        ],
        default='draft',
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        required=True,
    )
    rig_id = fields.Many2one('workover.rig', required=True, tracking=True)
    well_id = fields.Many2one('workover.well', required=True, tracking=True)
    operator_id = fields.Many2one('workover.operator', string='Operator', tracking=True)
    location = fields.Char()
    report_date = fields.Date(required=True, tracking=True)
    report_number = fields.Integer(string='Report #')
    spud_date = fields.Date(string='Spud Date')
    release_date = fields.Date(string='Release Date')
    depth = fields.Char()
    present_operation_title = fields.Char(string='Present Operation Title')
    summary_type = fields.Char(
        string='Summary Type',
        compute='_compute_summary_fields',
        store=True,
        readonly=False,
    )
    operations_summary = fields.Text(
        string='Operations Summary',
        compute='_compute_summary_fields',
        store=True,
        readonly=False,
    )

    # BIT DATA
    bit_no = fields.Char(string='Bit No')
    bit_size = fields.Float(string='Bit Size')
    bit_type = fields.Char(string='Bit Type')
    bit_ser_no = fields.Char(string='Bit Ser. No')
    bit_jets = fields.Char(string='Bit Jets')

    # MUD DATA
    mud_type = fields.Char(string='Mud Type')
    mud_wt = fields.Float(string='Mud Wt')
    mud_ph = fields.Float(string='Mud pH')
    mud_pv = fields.Float(string='Mud PV')
    mud_yp = fields.Float(string='Mud YP')

    # ENGINEERING DATA
    depth_in = fields.Float(string='Depth In')
    depth_out = fields.Float(string='Depth Out')
    operation_hrs = fields.Float(string='Operation Hrs')
    string_wt = fields.Float(string='String Wt')
    ann_vol = fields.Float(string='Ann. Vol')
    dc_wt = fields.Float(string='DC Wt')
    pressure = fields.Float(string='Pressure')
    wt_on_bit = fields.Float(string='Wt on Bit')
    solids_pct = fields.Float(string='Solids %')
    oil_pct = fields.Float(string='Oil %')

    # PUMP DATA
    pump_model = fields.Char(string='Pump Model')
    pump_no = fields.Char(string='Pump No')
    pump_stroke = fields.Float(string='Pump Stroke')
    pump_liner_size = fields.Float(string='Liner Size')
    pump_spm = fields.Float(string='SPM @ 95%')

    # TRANSPORT
    transport_own = fields.Integer(string='Own')
    transport_rental = fields.Integer(string='Rental')
    transport_toyota = fields.Integer(string='Toyota')
    transport_crane = fields.Integer(string='Crane')
    transport_forklift = fields.Integer(string='Forklift')
    transport_truck = fields.Integer(string='Truck')

    present_operation_ids = fields.One2many(
        'workover.present.operation.line',
        'report_id',
        string='Present Operations',
        copy=True,
    )
    time_breakdown_ids = fields.One2many(
        'workover.time.breakdown.line',
        'report_id',
        string='Time Breakdown',
        copy=True,
    )
    time_breakdown_total = fields.Float(
        string='Time Breakdown Total',
        compute='_compute_time_breakdown_total',
        store=True,
    )

    # Rig summary tab (same columns as Excel summary export)
    rig_summary_date_from = fields.Date(string='Summary From')
    rig_summary_date_to = fields.Date(string='Summary To')
    rig_summary_report_ids = fields.Many2many(
        'workover.daily.report',
        compute='_compute_rig_summary_reports',
        string='Rig Summary Reports',
    )
    rig_summary_full_ops = fields.Float(
        string='Full Ops Hrs Total',
        compute='_compute_rig_summary_totals',
    )
    rig_summary_standby_wcrew = fields.Float(
        string='Stand-By W/Crew Total',
        compute='_compute_rig_summary_totals',
    )
    rig_summary_standby_wocrew = fields.Float(
        string='Stand-By W-O/Crew Total',
        compute='_compute_rig_summary_totals',
    )
    rig_summary_full_repair = fields.Float(
        string='Full Repair Rate Total',
        compute='_compute_rig_summary_totals',
    )
    rig_summary_zero_rate = fields.Float(
        string='Zero Rate Total',
        compute='_compute_rig_summary_totals',
    )
    rig_summary_force_majeure = fields.Float(
        string='Force Majeure Total',
        compute='_compute_rig_summary_totals',
    )
    rig_summary_rd_ru_rmtime = fields.Float(
        string='R/D, R/U & R/MTime Total',
        compute='_compute_rig_summary_totals',
    )
    rig_summary_total = fields.Float(
        string='Grand Total',
        compute='_compute_rig_summary_totals',
    )

    summary_full_ops = fields.Float(
        string='Full Ops Hrs',
        compute='_compute_summary_column_hours',
    )
    summary_standby_wcrew = fields.Float(
        string='Stand-By W/Crew',
        compute='_compute_summary_column_hours',
    )
    summary_standby_wocrew = fields.Float(
        string='Stand-By W-O/Crew',
        compute='_compute_summary_column_hours',
    )
    summary_full_repair = fields.Float(
        string='Full Repair Rate',
        compute='_compute_summary_column_hours',
    )
    summary_zero_rate = fields.Float(
        string='Zero Rate',
        compute='_compute_summary_column_hours',
    )
    summary_force_majeure = fields.Float(
        string='Force Majeure',
        compute='_compute_summary_column_hours',
    )
    summary_rd_ru_rmtime = fields.Float(
        string='R/D, R/U & R/MTime',
        compute='_compute_summary_column_hours',
    )
    summary_total_hours = fields.Float(
        string='Total',
        compute='_compute_summary_column_hours',
    )

    @api.depends('time_breakdown_ids.hours')
    def _compute_time_breakdown_total(self):
        for report in self:
            report.time_breakdown_total = sum(report.time_breakdown_ids.mapped('hours'))

    @api.depends('present_operation_ids.operation_type', 'present_operation_ids.description')
    def _compute_summary_fields(self):
        for report in self:
            types = [t for t in report.present_operation_ids.mapped('operation_type') if t]
            report.summary_type = types[0] if types else False
            descriptions = [d for d in report.present_operation_ids.mapped('description') if d]
            report.operations_summary = '. '.join(descriptions) if descriptions else False

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        report_date = vals.get('report_date') or fields.Date.context_today(self)
        vals.setdefault('report_date', report_date)
        vals.setdefault('rig_summary_date_from', report_date)
        vals.setdefault('rig_summary_date_to', report_date)
        return vals

    @api.onchange('report_date')
    def _onchange_report_date_rig_summary(self):
        if self.report_date:
            self.rig_summary_date_from = self.report_date
            self.rig_summary_date_to = self.report_date

    @api.onchange('well_id')
    def _onchange_well_id(self):
        if self.well_id:
            if self.well_id.rig_id:
                self.rig_id = self.well_id.rig_id
            if self.well_id.location:
                self.location = self.well_id.location

    @api.depends(
        'time_breakdown_ids.hours',
        'time_breakdown_ids.category_id.summary_column',
    )
    def _compute_summary_column_hours(self):
        for report in self:
            hours = report._get_summary_hours()
            report.summary_full_ops = hours.get('full_ops', 0.0)
            report.summary_standby_wcrew = hours.get('standby_wcrew', 0.0)
            report.summary_standby_wocrew = hours.get('standby_wocrew', 0.0)
            report.summary_full_repair = hours.get('full_repair', 0.0)
            report.summary_zero_rate = hours.get('zero_rate', 0.0)
            report.summary_force_majeure = hours.get('force_majeure', 0.0)
            report.summary_rd_ru_rmtime = hours.get('rd_ru_rmtime', 0.0)
            report.summary_total_hours = hours.get('total', 0.0)

    def _get_rig_summary_date_range(self):
        self.ensure_one()
        date_from = self.rig_summary_date_from or self.report_date
        date_to = self.rig_summary_date_to or self.report_date
        if date_from and date_to and date_from > date_to:
            date_from, date_to = date_to, date_from
        return date_from, date_to

    @api.depends(
        'rig_id',
        'report_date',
        'rig_summary_date_from',
        'rig_summary_date_to',
        'state',
    )
    def _compute_rig_summary_reports(self):
        for report in self:
            if not report.rig_id:
                report.rig_summary_report_ids = False
                continue
            date_from, date_to = report._get_rig_summary_date_range()
            if not date_from or not date_to:
                report.rig_summary_report_ids = False
                continue
            domain = [
                ('rig_id', '=', report.rig_id.id),
                ('report_date', '>=', date_from),
                ('report_date', '<=', date_to),
                '|',
                ('state', '=', 'confirmed'),
                ('id', '=', report.id),
            ]
            report.rig_summary_report_ids = self.search(
                domain,
                order='well_id, report_date, id',
            )

    @api.depends(
        'rig_summary_report_ids',
        'rig_summary_report_ids.summary_full_ops',
        'rig_summary_report_ids.summary_standby_wcrew',
        'rig_summary_report_ids.summary_standby_wocrew',
        'rig_summary_report_ids.summary_full_repair',
        'rig_summary_report_ids.summary_zero_rate',
        'rig_summary_report_ids.summary_force_majeure',
        'rig_summary_report_ids.summary_rd_ru_rmtime',
        'rig_summary_report_ids.summary_total_hours',
    )
    def _compute_rig_summary_totals(self):
        for report in self:
            report.rig_summary_full_ops = sum(
                report.rig_summary_report_ids.mapped('summary_full_ops')
            )
            report.rig_summary_standby_wcrew = sum(
                report.rig_summary_report_ids.mapped('summary_standby_wcrew')
            )
            report.rig_summary_standby_wocrew = sum(
                report.rig_summary_report_ids.mapped('summary_standby_wocrew')
            )
            report.rig_summary_full_repair = sum(
                report.rig_summary_report_ids.mapped('summary_full_repair')
            )
            report.rig_summary_zero_rate = sum(
                report.rig_summary_report_ids.mapped('summary_zero_rate')
            )
            report.rig_summary_force_majeure = sum(
                report.rig_summary_report_ids.mapped('summary_force_majeure')
            )
            report.rig_summary_rd_ru_rmtime = sum(
                report.rig_summary_report_ids.mapped('summary_rd_ru_rmtime')
            )
            report.rig_summary_total = sum(
                report.rig_summary_report_ids.mapped('summary_total_hours')
            )

    @api.model
    def _get_breakdown_categories(self):
        return self.env['workover.time.category'].search([
            ('code', 'in', list(_BREAKDOWN_CATEGORY_CODES)),
        ], order='sequence')

    def _aggregate_hours_by_category(self, categories):
        """Sum present-operation durations grouped by type/category."""
        self.ensure_one()
        hours = {category.id: 0.0 for category in categories}
        name_to_category = {
            category.name.strip().upper(): category.id
            for category in categories
        }
        all_categories = self.env['workover.time.category'].search([])
        all_names = {
            category.name.strip().upper(): category.id
            for category in all_categories
        }

        for line in self.present_operation_ids:
            duration = line._get_duration_hours()
            if not duration:
                continue
            category_id = False
            if line.type_category_id:
                category_id = line.type_category_id.id
            elif line.operation_type:
                key = line.operation_type.strip().upper()
                category_id = name_to_category.get(key) or all_names.get(key)
            if category_id and category_id in hours:
                hours[category_id] += duration
        return hours

    def _sync_time_breakdown_from_present_ops(self):
        if self.env.context.get('skip_time_breakdown_sync'):
            return
        categories = self._get_breakdown_categories()
        for report in self:
            hours_by_category = report._aggregate_hours_by_category(categories)
            commands = [(5, 0, 0)]
            for category in categories:
                commands.append((0, 0, {
                    'category_id': category.id,
                    'sequence': category.sequence,
                    'hours': hours_by_category.get(category.id, 0.0),
                }))
            report.with_context(skip_time_breakdown_sync=True).write({
                'time_breakdown_ids': commands,
            })

    @api.onchange('present_operation_ids')
    def _onchange_present_operation_ids_sync_breakdown(self):
        categories = self._get_breakdown_categories()
        if not self.present_operation_ids:
            self.time_breakdown_ids = [(5, 0, 0)]
            return
        hours_by_category = self._aggregate_hours_by_category(categories)
        self.time_breakdown_ids = [(5, 0, 0)] + [
            (0, 0, {
                'category_id': category.id,
                'sequence': category.sequence,
                'hours': hours_by_category.get(category.id, 0.0),
            })
            for category in categories
        ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('workover.daily.report') or _('New')
            report_date = vals.get('report_date') or fields.Date.context_today(self)
            vals.setdefault('rig_summary_date_from', report_date)
            vals.setdefault('rig_summary_date_to', report_date)
        return super().create(vals_list)

    def action_confirm(self):
        self._sync_time_breakdown_from_present_ops()
        self.write({'state': 'confirmed'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def _get_summary_hours(self):
        """Return dict of summary column keys to hours for this report."""
        self.ensure_one()
        columns = {
            'full_ops': 0.0,
            'standby_wcrew': 0.0,
            'standby_wocrew': 0.0,
            'full_repair': 0.0,
            'zero_rate': 0.0,
            'force_majeure': 0.0,
            'rd_ru_rmtime': 0.0,
        }
        for line in self.time_breakdown_ids:
            col = line.category_id.summary_column
            if col and col != 'none':
                columns[col] = columns.get(col, 0.0) + (line.hours or 0.0)
        columns['total'] = sum(columns.values())
        return columns


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

    @api.onchange('well_id')
    def _onchange_well_id(self):
        if self.well_id:
            if self.well_id.rig_id:
                self.rig_id = self.well_id.rig_id
            if self.well_id.location:
                self.location = self.well_id.location

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


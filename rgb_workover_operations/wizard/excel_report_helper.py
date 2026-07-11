# -*- coding: utf-8 -*-
import base64
import io
import os
from copy import copy
from datetime import datetime, time

from odoo import fields
from odoo.tools.float_utils import float_round


def _set_cell_value(ws, row, column, value):
    """Write to a worksheet cell, including merged ranges."""
    from openpyxl.cell.cell import MergedCell

    cell = ws.cell(row=row, column=column)
    if isinstance(cell, MergedCell):
        for merged_range in ws.merged_cells.ranges:
            if cell.coordinate in merged_range:
                cell = ws.cell(
                    row=merged_range.min_row,
                    column=merged_range.min_col,
                )
                break
    cell.value = value


def _template_path(filename):
    module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(module_path, 'report', 'excel_templates', filename)


def _float_to_time(value):
    if not value:
        return None
    hours = int(value)
    minutes = int(round((value - hours) * 60))
    if minutes >= 60:
        hours += 1
        minutes = 0
    return time(hours % 24, minutes)


def _format_report_date(value):
    if not value:
        return ''
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime('%d/%m/%Y')


def fill_daily_report_sheet(ws, report, company_name):
    """Fill one daily report worksheet from a workover.daily.report record."""
    rig_label = report.rig_id.code or report.rig_id.name or ''
    _set_cell_value(ws, 1, 4, '%s ( %s )' % (company_name, rig_label))
    _set_cell_value(ws, 7, 3, rig_label)
    _set_cell_value(ws, 7, 7, report.well_id.name or '')
    _set_cell_value(ws, 7, 11, report.location or report.well_id.location or '')
    _set_cell_value(ws, 8, 8, report.report_number or '')
    _set_cell_value(ws, 9, 3, '           %s' % _format_report_date(report.report_date))
    _set_cell_value(ws, 9, 11, report.operation_hrs or report.time_breakdown_total or 0)

    # BIT DATA
    _set_cell_value(ws, 11, 2, report.bit_no or 0)
    _set_cell_value(ws, 12, 2, report.bit_size or 0)
    _set_cell_value(ws, 13, 2, report.bit_type or 0)
    _set_cell_value(ws, 14, 2, report.bit_ser_no or 0)
    _set_cell_value(ws, 15, 2, report.bit_jets or 0)

    # MUD DATA
    _set_cell_value(ws, 11, 5, report.mud_type or 0)
    _set_cell_value(ws, 12, 5, report.mud_wt or 0)
    _set_cell_value(ws, 13, 5, report.mud_ph or 0)
    _set_cell_value(ws, 14, 5, report.mud_pv or 0)
    _set_cell_value(ws, 15, 5, report.mud_yp or 0)

    # ENGINEERING
    _set_cell_value(ws, 11, 10, report.pump_model or '')
    _set_cell_value(ws, 16, 2, report.depth_in or 0)
    _set_cell_value(ws, 17, 2, report.depth_out or 0)
    _set_cell_value(ws, 18, 2, report.operation_hrs or 0)
    _set_cell_value(ws, 11, 9, report.string_wt or 0)
    _set_cell_value(ws, 12, 9, report.ann_vol or 0)
    _set_cell_value(ws, 13, 9, report.dc_wt or 0)
    _set_cell_value(ws, 14, 9, report.pressure or 0)
    _set_cell_value(ws, 15, 9, report.wt_on_bit or 0)
    _set_cell_value(ws, 16, 5, report.solids_pct or 0)
    _set_cell_value(ws, 17, 5, report.oil_pct or 0)

    # PUMP
    _set_cell_value(ws, 12, 12, report.pump_no or '')
    _set_cell_value(ws, 13, 12, report.pump_stroke or 0)
    _set_cell_value(ws, 14, 12, report.pump_liner_size or 0)
    _set_cell_value(ws, 15, 12, report.pump_spm or 0)

    # Transport
    _set_cell_value(ws, 18, 7, report.transport_toyota or 0)
    _set_cell_value(ws, 18, 9, report.transport_crane or 0)
    _set_cell_value(ws, 19, 7, report.transport_forklift or 0)
    _set_cell_value(ws, 19, 9, report.transport_truck or 0)

    _set_cell_value(ws, 21, 3, report.present_operation_title or '')
    _set_cell_value(ws, 22, 3, 'type')

    present_start = 23
    for idx, line in enumerate(report.present_operation_ids):
        row = present_start + idx
        if idx == 0:
            _set_cell_value(ws, row, 1, _float_to_time(line.time_from))
            _set_cell_value(ws, row, 2, _float_to_time(line.time_to))
        _set_cell_value(ws, row, 3, line.operation_type or '')
        _set_cell_value(ws, row, 4, line.description or '')

    tb_start = 23
    total_hours = 0.0
    for idx, line in enumerate(report.time_breakdown_ids):
        row = tb_start + idx
        _set_cell_value(ws, row, 11, line.category_id.name or '')
        _set_cell_value(ws, row, 14, line.hours or 0)
        total_hours += line.hours or 0
    total_row = tb_start + max(len(report.time_breakdown_ids), 7)
    _set_cell_value(ws, total_row, 12, 'TOTAL')
    _set_cell_value(ws, total_row, 14, float_round(total_hours, precision_digits=2))


def copy_sheet_style(source_ws, target_ws):
    for row in source_ws.iter_rows():
        for cell in row:
            new_cell = target_ws.cell(row=cell.row, column=cell.column, value=cell.value)
            if cell.has_style:
                new_cell.font = copy(cell.font)
                new_cell.border = copy(cell.border)
                new_cell.fill = copy(cell.fill)
                new_cell.number_format = copy(cell.number_format)
                new_cell.protection = copy(cell.protection)
                new_cell.alignment = copy(cell.alignment)
    for merged in source_ws.merged_cells.ranges:
        target_ws.merge_cells(str(merged))
    for col, dim in source_ws.column_dimensions.items():
        target_ws.column_dimensions[col].width = dim.width
    for row, dim in source_ws.row_dimensions.items():
        target_ws.row_dimensions[row].height = dim.height


def build_daily_workbook(reports, company_name):
    import openpyxl

    template_path = _template_path('daily_report_template.xlsx')
    template_wb = openpyxl.load_workbook(template_path)
    template_ws = template_wb[template_wb.sheetnames[0]]

    out_wb = openpyxl.Workbook()
    out_wb.remove(out_wb.active)

    for index, report in enumerate(reports, start=1):
        sheet_name = '(%s)' % (report.report_number or index)
        ws = out_wb.create_sheet(title=sheet_name[:31])
        copy_sheet_style(template_ws, ws)
        fill_daily_report_sheet(ws, report, company_name)

    buffer = io.BytesIO()
    out_wb.save(buffer)
    return buffer.getvalue()


SUMMARY_COLUMNS = {
    'full_ops': 2,
    'standby_wcrew': 3,
    'standby_wocrew': 4,
    'full_repair': 5,
    'zero_rate': 6,
    'force_majeure': 7,
    'rd_ru_rmtime': 8,
    'total': 9,
    'type': 10,
    'operations_summary': 11,
}


def fill_summary_sheet(ws, well, reports, operator_name, rig_name, month_label, company_name):
    # Shift the template Operations Summary column right to make room for Type.
    ws.insert_cols(10)
    _set_cell_value(ws, 1, 2, company_name)
    _set_cell_value(ws, 2, 2, 'Summary of Workover Operations')
    _set_cell_value(ws, 2, 11, 'Month of  ( %s )' % month_label)
    _set_cell_value(ws, 4, 3, operator_name or '')
    _set_cell_value(ws, 4, 8, rig_name or '')
    _set_cell_value(ws, 4, 11, 'Wells No.(s):         ( %s )' % (well.name or ''))

    _set_cell_value(ws, 5, 10, 'Type')
    _set_cell_value(ws, 6, 10, 'Type')
    _set_cell_value(ws, 7, 10, 'Type')

    row = 8
    totals = {key: 0.0 for key in SUMMARY_COLUMNS if key not in ('type', 'operations_summary')}

    for report in sorted(reports, key=lambda r: r.report_date or fields.Date.today()):
        hours = report._get_summary_hours()
        _set_cell_value(ws, row, 1, datetime.combine(report.report_date, time()))
        for key, col in SUMMARY_COLUMNS.items():
            if key in ('type', 'operations_summary'):
                continue
            value = hours.get(key, 0.0)
            if value:
                _set_cell_value(ws, row, col, value)
            totals[key] += value or 0.0
        _set_cell_value(ws, row, 10, report.summary_type or '')
        _set_cell_value(ws, row, 11, report.operations_summary or '')
        row += 1

    _set_cell_value(ws, row, 2, totals.get('full_ops', 0.0))
    _set_cell_value(ws, row, 3, totals.get('standby_wcrew', 0.0))
    _set_cell_value(ws, row, 4, totals.get('standby_wocrew', 0.0))
    _set_cell_value(ws, row, 5, totals.get('full_repair', 0.0))
    _set_cell_value(ws, row, 6, totals.get('zero_rate', 0.0))
    _set_cell_value(ws, row, 7, totals.get('force_majeure', 0.0))
    _set_cell_value(ws, row, 8, totals.get('rd_ru_rmtime', 0.0))
    _set_cell_value(ws, row, 9, totals.get('total', 0.0))
    row += 1
    for clear_row in range(row, 20):
        for col in range(1, 12):
            _set_cell_value(ws, clear_row, col, None)


def build_summary_workbook(well_reports_map, operator_name, rig_name, month_label, company_name):
    import openpyxl

    template_path = _template_path('summary_report_template.xlsx')
    template_wb = openpyxl.load_workbook(template_path)
    template_ws = template_wb[template_wb.sheetnames[0]]

    out_wb = openpyxl.Workbook()
    out_wb.remove(out_wb.active)

    for well, reports in well_reports_map.items():
        sheet_name = (well.name or 'Well')[:31]
        ws = out_wb.create_sheet(title=sheet_name)
        copy_sheet_style(template_ws, ws)
        fill_summary_sheet(ws, well, reports, operator_name, rig_name, month_label, company_name)

    buffer = io.BytesIO()
    out_wb.save(buffer)
    return buffer.getvalue()


def encode_xlsx(content, wizard, filename):
    wizard.write({
        'xlsx_file': base64.b64encode(content),
        'xlsx_filename': filename,
    })
    return {
        'type': 'ir.actions.act_url',
        'url': '/web/content/?model=%s&id=%s&field=xlsx_file&filename_field=xlsx_filename&download=true' % (
            wizard._name, wizard.id,
        ),
        'target': 'self',
    }

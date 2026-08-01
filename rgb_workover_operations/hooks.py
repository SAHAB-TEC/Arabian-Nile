# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta


def pre_init_hook(env):
    """Rename float time columns so Odoo can create Datetime columns cleanly."""
    cr = env.cr
    cr.execute(
        """
        SELECT data_type
          FROM information_schema.columns
         WHERE table_name = 'workover_present_operation_line'
           AND column_name = 'time_from'
        """
    )
    row = cr.fetchone()
    if not row:
        return
    if row[0] in ('double precision', 'numeric', 'real'):
        cr.execute(
            """
            ALTER TABLE workover_present_operation_line
                RENAME COLUMN time_from TO time_from_float_old;
            ALTER TABLE workover_present_operation_line
                RENAME COLUMN time_to TO time_to_float_old;
            """
        )


def _float_hours_to_datetime(report_date, float_hours):
    if report_date is None or float_hours is None:
        return False
    hours = int(float_hours)
    minutes = int(round((float_hours - hours) * 60))
    if minutes >= 60:
        hours += 1
        minutes = 0
    day_offset, hours = divmod(hours, 24)
    base = datetime.combine(report_date, time(hours, minutes))
    if day_offset:
        base += timedelta(days=day_offset)
    return base


def post_init_hook(env):
    """Migrate old float From/To values into Datetime using the report date."""
    cr = env.cr
    cr.execute(
        """
        SELECT EXISTS (
            SELECT 1
              FROM information_schema.columns
             WHERE table_name = 'workover_present_operation_line'
               AND column_name = 'time_from_float_old'
        )
        """
    )
    if not cr.fetchone()[0]:
        return

    Line = env['workover.present.operation.line'].with_context(
        skip_time_breakdown_sync=True,
    )
    cr.execute(
        """
        SELECT l.id,
               l.time_from_float_old,
               l.time_to_float_old,
               r.report_date
          FROM workover_present_operation_line l
          JOIN workover_daily_report r ON r.id = l.report_id
        """
    )
    for line_id, time_from_old, time_to_old, report_date in cr.fetchall():
        vals = {}
        dt_from = _float_hours_to_datetime(report_date, time_from_old)
        dt_to = _float_hours_to_datetime(report_date, time_to_old)
        if dt_from:
            vals['time_from'] = dt_from
        if dt_to:
            if dt_from and dt_to < dt_from:
                dt_to += timedelta(days=1)
            vals['time_to'] = dt_to
        if vals:
            Line.browse(line_id).write(vals)

    cr.execute(
        """
        ALTER TABLE workover_present_operation_line
            DROP COLUMN IF EXISTS time_from_float_old,
            DROP COLUMN IF EXISTS time_to_float_old;
        """
    )

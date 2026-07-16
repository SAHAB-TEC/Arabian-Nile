# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta


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


def migrate(cr, version):
    """Convert old float From/To values into Datetime using the report date."""
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
    rows = cr.fetchall()
    for line_id, time_from_old, time_to_old, report_date in rows:
        dt_from = _float_hours_to_datetime(report_date, time_from_old)
        dt_to = _float_hours_to_datetime(report_date, time_to_old)
        if dt_from and dt_to and dt_to < dt_from:
            dt_to += timedelta(days=1)
        cr.execute(
            """
            UPDATE workover_present_operation_line
               SET time_from = %s,
                   time_to = %s
             WHERE id = %s
            """,
            (dt_from or None, dt_to or None, line_id),
        )

    cr.execute(
        """
        ALTER TABLE workover_present_operation_line
            DROP COLUMN IF EXISTS time_from_float_old,
            DROP COLUMN IF EXISTS time_to_float_old;
        """
    )

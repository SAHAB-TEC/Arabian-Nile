# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Drop vendor-bill workflow: map legacy invoiced sheets to approved."""
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = 'rgb_attendance_sheet'
           AND column_name = 'state'
        """
    )
    if not cr.fetchone():
        return

    cr.execute(
        """
        UPDATE rgb_attendance_sheet
           SET state = 'approved'
         WHERE state = 'invoiced'
        """
    )

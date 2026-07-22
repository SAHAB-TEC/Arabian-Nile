# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Rename float time columns before ORM recreates them as Datetime."""
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

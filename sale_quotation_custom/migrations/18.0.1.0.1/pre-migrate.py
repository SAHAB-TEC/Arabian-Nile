# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Convert legacy Char delivery times to Integer safely."""
    cr.execute(
        """
        SELECT data_type
          FROM information_schema.columns
         WHERE table_name = 'sale_order'
           AND column_name = 'delivery_time_from'
        """
    )
    row = cr.fetchone()
    if not row or row[0] in ('integer', 'bigint', 'smallint'):
        return

    cr.execute(
        """
        ALTER TABLE sale_order
            ALTER COLUMN delivery_time_from TYPE integer
            USING CASE
                WHEN delivery_time_from ~ '^[0-9]+$'
                THEN delivery_time_from::integer
                ELSE NULL
            END,
            ALTER COLUMN delivery_time_to TYPE integer
            USING CASE
                WHEN delivery_time_to ~ '^[0-9]+$'
                THEN delivery_time_to::integer
                ELSE NULL
            END
        """
    )

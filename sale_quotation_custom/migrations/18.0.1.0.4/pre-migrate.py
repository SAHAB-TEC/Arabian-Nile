# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Keep legacy order-level countries so they can be moved to order lines."""
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = 'sale_order'
           AND column_name = 'country_of_origin_id'
        """
    )
    if not cr.fetchone():
        return

    cr.execute(
        """
        CREATE TABLE IF NOT EXISTS sale_quotation_custom_country_origin_backup (
            order_id INTEGER PRIMARY KEY,
            country_id INTEGER NOT NULL
        )
        """
    )
    cr.execute(
        """
        INSERT INTO sale_quotation_custom_country_origin_backup (order_id, country_id)
        SELECT id, country_of_origin_id
          FROM sale_order
         WHERE country_of_origin_id IS NOT NULL
        ON CONFLICT (order_id) DO UPDATE
           SET country_id = EXCLUDED.country_id
        """
    )

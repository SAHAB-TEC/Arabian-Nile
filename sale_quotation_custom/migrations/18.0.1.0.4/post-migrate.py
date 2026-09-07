# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Apply legacy order countries onto product lines and rebuild header tags."""
    cr.execute(
        """
        SELECT 1
          FROM information_schema.tables
         WHERE table_name = 'sale_quotation_custom_country_origin_backup'
        """
    )
    if not cr.fetchone():
        return

    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = 'sale_order_line'
           AND column_name = 'country_of_origin_id'
        """
    )
    if cr.fetchone():
        cr.execute(
            """
            UPDATE sale_order_line AS sol
               SET country_of_origin_id = backup.country_id
              FROM sale_quotation_custom_country_origin_backup AS backup
             WHERE sol.order_id = backup.order_id
               AND sol.country_of_origin_id IS NULL
               AND COALESCE(sol.display_type, '') = ''
            """
        )

    cr.execute(
        """
        SELECT 1
          FROM information_schema.tables
         WHERE table_name = 'sale_order_res_country_rel'
        """
    )
    if cr.fetchone():
        cr.execute(
            """
            INSERT INTO sale_order_res_country_rel (sale_order_id, res_country_id)
            SELECT DISTINCT sol.order_id, sol.country_of_origin_id
              FROM sale_order_line AS sol
             WHERE sol.country_of_origin_id IS NOT NULL
            ON CONFLICT DO NOTHING
            """
        )

    cr.execute("DROP TABLE IF EXISTS sale_quotation_custom_country_origin_backup")

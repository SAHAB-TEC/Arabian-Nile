# -*- coding: utf-8 -*-

def migrate(cr, version):
    """Clear legacy project.project references before switching to construction.project."""
    tables = (
        'material_requisition',
        'material_requisition_line',
        'stock_picking',
        'stock_move',
        'purchase_order',
    )
    for table in tables:
        cr.execute(
            """
            SELECT 1
              FROM information_schema.columns
             WHERE table_name = %s
               AND column_name = 'project_id'
            """,
            (table,),
        )
        if cr.fetchone():
            cr.execute(
                f"UPDATE {table} SET project_id = NULL WHERE project_id IS NOT NULL"
            )

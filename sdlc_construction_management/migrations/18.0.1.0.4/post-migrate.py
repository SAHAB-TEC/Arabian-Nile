# -*- coding: utf-8 -*-

def migrate(cr, version):
    """Assign a company to legacy construction projects without one."""
    cr.execute("""
        UPDATE construction_project
           SET company_id = (
               SELECT id FROM res_company ORDER BY sequence, id LIMIT 1
           )
         WHERE company_id IS NULL
    """)

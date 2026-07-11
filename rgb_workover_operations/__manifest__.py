# -*- coding: utf-8 -*-
{
    'name': 'RGB Workover Operations',
    'version': '18.0.1.0.3',
    'category': 'Operations',
    'summary': 'Daily workover operation reports and monthly summary Excel export',
    'description': """
RGB Workover Operations
=======================
Manage daily workover operation reports with present operations, time breakdown,
and export to Excel (daily report workbook and monthly summary per well).
    """,
    'author': 'RGB / Arabian Nile',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/time_category_data.xml',
        'views/workover_config_views.xml',
        'views/workover_daily_report_views.xml',
        'views/workover_report_wizard_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}

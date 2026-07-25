# -*- coding: utf-8 -*-
{
    'name': 'Invoice Approval Workflow',
    'version': '18.0.1.0.1',
    'category': 'Accounting/Accounting',
    'summary': 'Department-based invoice approval (متابعة الفواتير)',
    'description': """
Invoice follow-up for Arabian Nile:
- Mandatory Competent Department on customer and vendor invoices
- Path: Finance Draft → Department Review → Final Review → Post
- Department security groups and visibility rules
- Financial data lock after leaving Finance
- Reject and Recall supported
- Email + Activity + Inbox notifications
    """,
    'author': 'RGB / Arabian Nile',
    'depends': ['account', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'data/ir_cron_data.xml',
        'data/department_stage_data.xml',
        'views/approval_stage_views.xml',
        'views/account_move_views.xml',
        'views/approval_app_views.xml',
        'views/approval_reject_wizard_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

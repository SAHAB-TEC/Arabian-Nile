# -*- coding: utf-8 -*-
{
    'name': 'RGB NCR (Non-Conformance Report)',
    'version': '18.0.1.0.1',
    'category': 'Construction',
    'summary': 'Non-Conformance Reports with project linking and contractor financial freeze',
    'description': """
RGB NCR
=======
Manage Non-Conformance Reports (NCR) for construction projects:

- Link NCR to project, sub-project, contractor and work order
- Technical description with GPS coordinates
- Root cause and corrective action
- Before/after images and NDT attachments
- Workflow: Open → Under Review → Closed
- Financial freeze on contractor invoices/RA billings for the same project
    """,
    'author': 'RGB / Arabian Nile',
    'license': 'LGPL-3',
    'depends': [
        'mail',
        'account',
        'purchase',
        'analytic',
        'sdlc_construction_management',
    ],
    'data': [
        'security/rgb_ncr_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/rgb_ncr_views.xml',
        'views/construction_project_views.xml',
        'views/account_move_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}

# -*- coding: utf-8 -*-
{
    "name": "RGB POB (Personnel on Board)",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    "summary": "Personnel on Board travel permits for oil sites and rigs",
    "description": """
Manage Personnel on Board (POB) travel permits:

- Employee travel eligibility filter
- Wells and Rigs master data (module-owned)
- 5-stage approval: Draft → Operations → HSE/Rig → Active → Expired
- Smart alerts 4 days before expiry (Activity + Email + Notification)
- Extension workflow approved by Operations
    """,
    "author": "RGB / Al-Abar",
    "license": "LGPL-3",
    "depends": [
        "hr",
        "mail",
        "bus",
    ],
    "data": [
        "security/rgb_pob_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/mail_activity_data.xml",
        "data/mail_template_data.xml",
        "data/ir_cron_data.xml",
        "wizard/pob_extension_wizard_views.xml",
        "views/pob_well_views.xml",
        "views/pob_rig_views.xml",
        "views/hr_employee_views.xml",
        "views/pob_request_views.xml",
        "views/menus.xml",
        "data/demo_data.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
}

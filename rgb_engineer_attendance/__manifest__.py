# -*- coding: utf-8 -*-
{
    "name": "RGB Engineer Attendance",
    "version": "18.0.1.0.5",
    "category": "Human Resources",
    "summary": "Monthly engineer attendance grid, approval, and vendor invoice",
    "description": """
Engineer attendance at wells/rigs per company.
Monthly day checkboxes, approval workflow, vendor bill generation, PDF/Excel export.
    """,
    "author": "RGB / Al-Abar",
    "license": "LGPL-3",
    "depends": [
        "account",
        "mail",
        "product",
        "rgb_workover_operations",
    ],
    "data": [
        "security/rgb_attendance_security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/rgb_attendance_sheet_views.xml",
        "views/menu.xml",
        "reports/attendance_report.xml",
        "wizard/attendance_export_wizard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "rgb_engineer_attendance/static/src/scss/attendance_sheet.scss",
        ],
    },
    "installable": True,
    "application": True,
}

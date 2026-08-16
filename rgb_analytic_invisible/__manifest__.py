# -*- coding: utf-8 -*-
{
    "name": "RGB Analytic Invisible",
    "version": "18.0.1.0.1",
    "category": "Accounting/Accounting",
    "summary": "Hide analytic accounts and plans from all business screens",
    "description": """
Adds an Invisible flag on Analytic Accounts and Analytic Plans.
When set, the record is hidden from searches and cannot be selected
in any other screen (journals, invoices, MRs, etc.).
Configuration menus still show them via a dedicated context flag.
Only users in Manage Analytic Invisible can set the flag.
    """,
    "author": "RGB / Al-Abar",
    "license": "LGPL-3",
    "depends": ["analytic"],
    "data": [
        "security/rgb_analytic_invisible_security.xml",
        "views/analytic_account_views.xml",
        "views/analytic_plan_views.xml",
    ],
    "installable": True,
    "application": False,
}

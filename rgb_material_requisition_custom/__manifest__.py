# -*- coding: utf-8 -*-
{
    "name": "RGB Material Requisition Custom",
    "version": "18.0.1.0.15",
    "category": "Human Resources/Employees",
    "summary": "Arabian Nile customizations for material requisitions",
    "description": """
Custom material requisition extensions for Arabian Nile:
- Customer (required), well and rig on requisitions and linked documents
- Project (construction.project) and analytic account auto-filled from the project
- Analytic account on stock locations for transfer journal entries
- Product analytic account combined with MR analytic on transfer journal entries
- Allowed users per stock location for requisition destination selection
- Purchase receipts for material-requisition POs use the requisition location
- Internal transfers: one picking per source/destination with all products
    """,
    "author": "RGB / Arabian Nile",
    "license": "LGPL-3",
    "depends": [
        "material_requisition_and_approval",
        "rgb_crm_project_custom",
        "sdlc_construction_management",
        "purchase_stock",
        "analytic",
        "stock_account",
        "product",
    ],
    "data": [
        "security/rgb_material_requisition_security.xml",
        "views/material_requisition_views.xml",
        "views/material_requisition_line_views.xml",
        "views/material_requisition_approval_views.xml",
        "views/stock_purchase_views.xml",
        "views/stock_location_views.xml",
        "views/product_views.xml",
        "report/material_requisition_summary_report.xml",
    ],
    "installable": True,
    "application": False,
}

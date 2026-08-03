# -*- coding: utf-8 -*-
{
    "name": "RGB Delivery Ticket (أمر الحركة)",
    "version": "18.0.1.2.1",
    "category": "Inventory/Delivery",
    "summary": "Dedicated Delivery Ticket print (separate from Delivery Slip)",
    "description": """
Adds a dedicated Delivery Ticket / أمر الحركة report for stock pickings.

The standard Delivery Slip print stays unchanged.
Delivery Ticket is a separate print with:
- Auto Rig / Well / company / locations from the material requisition
- Manual load / driver / receipt signature fields
- Line notes column on the ticket
    """,
    "author": "RGB / Al-Abar",
    "license": "LGPL-3",
    "depends": [
        "stock",
        "material_requisition_and_approval",
        "rgb_material_requisition_custom",
    ],
    "data": [
        "report/delivery_ticket_report.xml",
        "report/delivery_ticket_templates.xml",
        "views/stock_picking_views.xml",
        "views/stock_move_views.xml",
        "views/requisition_request_type_views.xml",
    ],
    "installable": True,
    "application": False,
}

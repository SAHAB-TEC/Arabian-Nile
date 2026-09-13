# -*- coding: utf-8 -*-
{
    'name': 'Product Approval - Purchase Enforcement',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Blocks unapproved products from being added to or confirmed on a purchase order',
    'description': """
Bridge module between Product Creation Approval Workflow and Purchase.
Auto-installs when both custom_product_approval and purchase are installed.

* Adding a Draft (unapproved) product to a purchase order line is
  blocked immediately.
* Confirming a purchase order containing an unapproved product is
  blocked as a defense-in-depth check.
""",
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['custom_product_approval', 'purchase'],
    'data': [],
    'installable': True,
    'auto_install': True,
}

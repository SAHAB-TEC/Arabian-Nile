# -*- coding: utf-8 -*-
{
    'name': 'Product Approval - Sales Enforcement',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Blocks unapproved products from being added to or confirmed on a sales order',
    'description': """
Bridge module between Product Creation Approval Workflow and Sales.
Auto-installs when both custom_product_approval and sale are installed.

* Adding a Draft (unapproved) product to a sale order line is blocked
  immediately.
* Confirming a sale order containing an unapproved product is blocked
  as a defense-in-depth check.
""",
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['custom_product_approval', 'sale'],
    'data': [],
    'installable': True,
    'auto_install': True,
}

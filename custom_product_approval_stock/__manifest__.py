# -*- coding: utf-8 -*-
{
    'name': 'Product Approval - Inventory Enforcement',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Blocks unapproved products from being moved or validated in stock operations',
    'description': """
Bridge module between Product Creation Approval Workflow and Inventory.
Auto-installs when both custom_product_approval and stock are installed.

* Creating a stock move for a Draft (unapproved) product is blocked
  immediately - covers manual Receipts, Deliveries, Internal Transfers,
  and inventory adjustments.
* Validating (Mark as Done) a picking containing an unapproved product
  is blocked as a defense-in-depth check.
""",
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['custom_product_approval', 'stock'],
    'data': [],
    'installable': True,
    'auto_install': True,
}

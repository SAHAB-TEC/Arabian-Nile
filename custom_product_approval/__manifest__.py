# -*- coding: utf-8 -*-
{
    'name': 'Product Creation Approval Workflow',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Approval workflow for newly created products with automated activity notifications',
    'description': """
Product Creation Approval Workflow
===================================
This module adds a simple approval workflow on top of Product Templates:

* Adds a "Can Approve Products" right on Users.
* Adds a Draft / Approved state on Product Templates.
* Automatically creates a To-Do activity for every user with approval
  rights whenever a new product is created in the Draft state.
* Adds an "Approve" statusbar button, restricted to authorized users,
  that moves the product to Approved, stamps who/when, and marks the
  related approval activities as Done.
* Adds a smart button showing who created / approved the product and
  when.

A Draft product is never archived and stays fully visible and
selectable everywhere - it just cannot be *used* in a transaction yet.
Enforcing that in Sales, Purchase and Inventory requires this module's
optional companion modules, since actually blocking a sale/purchase
order line or a stock move has to live in code that depends on those
apps:

* custom_product_approval_sale
* custom_product_approval_purchase
* custom_product_approval_stock

Each one auto-installs only when its corresponding app is already
installed, so this core module stays lightweight (product + mail
only) on its own.
""",
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': ['product', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/res_users_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

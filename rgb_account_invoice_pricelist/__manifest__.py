# -*- coding: utf-8 -*-
{
    'name': 'RGB Customer Invoice Pricelist',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Sale pricelist on customer invoices (prices from pricelist)',
    'description': """
Apply product pricelist on draft customer invoices (same behavior as Sale Orders):
pricelist field, partner default, currency sync, and Update Prices button.
    """,
    'author': 'RGB / Arabian Nile',
    'license': 'LGPL-3',
    'depends': ['account', 'sale'],
    'data': [
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
}

# -*- coding: utf-8 -*-

{
    "name": "Account Report in multiple currencies (V18 Enterprise Edition)",
    "summary": "This module allows you to effortlessly check accounting reports in multiple currencies, enhancing financial visibility and simplifying global transactions.",
    "version": "18.0.0.1.1",
    "category": "Accounting",
    "author": "Maruti Softserv",
    "website": "https://marutisoftserv.com/",
    "license": "LGPL-3",
    "description": """This module allows you to effortlessly check accounting reports in multiple currencies, enhancing financial visibility and simplifying global transactions.""",
    "depends": ["account_reports"],
    "data": [],
    'assets': {
        'web.assets_backend': [
            'maruti_multi_currency_accounting_report/static/src/components/**/*',
        ],
    },
    "application": True,
    "installable": True,
    'images': ['static/description/banner.png'],
    'price': '45.00'
}

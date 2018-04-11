# -*- coding: utf-8 -*-
# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Xunnel Sync',
    'summary': '''
        Use Xunnel Sync to retrieve bank statements
    ''',
    'version': '11.0.1.0.0',
    'author': 'Jarsa Sistemas,Vauxoo',
    'category': 'Accounting',
    'website': 'http://www.jarsa.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'account_accountant',
    ],
    'data': [
        'data/ir_cron.xml',
        'views/account_config_settings.xml',
        'data/config_xunnel_url.xml',
    ],
    'installable': True,
}

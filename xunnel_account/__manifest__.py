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
        'account_online_sync',
        'account_accountant',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'wizards/account_pre_invoice_wizard_view.xml',
        'wizards/pre_invoice_link_wizard_view.xml',
        'views/account_invoice_view.xml',
        'views/account_pre_invoice.xml',
        'views/res_company.xml',
        'data/ir_cron.xml',
        'data/config_xunnel_url.xml',
        'views/account_config_settings.xml',
    ],
    'qweb': [
        'static/src/xml/xunnel_templates.xml',
    ],
    'external_dependencies': {
    },
    'installable': True,
}

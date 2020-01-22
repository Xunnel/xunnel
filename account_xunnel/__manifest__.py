# Copyright 2017, Vauxoo, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Xunnel Bank',
    'summary': '''
        Use Xunnel Bank to retrieve bank statements.
    ''',
    'version': '13.0.1.0.2',
    'author': 'Jarsa Sistemas,Vauxoo',
    'category': 'Accounting',
    'website': 'http://www.xunnel.com',
    'license': 'LGPL-3',
    'depends': [
        'account_accountant',
        'account_asset',
        'account_online_sync',
    ],
    'demo': [
        'demo/res_company.xml',
        'demo/online_providers.xml',
        'demo/online_journals.xml',
        'demo/account_journals.xml',
    ],
    'data': [
        'views/account_config_settings.xml',
        'views/accountant_dashboard.xml',
        'security/account_xunnel_security.xml',
        'views/assets.xml',
        'wizards/change_date.xml',
    ],
    'qweb': [
        'views/account_templates.xml'
    ],
    'installable': True,
}

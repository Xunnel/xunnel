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
        'account_online_sync',
        'l10n_mx_edi_vendor_bills',
    ],
    'data': [
        'views/account_config_settings.xml',
        'data/ir_cron.xml',
        'data/config_xunnel_url.xml',
    ],
    'demo': [
        'demo/res_company.xml',
        'demo/online_providers.xml',
        'demo/online_journals.xml',
        'demo/account_journals.xml',
        'demo/ir_attachments.xml',
    ],
    'installable': True,
}

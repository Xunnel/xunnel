# Copyright 2017, Vauxoo, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Xunnel Account',
    'summary': '''
        Use Xunnel Account to retrieve bank statements and add new bank accounts.
    ''',
    'version': '14.0.1.0.0',
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
    ],
    'data': [
        # WiZARDS
        'wizards/wizard_change_date.xml',
        'wizards/wizard_download_bank_accounts.xml',
        'wizards/wizard_set_up_connection_token.xml',

        # SECURITY
        'security/ir.model.access.csv',

        # DATA
        'data/config_parameters.xml',
        'data/images_library.xml',
        'data/xunnel_actions.xml',

        # VIEWS
        'views/account_online_sync.xml',
        'views/accountant_dashboard.xml',
        'views/assets.xml',
        'views/xunnel_menuitems.xml',

        # WIZARDS
    ],
    'qweb': [
        'static/src/xml/add_account_manager.xml',
    ],
    'installable': True,
}

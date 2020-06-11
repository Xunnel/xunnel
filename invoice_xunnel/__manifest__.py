# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Xunnel Invoice',
    'summary': '''
        Use Xunnel Invoice to retrieve invoices from SAT.
    ''',
    'version': '11.0.1.0.42',
    'author': 'Jarsa Sistemas,Vauxoo',
    'category': 'Accounting',
    'website': 'http://www.jarsa.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'account_xunnel',
        'l10n_mx_edi',
    ],
    'data': [
        'views/assets.xml',
        'data/groups.xml',
        'data/res_partner_category.xml',
        'wizards/attach_xmls_wizard_view.xml',
        'wizards/attachment.xml',
        'views/account_config_settings.xml',
        'views/account.xml',
    ],
    'demo': [
        'demo/res_company.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'installable': True,
}

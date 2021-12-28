# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Xunnel Invoice',
    'summary': '''
        Use Xunnel Invoice to retrieve invoices from SAT.
    ''',
    'version': '14.0.1.0.0',
    'author': 'Jarsa Sistemas, Vauxoo',
    'category': 'Accounting',
    'website': 'http://www.xunnel.com',
    'license': 'LGPL-3',
    'depends': [
        'account_xunnel',
        'documents',
        'l10n_mx_edi',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/documents_views.xml',
        'wizards/documents.xml',
        'views/xunnel_menuitems.xml',
    ],
    'demo': [
        'demo/res_company.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'installable': True,
}

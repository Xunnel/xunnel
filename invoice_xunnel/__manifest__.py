# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Xunnel Invoice",
    "summary": """
        Use Xunnel Invoice to retrieve invoices from SAT.
    """,
    "version": "19.0.1.0.0",
    "author": "Jarsa Sistemas, Vauxoo",
    "category": "Accounting",
    "website": "http://www.xunnel.com",
    "license": "LGPL-3",
    "depends": [
        "account_xunnel",
        "documents",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/documents_views.xml",
        "wizards/documents.xml",
        "views/xunnel_menuitems.xml",
        "data/ir_actions_server_data.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/web/static/lib/jquery/jquery.js",
            "/invoice_xunnel/static/src/lib/google_pretty_print.js",
            "/invoice_xunnel/static/src/scss/main.scss",
            "/invoice_xunnel/static/src/js/documents.js",
            "/invoice_xunnel/static/src/js/attachment_viewer_viewable.js",
            "/invoice_xunnel/static/src/js/documents_attachment_viewer.js",
            "/invoice_xunnel/static/src/js/documents_details_panel.js",
            "/invoice_xunnel/static/src/xml/attachment_viewer.xml",
            "/invoice_xunnel/static/src/xml/documents_details_panel.xml",
        ],
    },
    "installable": True,
}

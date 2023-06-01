# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Xunnel Invoice",
    "summary": """
        Use Xunnel Invoice to retrieve invoices from SAT.
    """,
    "version": "16.0.1.0.0",
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
    ],
    "assets": {
        "web.assets_backend": [
            "/invoice_xunnel/static/src/lib/google_pretty_print.js",
            "/invoice_xunnel/static/src/lib/notify.min.js",
            "/invoice_xunnel/static/src/scss/main.scss",
            "/invoice_xunnel/static/src/js/models/documents.js",
            "/invoice_xunnel/static/src/js/models/attachment_viewer_viewable.js",
            "/invoice_xunnel/static/src/js/components/attachment_viewer.xml",
            "/invoice_xunnel/static/src/js/documents_inspector.js",
            "/invoice_xunnel/static/src/js/documents_attachment_viewer.js",
            "/invoice_xunnel/static/src/js/documents_kanban_record.js",
            "/invoice_xunnel/static/src/xml/templates.xml",
        ],
    },
    "installable": True,
}

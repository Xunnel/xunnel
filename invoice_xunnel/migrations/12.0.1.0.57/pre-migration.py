from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    add_tags(cr)


def add_tags(cr):
    """Adding tags to the files that should not synchronize when updating
    the tables in the database."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    # super lame hack to avoid computing already downloaded invoices, thanks
    # Javi.
    env['ir.attachment'].search([('folder_id', '=', 2)]).write({
        'url': 'nocompute'
    })

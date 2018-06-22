from odoo import http
from odoo.http import request, Controller

class MainController(Controller):

    @http.route('/webhook/', type='http', auth='public', csrf=False)
    def webhook_hanlder(self, **kw):
        provider = kw.get('credential')
        if not provider:
            return
        request.env['res.company'].sync_providers_webhook(provider)

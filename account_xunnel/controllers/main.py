from odoo import http
from odoo.http import request, Controller

class MainController(Controller):

    @http.route('/webhook/', type='json', auth='public', csrf=False)
    def webhook_hanlder(self, **kw):
        post = request.jsonrequest
        provider = post.get('credential')
        if not provider:
            return
        request.env['res.company'].sudo().cron_get_xunnel_providers(provider)
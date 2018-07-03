from odoo import http
from odoo.http import request, Controller


class MainController(Controller):

    @http.route('/webhook/', type='json', auth='public', csrf=False)
    def webhook_hanlder(self, **kw):
        post = request.jsonrequest
        provider = post.get('provider')
        event = post.get('handle')
        data = post.get('sync_data')

        if event == 'refresh':
            journal = request.env['account.online.journal'].sudo().search(
                [('online_identifier', '=', data.get('journal'))])
            journal.retrieve_transactions(forced_params=data)
        else:
            request.env[
                'res.company'].sudo().cron_get_xunnel_providers(provider)

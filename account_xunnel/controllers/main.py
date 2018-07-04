from odoo import http
from odoo.http import request, Controller


class MainController(Controller):

    @http.route('/account_xunnel/webhook_notification/', type='json', auth='public', csrf=False)
    def webhook_hanlder(self, **kw):
        post = request.jsonrequest
        provider = post.get('provider')
        event = post.get('handle')
        data = post.get('sync_data')

        if event == 'refresh':
            for journal_id in data:
                journal_data = data[journal_id]
                journals = request.env['account.online.journal'].sudo().search(
                    [('online_identifier', '=', journal_data.get('journal'))])
                for journal in journals:
                    journal.retrieve_transactions(forced_params=journal_data)
        else:
            request.env[
                'res.company'].sudo().cron_get_xunnel_providers(provider)

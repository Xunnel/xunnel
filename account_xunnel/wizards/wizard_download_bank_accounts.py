from odoo import fields, models


class WizardDownloadBankAccounts(models.TransientModel):
    _name = 'wizard.download.bank.accounts'
    _description = """Xunnel: Download your bank accounts. This wizard allows the users to synchronize its bank
    accounts from the Accounting module"""

    xunnel_token = fields.Char('res.company', default=lambda self: self.env.user.company_id.xunnel_token)

    def sync_xunnel_providers(self):
        return self.env['res.config.settings'].sync_xunnel_providers()

from odoo import fields, models


class WizardNewtoken(models.TransientModel):
    _name = 'wizard.set.up.connection.token'
    _description = """Wizard to set the Xunnel Token of your company, this is given when you
    create a company at https://www.xunnel.com/"""

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, readonly=True)
    xunnel_token = fields.Char(related='company_id.xunnel_token', readonly=False)

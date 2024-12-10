# Copyright 2017, Vauxoo, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountOnlineLink(models.Model):
    _inherit = "account.online.link"

    is_xunnel = fields.Boolean()

    def sync_journals(self):
        """Get all journals and check them in the database
        to create them if they're not.
        """
        for journal in self._get_journals():
            online_account = self.env["account.online.account"].search(
                [("account_online_link_id", "=", self.id), ("online_identifier", "=", journal.get("id_account"))]
            )
            vals = {
                "name": journal.get("name"),
                "balance": journal.get("balance"),
                "account_number": journal.get("number"),
                "online_identifier": journal.get("id_account"),
                "account_online_link_id": self.id,
            }
            if online_account:
                online_account.write(vals)
            else:
                online_account.create(vals)

    def _get_journals(self):
        """Requests https://wwww.xunnel.com/ to retrive all journals
        related to the indicated provider.
        """
        res = self.company_id._xunnel("get_xunnel_journals", {"account_identifier": self.client_id})
        err = res.get("error")
        if err:
            raise UserError(err)
        return res.get("response")

    def update_credentials(self):
        raise UserError(
            _("Updating credentials is not allowed here. Please go to https://www.xunnel.com/ to achieve that.")
        )

    def _open_iframe(self, mode="link", include_param=None, preferred_institution=False, journal_id=False):
        if self.is_xunnel:
            self.xunnel_exception()
        return super()._open_iframe(mode, include_param, preferred_institution, journal_id)

    def xunnel_exception(self):
        raise UserError(
            _(
                "Xunnel bank: Unsupported operation.\
                Please check our documentation in: https://xunnel.com/en_US/user-manual"
            )
        )

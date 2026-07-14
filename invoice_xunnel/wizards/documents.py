from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class DocumentsWizard(models.TransientModel):
    _name = "xunnel.documents.wizard"
    _description = "Xunnel documents sync"

    date_from = fields.Date(
        default=lambda self: self.env.company.xunnel_last_sync,
        help="Lower bound used to request SAT XMLs from Xunnel.",
    )
    date_to = fields.Date(
        default=fields.Date.context_today,
        help=(
            "Upper bound used to stop the SAT XML synchronization range. "
            "If empty, it will download all invoices from the start date until today."
        ),
    )
    message = fields.Char(help="Used to show the synchronization status.")
    no_attachment_action = fields.Boolean(help="Used to toggle the redirect to the attachments.")

    def synchronize_documents(self):
        """Synchronize SAT XMLs from Xunnel for the selected date range.

        The wizard keeps `date_from` as the persisted lower bound through
        `xunnel_last_sync` and sends `date_to` as the optional upper bound
        supported by the Xunnel endpoint.

        If there was downloaded attachments, it also shows a button
        to redirect to those attachments.
        """
        if not self.date_from:
            raise UserError(_("Please select a start date."))
        if self.date_to and self.date_to < self.date_from:
            raise UserError(_("The end date cannot be earlier than the start date."))
        company = self.env.company.sudo()
        company.xunnel_last_sync = self.date_from
        # `get_invoices_sat` treats `last_sync_to` as an exclusive cutoff at
        # the exact instant sent, not normalized to end-of-day (confirmed
        # empirically against the real endpoint, see MR 216 description).
        # Adding a day keeps the whole calendar day the user picked inside
        # the requested window.
        date_to = self.date_to + timedelta(days=1) if self.date_to else False
        result = company._sync_xunnel_documents(date_to=date_to)
        failed = result.get("failed")
        created = result.get("created")
        message = _("%d xml have been downloaded.", len(created))
        if failed:
            message += _(" Also %d files have failed at the conversion.", failed)
        action = self.env.ref("invoice_xunnel.action_product_confirm_wizard").sudo().read()[0]
        action["context"] = {
            "default_message": message,
            "default_no_attachment_action": not created,
            "downloaded_invoice": created,
        }
        return action

    def open_documents(self):
        """Opens the Documents's dashboard, with the just downloaded
        attachments `ir.filter` active. Also the "Finance" folder is opened
        by default.
        """
        folder_id = self.env.ref("documents.documents_finance_folder")
        action = self.env.ref("documents.document_action").sudo().read()[0]
        action["context"] = {
            "search_default_filter_downloaded_xml": True,
            "searchpanel_default_folder_id": folder_id.id,
            "downloaded_invoice": self._context.get("downloaded_invoice"),
        }
        return action

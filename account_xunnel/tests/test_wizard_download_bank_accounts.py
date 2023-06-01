from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestWizardChangeDate(TransactionCase):
    @patch("odoo.addons.account_xunnel.models.res_config_settings.AccountConfigSettings.sync_xunnel_providers")
    def test_01_sync_xunnel_providers(self, patch_sync_xunnel_providers):
        self.env["wizard.download.bank.accounts"].sync_xunnel_providers()
        patch_sync_xunnel_providers.assert_called_once()

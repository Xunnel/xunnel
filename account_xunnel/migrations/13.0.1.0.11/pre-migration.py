

def delete_providers_rules(cr):
    cr.execute("""
        UPDATE ir_model_data set noupdate='f'
        WHERE module='account_xunnel'
        AND name=ANY(ARRAY[
            'account_online_sync_provider_rule',
            'account_online_sync_journal_rule'
        ]);
    """)


def migrate(cr, version):
    if not version:
        return
    delete_providers_rules(cr)

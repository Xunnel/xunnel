import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    clear_old_views(cr)


def clear_old_views(cr):
    """Clear the content of the dashboard views from previous versions that conflict.

    When migrating from previous versions, the views of the journal dashboard keep their old content
    in the database until this module updates them, but the merged view that inherits the same
    dashboard is loaded first. Since the old content of some of them references elements that no
    longer exist (e.g., ``//a[@name='manual_sync']``), applying the merged view fails.

    Their content is cleared, so they don't change the dashboard while it's loaded. The view that
    keeps its ID gets its new content from this module, and the ORM removes the one whose ID no
    longer exists after all modules are updated.
    """
    view_names_to_clear = (
        "account_journal_dashboard_inherit_online_sync_id",
        "journal_dashboard_view_inherit_inherit",
    )
    cr.execute(
        """
        UPDATE
            ir_ui_view AS view
        SET
            arch_db = '{"en_US": "<data/>"}'
        FROM
            ir_model_data AS xmlid
        WHERE
            xmlid.res_id = view.id
            AND xmlid.model = 'ir.ui.view'
            AND xmlid.module = 'account_xunnel'
            AND xmlid.name IN %(view_names)s
        RETURNING
            xmlid.module || '.' || xmlid.name;
        """,
        {"view_names": view_names_to_clear},
    )
    cleared_views = sorted(row[0] for row in cr.fetchall())
    _logger.info("Cleared the content of %d views: %s", len(cleared_views), ", ".join(cleared_views))

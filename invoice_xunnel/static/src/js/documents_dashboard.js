odoo.define('invoice_xunnel.documents_dashboard', (require) => {

    const Kanban = require('documents.DocumentsKanbanView');

    Kanban.include({
        init() {
            this._super.apply(this, arguments);
            _.defaults(this.fieldsInfo[this.viewType], _.pick(this.fields, [
                'emitter_partner_id',
                'xunnel_document',
                'invoice_total_amount',
                'product_list',
            ]));
        }
    });

    return Kanban;
});

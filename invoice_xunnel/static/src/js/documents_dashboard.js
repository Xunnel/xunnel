odoo.define('invoice_xunnel.documents_dashboard', (require) => {

    const Kanban = require('documents.DocumentsKanbanView');

    Kanban.include({
        init() {
            this._super.apply(this, arguments);
            _.defaults(this.fieldsInfo[this.viewType], _.pick(this.fields, [
                'emitter_partner_id',
                'xunnel_attachment'
            ]));
            this.fieldsInfo[this.viewType].available_rule_ids = _.extend({}, {
                fieldsInfo: {
                    default: {
                        display_name: {},
                        note: {},
                    },
                },
                relatedFields: {
                    display_name: {type: 'string'},
                    note: {type: 'string'},
                },
                viewType: 'default',
            }, this.fieldsInfo[this.viewType].available_rule_ids);
        }
    });

    return Kanban;
});

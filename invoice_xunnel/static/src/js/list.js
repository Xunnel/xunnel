
odoo.define('invoice_xunnel.list_controller', (require) => {

    const ListView = require('web.ListView');
    const ListController = require('web.ListController');
    const ViewRegistry = require('web.view_registry');
    const { qweb } = require('web.core');

    /**
     * Registers a new List Controller to open the wizard to sync invoices from SAT.
     * 
     * To retrieve the controller use `ViewRegistry.get` method.
     */    
    ViewRegistry.add('invoice_xunnel_sync_button', ListView.extend({
        config: Object.assign({}, ListView.prototype.config, {
            Controller: ListController.extend({
                renderButtons (node) {
                    this._super.call(this, node);
                    $(qweb.render('invoice_xunnel.import_button')).click(() => this.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'xunnel.documents.wizard',
                        target: 'new',
                        views: [[false, 'form']]
                    })).appendTo(this.$buttons);
                },
            }),
        }),
    }));
});

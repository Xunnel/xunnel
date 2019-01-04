odoo.define('account_xunnel.synchronized_accounts', (require) => {
    "use strict";

    const Widget = require('web.Widget');
    const core = require('web.core');

    const SyncrhonizedAccounts = Widget.extend({
        template: 'account_xunnel.synchronized_accounts',
        init(parent, ctx){
            this.message = ctx.message;
            this.message_class = ctx.message_class;
            return this._super.apply(this, arguments);
        }
    });

    core.action_registry.add('account_xunnel.syncrhonized_accounts', SyncrhonizedAccounts)
})

/** @odoo-module **/

import {registry} from "@web/core/registry";
import {Component} from "@odoo/owl";

class SyncrhonizedAccounts extends Component {
    setup() {
        this.message = this.props.action.params.message;
        this.message_class = this.props.action.params.message_class;
    }
    _close_action() {
        this.do_action({type: "ir.actions.act_window_close"});
    }
    // renderButtons($node) {
    //     debugger;
    //     this.$buttons = $(this.qweb.render("account_xunnel.synchronized_accounts_footer", {widget: this}));
    //     this.$buttons.find(".js_cancel").click(() => this.do_action({type: "ir.actions.act_window_close"}));
    //     this.$buttons.appendTo($node);
    // }
}
SyncrhonizedAccounts.template = "account_xunnel.synchronized_accounts_template";

registry.category("actions").add("account_xunnel.SyncrhonizedAccounts", SyncrhonizedAccounts);

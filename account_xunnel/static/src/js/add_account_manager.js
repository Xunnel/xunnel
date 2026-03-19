/** @odoo-module **/

import {registry} from "@web/core/registry";
import {Component, onMounted, onWillUnmount, useRef, useState} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {renderToString} from "@web/core/utils/render";

class AccountManager extends Component {
    async setup() {
        this.state = useState({
            loading: true,
        });
        this.orm = useService("orm");
        this.mainXunnelContainer = useRef("mainXunnelContainer");
        onMounted(async () => {
            const divMainXunnelContainer = document.createElement("div");
            divMainXunnelContainer.id = "mainXunnelContainer";
            window.document.body.appendChild(divMainXunnelContainer);
            const {src, token, locale, css} = await this.orm.call("res.users", "get_xunnel_token");
            this.locale = locale;
            this.token = token;
            const link = document.createElement("link");
            const script = document.createElement("script");
            link.rel = "stylesheet";
            link.href = css;
            script.src = src;
            script.async = false;
            window.document.head.append(link);
            window.document.head.append(script);
            script.onload = () => (this.state.loading = false);
        });
    }
    openManager() {
        this.mainXunnelContainer.el.closest(".modal")?.classList.add("d-none");
        const widget = new SyncWidget({
            token: this.token,
            element: "#mainXunnelContainer",
            config: {navigation: {quickAnswer: true}},
        });
        widget.$on("closed", () => window.location.reload());
        widget.$on("status", (...args) => console.warn(...args));
        widget.open();
    }
}
AccountManager.template = "account_xunnel.add_account_manager";

registry.category("actions").add("tag_xunnel_add_account_manager", AccountManager);

/** @odoo-module **/

import {registerPatch} from "@mail/model/model_core";
import {attr} from "@mail/model/model_field";
import "@documents/models/document";

registerPatch({
    name: "Document",
    fields: {
        isXml: attr({
            compute() {
                if (this.isMxXml) return false;
                return this.mimetype === "application/xml";
            },
        }),
    },
});

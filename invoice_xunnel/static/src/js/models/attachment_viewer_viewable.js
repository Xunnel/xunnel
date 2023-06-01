/** @odoo-module **/

import {registerPatch} from "@mail/model/model_core";
import {attr} from "@mail/model/model_field";
import "@mail/models/attachment_viewer_viewable";

registerPatch({
    name: "AttachmentViewerViewable",
    fields: {
        isXml: attr({
            compute() {
                return this.mimetype === "application/xml";
            },
        }),
    },
});

/* @odoo-module */

import {patch} from "@web/core/utils/patch";
import {Attachment} from "@mail/core/common/attachment_model";

patch(Attachment.prototype, {
    get isMxXml() {
        if (super.isMxXml) {
            return true;
        }
        if (["application/xml", "text/xml"].includes(this.mimetype)) {
            return true;
        }
        return this.mimetype === "text/plain" && this.name && this.name.toLowerCase().endsWith(".xml");
    },
    get isMimetypeTextual() {
        return this.isMxXml ? false : super.isMimetypeTextual;
    },
    async loadDocumentTextContent() {
        if (this.isMxXml) {
            return;
        }
        return super.loadDocumentTextContent();
    },
});

/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {DocumentsKanbanRecord} from "@documents/views/kanban/documents_kanban_model";

patch(DocumentsKanbanRecord.prototype, "documents_xunnel_kanban_record", {
    /**
     * @override
     * allow to visualize XML files in the documents kanban dashboard
     */
    isViewable() {
        return this.data.mimetype === "application/xml" || this._super(...arguments);
    },
});

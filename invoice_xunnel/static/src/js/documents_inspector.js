/** @odoo-module **/

import {inspectorFields} from "@documents/views/inspector/documents_inspector";

// charge the following fields in the list of fields per record in the document inspector
// to use them in the DocumentsInspector template.
inspectorFields.push(
    "emitter_partner_id",
    "sat_status",
    "invoice_total_amount",
    "xunnel_document",
    "product_list",
    "related_cfdi"
);

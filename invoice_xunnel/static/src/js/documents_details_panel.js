/* @odoo-module */

import {patch} from "@web/core/utils/patch";
import {DocumentsDetailsPanel} from "@documents/components/documents_details_panel/documents_details_panel";
import {SelectionField} from "@web/views/fields/selection/selection_field";
import {MonetaryField} from "@web/views/fields/monetary/monetary_field";

patch(DocumentsDetailsPanel.components, {
    SelectionField,
    MonetaryField,
    ...DocumentsDetailsPanel.components,
});

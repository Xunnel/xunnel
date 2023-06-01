/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {DocumentsAttachmentViewer} from "@documents/views/helper/documents_attachment_viewer";

const {useEffect} = owl;

patch(DocumentsAttachmentViewer.prototype, "documents_xunnel_attachment_viewer", {
    /**
     * @override
     * allow to prettify the text within a XML shown with
     * the iframe and add events to allow copy text to clipboard
     */
    setup() {
        this._super(...arguments);
        useEffect(
            (iframe) => {
                if (!iframe) {
                    return;
                }
                // Wait until the iframe is loaded to be able to bind our copy handler and prettify the
                // content within a XML
                const onLoad = () => {
                    if (!iframe.contentDocument) {
                        return;
                    }
                    const $iframe = $(iframe),
                        iframeDocumentElement = iframe.contentDocument.documentElement,
                        $iframePre = $(iframeDocumentElement).find("pre");
                    if ($iframe.hasClass("o_AttachmentViewer_isXml") && $iframePre.length) {
                        let content = $($iframePre)[0].innerHTML;
                        let pre_content = PR.prettyPrintOne(content.trim());
                        let prettyprint_css = document.createElement("link");
                        prettyprint_css.href =
                            "https://cdn.rawgit.com/google/code-prettify/master/loader/prettify.css";
                        prettyprint_css.rel = "stylesheet";
                        prettyprint_css.type = "text/css";
                        iframe.contentDocument.head.append(prettyprint_css);
                        let main_css = document.createElement("link");
                        main_css.href = "/invoice_xunnel/static/src/scss/main.scss";
                        main_css.rel = "stylesheet";
                        main_css.type = "text/css";
                        iframe.contentDocument.head.append(main_css);
                        $iframePre.html(pre_content);
                        $(iframeDocumentElement).find(".atn, .atv").click(this.copy_attribute.bind(this));
                    }
                };
                iframe.addEventListener("load", onLoad);
            },
            () => [this.root.el && this.root.el.querySelector("iframe")]
        );
    },

    copy_attribute(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const target = $(ev.currentTarget);
        const text = target.hasClass("atv")
            ? this.get_target_value(target)
            : this.get_target_value(target.next().next());
        this.copy(text);
    },

    get_target_value(element) {
        return element.text().replace(/\"/g, "");
    },

    copy(textContent) {
        const input = $();
        input.val(textContent);
        navigator.clipboard.writeText(textContent);
        $.notify("Data copied.", {
            className: "alert alert-warning",
        });
    },
});

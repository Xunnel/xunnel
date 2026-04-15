/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {DocumentsFileViewer} from "@documents/views/helper/documents_file_viewer";
import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";

const {useEffect} = owl;

patch(DocumentsFileViewer.prototype, {
    /**
     * @override
     * allow to prettify the text within a XML shown with
     * the iframe and add events to allow copy text to clipboard
     */
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
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
                    const iframeDocumentElement = iframe.contentDocument.documentElement;
                    const iframePreElements = iframeDocumentElement.querySelectorAll("pre");
                    if (iframe.classList.contains("o_AttachmentViewer_isXml") && iframePreElements.length) {
                        let content = iframePreElements[0].innerHTML;
                        let pre_content = PR.prettyPrintOne(content.trim());
                        let prettyprint_css = document.createElement("link");
                        prettyprint_css.href =
                            "https://cdn.rawgit.com/google/code-prettify/master/loader/prettify.css";
                        prettyprint_css.rel = "stylesheet";
                        prettyprint_css.type = "text/css";
                        iframe.contentDocument.head.append(prettyprint_css);
                        let main_css = document.createElement("link");
                        main_css.href = "/invoice_xunnel/static/src/css/iframe.css";
                        main_css.rel = "stylesheet";
                        main_css.type = "text/css";
                        iframe.contentDocument.head.append(main_css);
                        iframePreElements.forEach((pre) => (pre.innerHTML = pre_content));
                        iframeDocumentElement.querySelectorAll(".atn, .atv").forEach((el) => {
                            el.addEventListener("click", this.copy_attribute.bind(this));
                        });
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
        const target = ev.currentTarget;
        const text = target.classList.contains("atv")
            ? this.get_target_value(target)
            : this.get_target_value(target.nextSibling?.nextSibling);
        this.copy(text);
    },

    get_target_value(element) {
        if (!element) return "";
        return element.textContent.replace(/\"/g, "");
    },

    copy(textContent) {
        navigator.clipboard.writeText(textContent);
        this.notification.add(_t("Link copied to clipboard!"), {
            type: "success",
        });
    },
});

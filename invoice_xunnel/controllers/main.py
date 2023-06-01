from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.binary import Binary


class BinaryXunnel(Binary):
    @http.route(
        [
            "/web/content",
            "/web/content/<string:xmlid>",
            "/web/content/<string:xmlid>/<string:filename>",
            "/web/content/<int:id>",
            "/web/content/<int:id>/<string:filename>",
            "/web/content/<string:model>/<int:id>/<string:field>",
            "/web/content/<string:model>/<int:id>/<string:field>/<string:filename>",
        ],
        type="http",
        auth="public",
    )
    def content_common(
        self,
        xmlid=None,
        model="ir.attachment",
        id=None,
        field="raw",
        filename=None,
        filename_field="name",
        mimetype=None,
        unique=False,
        download=False,
        access_token=None,
        nocache=False,
    ):
        """Format the content of an XML file within the Documents previsualization iframe.

        To display the content inside the XML file some characteres are replaced
        by its HTML entity and the <pre> tag is also added."""
        # pylint: disable=redefined-builtin
        response = super().content_common(
            xmlid=xmlid,
            model=model,
            id=id,
            field=field,
            filename=filename,
            filename_field=filename_field,
            mimetype=mimetype,
            unique=unique,
            download=download,
            access_token=access_token,
            nocache=nocache,
        )
        if model == "documents.document":
            if not id:
                return response
            document = request.env["documents.document"].browse(id)
            if not document.attachment_id:
                return response
            if "xml" not in document.attachment_id.mimetype:
                return response
            response_content = list(response.response)[0]
            response_content = response_content.decode("utf-8")
            response_content = response_content.replace("<", "&lt;")
            response_content = response_content.replace(">", "&gt;")
            return '<pre class="prettyprint">' + response_content + "</pre>"
        return response

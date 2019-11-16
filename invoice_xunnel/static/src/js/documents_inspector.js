odoo.define('invoice_xunnel.DocumentsInspector', function( require ) {

    var DocumentsInspector = require('documents.DocumentsInspector');

    DocumentsInspector.include({
        _renderFields: function() {
            this._super();
            var only_xunnel = this.records.filter( function ( record ) { 
                return record.data.xunnel_document;
            });
            if(only_xunnel.length === 1){
                this._renderField('emitter_partner_id', {
                    label: 'Emitter',
                    icon: 'fa fa-user-circle o_documents_folder_color'
                });
                this._renderField('invoice_total_amount', {
                    label: 'Total',
                    icon: 'fa fa-usd o_documents_tag_color'
                });
            }
        }
    });
});

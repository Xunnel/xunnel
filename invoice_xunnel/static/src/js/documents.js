odoo.define('invoice_xunnel.documents', (require) => {

    const DocumentsInspector = require('documents.DocumentsInspector');

    DocumentsInspector.include({
        _renderFields(){
            this._super();
            if(this.records.length > 0){
                const only_xunnel = this.records.filter(
                    (record) => record.data.xunnel_attachment);
                if(only_xunnel.length > 0){
                    this._renderField('emitter_partner_id', {
                        label: 'Emitter',
                        icon: 'fa fa-user-circle o_documents_folder_color'
                    });
                }
            }
        }
    })
});

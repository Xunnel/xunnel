odoo.define('xunnel_account.acc_config_widget',function(require) {
    "use strict";  
    const core = require('web.core');
    const framework = require('web.framework');
    const rpc = require('web.rpc');
    const QWeb = core.qweb;
    const Widget = require('web.Widget');

    var XunnelAccountConfigurationWidget = Widget.extend({
        call(params, twofa){
            if(this.in_rpc_call === false){
                this.blockUI(true);
                this.$('.js_wait_updating_account').toggleClass('hidden');
                rpc.query({
                    model: 'account.online.provider',
                    method: 'xunnel_add_update_provider_account',
                    args: [[this.id], params, this.resp_json, twofa]
                }).then(result => {
                    this.blockUI(false);
                    if (result.account_online_provider_id !== undefined) {
                        this.id = result.account_online_provider_id;
                    }
                    this.resp_json = result;
                    this.renderElement();
                }, err => {
                    this.$('.js_wait_updating_account').toggleClass('hidden');
                    this.blockUI(false);
                })
            }
        },
        process_next_step() {
            const params = {};
            $(".js_online_sync_input").each(function(){
                params[this.name] = this.value;
            });
            return this.call(params, false);
        },
        blockUI(state){
            this.in_rpc_call = state;
            this.$('.btn').toggleClass('disabled');
            if (state === true) {
                framework.blockUI();
            }
            else {
                framework.unblockUI();
            }
        },
        init(parent, context){
            this._super(parent, context);
            this.site_info = context.site_info;
            this.resp_json = context.resp_json;
            this.in_rpc_call = false;
            this.init_call = true;
            if (context.context.init_call !== undefined) {
                this.init_call = context.context.init_call;
            }
            if (context.context.provider_account_identifier !== undefined) {
                this.id = context.context.provider_account_identifier;
            }
            if (context.context.open_action_end !== undefined) {
                this.action_end = context.context.open_action_end;
            }
            this.context = context.context;
            $('body').on('click', '.checked', function(){
                $('.checked').css({'opacity':'1', 'border':'0px'});
                $('#sect').find('input').prop('checked', false);
                $(this).css({'opacity':'.7', 'border':'2px solid purple'}).parent().find('input').prop('checked', true);
            });
        },
        bind_button(){
            this.$('.js_process_next_step').click(() => {
                this.process_next_step();
            });
            this.$('.js_process_twofa_step').click(() => {
                this.process_twofa_step();
            });
            this.$('.js_process_cancel').click(() => {
                this.$el.parents('.modal').modal('hide');
            });
        },
        renderElement(){
            if (this.resp_json && this.resp_json.action === 'success'){
                if (this.action_end){
                    rpc.query({
                        model: 'account.online.provider',
                        method: 'open_action',
                        args: [[this.id], this.action_end, this.resp_json.numberAccountAdded, this.context],
                    }).then(result => {
                        this.do_action(result);
                    });
                }
                else{
                    const local_dict = {
                        init_call: this.init_call, 
                        number_added: this.resp_json.numberAccountAdded,
                        transactions: this.resp_json.transactions
                    };
                    this.replaceElement($(QWeb.render('Success', local_dict)));
                }
            }
            else {
                this.resp_json.call = 'init';
                if (this.resp_json && this.resp_json.action === 'twofa') {
                    // this.show_mfa_to_user(this.resp_json);
                    this.resp_json.call = 'twofa';
                }
                else{
                    this.resp_json.institution_name = this.resp_json.name;
                }
                this.replaceElement($(QWeb.render('XunnelLogin', this.resp_json)));
            }
            this.bind_button();
        },
        process_twofa_step(){
            const params = this.resp_json.params;
            let token = $(".js_online_sync_input[name='token']").val();
            if (token === undefined){
                token = $(".js_online_sync_input[name='customtoken']").val();
            }
            if (token === undefined){
                token = $(".js_online_sync_input:checked").val();
            }
            this.call(params,{
                'twofa': token, 
                'twofa_config':this.resp_json.twofa[0], 
                'address': this.resp_json.address
            });
        },
    });
    core.action_registry.add('xunnel_online_sync_widget', XunnelAccountConfigurationWidget);
});

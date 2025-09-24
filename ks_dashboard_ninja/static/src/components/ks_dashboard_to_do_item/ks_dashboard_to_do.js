/** @odoo-module **/
import { Component, onWillStart, useState ,onMounted, onWillRender,useRef,onWillPatch, onRendered } from "@odoo/owl";
import { globalfunction } from '@ks_dashboard_ninja/js/ks_global_functions';
import { loadBundle } from "@web/core/assets";
import { isMobileOS } from "@web/core/browser/feature_detection";
import { useService } from "@web/core/utils/hooks";
import { Todoeditdialog, addtododialog } from "@ks_dashboard_ninja/components/ks_dashboard_to_do_item/editdialog";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { KsItemButton } from '@ks_dashboard_ninja/components/chart_buttons/chart_buttons';
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";

export class Ksdashboardtodo extends Component{
    setup(){
        super.setup();
        this._rpc = rpc
        this.dialogService = useService("dialog");
//        this.mailChatService = useService("mail.chat_window");
//        this.threadService = useService("mail.thread");
        this.state = useState({to_do_view_data : ""})
        this.todoRootRef = useRef("todoRootRef");
        this.item = this.props.item
        this.ks_dashboard_data = this.props.dashboard_data
        this.item.ksIsDashboardManager = this.props.dashboard_data.ks_dashboard_manager
        this.item.ks_dashboard_list = this.props.dashboard_data.ks_dashboard_list
        this.prepare_item();
    }

    get isMobile() {
        return isMobileOS();
    }


    ksFetchUpdateItem(item_id) {
        var self = this;
        return self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_fetch_item",{
            model: 'ks_dashboard_ninja.board',
            method: 'ks_fetch_item',
            args: [
                [parseInt(item_id)], self.ks_dashboard_data.ks_dashboard_id,{}
            ],
            kwargs: { context: self.env.getContext() },
        }).then(function(new_item_data) {
            this.ks_dashboard_data.ks_item_data[item_id] = new_item_data[item_id];
            this.item = this.ks_dashboard_data.ks_item_data[item_id] ;
            this.prepare_item()
        }.bind(this));
    }

    get ksIsDashboardManager(){
        return this.ks_dashboard_data.ks_dashboard_manager;
    }

    get ksIsUser(){
        return true;
    }

    get ks_dashboard_list(){
        return this.ks_dashboard_data.ks_dashboard_list;
    }

    prepare_item() {
            var self = this;
            var item = self.item
            self.ks_to_do_view_name = 'Test';
            self.item_id = item.id;
            self.list_to_do_data = JSON.parse(item.ks_to_do_data);
            self.state.to_do_view_data = JSON.parse(item.ks_to_do_data);

            self.ks_chart_title = item.name;

            if (item.ks_info){
                var ks_description = item.ks_info.replace?.(/\\n/g, '\n').split?.('\n');
                var ks_description = ks_description.filter(element => element !== '')?.join?.(' ') ?? false
            }else {
                var ks_description = false;
            }
            self.ks_header_color = self._ks_get_rgba_format(item.ks_header_bg_color);
            self.ks_font_color = self._ks_get_rgba_format(item.ks_font_color);
            var ks_rgba_button_color = self._ks_get_rgba_format(item.ks_button_color);
            self.ks_rgba_button_color = ks_rgba_button_color
            self.ks_info = ks_description
            self.ks_company = item.ks_company


    }

    _ks_get_rgba_format(val){
        var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
        rgba = rgba.map(function(v) {
            return parseInt(v, 16)
        }).join(",");
        return "rgba(" + rgba + "," + val.split(',')[1] + ")";
    }
    _onKsEditTask(e){
        var self = this;
        var ks_description_id = e.currentTarget.dataset.contentId;
        var ks_item_id = e.currentTarget.dataset.itemId;
        var ks_section_id = e.currentTarget.dataset.sectionId;
        var ks_description = $(e.currentTarget.parentElement.parentElement).find('.ks_description').attr('value');
        var ks_result = this.dialogService.add(Todoeditdialog,{
         ks_description :ks_description,
         confirm: (event) => {
                var content = $(event.currentTarget.parentElement.parentElement).find('.ks_description').val();
                    if (content.length === 0){
                        content = ks_description;
                    }
                    self.onSaveTask(content, parseInt(ks_description_id), parseInt(ks_item_id), parseInt(ks_section_id));
         },
            });

    }
    onSaveTask(content, ks_description_id, ks_item_id, ks_section_id){
        var self = this;
        rpc("/web/dataset/call_kw/ks_to.do.description/write",{
            model: 'ks_to.do.description',
            method: 'write',
            args: [ks_description_id, {
                        "ks_description": content
            }],
            kwargs:{},
            }).then(function() {
            self.ksFetchUpdateItem(ks_item_id).then(function(){
                $(".ks_li_tab[data-item-id=" + ks_item_id + "]").removeClass('active');
                $(".ks_li_tab[data-section-id=" + ks_section_id + "]").addClass('active');
                $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('active');
                $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('show');
                $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('active');
                $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('show');
                $(".header_add_btn[data-item-id=" + ks_item_id + "]").attr('data-section-id', ks_section_id);
                });
           });
    }

    _onKsDeleteContent(e){
            var self = this;
            var ks_description_id = e.currentTarget.dataset.contentId;
            var ks_item_id = e.currentTarget.dataset.itemId;
            var ks_section_id = e.currentTarget.dataset.sectionId;
            this.dialogService.add(ConfirmationDialog, {
                body: _t("Are you sure you want to remove this task?"),
                confirm: () => {
                    self._rpc("/web/dataset/call_kw/ks_to.do.description/unlink",{
                    model: 'ks_to.do.description',
                    method: 'unlink',
                    args: [parseInt(ks_description_id)],
                    kwargs:{}
                }).then(function(result) {
                self.ksFetchUpdateItem(ks_item_id).then(function(){
                    $(".ks_li_tab[data-item-id=" + ks_item_id + "]").removeClass('active');
                    $(".ks_li_tab[data-section-id=" + ks_section_id + "]").addClass('active');
                    $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('active');
                    $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('show');
                    $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('active');
                    $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('show');
                    $(".header_add_btn[data-item-id=" + ks_item_id + "]").attr('data-section-id', ks_section_id);
                 });
            });

            },
            cancel: () => {},
            });
        }

    _onKsAddTask(e){
            var self = this;
            var ks_section_id = e.currentTarget.dataset.sectionId;
            var ks_item_id = e.currentTarget.dataset.itemId;
            var ks_result = this.dialogService.add(addtododialog,{
                confirm: (event) => {
                var content = $(event.currentTarget.parentElement.parentElement).find('.ks_section').val();
                    self._onCreateTask(content, parseInt(ks_section_id), parseInt(ks_item_id));
                },
            });
    }
     _onCreateTask(content, ks_section_id, ks_item_id){
            var self = this;
            this._rpc("/web/dataset/call_kw/ks_to.do.description/create",{
                    model: 'ks_to.do.description',
                    method: 'create',
                    args: [{
                        ks_to_do_header_id: ks_section_id,
                        ks_description: content,
                    }],
                    kwargs:{}
                }).then(function() {
                    self.ksFetchUpdateItem(ks_item_id).then(function(){
                        $(".ks_li_tab[data-item-id=" + ks_item_id + "]").removeClass('active');
                        $(".ks_li_tab[data-section-id=" + ks_section_id + "]").addClass('active');
                        $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('active');
                        $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('show');
                        $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('active');
                        $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('show');
                        $(".header_add_btn[data-item-id=" + ks_item_id + "]").attr('data-section-id', ks_section_id);
                    });

                });
        }

        ksOnToDoClick(ev){
            ev.preventDefault();
            var self= this;
            var tab_id = $(ev.currentTarget).attr('href');
            var $tab_section = $('#' + tab_id.substring(1));
            $(ev.currentTarget).addClass("active");
            $(ev.currentTarget).parent().siblings().each(function(){
                $(this).children().removeClass("active");
            });
            $('#' + tab_id.substring(1)).siblings().each(function(){
                $(this).removeClass("active");
                $(this).addClass("fade");
            });
            $tab_section.removeClass("fade");
            $tab_section.addClass("active");
            $(ev.currentTarget).parent().parent().siblings().attr('data-section-id', $(ev.currentTarget).data().sectionId);
        }

        _onKsActiveHandler(e){
            var self = this;
            var ks_item_id = e.currentTarget.dataset.itemId;
            var content_id = e.currentTarget.dataset.contentId;
            var ks_task_id = e.currentTarget.dataset.contentId;
            var ks_section_id = e.currentTarget.dataset.sectionId;
            var ks_value = e.currentTarget.dataset.valueId;
            if (ks_value== 'True'){
                ks_value = false
            }else{
                ks_value = true
            }
            self.content_id = parseInt(content_id);
            rpc("/web/dataset/call_kw/ks_to.do.description/write",{
                    model: 'ks_to.do.description',
                    method: 'write',
                    args: [parseInt(content_id), {
                        "ks_active": ks_value
                    }],
                    kwargs:{}
                }).then(function() {
                    self.ksFetchUpdateItem(ks_item_id).then(function(){
                        $(".ks_li_tab[data-item-id=" + ks_item_id + "]").removeClass('active');
                        $(".ks_li_tab[data-section-id=" + ks_section_id + "]").addClass('active');
                        $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('active');
                        $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('show');
                        $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('active');
                        $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('show');
                        $(".header_add_btn[data-item-id=" + ks_item_id + "]").attr('data-section-id', ks_section_id);
                    });
                });
        }

};

Ksdashboardtodo.props = {
    item: { type: Object, Optional:true},
    dashboard_data: { type: Object, Optional:true},
    hideButtons: { type: Number, optional: true },
    on_dialog: { type: Boolean, optional: true },
    explain_ai_whole: { type: Boolean, optional: true }
};
Ksdashboardtodo.components = { Todoeditdialog, addtododialog, KsItemButton }

Ksdashboardtodo.template = "Ksdashboardtodo";

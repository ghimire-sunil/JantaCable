/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { setObjectInCookie, getObjectFromCookie, eraseCookie } from "@ks_dashboard_ninja/js/cookies";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";


export class FavFilterWizard extends Component{
    static template = "ks_dashboard_ninja.FavFilterWizard"
    static components = { Dialog }

    setup(){
//        this.favoriteFilterId = 0
    }
    save_favourite_filter(ev){
        let self = this;
        let ks_filter_name = $('#favourite_filter_name').val();
        let ks_is_fav_filter_shared = $('#favFilterShareBool').prop('checked')
        if (!ks_filter_name.length){
            this.notification.add(_t("A name for your favorite filter is required."), {
                    type: "warning",
                });

        }else{
            var ks_saved_fav_filters = Object.keys(self.props.dashboard_favourite_filter)
            const favourite = ks_saved_fav_filters.find(item => item == ks_filter_name)
            if (favourite?.length){
                this.notification.add(_t("A filter with same name already exists."), {
                    type: "warning",
                });
            }
            else{
                let domains_to_save = JSON.stringify(self.props.dashboard_domain_data)
                let newFavFilter = {name: ks_filter_name,
                                    ks_dashboard_board_id: self.props.dashboard_data.ks_dashboard_id,
                                    ks_filter: domains_to_save,
                                    ks_access_id: ks_is_fav_filter_shared ? false : user.userId}
                rpc("/web/dataset/call_kw/ks_dashboard_ninja.favourite_filters/create", {
                    model: 'ks_dashboard_ninja.favourite_filters',
                    method: 'create',
                    args: [newFavFilter],
                    kwargs: {}
                }).then(function(result){
                    newFavFilter.id = result
                    newFavFilter.ks_filter = self.props.dashboard_domain_data
                    self.props.save_favourite_filter(ks_filter_name, newFavFilter)
                    self.props.close();
                });
            }
        }
    }
}


export class FavouriteFilter extends Component{
    static props = {
        favourite_filters_data: { type: Object, optional: true },
        onDelete: { type: Function, optional: true },
        update: { type: Function, optional: true },
        remove: { type: Function, optional: true },
        options: { type: Object, optional: true },
    };
    static defaultProps = {

    };
    static template = "ks_dashboard_ninja.favourite_filter"
    static components = { Dropdown, DropdownItem }

    setup(){
//        this.dashboard_domain_data = {}
        this.state = useState({ current_active: ''})
        onWillStart( () => { this.setObjFromCookies() })

    }

    setObjFromCookies(){
        let current_active_from_cky = getObjectFromCookie('FFilter' + this.props.options.ks_dashboard_id)
        this.state.current_active = current_active_from_cky ?? ''
    }

    onFilterSelect(filterName){
        filterName !== this.state.current_active ? this.applyFavFilter(filterName) : this.removeFavFilter(filterName)
    }

    applyFavFilter(filterName){
        this.state.current_active = filterName
        eraseCookie('FFilter' + this.props.options.ks_dashboard_id)
        let domainsToUpdate = {}
        let filterToBeApplied = this.props.favourite_filters_data[filterName].ks_filter
        Object.keys(filterToBeApplied).forEach( (model) => {
            let domain = filterToBeApplied[model].domain
            domainsToUpdate[model] = { domain: domain , sub_domains: { [`FF_${filterName}`]: domain } }
        })
        setObjectInCookie('FFilter' + this.props.options.ks_dashboard_id, this.state.current_active, 1)
        this.props.update(domainsToUpdate)
    }

    removeFavFilter(filterName){
        eraseCookie('FFilter' + this.props.options.ks_dashboard_id)
        this.state.current_active = ''
        this.props.remove(Object.keys(this.props.favourite_filters_data[filterName].ks_filter) , [`FF_${filterName}`])
    }

    onDeleteBtnClick(filterName){
//        var ks_filter_domain = this.props.favourite_filters_data[filterName].filter;
        let ks_access_id = this.props.favourite_filters_data[filterName].ks_access_id;
//        var ks_remove_filter_models = Object.keys(ks_filter_domain)
//        const ks_items_to_update_remove = self.ks_dashboard_data.ks_dashboard_items_ids.filter((item) =>
//               ks_remove_filter_models.includes(self.ks_dashboard_data.ks_item_model_relation[item][0])|| ks_remove_filter_models.includes(self.ks_dashboard_data.ks_item_model_relation[item][1])
//        );
        this.env.services.dialog.add(ConfirmationDialog, {
            body: _t(`This filter is will be removed${ks_access_id ? '' : 'for everybody'} if you continue.`),
            confirmLabel: _t("Delete Filter"),
            title: _t("Delete Filter"),
            confirm: () => {
                this.delete_fav_filter(filterName)
            }
        })
    }

    delete_fav_filter(filterName){
         let self = this;
//         this.isFavFilter = false;
         rpc("/web/dataset/call_kw/ks_dashboard_ninja.favourite_filters/unlink", {
            model: 'ks_dashboard_ninja.favourite_filters',
            method: 'unlink',
            args: [Number(this.props.favourite_filters_data[filterName].id)],
            kwargs: {}
         }).then(function(result) {
            self.removeFavFilter(filterName)
            self.props.onDelete(filterName)
         });
    }


}

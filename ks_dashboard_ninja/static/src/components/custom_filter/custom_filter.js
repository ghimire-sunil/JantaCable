/** @odoo-module **/

import { Component, useState, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { useLoadFieldInfo } from "@web/core/model_field_selector/utils";
import { getDomainDisplayedOperators } from "@web/core/domain_selector/domain_selector_operator_editor";
import { Domain } from "@web/core/domain";
import { useService, useBus } from "@web/core/utils/hooks";
import { treeFromDomain, domainFromTree } from "@web/core/tree_editor/condition_tree";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { getOperatorLabel } from "@web/core/tree_editor/tree_editor_operator_editor";
import { getDefaultValue, getValueEditorInfo } from "@web/core/tree_editor/tree_editor_value_editors";
import { getExpressionDisplayedOperators } from "@web/core/expression_editor/expression_editor_operator_editor";
import { KsDropDown } from "@ks_dashboard_ninja/components/custom_filter/ks_dropdown";
import { _t } from "@web/core/l10n/translation";
import { disambiguate } from "@web/core/tree_editor/utils";
import { condition, connector } from "@web/core/tree_editor/condition_tree";
import { useGetTreeDescription } from "@web/core/tree_editor/utils";
import { setObjectInCookie, getObjectFromCookie, eraseCookie } from "@ks_dashboard_ninja/js/cookies";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";


export class CustomFilter extends Component{
    static props = {
        domain: { type: String, optional: true },
        update: { type: Function, optional: true },
        remove: { type: Function, optional: true },
        removeAllFilters: { type: Boolean, optional: true },
        options: { type: Object, optional: true },
        filter_info: { type: Object, optional: true },
    };
    static defaultProps = {
        update: () => {},
        domain: `[]`,
        filter_info: {},
    };

    setup(){
        this.notification = useService("notification");
        this.loadFieldInfo = useLoadFieldInfo();
        this.getDomainTreeDescription = useGetTreeDescription();
        this.state = useState({
            filtersRowList: [],
            toggleState: true
        });
        this.customDomainFacets = {}
        this.groupId = 0

        this.domain = this.props.domain
        this.filter_info = this.props.filter_info

        onWillStart(() => this.willStart());
        onWillUpdateProps((nextProps) => this.onPropsUpdated(nextProps))
    }

    onPropsUpdated(nextProps){
        if(nextProps.removeAllFilters){
            this.clearFacets_cookies()
            this.clearRows();
        }
    }

    willStart(){
        this.setObjFromCookies();
        const filters_list = Object.values(this.props.filter_info)
        this.loadFieldDefs_and_Labels(filters_list);
        const defaultOperator = getDomainDisplayedOperators(filters_list[0])[0]

        this.defaultFilterRowObject = {
            id: filters_list[0].id,
            operator: defaultOperator,
            value: getDefaultValue(filters_list[0], defaultOperator),
        }
        this.state.filtersRowList.push(JSON.parse(JSON.stringify(this.defaultFilterRowObject)));
    }

    setObjFromCookies(){
        let customDomainFacets_from_cky = getObjectFromCookie('CFilter' + this.props.options.ks_dashboard_id)
        this.customDomainFacets = customDomainFacets_from_cky?.lastAppliedFilters ?? {}
        this.groupId = customDomainFacets_from_cky?.lastGroupId ?? 0
    }

    rowFilter(filter_id){
        let filter = this.props.filter_info[filter_id]
        return filter.name + ' ( ' + filter.model_name + ' ) '
    }

    rowOperator(row_index){
        return getOperatorLabel(this.state.filtersRowList[row_index].operator)
    }

    // Remove Data from python , we load field defs here
     async loadFieldDefs_and_Labels(filters_list) {
        const promises = [];
        const filter_labels = [];
        const fieldDefs = {};
        for (const filter of filters_list) {
            filter_labels.push({ filter_name: filter.name + ' ( ' + filter.model_name + ' ) ', filter_id: filter.id})
            if (typeof filter.field_name === "string") {
                promises.push(
                    this.loadFieldInfo(filter.model, filter.field_name).then(({ fieldDef }) => {
                        fieldDefs[filter.id] = fieldDef;
                    })
                );
            }
        }
        await Promise.all(promises);
        this.fieldDefs = fieldDefs;
        this.filterLabels = filter_labels
    }

    getOperatorInfo(filter_id) {
        const fieldDef = this.fieldDefs[filter_id];
        const operators = getDomainDisplayedOperators(fieldDef);
        const operatorList = operators.map((operator) => ({
                                operator: operator,
                                label: getOperatorLabel(operator),
                            }));
        return operatorList;
    }

    getActiveOption(options, active){
        const foundOption = options.find(option => option[0] === active);
        return foundOption ? foundOption[1] : "Select";
    }

    getValueInfo(filter_row) {
        const fieldDef = this.fieldDefs?.[filter_row.id] || this.filter_info[filter_row.id];
        let valueInfo = getValueEditorInfo(fieldDef, filter_row.operator);
        if(valueInfo.component?.name === 'Select' || valueInfo.component?.name === 'List'){
            const options = fieldDef.selection || [];
            const params = {activeOption: this.getActiveOption(options, filter_row.value)}
            let KsSelectComponent = this.getKsSelectComponent(options, params)
            if(fieldDef.type === "boolean"){
                if (["is", "is_not"].includes(filter_row.operator)) {
                    const boolOptions = [
                        [true, _t("set")],
                        [false, _t("not set")],
                    ];
                    const boolParams = {activeOption: this.getActiveOption(boolOptions, filter_row.value)}
                    return this.getKsSelectComponent(boolOptions, boolParams)
                }
                const boolOptions2 = [
                    [true, _t("True")],
                    [false, _t("False")],
                ];
                const boolParams2 = {activeOption: this.getActiveOption(boolOptions2, filter_row.value)}
                return this.getKsSelectComponent(boolOptions2, boolParams2)
            }
            if(valueInfo.component?.name === 'List'){
                let editorInfo = getValueEditorInfo(fieldDef, "=", {
                    addBlankOption: true,
                    startEmpty: true,
                });
                if(editorInfo.component?.name === 'Select'){
                    editorInfo = KsSelectComponent
                    valueInfo.extractProps = ({ value, update }) => {
                        if (!disambiguate(value)) {
                            const { stringify } = editorInfo;
                            editorInfo.stringify = (val) => stringify(val, false);
                        }
                        return {
                            value,
                            update,
                            editorInfo,
                        };
                    }
                }
                return valueInfo;
            }
            return KsSelectComponent;
        }
        return valueInfo;
    }

    getKsSelectComponent(options, params){
        const getOption = (value) => options.find(([v]) => v === value) || null;
        return {
            component: KsDropDown,
            extractProps: ({ value, update }) => ({
                value,
                update,
                options,
                addBlankOption: params.addBlankOption,
                activeOption: params.activeOption || "Select"
            }),
            isSupported: (value) => Boolean(getOption(value)),
            defaultValue: () => options[0]?.[0] ?? false,
            stringify: (value, disambiguate) => {
                const option = getOption(value);
                return option ? option[1] : disambiguate ? formatValue(value) : String(value);
            },
            message: _t("Value not in selection"),
        };
    }

    getDefaultOperator(fieldDef) {
        return getExpressionDisplayedOperators(fieldDef)[0];
    }

    onUpdateFilter(filter_id, row_index){
        const fieldDef = this.fieldDefs[filter_id];
        const operator = this.getDefaultOperator(fieldDef)
        this.state.filtersRowList[row_index] = {
            id: filter_id,
            operator: operator,
            value: getDefaultValue(fieldDef, operator),
        }
    }

    addFilterRow(ev){
        const node = JSON.parse(JSON.stringify(this.defaultFilterRowObject));
        this.state.filtersRowList.push(node);
    }

    deleteRow(row_index){
        this.state.filtersRowList.splice(row_index, 1);
    }

    clearRows(ev){
        const node = JSON.parse(JSON.stringify(this.defaultFilterRowObject));
        this.state.filtersRowList = [node];
    }

    onUpdateValue(row_index, updated_value){
        let field_type = this.props?.filter_info?.[this.state.filtersRowList[row_index]?.id].type
        let operator = this.state.filtersRowList[row_index]?.operator
        if(field_type && ['many2many', 'many2one', 'one2many'].includes(field_type)){
            if (Array.isArray(updated_value)) {
                updated_value =  updated_value.flatMap(item => {
                                    if(item === "%UID") {
                                        return user.userId;
                                    } else if (item === "%MYCOMPANY") {
                                        return ["in", "not in"].includes(operator) ? this.env.services.company.activeCompanyIds : this.env.services.company.activeCompanyIds[0];
                                    } else {
                                        return item;
                                    }
                                });
            }
            else if(typeof updated_value === 'string'){
                if(updated_value === "%UID") {
                    updated_value =  user.userId;
                } else if (updated_value === "%MYCOMPANY") {
                    updated_value = this.env.services.company.activeCompanyIds[0];
                }
            }
        }
        this.state.filtersRowList[row_index].value = updated_value;
    }

    onUpdateOperator(operator, row_index){
        const fieldDef = this.fieldDefs[this.state.filtersRowList[row_index].id];
        this.state.filtersRowList[row_index].operator = operator;
        this.state.filtersRowList[row_index].value = getDefaultValue(fieldDef, operator, this.state.filtersRowList[row_index].value);
    }


    clearFacets_cookies(ev){
        eraseCookie('CFilter' + this.props.options.ks_dashboard_id)
        this.customDomainFacets = {}
    }

    async makeLabelsAndDomain(models_domain){
        await Promise.all(
            Object.entries(models_domain).map(async ([model, model_domain]) => {
                model_domain.label = await this.getDomainTreeDescription(model, model_domain.domain);
                model_domain.domain = new Domain(domainFromTree(model_domain.domain)).toList();
            })
        );
    }

    async applyFilters(ev) {
        eraseCookie('CFilter' + this.props.options.ks_dashboard_id)
        const filterRowList = this.state.filtersRowList;
        const models_domain = {};

        for (const filter_row of filterRowList) {
            const filter = this.filter_info[filter_row.id];
            const { model, field_name, model_name } = filter;
            const {operator, value} = filter_row

            if (!models_domain[model]) {
                models_domain[model] = {
                    domain: connector('|'),
                    label: 'Custom Filter',
                    model_name
                };
            }
            models_domain[model].domain.children.push(condition(field_name, operator, value));
        }

        await this.makeLabelsAndDomain(models_domain);
        let domainsToUpdate = await this.validate_and_ReturnDomainsToUpdate(models_domain);
        this.clearRows();
        setObjectInCookie('CFilter' + this.props.options.ks_dashboard_id,
                            { lastAppliedFilters: this.customDomainFacets, lastGroupId: this.groupId}, 1)
        this.props.update(domainsToUpdate);
    }

    async validate_and_ReturnDomainsToUpdate(models_domain){
        let domainsToUpdate = {}
        for(const [model, model_domain] of Object.entries(models_domain)){
            let domain;
            let isValid;
            try {
                const evalContext = { ...user.context };
                domain = new Domain(model_domain.domain).toList(evalContext);
            } catch {
                isValid = false;
            }
            if (isValid === undefined) {
                isValid = await rpc("/web/domain/validate", { model: model, domain, });
            }
            if (!isValid) {
                this.notification.add(_t("Domain is invalid. Please correct it"), {
                    type: "danger" });
                return;
            }
            this.updateFacets(model, model_domain);
            domainsToUpdate[model] = { [ `custom_filter_${this.groupId++}`] : { label: model_domain.label, domain: model_domain.domain } }

        }
        return domainsToUpdate;
    }

    updateFacets(model, model_domain){
        this.customDomainFacets[model] = this.customDomainFacets[model] || { groups: {}, model_name: model_domain.model_name }
        this.customDomainFacets[model].groups[`custom_filter_${this.groupId}`] = { label: model_domain.label, domain: model_domain.domain }
    }

    onRemoveFacet(model, group){
        eraseCookie('CFilter' + this.props.options.ks_dashboard_id)
        delete this.customDomainFacets[model].groups[group];

        if(!Object.values(this.customDomainFacets[model].groups).length)  delete this.customDomainFacets[model];
        setObjectInCookie('CFilter' + this.props.options.ks_dashboard_id,
                            { lastAppliedFilters: this.customDomainFacets, lastGroupId: this.groupId}, 1)
        this.props.remove([model], [group]);
        this.state.toggleState = !this.state.toggleState
    }

}

CustomFilter.template = "ks_dashboard_ninja.custom_filter"

CustomFilter.components = { Dropdown, DropdownItem }


import { patch } from "@web/core/utils/patch";
import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";

patch(AccountReportFilters.prototype, {
    async filterSalePersonClick({ optionKey, optionValue = undefined, reload = false }) {
        if (optionKey !== undefined) {
            optionKey.selected = !optionKey.selected;
            console.log(this);
            
            let selected = this.controller.options.sales_person_id.filter((item) => { return item.selected == true; })
            await this.controller.updateOption('sales_person_id', this.controller.options.sales_person_id, true);
        }
    }
});
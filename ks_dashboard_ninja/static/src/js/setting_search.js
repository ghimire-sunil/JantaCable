import { patch } from "@web/core/utils/patch";
import { escapeRegExp } from "@web/core/utils/strings";

import { SearchableSetting } from "@web/webclient/settings_form_view/settings/searchable_setting"


patch(SearchableSetting.prototype, {
    visible() {
        try {
            if (!this.state.search.value) {
                return true;
            }
            if (this.state.showAllContainer?.showAllContainer) {
                return true;
            }
            const regexp = new RegExp(escapeRegExp(this.state.search.value), "i");
            if (regexp.test(this.labels.join())) {
                return true;
            }
            return false;
        } catch (error) {
            console.log(error);

            return false
        }
    }

})
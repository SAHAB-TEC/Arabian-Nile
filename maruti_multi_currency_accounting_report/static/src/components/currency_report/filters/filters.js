/** @odoo-module */

import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";
import { patch } from "@web/core/utils/patch";

patch(AccountReportFilters.prototype,{

    //Extend base class and add new method for currency 
    async filterCurrency(currency) {
        currency.selected = !currency.selected;
        if (currency.selected){
            this.controller.options.currencies_selected = parseInt(currency.id)
            this.controller.options.currencies_selected_name = parseInt(currency.name)
        }
        console.log(currency)
        await this.controller.reload('currencies', this.controller.options);
    }

});
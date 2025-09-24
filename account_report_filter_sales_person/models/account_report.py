from odoo import models, api


# class AccountFilterPartnerLedger(models.AbstractModel):
#     _inherit = "account.partner.ledger.report.handler"

#     def _get_custom_display_config(self):
#         return {
#             "templates": {
#                 "AccountReportFilters": "account_report_filter_sales_person.AccountPartnerLedgerSalesFilter",
#             },
#         }


class AccountAgedPartnerBalance(models.AbstractModel):
    _inherit = "account.aged.partner.balance.report.handler"

    def _get_custom_display_config(self):
        return {
            "templates": {
                "AccountReportFilters": "account_report_filter_sales_person.AccountPartnerLedgerSalesFilter",
            },
        }


# class AccountGeneralLeadger(models.AbstractModel):
#     _inherit = "account.general.ledger.report.handler"

#     def _get_custom_display_config(self):
#         return {
#             "templates": {
#                 "AccountReportFilters": "account_report_filter_sales_person.AccountPartnerLedgerSalesFilter",
#             },
#         }


# class AccountTrialBalance(models.AbstractModel):
#     _inherit = "account.trial.balance.report.handler"

#     def _get_custom_display_config(self):
#         return {
#             "templates": {
#                 "AccountReportFilters": "account_report_filter_sales_person.AccountPartnerLedgerSalesFilter",
#             },
#         }


# class AccountBalanceSheet(models.AbstractModel):
#     _inherit = "account.balance.sheet.report.handler"

#     def _get_custom_display_config(self):
#         return {
#             "templates": {
#                 "AccountReportFilters": "account_report_filter_sales_person.AccountPartnerLedgerSalesFilter",
#             },
#         }


class AccountReport(models.Model):
    _inherit = "account.report"

    def _get_filter_all_sales_person(self, options):
        """
        Function to get the salespersons data in the filter dropdown.
        """
        item = [
            {"id": rec.id, "display_name": rec.display_name, "selected": False}
            for rec in self.env["res.users"].search(
                [
                    (
                        "groups_id",
                        "=",
                        self.env.ref("sales_team.group_sale_salesman").id,
                    ),
                    ("share", "=", False),
                    ("company_ids", "in", models.to_company_ids(self.env.company)),
                ]
            )
        ]
        return item

    def _init_options_accounts(self, options, previous_options):
        all_sales_person = self._get_filter_all_sales_person(options)
        previous_accounts = previous_options.get("sales_person_id", [])
        options["sales_person_id"] = []
        options["selected_sales_person_id"] = {}
        previous_selected_account_ids = {
            account["id"] for account in previous_accounts if account.get("selected")
        }
        for account in all_sales_person:
            if account.get("id") in previous_selected_account_ids:
                account["selected"] = True
            else:
                account["selected"] = False
        if all_sales_person:
            options["sales_person_id"] = all_sales_person

    @api.model
    def _get_options_account_id_domain(self, options):
        """Domain creating based on the selection."""
        domain = []
        selected_sales_person_id = [
            person
            for person in options.get("sales_person_id", [])
            if person["selected"]
        ]
        if selected_sales_person_id:
            sales_person_ids = [
                int(person.get("id")) for person in selected_sales_person_id
            ]
            domain.append(("move_id.user_id", "in", sales_person_ids))
        return domain

    def _get_options_domain(self, options, date_scope):
        res = super()._get_options_domain(options, date_scope)
        return res + self._get_options_account_id_domain(options)

# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, Command, _
from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template(model="account.fiscal.year")
    def _get_account_fiscal_year(self, template_code):
        return self._parse_csv(template_code, "account.fiscal.year")

    @template("np")
    def _get_np_template_data(self):
        return {
            "name": _("🇳🇵 Nepal Accounting"),
            "country": "base.np",
            "property_account_receivable_id": "receivable",
            "property_account_payable_id": "payable",
            "property_account_expense_categ_id": "expense",
            "property_account_income_categ_id": "income",
            "property_stock_account_input_categ_id": "stock_in",
            "property_stock_account_output_categ_id": "stock_out",
            "property_stock_valuation_account_id": "stock_valuation",
            "property_stock_account_production_cost_id": "cost_of_production",
        }

    @template("np", "res.company")
    def _get_np_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.np",
                "bank_account_code_prefix": "1014",
                "cash_account_code_prefix": "1015",
                "transfer_account_code_prefix": "1017",
                "account_default_pos_receivable_account_id": "pos_receivable",
                "income_currency_exchange_account_id": "income_currency_exchange",
                "expense_currency_exchange_account_id": "expense_currency_exchange",
                "default_cash_difference_income_account_id": "cash_diff_income",
                "default_cash_difference_expense_account_id": "cash_diff_expense",
                "account_journal_early_pay_discount_loss_account_id": "cash_discount_loss",
                "account_journal_early_pay_discount_gain_account_id": "cash_discount_gain",
                "account_sale_tax_id": "sale_tax_template",
                "account_purchase_tax_id": "purchase_tax_template",
                "country_id": "base.np",
                "currency_id": "base.NPR",
            }
        }

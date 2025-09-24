# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import SQL
from odoo.addons.sale.models.sale_order import SALE_ORDER_STATE


class InventoryAgedReport(models.Model):
    _name = "inventory.aged.report"
    _description = "Inventory Aged"
    _auto = False
    _rec_name = "date"
    _order = "date desc"

    @api.model
    def _get_done_states(self):
        return ["sale"]

    # sale.order fields
    name = fields.Char(string="Order Reference", readonly=True)
    date = fields.Datetime(string="Order Date", readonly=True)
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Customer", readonly=True
    )
    company_id = fields.Many2one(comodel_name="res.company", readonly=True)
    state = fields.Selection(selection=SALE_ORDER_STATE, string="Status", readonly=True)
    currency_id = fields.Many2one(
        comodel_name="res.currency", compute="_compute_currency_id"
    )
    price_total = fields.Monetary(string="Total", readonly=True)
    aged_bucket = fields.Char(string="Aged Bucket")

    @api.depends_context("allowed_company_ids")
    def _compute_currency_id(self):
        self.currency_id = self.env.company.currency_id

    def _with_sale(self):
        return ""

    def _select_sale(self):
        select_ = """
            s.id AS id,
            s.name AS name,
            TO_CHAR(s.date_order, 'YYYY-MM-DD') AS date,
            s.state AS state,
            s.partner_id AS partner_id,
            s.company_id AS company_id,
            s.amount_total AS price_total,
            CASE
                WHEN (CURRENT_DATE - s.date_order::date)::int BETWEEN 1 AND 30 THEN '1-30 days'
                WHEN (CURRENT_DATE - s.date_order::date)::int BETWEEN 31 AND 60 THEN '31-60 days'
                WHEN (CURRENT_DATE - s.date_order::date)::int BETWEEN 61 AND 90 THEN '61-90 days'
                WHEN (CURRENT_DATE - s.date_order::date)::int BETWEEN 91 AND 120 THEN '91-120 days'
                WHEN (CURRENT_DATE - s.date_order::date)::int > 120 THEN '121+ days'
                ELSE '1-30 days'
            END AS aged_bucket
        """

        return select_

    def _from_sale(self):
        currency_table = self.env["res.currency"]._get_simple_currency_table(
            self.env.companies
        )
        currency_table = self.env.cr.mogrify(currency_table).decode(
            self.env.cr.connection.encoding
        )
        return f"""
            sale_order s
            JOIN res_partner partner ON s.partner_id = partner.id
            JOIN {currency_table} ON account_currency_table.company_id = s.company_id
            """

    def _where_sale(self):
        return """ s.state = 'sale'"""

    def _group_by_sale(self):
        return """s.partner_id, s.date_order, s.id"""

    def _query(self):
        with_ = self._with_sale()
        return f"""
            {"WITH" + with_ + "(" if with_ else ""}
            SELECT {self._select_sale()}
            FROM {self._from_sale()}
            WHERE {self._where_sale()}
            GROUP BY {self._group_by_sale()}
            {")" if with_ else ""}
        """

    @property
    def _table_query(self):
        return self._query()

    def action_open_order(self):
        self.ensure_one()
        sale = self.env["sale.order"].sudo().search([("name", "=", self.name)], limit=1)
        return {
            "res_model": sale._name,
            "type": "ir.actions.act_window",
            "views": [[False, "form"]],
            "res_id": sale.id,
        }

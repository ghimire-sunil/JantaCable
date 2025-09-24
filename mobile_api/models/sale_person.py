# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools import SQL


class SalePersonReport(models.Model):
    _name = "sale.persons.report"
    _description = "Sales Person Report"
    _auto = False
    _rec_name = "date"
    _order = "date desc"

    date = fields.Date(string="Date", readonly=True)
    partner_id = fields.Many2one(string="Partner", comodel_name="res.partner")
    start_latitude = fields.Float("Start Latitude")
    start_longitude = fields.Float("Start Longitude")
    end_latitude = fields.Float("End Latitude")
    end_longitude = fields.Float("End Longitude")

    @property
    def _table_query(self):
        return """
            WITH base AS (
                SELECT
                    partner_id,
                    DATE(date) AS location_date,
                    date,
                    latitude,
                    longitude
                FROM
                    partner_location
            ),
            first_last AS (
                SELECT
                    b.partner_id,
                    b.location_date,
                    (SELECT latitude FROM base
                    WHERE partner_id = b.partner_id AND location_date = b.location_date
                    ORDER BY date ASC
                    LIMIT 1) AS start_latitude,

                    (SELECT longitude FROM base
                    WHERE partner_id = b.partner_id AND location_date = b.location_date
                    ORDER BY date ASC
                    LIMIT 1) AS start_longitude,

                    (SELECT latitude FROM base
                    WHERE partner_id = b.partner_id AND location_date = b.location_date
                    ORDER BY date DESC
                    LIMIT 1) AS end_latitude,

                    (SELECT longitude FROM base
                    WHERE partner_id = b.partner_id AND location_date = b.location_date
                    ORDER BY date DESC
                    LIMIT 1) AS end_longitude
                FROM base b
                GROUP BY b.partner_id, b.location_date
            )
            SELECT
                ROW_NUMBER() OVER () AS id,
                partner_id,
                location_date AS date,
                start_latitude,
                start_longitude,
                end_latitude,
                end_longitude
            FROM
                first_last
            ORDER BY
                partner_id, date
        """

    def button_action_map_view(self):
        self.ensure_one()

        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        map_url = f"{base_url}/sale-person-tracking?partnerId={self.partner_id.id}&date={self.date}"
        return {"url": map_url, "type": "ir.actions.act_url"}

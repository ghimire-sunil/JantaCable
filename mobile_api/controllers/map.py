import json
import os
from datetime import datetime, timedelta, time, date

import pytz
from odoo.exceptions import UserError
from odoo.http import request

from odoo import http
from werkzeug.exceptions import NotFound

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
kathmandu_tz = pytz.timezone("Asia/Kathmandu")


def response(status, message, data=None):
    headers = [
        ("Content-Type", "application/json"),
    ]
    return request.make_response(
        json.dumps({"status": status, "message": message, "data": data}), headers
    )


class SalePersonController(http.Controller):
    @http.route(route="/sale-person-tracking", auth="user", csrf=False, type="http")
    def maps(self):
        try:
            with open(os.path.join(BASE_DIR, "templates/index.html"), "r") as file:
                html_content = file.read()
                return http.request.make_response(
                    html_content, headers=[("Content-Type", "text/html")]
                )
        except Exception as e:
            raise UserError("Fail to load Page")

    @http.route(route=["/api/get-saleperson-report-by-id"], auth="public", type="http")
    def get_device_report_by_id(self):
        request_params = request.httprequest.args

        if not request_params.get("partnerId"):
            raise NotFound()

        partner_id = request_params.get("partnerId")

        if request_params.get("date"):
            filter_date = datetime.strptime(
                request_params.get("date"), "%Y-%m-%d"
            ).date()
        else:
            filter_date = date.today()

        data_date = datetime.combine(filter_date, time())
        start_of_day = data_date.replace(hour=0, minute=0, second=0)
        end_of_day = start_of_day + timedelta(days=1) - timedelta(microseconds=1)

        partner = (
            request.env["res.partner"].sudo().search([("id", "=", int(partner_id))])
        )

        locations = (
            request.env["partner.location"]
            .sudo()
            .search(
                [
                    ("date", ">=", start_of_day),
                    ("date", "<=", end_of_day),
                    ("partner_id", "=", partner.id),
                ]
            )
        )

        if locations:
            report_positions = []
            for position in locations:
                report_positions.append(
                    {
                        "lat": position.latitude,
                        "lon": position.longitude,
                        "time": position.date.astimezone(kathmandu_tz).strftime(
                            "%Y-%m-%d %I:%M %p"
                        ),
                    }
                )
            start_position = locations[0]
            end_position = locations[-1]

            response_reports = {
                "date": filter_date.strftime("%Y-%m-%d"),
                "saleman": {
                    "id": partner.id,
                    "name": partner.name,
                },
                "start_address": {
                    "lat": start_position.latitude,
                    "lon": start_position.longitude,
                },
                "end_address": {
                    "lat": end_position.latitude,
                    "lon": end_position.longitude,
                },
                "positions": report_positions,
            }

            return response(status=True, message="Positions", data=response_reports)
        else:
            return response(status=False, message="Report not found")

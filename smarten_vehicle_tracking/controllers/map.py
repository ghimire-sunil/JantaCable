import json
import os
from datetime import datetime, timedelta, time, date

import pytz
from odoo.exceptions import UserError
from odoo.http import request

from odoo import http

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
kathmandu_tz = pytz.timezone("Asia/Kathmandu")


def response(status, message, data=None):
    headers = [
        ("Content-Type", "application/json"),
    ]
    return request.make_response(
        json.dumps({"status": status, "message": message, "data": data}), headers
    )


class GpsController(http.Controller):
    def _get_report(self, device_id, date):
        query = f"""
            SELECT
            extract(epoch from now())::bigint * 1000 + floor(random() * 1000)::bigint AS id,
                v.id AS vehicle_id,
                v.driver_id AS driver_id,
                f.device_id,
                fmin.device_time AS start_time,
                fmin.latitude    AS start_lat,
                DATE(fmin.device_time) AS date,
                fmin.longitude   AS start_lon,
                fmax.device_time AS end_time,
                fmax.latitude    AS end_lat,
                fmax.longitude   AS end_lon,
                f.avg_speed as average_speed,
                f.max_speed,
                CONCAT(fmin.latitude , '_', fmin.longitude) AS start_address,
                CONCAT(fmax.latitude , '_', fmax.longitude) AS end_address,
                CONCAT(v.name, '_', TO_CHAR(DATE(fmin.device_time), 'YYYYMMDD')) AS name
            FROM (
                SELECT
                    device_id,
                    MIN(device_time) AS start_time,
                    MAX(device_time) AS end_time,
                    AVG(speed) AS avg_speed,
                    MAX(speed) AS max_speed
                FROM fleet_gps_position
                GROUP BY device_id
            ) f
            JOIN fleet_gps_position fmin
                ON f.device_id = fmin.device_id AND f.start_time = fmin.device_time
            JOIN fleet_gps_position fmax
                ON f.device_id = fmax.device_id AND f.end_time = fmax.device_time
            JOIN fleet_vehicle v
                ON v.device_id = f.device_id
            where f.device_id ={device_id} and DATE(f.start_time) ='{date}';
        """

        request.env.cr.execute(query)
        reports = request.env.cr.dictfetchall()

        if reports:
            return reports[0]

        return []

    def _get_vehicle(self, vehicle_id):
        return (
            request.env["fleet.vehicle"]
            .sudo()
            .search([("id", "=", vehicle_id)], limit=1)
        )

    def _get_device_report(self, device_id, date):
        reports = self._get_report(device_id=device_id, date=date)
        report_response = {}
        if reports:
            report_response = {
                "location": {
                    "start": {
                        "lat": reports["start_lat"],
                        "lon": reports["start_lon"],
                        "address": reports["start_address"],
                    },
                    "end": {
                        "lat": reports["end_lat"],
                        "lon": reports["end_lon"],
                        "address": reports["end_address"],
                    },
                },
                "distance": "",
                "data": {
                    "max": round(reports["max_speed"], 2),
                    "average": round(reports["average_speed"], 2),
                    "duration": "",
                },
            }

        return report_response

    @http.route(
        route=["/api/get-latest-location"], auth="public", type="http", csrf=False
    )
    def get_latest_location(self):
        devices = request.env["gps.device"].sudo().search([])
        response_positions = []

        for device in devices:
            positions = (
                request.env["fleet.gps_position"]
                .sudo()
                .search([("device_id", "=", device.id)], order="id desc", limit=1)
            )

            fleet = (
                request.env["fleet.vehicle"]
                .sudo()
                .search([("device_id", "=", device.id)])
            )

            vehicle = {
                "name": "",
                "id": 0,
            }
            if fleet:
                vehicle = {"name": fleet[0].license_plate, "id": fleet[0].id}

            for position in positions:
                response_positions.append(
                    {
                        "lat": position.latitude,
                        "lon": position.longitude,
                        "device": {"id": device.id, "name": device.name},
                        "speed": f"{round(position.speed, 2)} Km/h",
                        "vehicle": vehicle,
                        "report": self._get_device_report(
                            device_id=device.id, date=date.today().strftime("%Y-%m-%d")
                        ),
                    }
                )

        return response(
            status=True, message="Device Latest Position", data=response_positions
        )

    @http.route(route="/maps", auth="user", csrf=False, type="http")
    def maps(self):
        try:
            with open(os.path.join(BASE_DIR, "templates/index.html"), "r") as file:
                html_content = file.read()
                return http.request.make_response(
                    html_content, headers=[("Content-Type", "text/html")]
                )
        except Exception as e:
            raise UserError("Fail to load Page")

    @http.route(route="/api/get-config-parameters", auth="public", type="http")
    def get_config_parameters(self):
        token = request.env["ir.config_parameter"].sudo().get_param("traccar.token")
        api_url = request.env["ir.config_parameter"].sudo().get_param("traccar.url")

        return response(
            status=True,
            message="Config parameters",
            data={"token": token, "url": api_url},
        )

    @http.route(route="/api/get-gps-devices", auth="public", type="http")
    def get_devices(self):
        devices = request.env["gps.device"].sudo().search([])

        response_devices = []
        for device in devices:
            fleet = (
                request.env["fleet.vehicle"]
                .sudo()
                .search([("device_id", "=", device.id)])
            )

            name = ""
            if fleet:
                name = fleet[0].name

            response_devices.append(
                {
                    "id": device.id,
                    "name": device.name,
                    "imei": device.imei,
                    "traccar_id": device.server_device_id,
                    "vehicle": name,
                }
            )

        return response(status=True, message="Device Lists", data=response_devices)

    @http.route(route=["/api/get-device-positions"], auth="public", type="http")
    def get_device_positions(self):
        request_params = request.httprequest.args

        device_id = request_params.get("deviceId")
        device = request.env["gps.device"].sudo().search([("id", "=", device_id)])

        if device:
            fleet = (
                request.env["fleet.vehicle"]
                .sudo()
                .search([("device_id", "=", device.id)])
            )

            vehicle = {
                "name": "",
                "id": 0,
            }
            if fleet:
                vehicle = {"name": fleet[0].license_plate, "id": fleet[0].id}

            positions = (
                request.env["fleet.gps_position"]
                .sudo()
                .search(
                    [
                        ("device_id", "=", device.id),
                    ]
                )
                .filtered(
                    lambda p: p.device_time.astimezone(kathmandu_tz).date()
                    == datetime.now().astimezone(kathmandu_tz).date()
                )
            )
            response_positions = []
            for position in positions:
                response_positions.append(
                    {
                        "lat": position.latitude,
                        "lon": position.longitude,
                        "device": {"id": device.id, "name": device.name},
                        "speed": position.speed,
                        "vehicle": vehicle,
                        "address": position.address,
                    }
                )

            response_data = {
                "positions": response_positions,
                "report": self._get_device_report(
                    device_id=device.id, date=date.today().strftime("%Y-%m-%d")
                ),
                "vehicle": vehicle,
            }

            return response(status=True, message="Positions", data=response_data)
        else:
            return response(status=False, message="Unable to fetch GPS")

    @http.route(route=["/api/get-vehicle-reports"], auth="public", type="http")
    def get_device_reports(self):
        request_params = request.httprequest.args

        device_id = request_params.get("deviceId")
        from_date = request_params.get("from_date")
        to_date = request_params.get("to_date")

        device = request.env["gps.device"].sudo().search([("id", "=", device_id)])

        date_format = "%Y-%m-%d %H:%M"
        i_from_date = datetime.strptime(from_date, date_format)
        i_to_date = datetime.strptime(to_date, date_format)
        c_from_date = datetime.strptime(from_date, date_format)

        if device:
            response_reports = []
            delta = timedelta(days=1)
            while c_from_date <= i_to_date:
                report = self._get_report(
                    device_id=device.id, date=c_from_date.strftime("%Y-%m-%d")
                )

                start_of_day = c_from_date.replace(hour=0, minute=0, second=0)
                end_of_day = start_of_day + timedelta(days=1) - timedelta(minutes=1)

                if start_of_day.date() == i_from_date.date():
                    start_of_day = i_from_date

                if end_of_day.date() == i_to_date.date():
                    end_of_day = i_to_date

                if report:
                    fleet = self._get_vehicle(report["vehicle_id"])
                    positions = (
                        request.env["fleet.gps_position"]
                        .sudo()
                        .search(
                            [
                                ("device_id", "=", device.id),
                                ("device_time", ">=", start_of_day),
                                ("device_time", "<=", end_of_day),
                            ]
                        )
                    )
                    report_positions = []
                    for position in positions:
                        report_positions.append(
                            {
                                "lat": position.latitude,
                                "lon": position.longitude,
                                "speed": position.speed,
                                "time": position.device_time.astimezone(
                                    kathmandu_tz
                                ).strftime("%Y-%m-%d %I:%M %p"),
                                "course": position.course,
                            }
                        )

                    durations = "0 minute"
                    # minutes = report.duration / (1000 * 60)
                    # if minutes > 60:
                    #     hours = minutes / 60
                    #     durations = f"{round(hours, 2)} hours"
                    # else:
                    #     durations = f"{round(minutes, 2)} minutes"
                    durations = ""
                    response_reports.append(
                        {
                            "date": start_of_day.strftime("%Y-%m-%d"),
                            "id": report["id"],
                            "driver": {
                                "id": fleet.driver_id.id,
                                "name": fleet.driver_id.name,
                            },
                            "vehicle": fleet.id,
                            "max_Speed": f"{round(report['max_speed'], 2)} Km/h",
                            "average_speed": f"{round(report['average_speed'], 2)} Km/h",
                            "distance": "",
                            "spent_fuel": "",
                            "duration": durations,
                            "start_time": report["start_time"]
                            .astimezone(kathmandu_tz)
                            .strftime("%Y-%m-%d %I:%M %p"),
                            "end_time": report["end_time"]
                            .astimezone(kathmandu_tz)
                            .strftime("%Y-%m-%d %I:%M %p"),
                            "start_address": {
                                "lat": report["start_lat"],
                                "lon": report["start_lon"],
                            },
                            "end_address": {
                                "lat": report["end_lat"],
                                "lon": report["end_lon"],
                            },
                            "positions": report_positions,
                        }
                    )

                c_from_date += delta

            return response(status=True, message="Positions", data=response_reports)
        else:
            return response(status=False, message="Unable to fetch GPS")

    @http.route(route=["/api/get-vehicle-report-by-id"], auth="public", type="http")
    def get_device_report_by_id(self):
        request_params = request.httprequest.args

        report_id = request_params.get("reportId")
        report = (
            request.env["fleet.gps_report"]
            .sudo()
            .search(
                [
                    ("id", "=", report_id),
                ]
            )
        )

        if report:
            data_date = datetime.combine(report.date, time())
            start_of_day = data_date.replace(hour=0, minute=0, second=0)
            end_of_day = start_of_day + timedelta(days=1) - timedelta(microseconds=1)

            positions = (
                request.env["fleet.gps_position"]
                .sudo()
                .search(
                    [
                        ("device_id", "=", report.device_id.id),
                        ("device_time", ">=", start_of_day),
                        ("device_time", "<=", end_of_day),
                    ]
                )
            )

            report_positions = []
            for position in positions:
                report_positions.append(
                    {
                        "lat": position.latitude,
                        "lon": position.longitude,
                        "speed": position.speed,
                        "time": position.device_time.astimezone(kathmandu_tz).strftime(
                            "%Y-%m-%d %I:%M %p"
                        ),
                        "course": position.course,
                    }
                )

            durations = "0 minute"
            minutes = report.duration / (1000 * 60)
            if minutes > 60:
                hours = minutes / 60
                durations = f"{round(hours, 2)} hours"
            else:
                durations = f"{round(minutes, 2)} minutes"

            response_reports = {
                "date": report.date.strftime("%Y-%m-%d"),
                "driver": {
                    "id": report.driver_id.id,
                    "name": report.driver_id.name,
                },
                "vehicle": report.vehicle_id.id,
                "max_Speed": f"{round(report.max_speed, 2)} Km/h",
                "average_speed": f"{round(report.average_speed, 2)} Km/h",
                "distance": f"{report.distance / 1000} Km",
                "spent_fuel": f"{report.spent_fuel} L",
                "duration": durations,
                "start_address": {
                    "lat": report.start_lat,
                    "lon": report.start_lon,
                },
                "end_address": {
                    "lat": report.end_lat,
                    "lon": report.end_lon,
                },
                "positions": report_positions,
                "device_id": report.device_id.id,
            }

            return response(status=True, message="Positions", data=response_reports)
        else:
            return response(status=False, message="Report not found")

    @http.route(
        route="/map/report/<int:fleet_id>", auth="user", csrf=False, type="http"
    )
    def fleet_report(self, fleet_id):
        try:
            fleet = request.env["fleet.vehicle"].sudo().search([("id", "=", fleet_id)])
            domain = [("device_id", "=", fleet.device_id.id)]

            action_id = request.env.ref(
                "smarten_vehicle_tracking.action_smarten_vehicle_tracking_gps_report"
            )

            # Redirect to the list view with the specified parameters
            return request.redirect(
                f"/web#view_type=list&model=fleet.gps_report&menu_id={action_id.id}&action={action_id.id}&active_id={fleet.id}&domain={domain}"
            )

            # return request.redirect(
            #     f'/web#active_id={fleet.id}&view_type=list&model=fleet.gps_report&action={action_id.id}')
        except Exception:
            return request.redirect("/web")

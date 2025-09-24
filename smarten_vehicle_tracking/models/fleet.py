import base64
import requests
from datetime import datetime, timezone, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

from odoo import models, fields, api


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"
    device_id = fields.Many2one(
        comodel_name="gps.device", string="GPS Device", index=True
    )

    def return_action_to_gps_report(self):
        self.ensure_one()
        xml_id = "action_smarten_vehicle_tracking_gps_report"
        res = self.env["ir.actions.act_window"]._for_xml_id(
            "smarten_vehicle_tracking.%s" % xml_id
        )
        res.update(
            context=dict(
                self.env.context, default_device_id=self.device_id, group_by=False
            ),
            domain=[("device_id", "=", self.device_id.id)],
        )
        return res


class GpsDevice(models.Model):
    _name = "gps.device"

    name = fields.Char(string="Device Name", required=True)
    imei = fields.Char(string="IMEI", required=True)
    phone = fields.Char(string="Phone", required=True)
    model = fields.Char(string="Model")
    server_device_id = fields.Char("Server Device ID", readonly=True)
    last_fetch_time = fields.Datetime(string="Last Fetch Datetime")

    def sync_with_traccar(self):
        username = self.env["ir.config_parameter"].sudo().get_param("traccar.username")
        password = self.env["ir.config_parameter"].sudo().get_param("traccar.password")
        token = self.env["ir.config_parameter"].sudo().get_param("traccar.token")
        api_url = self.env["ir.config_parameter"].sudo().get_param("traccar.url")

        credentials_str = f"{username}:{password}"

        credentials = base64.b64encode(credentials_str.encode())

        if not api_url:
            raise UserError("Please set Geotrack  url")

        if not username or not password:
            raise UserError("Please set username and password first.")

        if not token:
            expiration_dt = datetime.now() + relativedelta(months=20)

            token_response = requests.post(
                url=f"{api_url}/api/session/token",
                headers={
                    "authorization": f"Basic {credentials.decode()}",
                    "Content-Type'": "application/x-www-form-urlencoded",
                },
                data={"expiration": expiration_dt.strftime("%Y-%m-%dT%H:%M:%SZ")},
            )
            if token_response.status_code != 200:
                raise UserError(token_response.text)
            else:
                token = token_response.text
                self.env["ir.config_parameter"].sudo().set_param("traccar.token", token)

        response = requests.get(
            url=f"{api_url}/api/devices",
            headers={
                "authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

        if response.status_code != 200:
            raise UserError(response.json()["message"])

        for device in response.json():
            if not self.search([("server_device_id", "=", device.get("id"))]):
                self.create(
                    {
                        "server_device_id": device.get("id"),
                        "name": device.get("name"),
                        "phone": device.get("phone"),
                        "imei": device.get("uniqueId"),
                        "model": device.get("model"),
                    }
                )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Device Sync Successfully",
                "type": "success",
                "sticky": False,
            },
        }


class GpsPosition(models.Model):
    _name = "fleet.gps_position"

    device_id = fields.Many2one(
        comodel_name="gps.device", string="Device", required=True
    )
    server_id = fields.Char(string="Server Id", required=True)
    device_time = fields.Datetime(string="Device Time")
    latitude = fields.Float(string="Latitude")
    longitude = fields.Float(string="Longitude")
    altitude = fields.Float(string="Altitude")
    speed = fields.Float(string="Speed")
    course = fields.Float(string="Course")
    address = fields.Char(string="Address")

    @api.model
    def get_position(self):
        token = self.env["ir.config_parameter"].sudo().get_param("traccar.token")
        api_url = self.env["ir.config_parameter"].sudo().get_param("traccar.url")

        if not token or not api_url:
            return

        devices = self.env["gps.device"].sudo().search([])

        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        for device in devices:
            if not device.last_fetch_time:
                last_fetch_time = (
                    (datetime.now(timezone.utc) - timedelta(hours=2))
                    .isoformat()
                    .replace("+00:00", "Z")
                )
            else:
                last_fetch_time = (
                    device.last_fetch_time.astimezone(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z")
                )

            payload = {
                "deviceId": device.server_device_id,
                "from": last_fetch_time,
                "to": now_iso,
            }

            fetch_time = datetime.now()
            response = requests.get(
                url=f"{api_url}/api/positions",
                headers={
                    "authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                params=payload,
            )

            if response.status_code != 200:
                raise UserError(response.json()["message"])
            response_data = response.json()

            date_format = "%Y-%m-%dT%H:%M:%S.%f%z"
            db_data = []
            for data in response_data:
                position_id = data["id"]

                device_time = datetime.strptime(data["deviceTime"], date_format)
                address = ""

                db_data.append(
                    {
                        "device_id": device.id,
                        "server_id": position_id,
                        "device_time": device_time.replace(tzinfo=None),
                        "latitude": data["latitude"],
                        "longitude": data["longitude"],
                        "altitude": data["altitude"],
                        "speed": data["speed"],
                        "course": data["course"],
                        "address": address,
                    }
                )
            self.sudo().create(db_data)
            device.last_fetch_time = fetch_time


class GPSReport(models.Model):
    _name = "fleet.gps_report"
    _description = "GPS Device Daily Report"
    _auto = False
    _rec_name = "date"
    _order = "date desc"

    name = fields.Char(string="Name")
    device_id = fields.Many2one(
        comodel_name="gps.device", string="Device", required=True, readonly=True
    )
    vehicle_id = fields.Many2one(
        comodel_name="fleet.vehicle", string="Vehicle", readonly=True
    )
    driver_id = fields.Many2one(
        comodel_name="res.partner", string="Driver", readonly=True
    )
    max_speed = fields.Float(string="Max Speed", readonly=True)
    max_speed_formatted = fields.Char(
        string="Max Speed",
        readonly=True,
        store=False,
        compute="_compute_max_speed",
    )
    average_speed = fields.Float(string="Average Speed", readonly=True)
    average_speed_formatted = fields.Char(
        string="Average Speed",
        readonly=True,
        store=False,
        compute="_compute_average_speed",
    )
    start_time = fields.Datetime(string="Start Time", readonly=True)
    start_address = fields.Char(string="Start Address", readonly=True)
    start_lat = fields.Float(string="Start Latitude", readonly=True)
    start_lon = fields.Float(string="Start Longitude", readonly=True)
    end_time = fields.Datetime(string="End Time", readonly=True)
    end_address = fields.Char(string="End Address", readonly=True)
    end_lat = fields.Float(string="End Latitude", readonly=True)
    end_lon = fields.Float(string="EndLongitude", readonly=True)
    date = fields.Date(string="Date", readonly=True)

    @property
    def _table_query(self):
        return """
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
        """

    def button_action_map_view(self):
        self.ensure_one()

        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        map_url = f"{base_url}/maps?reportId={self.id}"
        return {"url": map_url, "type": "ir.actions.act_url"}

    @api.depends("max_speed")
    def _compute_max_speed(self):
        for record in self:
            record.max_speed_formatted = f"{round(record.max_speed, 2)} Km/h"

    @api.depends("average_speed")
    def _compute_average_speed(self):
        for record in self:
            record.average_speed_formatted = f"{round(record.average_speed, 2)} Km/h"

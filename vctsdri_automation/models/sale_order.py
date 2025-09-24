import re
import nepali_datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta
from ..tools.automation import VCTSAutomation


class StockPicking(models.Model):
    _inherit = "stock.picking"

    vcts_type = fields.Selection(
        string="Type",
        selection=[
            ("vehicle", "Vehicle"),
            ("others", "Others"),
        ],
    )
    responsible_person_id = fields.Many2one(
        string="Responsible Person",
        comodel_name="res.partner",
    )
    consignment_number = fields.Char(string="Consignment Number", copy=False)
    fleet_id = fields.Many2one(
        string="Fleet",
        comodel_name="fleet.vehicle",
        domain=[("model_id.vehicle_type", "=", "truck")],
    )
    plain_note = fields.Text(string="Remarks")
    consignment_document = fields.Binary(string="Consignment Document", copy=False)
    goods_nature = fields.Char(string="Goods Nature")
    package_unit = fields.Selection(
        string="Package Unit",
        selection=[
            ("पोका", "पोका"),
            ("बोरा", "बोरा"),
            ("थान", "थान"),
            ("बाकस", "बाकस"),
            ("कार्टुन", "कार्टुन"),
            ("लिटर", "लिटर"),
            ("झोला", "झोला"),
            ("मिटर", "मिटर"),
            ("केजी", "केजी"),
            ("अन्य", "अन्य"),
            ("मे‍. टन", "मे‍. टन"),
            ("ड्रम", "ड्रम"),
            ("पिस", "पिस"),
            ("ग्यालेन", "ग्यालेन"),
            ("बाल्टी", "बाल्टी"),
            ("वर्ग मिटर", "वर्ग मिटर"),
            ("बर्गफीट", "बर्गफीट"),
            ("Gross", "Gross"),
        ],
    )
    document_number = fields.Integer(
        string="Document Number", readonly=False, copy=False
    )
    departure_date = fields.Date(string="Departure Date")
    document_date = fields.Date(string="Document Date")
    vcts_is_lock = fields.Boolean(
        string="Lock Status", default=False, readonly=True, copy=False
    )
    vcts_status = fields.Selection(
        string="VCTS Status",
        selection=[
            ("not_dispatched", "Not Dispatched"),
            ("ongoing", "Ongoing"),
            ("delivered", "Delivered"),
        ],
        readonly=True,
        copy=False,
    )
    departure_district = fields.Many2one(
        string="Departure District",
        comodel_name="res.district",
        related="company_id.district_id",
        store=True,
        readonly=False,
    )
    departure_location = fields.Char(
        string="Departure Location",
        related="company_id.street",
        store=True,
        readonly=False,
    )

    destination_district = fields.Many2one(
        string="Destination District",
        comodel_name="res.district",
    )
    destination_location = fields.Char(
        string="Destination Location",
    )
    amount_with_out_vat = fields.Float(
        string="Amount With Out VAT",
        compute="_compute_amount_with_out_vat",
        readonly=False,
    )

    def _compute_amount_with_out_vat(self):
        for rec in self:
            if rec.sale_id:
                rec.amount_with_out_vat = rec.sale_id.amount_untaxed

    @api.onchange("vcts_type")
    def _onchange_vcts_type(self):
        if self.vcts_type == "others":
            self.fleet_id = False
        else:
            self.responsible_person_id = False

    # @api.model
    # def default_get(self, fields_list):
    #     res = super().default_get(fields_list)
    #     if "company_id" in fields_list:
    #         company = self.env["res.company"].browse(res["company_id"])
    #         res["departure_district"] = company.district_id
    #         res["departure_location"] = company.street
    #     return res

    @api.onchange("partner_id")
    def _on_change_partner_id(self):
        if self.partner_id:
            self.destination_district = self.partner_id.district_id
            self.destination_location = self.partner_id.street
        else:
            self.destination_district = None
            self.destination_location = None

    @api.constrains("departure_date")
    def _check_departure_date(self):
        for rec in self:
            max_allowed_date = date.today() + timedelta(days=1)
            if rec.departure_date and rec.departure_date > max_allowed_date:
                raise ValidationError(
                    f"Departure date must be within 1 days from today. Max Allowed Date : {max_allowed_date}"
                )

    @api.constrains("document_date")
    def _check_document_date(self):
        for rec in self:
            if rec.document_date:
                min_date = date.today() - timedelta(days=6)
                max_date = date.today() + timedelta(days=2)
                if rec.document_date < min_date:
                    raise ValidationError(
                        f"Document date cannot be earlier than {min_date}."
                    )
                if rec.document_date > max_date:
                    raise ValidationError(
                        f"Document date cannot be later than {max_date}."
                    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["document_number"] = self.env["ir.sequence"].next_by_code(
                "vcts.document.number"
            )

        return super().create(vals_list)

    def write(self, vals):
        resp = super().write(vals)
        if not self.document_number:
            self.document_number = self.env["ir.sequence"].next_by_code(
                "vcts.document.number"
            )

        return resp

    def get_date_bs(self, date):
        return nepali_datetime.date.from_datetime_date(date).strftime("%Y-%m-%d")

    def action_post_to_vcts(self):
        url = self.env["ir.config_parameter"].sudo().get_param("vstcs.url")
        username = self.env["ir.config_parameter"].sudo().get_param("vstcs.username")
        password = self.env["ir.config_parameter"].sudo().get_param("vstcs.password")

        if not url or not username or not password:
            raise UserError("Please setup VCTS properly")

        if not self.partner_id.vat:
            raise ValidationError("Partner VAT is Required")

        required_fields = {
            "document_number": "Document Number",
            "package_unit": "Package Unit",
            "goods_nature": "Nature of Goods",
            "departure_date": "Departure Date",
            "departure_district": "Departure District",
            "departure_location": "Departure Location",
            "destination_district": "Destination District",
            "destination_location": "Destination Location",
            "move_ids_without_package": "Order Line",
        }
        for field, label in required_fields.items():
            if not getattr(self, field):
                raise ValidationError(
                    f"Please provide a value for '{label}' before proceeding."
                )

        fleet = self.fleet_id
        vehicleInfo = None
        driverInfo = None
        responsibleInfo = None
        if fleet:
            if not fleet.driver_id:
                raise ValidationError(_("Please Assign Driver in Sleeted Fleet"))

            if not fleet.driver_id.phone_sanitized:
                raise ValidationError(_("Driver Phone Number is Required"))

            # check is driver_phone_number 10 digits
            driver_phone_number = fleet.driver_id.phone_sanitized.replace(
                "-", ""
            ).strip()
            driver_phone_number = "".join(filter(str.isdigit, driver_phone_number))
            driver_phone_number = driver_phone_number[-10:]

            if not re.fullmatch(r"\d{10}", driver_phone_number):
                raise ValidationError(
                    _("Driver phone number must be exactly 10 digits.")
                )

            if not fleet.driver_id.license_number:
                raise ValidationError(_("Driver License Number is Required"))
            vehicleInfo = {
                "vehicle_category": fleet.vehicle_category
                if fleet.vehicle_category != "others"
                else "Indian Number Plate",
                "zonal_code": fleet.zonal_code,
                "provincal_id": fleet.provincal_id.name,
                "symbol": fleet.symbol,
                "office_code": fleet.office_code,
                "vehicle_code": fleet.vehicle_code,
                "lot_number": fleet.lot_number,
                "vehicle_number": fleet.vehicle_number,
            }
            driverInfo = {
                "name": fleet.driver_id.name,
                "phone": driver_phone_number,
                "license_number": fleet.driver_id.license_number,
                "username": fleet.driver_id.email,
                "password": "bhJ%!78hjk12",
            }
        else:
            if not self.responsible_person_id:
                raise ValidationError("Responsible Person is Required.")

            if not self.responsible_person_id.phone:
                raise ValidationError("Responsible Person Phone is Required")

            responsible_phone_number = (
                self.responsible_person_id.phone_sanitized.replace("-", "").strip()
            )
            responsible_phone_number = "".join(
                filter(str.isdigit, responsible_phone_number)
            )
            responsible_phone_number = responsible_phone_number[-10:]

            if not re.fullmatch(r"\d{10}", responsible_phone_number):
                raise ValidationError(
                    _("Responsible Person phone number must be exactly 10 digits.")
                )
            responsibleInfo = {
                "name": self.responsible_person_id.name,
                "phone": responsible_phone_number,
            }
        total_qty = 1
        for line in self.move_ids_without_package:
            total_qty += line.quantity

        shippingInfo = {
            "type": self.vcts_type,
            "vehicleInfo": vehicleInfo,
            "driverInfo": driverInfo,
            "departureDistrict": (self.departure_district.name).upper(),
            "departureLocation": self.departure_location,
            "departureDate": self.get_date_bs(
                self.departure_date
            ),  # departure Date only accept today and tomorrow date
            "destinationDistrict": (self.destination_district.name).upper(),
            "multipleVehicle": "No",
            "viaTransportCompany": "No",
            "remarks": self.plain_note,
            "responsiblePerson": responsibleInfo,
            "lines": [
                {
                    "document_type": "बिल",
                    "document_number": self.document_number,
                    "document_date": self.get_date_bs(
                        self.document_date
                    ),  # date is accept 2 days after today and 6 days before today
                    "goods_nature": self.goods_nature,
                    "package_unit": self.package_unit,
                    "qty": total_qty,
                    "amount_with_out_vat": self.amount_with_out_vat,
                    "supplier": self.company_id.vat,  # valid pan is required . vcts auto fetch supplier and buyer details
                    "buyer": self.partner_id.vat,
                    "destination_location": self.destination_location,
                    "remarks": self.plain_note,
                }
            ],
        }

        try:
            vcts = VCTSAutomation(env=self.env, sale=self, shippingInfo=shippingInfo)
            vcts.main()

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Success"),
                    "message": _("VCTS automation test completed successfully."),
                    "type": "success",
                    "sticky": False,
                    "next": {
                        "type": "ir.actions.client",
                        "tag": "reload",
                    },
                },
            }
        except Exception as e:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Error"),
                    "message": _("Error: %s" % str(e)),
                    "type": "danger",
                    "sticky": True,
                    "next": {
                        "type": "ir.actions.client",
                        "tag": "reload",
                    },
                },
            }

    def action_vcts_lock(self):
        try:
            vcts = VCTSAutomation(env=self.env, sale=self, shippingInfo={})
            vcts.action_lock_consignment()

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Success"),
                    "message": _("VCTS automation completed successfully."),
                    "type": "success",
                    "sticky": False,
                    "next": {
                        "type": "ir.actions.client",
                        "tag": "reload",
                    },
                },
            }
        except Exception as e:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Error"),
                    "message": _("Error: %s" % str(e)),
                    "type": "danger",
                    "sticky": True,
                    "next": {
                        "type": "ir.actions.client",
                        "tag": "reload",
                    },
                },
            }

    def action_start_consignments(self):
        try:
            vcts = VCTSAutomation(env=self.env, sale=self, shippingInfo={})
            vcts.action_start_consignments()

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Success"),
                    "message": _("VCTS automation completed successfully."),
                    "type": "success",
                    "sticky": False,
                    "next": {
                        "type": "ir.actions.client",
                        "tag": "reload",
                    },
                },
            }
        except Exception as e:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Error"),
                    "message": _("Error: %s" % str(e)),
                    "type": "danger",
                    "sticky": True,
                    "next": {
                        "type": "ir.actions.client",
                        "tag": "reload",
                    },
                },
            }

    def action_print_document(self):
        try:
            vcts = VCTSAutomation(env=self.env, sale=self, shippingInfo={})
            vcts.action_print_document()

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Success"),
                    "message": _("VCTS automation completed successfully."),
                    "type": "success",
                    "sticky": False,
                    "next": {
                        "type": "ir.actions.client",
                        "tag": "reload",
                    },
                },
            }
        except Exception as e:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Error"),
                    "message": _("Error: %s" % str(e)),
                    "type": "danger",
                    "sticky": True,
                    "next": {
                        "type": "ir.actions.client",
                        "tag": "reload",
                    },
                },
            }

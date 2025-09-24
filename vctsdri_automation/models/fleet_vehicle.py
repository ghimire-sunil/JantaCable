import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    license_plate = fields.Char(
        tracking=True,
        help="License plate number of the vehicle (i = plate number for a car)",
        compute="_compute_license_plate",
        store=True,
    )
    vehicle_category = fields.Selection(
        string="Vehicle Category",
        selection=[
            ("zonal", "Zonal"),
            ("provincal", "Provincal"),
            ("embosed", "Embosed"),
            ("others", "Others"),
        ],
        default="provincal",
        tracking=True,
    )
    zonal_code = fields.Selection(
        string="Zonal Code",
        selection=[
            ("मे", "मे"),
            ("को", "को"),
            ("स", "स"),
            ("ज", "ज"),
            ("बा", "बा"),
            ("ना", "ना"),
            ("ग", "ग"),
            ("लु", "लु"),
            ("ध", "ध"),
            ("रा", "रा"),
            ("भे", "भे"),
            ("क", "क"),
            ("से", "से"),
            ("म", "म"),
        ],
    )
    provincal_id = fields.Many2one(
        comodel_name="fleet.vehicle.provincal", string="Provincal"
    )
    symbol = fields.Selection(
        string="Symbol",
        selection=[
            ("क", "क"),
            ("ख", "ख"),
            ("ग", "ग"),
            ("घ", "घ"),
            ("च", "च"),
            ("ज", "ज"),
            ("झ", "झ"),
            ("ञ", "ञ"),
            ("प", "प"),
            ("फ", "फ"),
            ("ब", "ब"),
            ("य", "य"),
            ("सी.डी.", "सी.डी."),
        ],
    )
    office_code = fields.Selection(
        string="Office Code",
        selection=[
            ("01", "01"),
            ("02", "02"),
            ("03", "03"),
            ("04", "04"),
            ("05", "05"),
            ("06", "06"),
            ("07", "07"),
            ("08", "08"),
            ("09", "09"),
            ("10", "10"),
        ],
    )
    vehicle_code = fields.Selection(
        string="Vehicle Code",
        selection=[
            ("A", "A"),
            ("B", "B"),
            ("C", "C"),
            ("D", "D"),
            ("E", "E"),
            ("F", "F"),
            ("G", "G"),
            ("H", "H"),
            ("I", "I"),
            ("J", "J"),
            ("K", "K"),
        ],
    )
    lot_number = fields.Char(string="LOT Number")
    vehicle_number = fields.Char(string="Vehicle Number")

    @api.onchange("vehicle_category")
    def _onchange_vehicle_category(self):
        self.write(
            {
                "provincal_id": None,
                "zonal_code": None,
                "office_code": None,
                "lot_number": None,
                "vehicle_number": None,
                "symbol": None,
                "vehicle_code": None,
            }
        )

    @api.depends(
        "vehicle_category",
        "zonal_code",
        "provincal_id",
        "symbol",
        "office_code",
        "vehicle_code",
        "lot_number",
        "vehicle_number",
    )
    def _compute_license_plate(self):
        for record in self:
            if record.vehicle_category == "provincal":
                record.license_plate = f"{record.provincal_id.name} {record.office_code} {record.lot_number} {record.vehicle_number}"
            elif record.vehicle_category == "zonal":
                record.license_plate = f"{record.zonal_code} {record.lot_number} {record.symbol} {record.vehicle_number}"
            if record.vehicle_category == "embosed":
                record.license_plate = f"{record.provincal_id.name} {record.vehicle_code} {record.lot_number} {record.vehicle_number}"
            else:
                record.license_plate = record.vehicle_number

    # TODO: validate lot_number , vehicle_number by vehicle_category

    @api.constrains("vehicle_number")
    def _check_vehicle_number(self):
        for record in self:
            if record.vehicle_category in ["provincal", "zonal", "embosed"]:
                # record.vehicle_number should be number only and has 4 digits only
                if not record.vehicle_number or not re.fullmatch(
                    r"\d{4}", record.vehicle_number
                ):
                    raise ValidationError(
                        _("Vehicle number must be exactly 4 digits for category %s.")
                        % record.vehicle_category.capitalize()
                    )

    @api.constrains("lot_number")
    def _check_lot_number(self):
        for record in self:
            if record.vehicle_category == "embosed":
                # record.lot_number should start most be Alphabet
                # eg:  A123, ABB,
                # it does not accept 1234
                if not record.lot_number or not re.match(
                    r"^[A-Za-z]", record.lot_number
                ):
                    raise ValidationError(_("Lot number must be Alphabet"))

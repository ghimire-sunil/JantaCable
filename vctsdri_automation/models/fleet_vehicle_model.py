from odoo import models, fields


class FleetVehicleModel(models.Model):
    _inherit = "fleet.vehicle.model"

    vehicle_type = fields.Selection(
        selection_add=[("truck", "Truck")],
        ondelete={
            "truck": "set default",
        },
        required=True,
        tracking=True,
    )

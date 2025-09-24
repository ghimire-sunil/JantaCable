from odoo import models, fields


class FleetVehicleProvincal(models.Model):
    _name = "fleet.vehicle.provincal"
    _description = "Vehicle Provincal"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    is_both = fields.Boolean(string="Is Both", default=False)
    is_embosed = fields.Boolean(string="Is Embosed", default=False)

    _sql_constraints = [
        ("fleet_provincal_name_unique", "unique(name)", "Provincal name already exists")
    ]

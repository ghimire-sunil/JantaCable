import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"   
    transpoter_cn = fields.Char('Transpoter C.N.')
    transport_inv_no = fields.Char('Transport Inv.No.')

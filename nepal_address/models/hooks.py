import os
import base64
import tempfile
import openpyxl
from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    module_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(module_path, 'data', 'address_data.xlsx')

    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active

    # Assuming headers are: Province, District, Municipality, Ward
    for row in sheet.iter_rows(min_row=2, values_only=True):
        province_name, district_name, municipality_name, ward_name = row

        country = env.ref('base.np', raise_if_not_found=False)
        
        # Create or get Province
        province = env['res.province'].search([('name', '=', province_name)], limit=1)
        if not province:
            province = env['res.province'].create({
                'name': province_name,
                'country_id': country.id if country else False,
            })

        # Create or get District
        district = env['res.district'].search([('name', '=', district_name), ('province_id', '=', province.id)], limit=1)
        if not district:
            district = env['res.district'].create({
                'name': district_name,
                'province_id': province.id,
                'country_id': country.id if country else False,
            })

        # Create or get Municipality
        municipality = env['res.municipality'].search([('name', '=', municipality_name), ('district_id', '=', district.id)], limit=1)
        if not municipality:
            municipality = env['res.municipality'].create({
                'name': municipality_name,
                'district_id': district.id,
                'country_id': country.id if country else False,
            })

        # Create or get Ward
        ward = env['res.ward'].search([('name', '=', ward_name), ('municipality_id', '=', municipality.id)], limit=1)
        if not ward:
            env['res.ward'].create({
                'name': ward_name,
                'municipality_id': municipality.id,
                'district_id': district.id,
                'country_id': country.id if country else False,
            })

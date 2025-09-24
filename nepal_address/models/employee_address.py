from odoo import api, fields, models

class ContactAddress(models.Model):
    _inherit = 'res.partner'

    #contact Address
    private_country_id = fields.Many2one(
        'res.country',
        string="Private Country",
        default=lambda self: self.env.ref('base.np').id if self.env.ref('base.np', raise_if_not_found=False) else None
    )
    contact_province_id = fields.Many2one('res.province', string="Province")
    contact_district_id = fields.Many2one('res.district', string="District")
    contact_municipality_id = fields.Many2one('res.municipality', string="Municipality")
    contact_ward_id = fields.Many2one('res.ward', string="Ward")
    
    

class CompanyAddress(models.Model):
    _inherit = 'res.company'

    #contact Address
    private_country_id = fields.Many2one(
        'res.country',
        string="Private Country",
        default=lambda self: self.env.ref('base.np').id if self.env.ref('base.np', raise_if_not_found=False) else None
    )
    company_province_id = fields.Many2one('res.province', string="Province")
    company_district_id = fields.Many2one('res.district', string="District")
    company_municipality_id = fields.Many2one('res.municipality', string="Municipality")
    company_ward_id = fields.Many2one('res.ward', string="Ward")

    
class EmployeeAddress(models.Model):
    _inherit = 'hr.employee'

    # Permanent Address
    street = fields.Char()
    private_country_id = fields.Many2one('res.country', default=lambda self: self._get_default_country())
    province_id = fields.Many2one('res.province', string='Province')
    district_id = fields.Many2one('res.district', string='District')
    municipality_id = fields.Many2one('res.municipality', string='Municipality')
    ward_id = fields.Many2one('res.ward', string='Ward')
    city = fields.Char(string='City')

    # Temporary Address
    temp_province_id = fields.Many2one('res.province', string='Province')
    temp_district_id = fields.Many2one('res.district', string='District')
    temp_municipality_id = fields.Many2one('res.municipality', string='Municipality')
    temp_ward_id = fields.Many2one('res.ward', string='Ward')
    temp_city = fields.Char(string='City')

    emp_province_id = fields.Many2one('res.province', string="Province")
    emp_district_id = fields.Many2one('res.district', string="District")
    emp_municipality_id = fields.Many2one('res.municipality', string="Municipality")
    emp_ward_id = fields.Many2one('res.ward', string="Ward")
    

    helpers_ids = fields.One2many('hr.employee', 'parent_helpers_id', string='Helpers')
    parent_helpers_id = fields.Many2one('hr.employee', string='Parent Helper')

    @api.model
    def _get_default_country(self):
        country = self.env['res.country'].search([('name', '=', 'Nepal')], limit=1)
        return country.id if country else False

    @api.onchange("province_id")
    def onchange_province_id(self):
        if self.province_id:
            self.district_id = False
            self.municipality_id = False
            self.ward_id = False

    @api.onchange("district_id")
    def onchange_district_id(self):
        if self.district_id:
            self.municipality_id = False
            self.ward_id = False

    @api.onchange("municipality_id")
    def onchange_municipality_id(self):
        if self.municipality_id:
            self.ward_id = False




class Province(models.Model):
    _name = 'res.province'
    
    name = fields.Char(string='Province Name', required=True)
    country_id =  fields.Many2one('res.country',"Country",default=lambda self: self._get_default_country())
    district_ids = fields.One2many(comodel_name="res.district", inverse_name='province_id', string="Districts")

    @api.model
    def _get_default_country(self):
        country = self.env['res.country'].search([('name', '=', 'Nepal')], limit=1)
        return country.id if country else False

class District(models.Model):
    _name = "res.district"

    name = fields.Char(string='District Name', required=True)
    country_id =  fields.Many2one('res.country',"Country",default=lambda self: self._get_default_country())
    province_id = fields.Many2one('res.province', 'Province')
    municipality_ids = fields.One2many(comodel_name="res.municipality",inverse_name="district_id",string="Municipality")

    @api.model
    def _get_default_country(self):
        country = self.env['res.country'].search([('name', '=', 'Nepal')], limit=1)
        return country.id if country else False
    

class Municipality(models.Model):
    _name = 'res.municipality'
    
    name = fields.Char(string='Municipality Name', required=True)
    country_id =  fields.Many2one('res.country',"Country",default=lambda self: self._get_default_country())
    district_id = fields.Many2one('res.district', "Districts")
    ward_ids = fields.One2many(comodel_name="res.ward", inverse_name="municipality_id",string="Ward")

    @api.model
    def _get_default_country(self):
        country = self.env['res.country'].search([('name', '=', 'Nepal')], limit=1)
        return country.id if country else False
    
class Ward(models.Model):
    _name = 'res.ward'

    name = fields.Char(string='Ward Name', required=True)
    country_id =  fields.Many2one('res.country',"Country",default=lambda self: self._get_default_country())
    district_id = fields.Many2one('res.district', "District")
    municipality_id = fields.Many2one('res.municipality', string = 'Municipality')
    

    @api.model
    def _get_default_country(self):
        country = self.env['res.country'].search([('name', '=', 'Nepal')], limit=1)
        return country.id if country else False

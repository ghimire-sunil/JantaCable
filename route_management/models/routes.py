from odoo import fields, models


class Route(models.Model):
    _name = "partner.route"
    _inherit = ['mail.thread']  
    
    name = fields.Char(string='Name', required=True, tracking=True)
    code = fields.Char(string="Code", required=True, tracking=True)
    parent_id = fields.Many2one('partner.route', 'Parent Route', index=True, ondelete='cascade')
    partners_ids  = fields.One2many(
        string="Partners",
        comodel_name="res.partner",
        inverse_name="route_id"
    )   
    partner_counts = fields.Integer(
        string="Partner Count",
        compute="_compute_partner_count"
    )
    active = fields.Boolean(default=True)
    
    def _compute_partner_count(self):
        for record in self:
            record.partner_counts = len(record.partners_ids)
    
    def action_view_partner(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Partners',
            'view_mode': 'list,form',
            'res_model': 'res.partner',         
            'domain': [('id', 'in', self.partners_ids.ids)],
            'target': 'current', 
        }

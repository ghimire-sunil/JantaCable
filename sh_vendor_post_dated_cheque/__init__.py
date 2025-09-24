# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from . import models
from . import wizard


def post_init_hook(env):
    for company in env['res.company'].sudo().search([]):
        company.write({
            'pdc_vendor': env['account.account'].search([('name', '=', 'PDC Payable'), ('company_ids', 'in', company.id)], limit=1).id
        })

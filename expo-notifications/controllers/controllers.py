# -*- coding: utf-8 -*-
from odoo import http


class ExpoNotification(http.Controller):
    @http.route('/expo-notifications/register', auth='public',type='json')
    def index(self, **kw):
        pass


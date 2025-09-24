# -*- coding: utf-8 -*-
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)
from odoo import api, models, fields
from odoo.exceptions import UserError,ValidationError
import requests
from requests.exceptions import ConnectionError, HTTPError
from datetime import datetime, timedelta

# Optionally providing an access token within a session if you have enabled push security
session = requests.Session()
session.headers.update(
    {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate",
        "content-type": "application/json",
    }
)

class ExpoDevice(models.Model):
    _name = 'expo.device'
    _description = 'Expo Notifications'

    name = fields.Char('name',related='user_id.name')
    user_id = fields.Many2one('res.users','User',required=True)
    expo_push_token = fields.Char("Expo Push Token",required=True)
    origin_app = fields.Char("Origin App",required=True)


class ExpoMessage(models.Model):
    _name = 'expo.message'
    _description = 'Expo Message'
   
    name= fields.Char('name',related='title') 
    device_ids = fields.Many2many('expo.device',required=True ,ondelete='cascade', compute="_compute_device_ids")
    user_id = fields.Many2one('res.users')
    # user_ids = fields.Many2many('res.users', compute="_compute_user_ids")
    body = fields.Char("Body",required=True)
    title = fields.Char("Title",required=True)
    state = fields.Selection([('draft','Draft'),('sent','Sent'),('failed','Failed')],default="draft")
    read_message = fields.Boolean("Read Message")
    date = fields.Datetime(string="Date", required=True)

    @api.depends('user_id')
    def _compute_device_ids(self):
        for message in self:
            devices = self.env['expo.device'].sudo().search([('user_id','=',message.user_id.id)])
            message.device_ids = devices.ids

    @api.constrains('date')
    def _date_constraint(self):
        for message in self:
            if message.date < datetime.now():
                raise UserError("Date cannot be in he past!!")
            
    @api.constrains('user_id')
    def _user_constrains(self):
        for message in self:
            devices = self.env['expo.device'].sudo().search([('user_id','=',message.user_id.id)])
            if not devices:
                raise UserError("User has no registered device!!")

    def _send_notification(self,**kwargs):
        try:
            if  kwargs.get('title'):
                del kwargs['title']
            if kwargs.get('body'):
                del kwargs['body']

            unsent = []

            for device in self.device_ids:
                response = PushClient(session=session).publish(
                    PushMessage(to=device.expo_push_token,
                                body=self.body,
                                title=self.title,
                                ttl=86400, 
                                **kwargs
                                ))
                if response.status == 'ok':
                    pass
                else:
                    unsent.append(device)
            if not unsent:
                self.state = 'sent'
            else: 
                self.state = 'failed'

        except PushServerError as exc:
            raise ValidationError(exc.errors)
            
        except (ConnectionError, HTTPError) as exc:
            
            raise UserError("No response from server")

        try:
            response.validate_response()
        except DeviceNotRegisteredError:
            print(exec)
        except PushTicketError as exc:
            print(exec)
            
    def action_send_notifications(self):
        for rec in self:
            try:
             rec._send_notification()
            except Exception as e:
                print(e)


# class ResUsersInherited(models.Model):
#     _inherit = 'res.users'

#     device_ids = fields.Many2many('expo.device', compute="")

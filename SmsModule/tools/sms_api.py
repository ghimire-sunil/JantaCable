from odoo import _, exceptions
import requests
from odoo.addons.sms.tools.sms_api import SmsApi


class SMSApi(SmsApi):
    def _contact_iap(self, local_endpoint, params, timeout=15):
        auth_token = self.env['ir.config_parameter'].sudo().\
            get_param('src.sms_token')
        sent_sms_status = []

        for content in params['messages']:
            try:
                for number in content["numbers"]:
                    numb = number['number'].\
                        replace("-", "").\
                        replace(" ", "").replace("+", "")[-10:]
                    req = requests.post(
                        url="https://sms.aakashsms.com/sms/v3/send",
                        data={
                            'auth_token': auth_token,
                            'to': numb,
                            'text': content['content']
                        })

                    if req.json()["error"] == True:
                        sent_sms_status.append({
                            'state': 'failed',
                            'uuid': number['uuid'],
                            'credit': 0
                        })
                    else:
                        sent_sms_status.append({
                            'state': 'success',
                            'uuid': number['uuid'],
                            'credit': 0
                        })

            except (ValueError, requests.exceptions.ConnectionError, requests.exceptions.MissingSchema, requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
                raise exceptions.AccessError(
                    _('The url that this service requested returned an error. Please contact the author of the app. The url it tried to contact was %s',
                        "https://sms.aakashsms.com/sms/v3/send")
                )

        return sent_sms_status

from odoo import http, Command
from odoo.http import request
from odoo.addons.payment.controllers.portal import PaymentPortal
import logging
import psycopg2
_logger = logging.getLogger(__name__)

class MobilePayment(PaymentPortal):


    @http.route(
        '/api/v1/transaction/<int:order_id>', type='json', auth='public',
    )
    def mobile_payment_transaction(self, order_id,**kwargs):

        order_sudo = request.env['sale.order'].sudo().browse(order_id)
        
        provider_code = kwargs.get('code')
        # if provider_code == 'esewa':
        #     provider_code = 'esewa-v2'

        provider = request.env['payment.provider'].sudo().search([('code','=',provider_code)],limit=1)
        # payment_method = request.env['payment.method'].sudo().search([('code','=',kwargs.get('code'))],limit=1)

        _logger.info(provider)
        _logger.info(provider_code)
        if not provider:
            raise ValueError("Provider not found")
            
        payment_method =provider.payment_method_ids[0]
        
        del kwargs['code']
        self._validate_transaction_kwargs(kwargs)
        kwargs.update({
            'partner_id': order_sudo.partner_invoice_id.id,
            'currency_id': order_sudo.currency_id.id,
            'sale_order_id': order_id,
            'provider_id':provider.id,
            'payment_method_id':payment_method.id,
            'token_id':None,
            'flow':'redirect',
            'tokenization_requested':False,
            'landing_route':'/shop/payment/validate',
            'is_validation':False
              # Include the SO to allow Subscriptions to tokenize the tx
        })
        
        if not kwargs.get('amount'):
            kwargs['amount'] = order_sudo.amount_total
        
        tx_sudo = self._create_transaction(
            custom_create_values={'sale_order_ids': [Command.set([order_id])]}, **kwargs,
        )

        print("whatttttt")
        return tx_sudo._get_processing_values()


    @http.route(
        '/api/v1/poll/<string:reference>', type='json', auth='public',
    )
    def mobile_polling(self, reference, **kwargs):

        monitored_tx = request.env['payment.transaction'].sudo().search([('reference','=',reference)],limit=1)

        if not monitored_tx:  # The session might have expired, or the tx has never existed.
            return Exception('Tx Not Found !!')
        
        if not monitored_tx.is_post_processed:
            try:
                monitored_tx._post_process()
            except psycopg2.OperationalError:  # The database cursor could not be committed.
                request.env.cr.rollback()  # Rollback and try later.
                raise Exception('retry')
            except Exception as e:
                request.env.cr.rollback()
                _logger.exception(
                    "Encountered an error while post-processing transaction with id %s:\n%s",
                    monitored_tx.id, e
                )
                raise
    
        return {
            'provider_code': monitored_tx.provider_code,
            'state': monitored_tx.state,
            'landing_route': monitored_tx.landing_route,
        }

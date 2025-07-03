from odoo import http
from odoo.http import request
import requests

class OrangeMoneyController(http.Controller):

    @http.route('/api/payment/orange', type='json', auth='public', cors='*', methods=['POST'])
    def initiate_orange_payment(self, **kwargs):
        phone_number = kwargs.get('phoneNumber')
        amount = kwargs.get('amount')
        reference = kwargs.get('reference')
        description = kwargs.get('description')

        # Récupérer la configuration Orange Money
        config = request.env['orange.money.config'].sudo().search([('is_active', '=', True)], limit=1)
        if not config:
            return {'error': 'Configuration Orange Money not found'}

        token = config.token

        payload = {
            "amount": amount,
            "currency": "XOF",
            "payer_name": description,
            "payer_phone_number": phone_number,
            "reference": reference,
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        res = requests.post("https://api.orange.com/orange-money-webpay/1.0/payment", json=payload, headers=headers)

        if res.status_code == 200:
            data = res.json()
            # Stocker dans Odoo si nécessaire
            request.env['orange.money.transaction'].sudo().create({
                'orange_id': data['payment_id'],
                'amount': amount,
                'status': 'pending',
                'phone': phone_number,
                'reference': reference,
            })
            return {'url': data['payment_url']}
        else:
            return {'error': res.text}

    @http.route('/api/payment/orange', type='json', auth='public', cors='*', methods=['GET'])
    def verify_orange_payment(self, **kwargs):
        reference = kwargs.get('reference')
        tx = request.env['orange.money.transaction'].sudo().search([('reference', '=', reference)], limit=1)
        if tx:
            return {'status': tx.status}
        else:
            return {'error': 'Transaction not found'}

    @http.route('/api/orange/webhook', type='json', auth='public', csrf=False)
    def orange_webhook(self, **kwargs):
        data = kwargs
        tx = request.env['orange.money.transaction'].sudo().search([('orange_id', '=', data.get('payment_id'))], limit=1)
        if tx:
            tx.status = data.get('status')
        return 'OK'

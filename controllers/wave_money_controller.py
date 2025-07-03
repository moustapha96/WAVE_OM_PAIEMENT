
from odoo import http, fields
from odoo.http import request, Response
import requests
import hmac
import hashlib
import json
import logging
import werkzeug

_logger = logging.getLogger(__name__)

class WaveMoneyController(http.Controller):
    
    @http.route('/api/payment/wave/initiate', type='http', auth='public', cors='*', methods=['POST'], csrf=False)
    def initiate_wave_payment(self, **kwargs):
        """Initier un paiement Wave avec checkout sessions"""
        try:
            # Validation des paramètres requis
            data = json.loads(request.httprequest.data)
            transaction_id = data.get('transaction_id')
            order_id = data.get('order_id')
            partner_id = data.get('partner_id')
            phone_number = data.get('phoneNumber')
            amount = data.get('amount')
            description = data.get('description', 'Payment via Wave')
            currency = data.get('currency', 'XOF')
            reference = data.get('reference')

            # Validation des champs obligatoires
            if not all([transaction_id, order_id, partner_id , phone_number , amount]):
                return self._make_response({'message': "Missing required fields: transaction_id, order_id, partner_id"}, 400)
                
            
            # Réccupérer la configuration Wave active
            config = request.env['wave.config'].sudo().search([('is_active', '=', True)], limit=1)
            if not config:
                return {'error': 'Wave configuration not found', 'success': False}

            # Vérifier l'existence de l'order et du partner
            order = request.env['sale.order'].sudo().browse(int(order_id)) if order_id else None
            partner = request.env['res.partner'].sudo().browse(int(partner_id)) if partner_id else None
           
            if not order:
                return self._make_response({'message': "la commande n'exite pas"}, 400)
            if not partner:
                return self._make_response({'message': "le partner n'exite pas"}, 400)

            # Vérifier si payment.details existe déjà avec ce transaction_id
        
            # Vérifier si la transaction Wave existe déjà
            existing_tx = request.env['wave.transaction'].sudo().search([('transaction_id', '=', transaction_id)], limit=1)
            if existing_tx:
               
                return self._make_response({
                        'success': True,
                        'transaction_id': existing_tx.transaction_id,
                        'wave_id': existing_tx.wave_id,
                        'session_id': existing_tx.wave_id,
                        'payment_url': existing_tx.payment_link_url,
                        'status': existing_tx.status or 'pending',
                        'order_id': existing_tx.order_id.id,
                        'partner_id': existing_tx.partner_id.id,
                        'reference': existing_tx.reference,
                        'existe': True
                    }, 200)

            _logger.info(f"config callback_url: {config.callback_url}")
            payload = {
                "amount": amount,
                "currency": currency,
                "success_url":  config.callback_url,
                "error_url": config.callback_url
            }

            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            }

            # Appel à l'API Wave checkout sessions
            response = requests.post(
                "https://api.wave.com/v1/checkout/sessions", 
                json=payload, 
                headers=headers,
                timeout=30
            )

            if response.status_code in [200, 201]:  # Wave peut retourner 200 ou 201
                data = response.json()
                
                # Créer la transaction dans Odoo
                wave_transaction = request.env['wave.transaction'].sudo().create({
                    'wave_id': data.get('id'),
                    'transaction_id': transaction_id,
                    'amount': amount,
                    'currency': currency,
                    'status': 'pending',
                    'phone': phone_number,
                    'reference': reference,
                    'description': description,
                    'payment_link_url': data.get('wave_launch_url') or data.get('checkout_url'),
                    'wave_response': json.dumps(data),
                    'order_id': order.id,
                    'partner_id': partner.id
                })
                return self._make_response({
                    'success': True,
                    'transaction_id': wave_transaction.transaction_id,
                    'wave_id': data.get('id'),
                    'session_id': data.get('id'),
                    'payment_url': data.get('wave_launch_url') or data.get('checkout_url'),
                    'status': 'pending',
                    'order_id': wave_transaction.order_id.id,
                    'partner_id': wave_transaction.partner_id.id,
                    'reference': reference
                }, 200)
                
            else:
                _logger.error(f"Wave API Error: {response.status_code} - {response.text}")
                return self._make_response_json(response.text, 400)
                

        except Exception as e:
            _logger.error(f"Error initiating Wave payment: {str(e)}")
            return self._make_response( str(e), 400)
           

    @http.route('/api/payment/wave/status/<string:transaction_id>', type='http', auth='public', cors='*', methods=['GET'])
    def get_wave_payment_status(self, transaction_id , **kwargs):
        """Vérifier le statut d'un paiement Wave"""
        try:
            if not transaction_id:
                return self._make_response({"error": "Paiement wave avec cette transaction_id nexiste pas"}, 400)

            # Rechercher la transaction selon les paramètres fournis
            transaction = None

            # Priorité 1: transaction_id (notre ID personnalisé)
            if transaction_id:
                transaction = request.env['wave.transaction'].sudo().search([('transaction_id', '=', transaction_id)], limit=1)
                result = self._refresh_transaction_status(transaction)
                if result:
                    transaction_up = request.env['wave.transaction'].sudo().search([('transaction_id', '=', transaction_id)], limit=1)
                    return self._make_response({
                        'success': True,
                        'transaction_id': transaction_up.id,
                        'custom_transaction_id': transaction_up.transaction_id,
                        'wave_id': transaction_up.wave_id,
                        'session_id': transaction_up.wave_id,
                        'reference': transaction_up.reference,
                        'status': transaction_up.status,
                        'amount': transaction_up.amount,
                        'currency': transaction_up.currency,
                        'phone': transaction_up.phone,
                        'description': transaction_up.description,
                        'payment_url': transaction_up.payment_link_url,
                        'order_id': transaction_up.order_id.id if transaction.order_id else False,
                        'order_type' : transaction_up.order_id.order_type,
                        'type_sale': transaction_up.order_id.type_sale,
                        'partner_id': transaction_up.partner_id.id if transaction.partner_id else False,
                        'created_at': transaction_up.created_at.isoformat() if transaction.created_at else None,
                        'updated_at': transaction_up.updated_at.isoformat() if transaction.updated_at else None,
                        'completed_at': transaction_up.completed_at.isoformat() if transaction.completed_at else None
                    }, 200)
                else:
                    return self._make_response({
                        'success': True,
                        'transaction_id': transaction.transaction_id,
                        'wave_id': transaction.wave_id,
                        'session_id': transaction.wave_id,
                        'payment_url': transaction.payment_link_url,
                        'status': transaction.status or 'pending',
                        'order_id': transaction.order_id.id,
                        'partner_id': transaction.partner_id.id,
                        'reference': transaction.reference,
                        'existe': True
                    }, 200)

            return self._make_response({"error": "Transaction not found"}, 400)

        except Exception as e:
            _logger.error(f"Error getting Wave payment status: {str(e)}")
            return self._make_response({"error": str(e)}, 400)


    @http.route('/api/payment/wave/status/by-transaction-id/<string:custom_transaction_id>', type='json', auth='public', cors='*', methods=['GET'])
    def get_wave_payment_status_by_transaction_id(self, custom_transaction_id, **kwargs):
        """Vérifier le statut d'un paiement Wave par transaction_id personnalisé"""
        try:
            transaction = request.env['wave.transaction'].sudo().search([('transaction_id', '=', custom_transaction_id)], limit=1)
            
            if not transaction:
                return {'error': f'Transaction not found for transaction_id: {custom_transaction_id}', 'success': False}

            # Optionnel: Rafraîchir le statut depuis Wave
            if kwargs.get('refresh', False):
                self._refresh_transaction_status(transaction)

            return {
                'success': True,
                'transaction_id': transaction.id,
                'custom_transaction_id': transaction.transaction_id,
                'wave_id': transaction.wave_id,
                'session_id': transaction.wave_id,
                'reference': transaction.reference,
                'status': transaction.status,
                'amount': transaction.amount,
                'currency': transaction.currency,
                'phone': transaction.phone,
                'description': transaction.description,
                'payment_url': transaction.payment_link_url,
                'order_id': transaction.order_id.id if transaction.order_id else False,
                'partner_id': transaction.partner_id.id if transaction.partner_id else False,
                'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
                'updated_at': transaction.updated_at.isoformat() if transaction.updated_at else None,
                'completed_at': transaction.completed_at.isoformat() if transaction.completed_at else None
            }

        except Exception as e:
            _logger.error(f"Error getting Wave payment status by transaction_id: {str(e)}")
            return {'error': f'Internal error: {str(e)}', 'success': False}

    @http.route('/api/payment/wave/session/<string:session_id>', type='json', auth='public', cors='*', methods=['GET'])
    def get_wave_session(self, session_id, **kwargs):
        """Récupérer les détails d'une session Wave par son ID"""
        try:
            # Récupérer la configuration Wave active
            config = request.env['wave.config'].sudo().search([('is_active', '=', True)], limit=1)
            if not config:
                return {'error': 'Wave configuration not found', 'success': False}

            # Utiliser la méthode du modèle pour récupérer la session
            session_data = config.get_session_by_id(session_id)
            
            if session_data:
                # Rechercher la transaction correspondante
                transaction = request.env['wave.transaction'].sudo().search([('wave_id', '=', session_id)], limit=1)
                
                result = {
                    'success': True,
                    'session': session_data
                }
                
                if transaction:
                    result['transaction'] = {
                        'id': transaction.id,
                        'custom_transaction_id': transaction.transaction_id,
                        'status': transaction.status,
                        'reference': transaction.reference
                    }
                
                return result
            else:
                return {'error': 'Session not found', 'success': False}

        except Exception as e:
            _logger.error(f"Error getting Wave session: {str(e)}")
            return {'error': f'Internal error: {str(e)}', 'success': False}

    @http.route('/api/payment/wave/refund', type='json', auth='public', cors='*', methods=['POST'])
    def refund_wave_payment(self, **kwargs):
        """Rembourser un paiement Wave"""
        try:
            session_id = kwargs.get('session_id')
            reference = kwargs.get('reference')
            custom_transaction_id = kwargs.get('custom_transaction_id')

            if not session_id and not reference and not custom_transaction_id:
                return {'error': 'session_id, reference or custom_transaction_id is required', 'success': False}

            # Récupérer la configuration Wave active
            config = request.env['wave.config'].sudo().search([('is_active', '=', True)], limit=1)
            if not config:
                return {'error': 'Wave configuration not found', 'success': False}

            # Trouver la transaction
            transaction = None
            if custom_transaction_id:
                transaction = request.env['wave.transaction'].sudo().search([('transaction_id', '=', custom_transaction_id)], limit=1)
            elif reference:
                transaction = request.env['wave.transaction'].sudo().search([('reference', '=', reference)], limit=1)
            elif session_id:
                transaction = request.env['wave.transaction'].sudo().search([('wave_id', '=', session_id)], limit=1)

            if not transaction:
                return {'error': 'Transaction not found', 'success': False}

            session_id = transaction.wave_id

            # Utiliser la méthode du modèle pour rembourser
            refund_data = config.refund_transaction(session_id)
            
            if refund_data:
                # Mettre à jour la transaction
                transaction.write({
                    'status': 'refunded',
                    'updated_at': fields.Datetime.now(),
                    'wave_response': json.dumps(refund_data)
                })

                return {
                    'success': True,
                    'refund': refund_data,
                    'transaction_id': transaction.id,
                    'custom_transaction_id': transaction.transaction_id,
                    'message': 'Refund processed successfully'
                }
            else:
                return {'error': 'Refund failed', 'success': False}

        except Exception as e:
            _logger.error(f"Error refunding Wave payment: {str(e)}")
            return {'error': f'Internal error: {str(e)}', 'success': False}

    @http.route('/api/payment/wave/transactions', type='json', auth='public', cors='*', methods=['GET'])
    def get_wave_transactions(self, **kwargs):
        """Récupérer la liste des transactions Wave"""
        try:
            limit = int(kwargs.get('limit', 50))
            offset = int(kwargs.get('offset', 0))
            status = kwargs.get('status')
            order_id = kwargs.get('order_id')
            partner_id = kwargs.get('partner_id')

            domain = []
            if status:
                domain.append(('status', '=', status))
            if order_id:
                domain.append(('order_id', '=', int(order_id)))
            if partner_id:
                domain.append(('partner_id', '=', int(partner_id)))

            transactions = request.env['wave.transaction'].sudo().search(
                domain, 
                limit=limit, 
                offset=offset, 
                order='created_at desc'
            )

            result = []
            for tx in transactions:
                result.append({
                    'id': tx.id,
                    'custom_transaction_id': tx.transaction_id,
                    'wave_id': tx.wave_id,
                    'session_id': tx.wave_id,
                    'reference': tx.reference,
                    'amount': tx.amount,
                    'currency': tx.currency,
                    'status': tx.status,
                    'phone': tx.phone,
                    'description': tx.description,
                    'payment_url': tx.payment_link_url,
                    'order_id': tx.order_id.id if tx.order_id else False,
                    'partner_id': tx.partner_id.id if tx.partner_id else False,
                    'created_at': tx.created_at.isoformat() if tx.created_at else None,
                    'updated_at': tx.updated_at.isoformat() if tx.updated_at else None
                })

            return {
                'success': True,
                'transactions': result,
                'total': len(result),
                'limit': limit,
                'offset': offset
            }

        except Exception as e:
            _logger.error(f"Error getting Wave transactions: {str(e)}")
            return {'error': f'Internal error: {str(e)}', 'success': False}

    # @http.route('/api/wave/webhook', type='json', auth='public', csrf=False, methods=['POST'])
    # def wave_webhook(self, **kwargs):
    #     """Gérer les webhooks Wave"""
    #     try:
    #         # Récupérer la configuration Wave
    #         config = request.env['wave.config'].sudo().search([('is_active', '=', True)], limit=1)
    #         if not config:
    #             _logger.error("Wave configuration not found for webhook")
    #             return {'error': 'Configuration not found'}, 400

    #         # Récupérer les headers et le body
    #         headers = request.httprequest.headers
    #         body = request.httprequest.get_data()
            
    #         # Vérification de la signature Wave
    #         if not self._verify_wave_signature(body, headers, config.webhook_secret):
    #             _logger.error("Invalid Wave webhook signature")
    #             return {'error': 'Invalid signature'}, 401

    #         # Parser les données JSON
    #         try:
    #             webhook_data = json.loads(body.decode('utf-8'))
    #         except json.JSONDecodeError:
    #             _logger.error("Invalid JSON in webhook payload")
    #             return {'error': 'Invalid JSON'}, 400

    #         # Traiter le webhook
    #         result = self._process_wave_webhook(webhook_data)
            
    #         if result.get('success'):
    #             return {'status': 'success'}, 200
    #         else:
    #             return {'error': result.get('error', 'Processing failed')}, 400

    #     except Exception as e:
    #         _logger.error(f"Error processing Wave webhook: {str(e)}")
    #         return {'error': 'Internal server error'}, 500


    @http.route('/wave/webhook', type='http', auth='public', csrf=False, methods=['POST'])
    def wave_webhook(self, **kwargs):
        """Gérer les webhooks Wave"""
        try:
            # Récupérer la configuration Wave
            config = request.env['wave.config'].sudo().search([('is_active', '=', True)], limit=1)
            if not config:
                _logger.error("Wave configuration not found for webhook")
                return Response(json.dumps({'error': 'Configuration not found'}), status=200, mimetype='application/json')

            # Récupérer les headers et le body
            headers = request.httprequest.headers
            body = request.httprequest.get_data()

            _logger.info(f"Wave webhook headers: {headers}")
            _logger.info(f"Wave webhook body: {body}")

            # Vérification de la signature Wave
            if not self._verify_wave_signature(body, headers, config.webhook_secret):
                _logger.error("Invalid Wave webhook signature")
                return Response(json.dumps({'error': 'Invalid signature'}), status=401, mimetype='application/json')

            # Parser les données JSON
            try:
                webhook_data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError:
                _logger.error("Invalid JSON in webhook payload")
                return Response(json.dumps({'error': 'Invalid JSON'}), status=200, mimetype='application/json')

            # Traiter le webhook
            result = self._process_wave_webhook(webhook_data)

            if result.get('success'):
                return Response(json.dumps({'status': 'success'}), status=200, mimetype='application/json')
            else:
                return Response(json.dumps({'error': result.get('error', 'Processing failed')}), status=400, mimetype='application/json')

        except Exception as e:
            _logger.error(f"Error processing Wave webhook: {str(e)}")
            return Response(json.dumps({'error': 'Internal server error'}), status=500, mimetype='application/json')

    def _verify_wave_signature(self, body, headers, webhook_secret):
        wave_signature = headers.get('Wave-Signature')
        if not wave_signature:
            return False

        parts = wave_signature.split(',')
        timestamp = None
        # timestamp = parts[0].split('=')[1]
        # signatures = [s.split('=')[1] for s in parts[1:]]
        
        signatures = []

        for part in parts:
            key, value = part.split('=', 1)
            if key == 't':
                timestamp = value
            elif key == 'v1':
                signatures.append(value)

        if not timestamp or not signatures:
            return False

        # Construire la charge utile en concaténant la valeur d'horodatage avec le corps de la requête
        payload = f"{timestamp}.{body.decode('utf-8')}"

        # Calculer la valeur HMAC attendue
        computed_hmac = hmac.new(webhook_secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()

        # Vérifier si la valeur HMAC calculée correspond à l'une des signatures fournies
        return computed_hmac in signatures


    @http.route('/wave/payment/callback', type='http', auth='public', csrf=False, methods=['GET', 'POST'])
    def wave_payment_callback(self, **kwargs):
        """Gérer les callbacks de paiement Wave"""
        try:
            session_id = kwargs.get('session_id') or kwargs.get('id')
            status = kwargs.get('status')
            reference = kwargs.get('client_reference')

            _logger.info(f"Wave callback received: session_id={session_id}, status={status}, reference={reference}")

            if session_id:
                # Rechercher la transaction
                transaction = request.env['wave.transaction'].sudo().search([
                    '|', 
                    ('wave_id', '=', session_id),
                    ('reference', '=', reference)
                ], limit=1)

                if transaction:
                    # Récupérer les détails de la session depuis Wave
                    config = request.env['wave.config'].sudo().search([('is_active', '=', True)], limit=1)
                    if config:
                        session_data = config.get_session_by_id(session_id)
                        if session_data:
                            # Mettre à jour le statut selon les données de la session
                            wave_status = session_data.get('status', '').lower()
                            odoo_status = self._map_wave_status_to_odoo(wave_status)
                            
                            transaction.write({
                                'status': odoo_status,
                                'updated_at': fields.Datetime.now(),
                                'wave_response': json.dumps(session_data)
                            })

                            # Déclencher les actions selon le statut
                            if odoo_status == 'completed':
                                self._handle_payment_completed(transaction, session_data)
                            elif odoo_status == 'failed':
                                self._handle_payment_failed(transaction, session_data)

            # Rediriger vers une page de succès ou d'erreur
            if status == 'success' or status == 'completed':
                return request.redirect('/payment/success')
            else:
                return request.redirect('/payment/error')

        except Exception as e:
            _logger.error(f"Error processing Wave callback: {str(e)}")
            return request.redirect('/payment/error')

    def _verify_wave_signature(self, body, headers, secret):
        """Vérifier la signature du webhook Wave"""
        try:
            signature = headers.get('Wave-Signature') or headers.get('X-Wave-Signature')
            if not signature:
                return False

            # Calculer la signature attendue
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()

            # Comparer les signatures
            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            _logger.error(f"Error verifying Wave signature: {str(e)}")
            return False

    def _process_wave_webhook(self, webhook_data):
        """Traiter les données du webhook Wave"""
        try:
            event_type = webhook_data.get('type') or webhook_data.get('event')
            session_data = webhook_data.get('data', {})
            session_id = session_data.get('id')

            if not session_id:
                return {'error': 'Missing session ID in webhook data', 'success': False}

            # Rechercher la transaction
            transaction = request.env['wave.transaction'].sudo().search([('wave_id', '=', session_id)], limit=1)
            
            if not transaction:
                _logger.warning(f"Transaction not found for Wave session ID: {session_id}")
                return {'error': 'Transaction not found', 'success': False}

            # Mettre à jour le statut selon le type d'événement
            status_mapping = {
                'checkout.session.completed': 'completed',
                'checkout.session.failed': 'failed',
                'checkout.session.cancelled': 'cancelled',
                'checkout.session.pending': 'pending',
                'payment.completed': 'completed',
                'payment.failed': 'failed',
                'payment.cancelled': 'cancelled',
                'payment.pending': 'pending'
            }

            new_status = status_mapping.get(event_type)
            if new_status:
                transaction.write({
                    'status': new_status,
                    'updated_at': fields.Datetime.now(),
                    'completed_at': session_data.get('when_completed'),
                    'webhook_data': json.dumps(webhook_data),
                    # 'client_reference': session_data.get('client_reference', '')
                })

                # Déclencher des actions selon le statut
                if new_status == 'completed':
                    self._handle_payment_completed(transaction, session_data)
                elif new_status == 'failed':
                    self._handle_payment_failed(transaction, session_data)

            return {'success': True, 'transaction_updated': True, 'custom_transaction_id': transaction.transaction_id}

        except Exception as e:
            _logger.error(f"Error processing webhook data: {str(e)}")
            return {'error': f'Processing error: {str(e)}', 'success': False}

    def _map_wave_status_to_odoo(self, wave_status):
        """Mapper les statuts Wave vers les statuts Odoo"""
        mapping = {
            'completed': 'completed',
            'succeeded': 'completed',
            'failed': 'failed',
            'cancelled': 'cancelled',
            'canceled': 'cancelled',
            'pending': 'pending',
            'processing': 'pending',
            'expired': 'expired'
        }
        return mapping.get(wave_status, 'pending')

    def _handle_payment_completed(self, transaction, payment_data):
        """Gérer un paiement complété"""
        try:
            # Mettre à jour la commande liée si elle existe
            # if transaction.order_id:
            #     transaction.order_id.write({
            #         'state': 'sale',
            #         # 'wave_payment_confirmed': True
            #     })

            # Log de succès
            _logger.info(f"Payment completed for transaction {transaction.reference} (custom_id: {transaction.transaction_id})")

        except Exception as e:
            _logger.error(f"Error handling completed payment: {str(e)}")

    def _handle_payment_failed(self, transaction, payment_data):
        """Gérer un paiement échoué"""
        try:
            # Log d'échec
            _logger.warning(f"Payment failed for transaction {transaction.reference} (custom_id: {transaction.transaction_id})")
            
            # # Optionnel: Annuler la commande liée
            # if transaction.order_id:
            #     transaction.order_id.write({
            #         'state': 'cancel',
            #         # 'wave_payment_failed': True
            #     })

        except Exception as e:
            _logger.error(f"Error handling failed payment: {str(e)}")

    def _refresh_transaction_status(self, transaction):
        """Rafraîchir le statut d'une transaction depuis l'API Wave"""
        try:
            config = request.env['wave.config'].sudo().search([('is_active', '=', True)], limit=1)
            if not config:
                return False

            # Utiliser la méthode du modèle pour récupérer la session
            session_data = config.get_session_by_id(transaction.wave_id)
            
            if session_data:
                wave_status = session_data.get('status', '').lower()
                new_status = self._map_wave_status_to_odoo(wave_status)
                
                if new_status != transaction.status:
                    transaction.write({
                        'status': new_status,
                        'updated_at': fields.Datetime.now(),
                        'wave_response': json.dumps(session_data)
                    })

                return True

        except Exception as e:
            _logger.error(f"Error refreshing transaction status: {str(e)}")
            return False

 
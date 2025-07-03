# # -*- coding: utf-8 -*-
# import json
# import logging
# import hmac
# import hashlib
# from datetime import datetime
# from odoo import http, fields
# from odoo.http import request
# from odoo.exceptions import ValidationError

# _logger = logging.getLogger(__name__)


# class OrangeMoneyWebhook(http.Controller):
    
#     @http.route('/orange_money/webhook/callback', type='json', auth='none', methods=['POST'], csrf=False)
#     def orange_money_callback(self, **kwargs):
#         """
#         Endpoint pour recevoir les callbacks d'Orange Money
#         """
#         try:
#             # Récupérer les données du webhook
#             data = request.jsonrequest or {}
#             headers = request.httprequest.headers
            
#             _logger.info("Orange Money Webhook reçu: %s", json.dumps(data, indent=2))
#             _logger.info("Headers reçus: %s", dict(headers))
            
#             # Vérifier l'authentification si nécessaire
#             api_key = headers.get('X-Api-Key') or headers.get('Authorization')
#             if not self._verify_webhook_auth(api_key, data):
#                 _logger.warning("Webhook Orange Money non autorisé")
#                 return {'status': 'error', 'message': 'Unauthorized'}
            
#             # Traiter le callback selon le type de transaction
#             result = self._process_orange_money_callback(data)
            
#             return {
#                 'status': 'success',
#                 'message': 'Callback traité avec succès',
#                 'data': result
#             }
            
#         except Exception as e:
#             _logger.error("Erreur lors du traitement du callback Orange Money: %s", str(e))
#             return {
#                 'status': 'error',
#                 'message': str(e)
#             }
    
#     @http.route('/orange_money/webhook/status', type='http', auth='none', methods=['GET'], csrf=False)
#     def webhook_status(self, **kwargs):
#         """
#         Endpoint pour vérifier le statut du webhook (health check)
#         """
#         return request.make_response(
#             json.dumps({
#                 'status': 'active',
#                 'timestamp': fields.Datetime.now().isoformat(),
#                 'service': 'Orange Money Webhook'
#             }),
#             headers=[('Content-Type', 'application/json')]
#         )
    
#     @http.route('/orange_money/webhook/test', type='json', auth='*', methods=['POST'], csrf=False)
#     def test_webhook(self, **kwargs):
#         """
#         Endpoint pour tester le webhook (accessible aux utilisateurs connectés)
#         """
#         try:
#             test_data = {
#                 'transactionId': 'TEST123456789012345',
#                 'status': 'SUCCESS',
#                 'amount': {'value': 1000, 'unit': 'XOF'},
#                 'reference': 'TEST-REF-001',
#                 'timestamp': fields.Datetime.now().isoformat(),
#                 'type': 'MERCHANT_PAYMENT',
#                 'customer': {'id': '221234567890', 'idType': 'MSISDN'},
#                 'partner': {'id': '123456', 'idType': 'CODE'}
#             }
            
#             result = self._process_orange_money_callback(test_data)
            
#             return {
#                 'status': 'success',
#                 'message': 'Test webhook exécuté avec succès',
#                 'data': result
#             }
            
#         except Exception as e:
#             _logger.error("Erreur lors du test webhook: %s", str(e))
#             return {
#                 'status': 'error',
#                 'message': str(e)
#             }
    
#     def _verify_webhook_auth(self, api_key, data):
#         """
#         Vérifier l'authentification du webhook
#         """
#         try:
#             # Récupérer la clé API configurée dans Odoo
#             config_api_key = request.env['ir.config_parameter'].sudo().get_param('orange_money.webhook_api_key')
            
#             if not config_api_key:
#                 _logger.warning("Clé API webhook Orange Money non configurée")
#                 return True  # Permettre si pas de clé configurée (à adapter selon vos besoins)
            
#             # Vérifier la clé API
#             if api_key and (api_key == config_api_key or api_key.replace('Bearer ', '') == config_api_key):
#                 return True
            
#             return False
            
#         except Exception as e:
#             _logger.error("Erreur lors de la vérification d'authentification: %s", str(e))
#             return False
    
#     def _process_orange_money_callback(self, data):
#         """
#         Traiter les données du callback Orange Money
#         """
#         try:
#             transaction_id = data.get('transactionId')
#             status = data.get('status')
#             amount_data = data.get('amount', {})
#             reference = data.get('reference')
#             customer = data.get('customer', {})
            
#             if not transaction_id:
#                 raise ValidationError("ID de transaction manquant dans le callback")
            
#             # Extraire le montant et le numéro de téléphone
#             amount = float(amount_data.get('value', 0)) if amount_data.get('value') else 0.0
#             phone = customer.get('id') if customer.get('idType') == 'MSISDN' else None
            
#             # Rechercher la transaction existante dans le modèle OrangeMoneyTransaction
#             transaction = self._find_orange_money_transaction(transaction_id, reference)
            
#             if transaction:
#                 # Mettre à jour la transaction existante
#                 self._update_orange_money_transaction(transaction, data, status, amount, phone)
#             else:
#                 # Créer une nouvelle transaction si elle n'existe pas
#                 transaction = self._create_orange_money_transaction(data, transaction_id, status, amount, phone, reference)
            
#             # Traiter selon le statut
#             if status in ['SUCCESS', 'SUCCESSFUL']:
#                 self._handle_successful_payment(transaction, data)
#             elif status in ['FAILED', 'CANCELLED', 'EXPIRED']:
#                 self._handle_failed_payment(transaction, data)
            
#             return {
#                 'transaction_id': transaction_id,
#                 'odoo_transaction_id': transaction.id if transaction else None,
#                 'status_processed': status
#             }
            
#         except Exception as e:
#             _logger.error("Erreur lors du traitement du callback: %s", str(e))
#             raise
    
#     def _find_orange_money_transaction(self, transaction_id, reference):
#         """
#         Rechercher une transaction Orange Money existante
#         """
#         try:
#             OrangeMoneyTransaction = request.env['orange.money.transaction'].sudo()
            
#             # Rechercher par transaction_id Orange Money
#             transaction = OrangeMoneyTransaction.search([
#                 ('orange_id', '=', transaction_id)
#             ], limit=1)
            
#             if not transaction and reference:
#                 # Rechercher par référence dans les commandes liées
#                 SaleOrder = request.env['sale.order'].sudo()
#                 orders = SaleOrder.search([
#                     ('client_order_ref', '=', reference)
#                 ], limit=1)
                
#                 if orders:
#                     transaction = OrangeMoneyTransaction.search([
#                         ('order_id', '=', orders.id)
#                     ], limit=1)
            
#             return transaction
            
#         except Exception as e:
#             _logger.error("Erreur lors de la recherche de transaction: %s", str(e))
#             return None
    
#     def _create_orange_money_transaction(self, data, transaction_id, status, amount, phone, reference):
#         """
#         Créer une nouvelle transaction Orange Money
#         """
#         try:
#             OrangeMoneyTransaction = request.env['orange.money.transaction'].sudo()
            
#             # Rechercher une commande liée par référence
#             order_id = False
#             if reference:
#                 SaleOrder = request.env['sale.order'].sudo()
#                 order = SaleOrder.search([
#                     ('client_order_ref', '=', reference)
#                 ], limit=1)
#                 if order:
#                     order_id = order.id
            
#             # Mapper le statut Orange Money vers le statut du modèle
#             mapped_status = self._map_orange_status_to_model(status)
            
#             vals = {
#                 'orange_id': transaction_id,
#                 'amount': amount,
#                 'phone': phone,
#                 'status': mapped_status,
#                 'date': fields.Datetime.now(),
#                 'created_at': fields.Datetime.now(),
#                 'order_id': order_id,
#             }
            
#             transaction = OrangeMoneyTransaction.create(vals)
#             _logger.info("Nouvelle transaction Orange Money créée: %s", transaction_id)
            
#             return transaction
            
#         except Exception as e:
#             _logger.error("Erreur lors de la création de transaction: %s", str(e))
#             return None
    
#     def _update_orange_money_transaction(self, transaction, data, status, amount, phone):
#         """
#         Mettre à jour une transaction Orange Money existante
#         """
#         try:
#             # Mapper le statut Orange Money vers le statut du modèle
#             mapped_status = self._map_orange_status_to_model(status)
            
#             vals = {
#                 'status': mapped_status,
#                 'date': fields.Datetime.now(),
#             }
            
#             # Mettre à jour le montant et le téléphone s'ils sont fournis
#             if amount > 0:
#                 vals['amount'] = amount
            
#             if phone:
#                 vals['phone'] = phone
            
#             transaction.write(vals)
#             _logger.info("Transaction Orange Money mise à jour: %s", transaction.orange_id)
            
#         except Exception as e:
#             _logger.error("Erreur lors de la mise à jour de transaction: %s", str(e))
    
#     def _map_orange_status_to_model(self, orange_status):
#         """
#         Mapper les statuts Orange Money vers les statuts du modèle OrangeMoneyTransaction
#         """
#         status_mapping = {
#             'SUCCESS': 'completed',
#             'SUCCESSFUL': 'completed',
#             'FAILED': 'failed',
#             'CANCELLED': 'failed',
#             'EXPIRED': 'failed',
#             'PENDING': 'pending',
#             'ACCEPTED': 'pending',
#             'REJECTED': 'failed',
#         }
#         return status_mapping.get(orange_status, 'pending')
    
#     def _handle_successful_payment(self, transaction, data):
#         """
#         Traiter un paiement réussi
#         """
#         try:
#             if transaction and transaction.status != 'completed':
#                 # Mettre à jour le statut
#                 transaction.write({'status': 'completed'})
                
#                 # Si une commande est liée, la confirmer
#                 if transaction.order_id:
#                     order = transaction.order_id
#                     if order.state in ['draft', 'sent']:
#                         order.action_confirm()
#                         _logger.info("Commande %s confirmée suite au paiement Orange Money", order.name)
                
#                 _logger.info("Paiement Orange Money confirmé pour la transaction: %s", transaction.orange_id)
                
#         except Exception as e:
#             _logger.error("Erreur lors du traitement du paiement réussi: %s", str(e))
    
#     def _handle_failed_payment(self, transaction, data):
#         """
#         Traiter un paiement échoué
#         """
#         try:
#             if transaction and transaction.status != 'failed':
#                 transaction.write({'status': 'failed'})
#                 _logger.info("Paiement Orange Money échoué pour la transaction: %s", transaction.orange_id)
                
#         except Exception as e:
#             _logger.error("Erreur lors du traitement du paiement échoué: %s", str(e))

# -*- coding: utf-8 -*-
import json
import logging
import hmac
import hashlib
from datetime import datetime
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class OrangeMoneyWebhook(http.Controller):
    
    def _make_response(self, data, status=200):
        """Créer une réponse HTTP JSON avec headers CORS"""
        return request.make_response(
            json.dumps(data, ensure_ascii=False, indent=2),
            status=status,
            headers={
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, X-Api-Key'
            }
        )
    
    def _ensure_authenticated_env(self):
        """S'assurer que l'environnement est authentifié"""
        try:
            # Si pas d'utilisateur connecté, utiliser l'utilisateur admin
            if not request.env.user or request.env.user._is_public():
                admin_user = request.env.ref('base.user_admin')
                request.env = request.env(user=admin_user.id)
            return True
        except Exception as e:
            _logger.error("Erreur d'authentification webhook: %s", str(e))
            return False
    
    @http.route('/orange_money/webhook/callback', type='http', auth='public', methods=['POST'], csrf=False, cors='*')
    def orange_money_callback(self, **kwargs):
        """
        Endpoint pour recevoir les callbacks d'Orange Money
        """
        try:
            # S'assurer de l'authentification
            self._ensure_authenticated_env()
            
            # Récupérer les données du webhook
            try:
                if request.httprequest.data:
                    data = json.loads(request.httprequest.data.decode('utf-8'))
                else:
                    data = request.params
            except json.JSONDecodeError as e:
                _logger.error("Erreur de décodage JSON webhook: %s", str(e))
                return self._make_response({
                    'status': 'error',
                    'message': 'Données JSON invalides'
                }, 400)
            
            headers = request.httprequest.headers
            
            _logger.info("Orange Money Webhook reçu: %s", json.dumps(data, indent=2))
            _logger.info("Headers reçus: %s", dict(headers))
            
            # Vérifier l'authentification si nécessaire
            api_key = headers.get('X-Api-Key') or headers.get('Authorization')
            if not self._verify_webhook_auth(api_key, data):
                _logger.warning("Webhook Orange Money non autorisé")
                return self._make_response({
                    'status': 'error', 
                    'message': 'Unauthorized'
                }, 401)
            
            # Traiter le callback selon le type de transaction
            result = self._process_orange_money_callback(data)
            
            return self._make_response({
                'status': 'success',
                'message': 'Callback traité avec succès',
                'data': result
            })
            
        except Exception as e:
            _logger.error("Erreur lors du traitement du callback Orange Money: %s", str(e))
            return self._make_response({
                'status': 'error',
                'message': str(e)
            }, 500)
    
    
    @http.route('/orange_money/webhook/status', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def webhook_status(self, **kwargs):
        """
        Endpoint pour vérifier le statut du webhook (health check)
        """
        try:
            # S'assurer de l'authentification
            self._ensure_authenticated_env()
            
            return self._make_response({
                'status': 'active',
                'timestamp': fields.Datetime.now().isoformat(),
                'service': 'Orange Money Webhook',
                'version': '1.0'
            })
            
        except Exception as e:
            _logger.error("Erreur health check webhook: %s", str(e))
            return self._make_response({
                'status': 'error',
                'message': str(e)
            }, 500)
    
    @http.route('/orange_money/webhook/test', type='http', auth='public', methods=['POST'], csrf=False, cors='*')
    def test_webhook(self, **kwargs):
        """
        Endpoint pour tester le webhook
        """
        try:
            # S'assurer de l'authentification
            self._ensure_authenticated_env()
            
            test_data = {
                'transactionId': f'TEST{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'status': 'SUCCESS',
                'amount': {'value': 1000, 'unit': 'XOF'},
                'reference': f'TEST-REF-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'timestamp': fields.Datetime.now().isoformat(),
                'type': 'MERCHANT_PAYMENT',
                'customer': {'id': '221234567890', 'idType': 'MSISDN'},
                'partner': {'id': '123456', 'idType': 'CODE'}
            }
            
            result = self._process_orange_money_callback(test_data)
            
            return self._make_response({
                'status': 'success',
                'message': 'Test webhook exécuté avec succès',
                'data': result,
                'test_data': test_data
            })
            
        except Exception as e:
            _logger.error("Erreur lors du test webhook: %s", str(e))
            return self._make_response({
                'status': 'error',
                'message': str(e)
            }, 500)
    
    # Route OPTIONS pour CORS
    @http.route([
        '/orange_money/webhook/callback',
        '/orange_money/webhook/status',
        '/orange_money/webhook/test'
    ], type='http', auth='public', methods=['OPTIONS'], csrf=False, cors='*')
    def options_handler(self, **kwargs):
        """Gérer les requêtes OPTIONS pour CORS"""
        return self._make_response({'success': True})
    
    def _verify_webhook_auth(self, api_key, data):
        """
        Vérifier l'authentification du webhook
        """
        try:
            # Récupérer la clé API configurée dans Odoo
            config_api_key = request.env['ir.config_parameter'].sudo().get_param('orange_money.webhook_api_key')
            
            if not config_api_key:
                _logger.warning("Clé API webhook Orange Money non configurée - autorisation par défaut")
                return True  # Permettre si pas de clé configurée
            
            # Vérifier la clé API
            if api_key:
                # Nettoyer la clé API (enlever Bearer si présent)
                clean_api_key = api_key.replace('Bearer ', '').strip()
                if clean_api_key == config_api_key:
                    return True
            
            _logger.warning("Clé API webhook invalide: %s", api_key)
            return False
            
        except Exception as e:
            _logger.error("Erreur lors de la vérification d'authentification: %s", str(e))
            return False
    
    def _process_orange_money_callback(self, data):
        """
        Traiter les données du callback Orange Money
        """
        try:
            transaction_id = data.get('transactionId')
            status = data.get('status')
            amount_data = data.get('amount', {})
            reference = data.get('reference')
            customer = data.get('customer', {})
            
            if not transaction_id:
                raise ValidationError("ID de transaction manquant dans le callback")
            
            # Extraire le montant et le numéro de téléphone
            amount = float(amount_data.get('value', 0)) if amount_data.get('value') else 0.0
            phone = customer.get('id') if customer.get('idType') == 'MSISDN' else None
            
            # Rechercher la transaction existante dans le modèle OrangeMoneyTransaction
            transaction = self._find_orange_money_transaction(transaction_id, reference)
            
            if transaction:
                # Mettre à jour la transaction existante
                self._update_orange_money_transaction(transaction, data, status, amount, phone)
                _logger.info("Transaction existante mise à jour: %s", transaction_id)
            else:
                # Créer une nouvelle transaction si elle n'existe pas
                transaction = self._create_orange_money_transaction(data, transaction_id, status, amount, phone, reference)
                _logger.info("Nouvelle transaction créée: %s", transaction_id)
            
            # Traiter selon le statut
            if status in ['SUCCESS', 'SUCCESSFUL']:
                self._handle_successful_payment(transaction, data)
            elif status in ['FAILED', 'CANCELLED', 'EXPIRED']:
                self._handle_failed_payment(transaction, data)
            else:
                _logger.info("Statut de transaction en attente: %s", status)
            
            return {
                'transaction_id': transaction_id,
                'odoo_transaction_id': transaction.id if transaction else None,
                'status_processed': status,
                'mapped_status': self._map_orange_status_to_model(status)
            }
            
        except Exception as e:
            _logger.error("Erreur lors du traitement du callback: %s", str(e))
            raise
    
    def _find_orange_money_transaction(self, transaction_id, reference):
        """
        Rechercher une transaction Orange Money existante
        """
        try:
            OrangeMoneyTransaction = request.env['orange.money.transaction'].sudo()
            
            # Rechercher par transaction_id Orange Money
            transaction = OrangeMoneyTransaction.search([
                ('orange_id', '=', transaction_id)
            ], limit=1)
            
            if transaction:
                _logger.info("Transaction trouvée par orange_id: %s", transaction_id)
                return transaction
            
            # Si pas trouvé et référence fournie, rechercher par référence
            if reference:
                # Rechercher par référence directe dans les transactions
                transaction = OrangeMoneyTransaction.search([
                    ('reference', '=', reference)
                ], limit=1)
                
                if transaction:
                    _logger.info("Transaction trouvée par référence: %s", reference)
                    return transaction
                
                # Rechercher par référence dans les commandes liées
                SaleOrder = request.env['sale.order'].sudo()
                orders = SaleOrder.search([
                    '|',
                    ('client_order_ref', '=', reference),
                    ('name', '=', reference)
                ], limit=1)
                
                if orders:
                    transaction = OrangeMoneyTransaction.search([
                        ('order_id', '=', orders.id)
                    ], limit=1)
                    
                    if transaction:
                        _logger.info("Transaction trouvée via commande: %s", orders.name)
                        return transaction
            
            _logger.info("Aucune transaction existante trouvée pour: %s", transaction_id)
            return None
            
        except Exception as e:
            _logger.error("Erreur lors de la recherche de transaction: %s", str(e))
            return None
    
    def _create_orange_money_transaction(self, data, transaction_id, status, amount, phone, reference):
        """
        Créer une nouvelle transaction Orange Money
        """
        try:
            OrangeMoneyTransaction = request.env['orange.money.transaction'].sudo()
            
            # Rechercher une commande liée par référence
            order_id = False
            if reference:
                SaleOrder = request.env['sale.order'].sudo()
                order = SaleOrder.search([
                    '|',
                    ('client_order_ref', '=', reference),
                    ('name', '=', reference)
                ], limit=1)
                if order:
                    order_id = order.id
                    _logger.info("Commande liée trouvée: %s", order.name)
            
            # Mapper le statut Orange Money vers le statut du modèle
            mapped_status = self._map_orange_status_to_model(status)
            
            vals = {
                'orange_id': transaction_id,
                'amount': amount,
                'phone': phone or '',
                'status': mapped_status,
                'reference': reference or f'WH-{transaction_id}',
                'currency': 'XOF',
                'date': fields.Datetime.now(),
                'created_at': fields.Datetime.now(),
                'order_id': order_id,
                'callback_data': json.dumps(data)
            }
            
            transaction = OrangeMoneyTransaction.create(vals)
            _logger.info("Nouvelle transaction Orange Money créée: %s (ID: %s)", transaction_id, transaction.id)
            
            return transaction
            
        except Exception as e:
            _logger.error("Erreur lors de la création de transaction: %s", str(e))
            return None
    
    def _update_orange_money_transaction(self, transaction, data, status, amount, phone):
        """
        Mettre à jour une transaction Orange Money existante
        """
        try:
            # Mapper le statut Orange Money vers le statut du modèle
            mapped_status = self._map_orange_status_to_model(status)
            
            vals = {
                'status': mapped_status,
                'date': fields.Datetime.now(),
                'callback_data': json.dumps(data)
            }
            
            # Mettre à jour le montant et le téléphone s'ils sont fournis et différents
            if amount > 0 and amount != transaction.amount:
                vals['amount'] = amount
                _logger.info("Montant mis à jour: %s -> %s", transaction.amount, amount)
            
            if phone and phone != transaction.phone:
                vals['phone'] = phone
                _logger.info("Téléphone mis à jour: %s -> %s", transaction.phone, phone)
            
            transaction.write(vals)
            _logger.info("Transaction Orange Money mise à jour: %s (statut: %s)", transaction.orange_id, mapped_status)
            
        except Exception as e:
            _logger.error("Erreur lors de la mise à jour de transaction: %s", str(e))
    
    def _map_orange_status_to_model(self, orange_status):
        """
        Mapper les statuts Orange Money vers les statuts du modèle OrangeMoneyTransaction
        """
        status_mapping = {
            'SUCCESS': 'completed',
            'SUCCESSFUL': 'completed',
            'FAILED': 'failed',
            'CANCELLED': 'failed',
            'EXPIRED': 'failed',
            'PENDING': 'pending',
            'ACCEPTED': 'pending',
            'REJECTED': 'failed',
        }
        mapped = status_mapping.get(orange_status, 'pending')
        _logger.debug("Statut mappé: %s -> %s", orange_status, mapped)
        return mapped
    
    def _handle_successful_payment(self, transaction, data):
        """
        Traiter un paiement réussi
        """
        try:
            if not transaction:
                _logger.warning("Impossible de traiter le paiement réussi - transaction manquante")
                return
                
            # Mettre à jour le statut si nécessaire
            if transaction.status != 'completed':
                transaction.write({'status': 'completed'})
                _logger.info("Statut de transaction mis à jour vers 'completed': %s", transaction.orange_id)
            
            # Si une commande est liée, la traiter
            if transaction.order_id:
                order = transaction.order_id
                _logger.info("Commande liée trouvée: %s (état: %s)", order.name, order.state)
                
                # Confirmer la commande si elle est en brouillon ou envoyée
                if order.state in ['draft', 'sent']:
                    try:
                        order.action_confirm()
                        _logger.info("Commande %s confirmée suite au paiement Orange Money", order.name)
                        
                        # Ajouter un message dans la commande
                        message = f"Paiement Orange Money confirmé - Transaction: {transaction.orange_id}"
                        order.message_post(body=message)
                        
                    except Exception as e:
                        _logger.error("Erreur lors de la confirmation de commande %s: %s", order.name, str(e))
                else:
                    _logger.info("Commande %s déjà dans l'état %s - pas de confirmation nécessaire", order.name, order.state)
            else:
                _logger.info("Aucune commande liée à la transaction %s", transaction.orange_id)
                
            _logger.info("Paiement Orange Money traité avec succès pour la transaction: %s", transaction.orange_id)
                
        except Exception as e:
            _logger.error("Erreur lors du traitement du paiement réussi: %s", str(e))
    
    def _handle_failed_payment(self, transaction, data):
        """
        Traiter un paiement échoué
        """
        try:
            if not transaction:
                _logger.warning("Impossible de traiter le paiement échoué - transaction manquante")
                return
                
            if transaction.status != 'failed':
                transaction.write({'status': 'failed'})
                _logger.info("Statut de transaction mis à jour vers 'failed': %s", transaction.orange_id)
                
                # Ajouter un message dans la commande si elle existe
                if transaction.order_id:
                    message = f"Paiement Orange Money échoué - Transaction: {transaction.orange_id}"
                    transaction.order_id.message_post(body=message)
                    _logger.info("Message d'échec ajouté à la commande %s", transaction.order_id.name)
            
            _logger.info("Paiement Orange Money échoué traité pour la transaction: %s", transaction.orange_id)
                
        except Exception as e:
            _logger.error("Erreur lors du traitement du paiement échoué: %s", str(e))

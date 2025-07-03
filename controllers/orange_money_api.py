# # -*- coding: utf-8 -*-
# import json
# import logging
# import requests
# from datetime import datetime, timedelta
# from odoo import http, fields, _

# from odoo.exceptions import ValidationError, UserError, AccessError
# from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

# from odoo.http import request

# import json
# _logger = logging.getLogger(__name__)

# # Import du service adaptateur
# from ..services.orange_money_service_adapter import OrangeMoneyConfigService

# class OrangeMoneyAPI(http.Controller):
    

#     def _make_response(self, data, status):
#         return request.make_response(
#             json.dumps(data),
#             status=status,
#             headers={'Content-Type': 'application/json'}
#         )
    
#     def _get_orange_config(self):
#         """Récupérer la configuration Orange Money via le service"""
#         try:
#             return OrangeMoneyConfigService.get_config_for_api(request.env)
#         except Exception as e:
#             _logger.error("Erreur lors de la récupération de la configuration: %s", str(e))
#             raise UserError(_('Configuration Orange Money non disponible: %s') % str(e))


#     def _get_orange_config(self):
#         """Récupérer la configuration Orange Money"""
#         IrConfigParameter = request.env['ir.config_parameter'].sudo()
       
        
#         return {
#             'base_url': IrConfigParameter.get_param('orange_money.base_url', 'https://api.sandbox.orange-sonatel.com'),
#             'client_id': IrConfigParameter.get_param('orange_money.client_id'),
#             'client_secret': IrConfigParameter.get_param('orange_money.client_secret'),
#             'api_key': IrConfigParameter.get_param('orange_money.api_key'),
#             'merchant_code': IrConfigParameter.get_param('orange_money.merchant_code'),
#             'merchant_name': IrConfigParameter.get_param('orange_money.merchant_name'),
#             'callback_success_url': IrConfigParameter.get_param('orange_money.callback_success_url'),
#             'callback_cancel_url': IrConfigParameter.get_param('orange_money.callback_cancel_url'),
#         }
   
#     def _authenticate_user(self):
#         """Authentifier l'utilisateur via token ou session"""
#         try:
#             # Vérifier si l'utilisateur est connecté
#             if request.session.uid:
#                 return request.env.user
            
#             # Vérifier le token dans les headers
#             auth_header = request.httprequest.headers.get('Authorization')
#             if auth_header and auth_header.startswith('Bearer '):
#                 token = auth_header.split(' ')[1]
#                 # Ici vous pouvez implémenter votre logique de validation de token
#                 # Pour l'exemple, on utilise la session
#                 return request.env.user
            
#             return None
#         except Exception as e:
#             _logger.error("Erreur d'authentification: %s", str(e))
#             return None
    
#     def _validate_partner_access(self, partner_id):
#         """Valider l'accès du partenaire"""
#         try:
#             # Vérifier si l'utilisateur peut accéder aux données de ce partenaire
#             partner = request.env['res.partner'].sudo().browse(partner_id)
#             if not partner.exists():
#                 return False
#             return True
#         except Exception as e:
#             _logger.error("Erreur de validation d'accès: %s", str(e))
#             return False
    

#     @http.route('/api/orange_money/token', type='http', auth='*', methods=['POST'], csrf=False)
#     def get_orange_token_url(self, **kwargs):
#         """
#         Obtenir un token d'accès Orange Money
#         """
#         try:
#             config = self._get_orange_config()
            
#             if not all([config['client_id'], config['client_secret'], config['base_url']]):
#                 _logger.error("Configuration Orange Money incomplète")
#                 return self._make_response(
#                     {
#                         'success': False,
#                         'error': 'Configuration Orange Money incomplète'
#                     }, 400
#                 )

#             # Préparer les données d'authentification
#             auth_data = {
#                 'grant_type': 'client_credentials',
#                 'client_id': config['client_id'],
#                 'client_secret': config['client_secret']
#             }
            
#             headers = {
#                 'Content-Type': 'application/x-www-form-urlencoded',
#                 'Accept': 'application/json'
#             }
            
#             # Encoder les données
#             form_data = '&'.join([f"{k}={v}" for k, v in auth_data.items()])
            
#             # Faire la requête
#             response = requests.post(
#                 f"{config['base_url']}/oauth/v1/token",
#                 data=form_data,
#                 headers=headers,
#                 timeout=30
#             )
            
#             if response.status_code == 200:
#                 token_data = response.json()
#                 return self._make_response(
#                     {
#                         'success': True,
#                         'data': {
#                             'access_token': token_data.get('access_token'),
#                             'expires_in': token_data.get('expires_in', 3600),
#                             'token_type': token_data.get('token_type', 'Bearer')
#                         }
#                     }, 200
#                 )
               
#             else:
#                 _logger.error("Erreur d'obtention du token Orange Money: %s", response.text)
#                 return self._make_response(
#                     {
#                         'success': False,
#                         'error': f'Erreur d\'authentification: {response.status_code}'
#                     }, 400
#                 )

#         except Exception as e:
#             _logger.error("Erreur lors de l'obtention du token: %s", str(e))
#             return self._make_response(
#                 {
#                     'success': False,
#                     'error': str(e)
#                 }, 400
#             )

#     def get_orange_token(self, **kwargs):
#         """
#         Obtenir un token d'accès Orange Money
#         """
#         try:
#             config = self._get_orange_config()
#             _logger.info("🔧 Configuration Orange Money (debug): %s", json.dumps(config, indent=2))
#             if not all([config.get('client_id'), config.get('client_secret'), config.get('base_url')]):
#                 _logger.error("Configuration Orange Money incomplète")
#                 return {
#                     'success': False,
#                     'error': 'Configuration Orange Money incomplète'
#                 }

#             # Préparer les données d'authentification
#             auth_data = {
#                 'grant_type': 'client_credentials',
#                 'client_id': config['client_id'],
#                 'client_secret': config['client_secret']
#             }

#             headers = {
#                 'Content-Type': 'application/x-www-form-urlencoded',
#                 'Accept': 'application/json'
#             }

#             # Encoder les données
#             form_data = '&'.join([f"{k}={v}" for k, v in auth_data.items()])

#             # Faire la requête
#             response = requests.post(
#                 f"{config['base_url']}/oauth/v1/token",
#                 data=form_data,
#                 headers=headers,
#                 timeout=30
#             )

#             if response.status_code == 200:
#                 token_data = response.json()
#                 return {
#                     'success': True,
#                     'data': {
#                         'access_token': token_data.get('access_token'),
#                         'expires_in': token_data.get('expires_in', 3600),
#                         'token_type': token_data.get('token_type', 'Bearer')
#                     }
#                 }

#             else:
#                 _logger.error("Erreur d'obtention du token Orange Money: %s", response.text)
#                 return {
#                     'success': False,
#                     'error': f"Erreur d'authentification: {response.status_code}"
#                 }

#         except Exception as e:
#             _logger.error("Erreur lors de l'obtention du token: %s", str(e))
#             return {
#                 'success': False,
#                 'error': str(e)
#             }


#     @http.route('/api/orange_money/qrcode/generate', type='http', auth='*', methods=['POST'], csrf=False)
#     def generate_qr_code(self, **kwargs):
#         """
#         Générer un QR Code Orange Money
#         Paramètres attendus: amount, description, merchant_code, business_name, validity, partner_id , order
#         """

#         user = request.env['res.users'].sudo().browse(request.env.uid)
#         if not user or user._is_public():
#             admin_user = request.env.ref('base.user_admin')
#             request.env = request.env(user=admin_user.id)

#         try:
#             data = json.loads(request.httprequest.data)
            
#             # Validation des paramètres
#             required_fields = ['amount', 'description', 'partner_id']
#             for field in required_fields:
#                 if field not in data:
#                     return self._make_response( 
#                         {
#                             'success': False,
#                             'error': f'Champ requis manquant: {field}'
#                         }, 400
#                     )            
#             # Vérifier l'accès au partenaire
#             if not self._validate_partner_access(data['partner_id']):
#                 return self._make_response(
#                     {
#                         'success': False,
#                         'error': 'Accès non autorisé'
#                     }, 403
#                 )

#             order_id = data.get('order_id')
#             order = None
#             if order_id:
#                 order = request.env['sale.order'].sudo().browse(order_id)
#                 if not order.exists() or order.partner_id.id != data['partner_id']:
#                     return self._make_response(
#                         {
#                             'success': False,
#                             'error': 'Commande non trouvée ou accès non autorisé'
#                         }, 404
#                     )
#             partner = None
#             # Vérifier si un partenaire est fourni et s'il existe
#             if partner_id := data.get('partner_id'):
#                 partner = request.env['res.partner'].sudo().browse(partner_id)
#                 if not partner.exists():
#                     return self._make_response(
#                         {
#                             'success': False,
#                             'error': 'Partenaire non trouvé'
#                         }, 404
#                     )

#             # Obtenir la configuration
#             config = self._get_orange_config()
#             _logger.info("🔧 Configuration Orange Money (debug): %s", json.dumps(config, indent=2))
            
#             # Obtenir un token d'accès
#             token_response = self.get_orange_token()
#             if not token_response['success']:
#                 return self._make_response(token_response, 400)
            
#             token = token_response['data']['access_token']
            
#             # Préparer les données pour la génération du QR Code
#             merchant_code = config['merchant_code']
#             if not merchant_code or len(merchant_code) != 6:
#                 merchant_code = config['merchant_code'][:6].zfill(6)
            
#             qr_data = {
#                 'amount': {
#                     'unit': 'XOF',
#                     'value': float(data['amount'])
#                 },
#                 'callbackCancelUrl': config['callback_cancel_url'],
#                 'callbackSuccessUrl': config['callback_success_url'],
#                 'code': merchant_code,
#                 'metadata': {
#                     'description': data['description'],
#                     'partner_id': str(data['partner_id']),
#                     'commande': order.name if order else 'N/A',
#                     'reference': f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
#                 },
#                 # 'name': data.get('business_name', config['merchant_name']),
#                 'name': config['merchant_name'],
#                 'validity': min(int(data.get('validity', 300)), 86400)
#             }
            
#             headers = {
#                 'Content-Type': 'application/json',
#                 'Accept': 'application/json',
#                 'Authorization': f'Bearer {token}',
#                 'X-Api-Key': config['api_key']
#             }
            
#             # Générer le QR Code
#             response = requests.post(
#                 f"{config['base_url']}/api/eWallet/v4/qrcode",
#                 json=qr_data,
#                 headers=headers,
#                 timeout=30
#             )
            
#             if response.status_code in [200, 201]:
#                 qr_response = response.json()
                
#                 # Créer une transaction dans Odoo
#                 transaction_data = {
#                     'orange_id': qr_response.get('transactionId', ''),
#                     'amount': float(data['amount']),
#                     'phone': partner.phone if partner else '',
#                     'status': 'pending',
#                     'reference': qr_data['metadata']['reference'],
#                     'currency': 'XOF',
#                     'callback_data': json.dumps(qr_response),
#                     'date': fields.Datetime.now(),
#                     'order_id' : order.id if order else False,
#                 }

#                 # Créer la transaction
#                 transaction = request.env['orange.money.transaction'].sudo().create(transaction_data)
                

#                 return self._make_response(
#                     {
#                         'success': True,
#                         'data': {
#                             'qr_code': qr_response.get('qrCode'),
#                             'transaction_id': qr_response.get('transactionId'),
#                             'odoo_transaction_id': transaction.id,
#                             'reference': qr_data['metadata']['reference'],
#                             'validity': qr_data['validity'],
#                             'amount': qr_data['amount'],
#                             'deeplinks': qr_response.get('deeplinks', {})
#                         }
#                     }, 200
#                 )
#             else:
#                 _logger.error("Erreur de génération QR Code: %s", response.text)
#                 return self._make_response(
#                     {
#                         'success': False,
#                         'error': f'Erreur de génération: {response.status_code}'
#                     }, response.status_code
#                 )

#         except Exception as e:
#             _logger.error("Erreur lors de la génération du QR Code: %s", str(e))
#             return self._make_response(
#                 {
#                     'success': False,
#                     'error': str(e)
#                 }, 400
#             )

#     @http.route('/api/orange_money/transaction/create', type='http', auth='*', methods=['POST'], csrf=False)
#     def create_transaction(self, **kwargs):
#         """
#         Créer une nouvelle transaction Orange Money
#         """
#         try:
#             data = request.jsonrequest or {}
            
#             # Validation des paramètres
#             required_fields = ['amount', 'partner_id', 'order_id']
#             for field in required_fields:
#                 if field not in data:
#                     return {
#                         'success': False,
#                         'error': f'Champ requis manquant: {field}'
#                     }
            
#             order_id = data.get('order_id')
#             order = None
#             if order_id:
#                 order = request.env['sale.order'].sudo().browse(order_id)
#                 if not order.exists() or order.partner_id.id != data['partner_id']:
#                     return {
#                         'success': False,
#                         'error': 'Commande non trouvée ou accès non autorisé'
#                     }
                
#             partner = None
#             partner_id = data.get('partner_id')
#             if partner_id:
#                 partner = request.env['res.partner'].sudo().browse(partner_id)
#                 if not partner.exists():
#                     return {
#                         'success': False,
#                         'error': 'Partenaire non trouvé'
#                     }

#             # Préparer les données de la transaction
#             transaction_data = {
#                 'orange_id': data.get('orange_id', ''),
#                 'amount': float(data['amount']),
#                 'phone': partner.phone if partner else '',
#                 'status': data.get('status', 'pending'),
#                 'reference': data.get('reference', f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
#                 'currency': data.get('currency', 'XOF'),
#                 'date': fields.Datetime.now(),
#                 'order_id': order.id if order else False
#             }
            
#             # Créer la transaction
#             transaction = request.env['orange.money.transaction'].sudo().create(transaction_data)
            
#             return {
#                 'success': True,
#                 'data': {
#                     'id': transaction.id,
#                     'orange_id': transaction.orange_id,
#                     'amount': transaction.amount,
#                     'status': transaction.status,
#                     'reference': transaction.reference,
#                     'date': transaction.date.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if transaction.date else None
#                 }
#             }
            
#         except Exception as e:
#             _logger.error("Erreur lors de la création de transaction: %s", str(e))
#             return {
#                 'success': False,
#                 'error': str(e)
#             }
    
#     @http.route('/api/orange_money/transaction/update/<int:transaction_id>', type='http', auth='*', methods=['PUT'], csrf=False)
#     def update_transaction(self, transaction_id, **kwargs):
#         """
#         Mettre à jour une transaction Orange Money
#         """
#         try:
#             data = request.jsonrequest or {}
            
#             # Récupérer la transaction
#             transaction = request.env['orange.money.transaction'].sudo().browse(transaction_id)
#             if not transaction.exists():
#                 return {
#                     'success': False,
#                     'error': 'Transaction non trouvée'
#                 }
            
#             # Vérifier l'accès (via la commande liée ou directement)
#             partner_id = None
#             if transaction.order_id:
#                 partner_id = transaction.order_id.partner_id.id
#             elif data.get('partner_id'):
#                 partner_id = data['partner_id']
            
#             if not partner_id :
#                 return {
#                     'success': False,
#                     'error': 'Accès non autorisé'
#                 }
            
#             # Préparer les données de mise à jour
#             update_data = {}
#             updatable_fields = ['orange_id', 'amount', 'phone', 'status', 'reference', 'currency']
            
#             for field in updatable_fields:
#                 if field in data:
#                     if field == 'amount':
#                         update_data[field] = float(data[field])
#                     else:
#                         update_data[field] = data[field]
            
#             # Mettre à jour la transaction
#             if update_data:
#                 transaction.write(update_data)

#             return {
#                 'success': True,
#                 'data': {
#                     'id': transaction.id,
#                     'orange_id': transaction.orange_id,
#                     'amount': transaction.amount,
#                     'status': transaction.status,
#                     'reference': transaction.reference,
#                     'date': transaction.date.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if transaction.date else None
#                 }
#             }
            
#         except Exception as e:
#             _logger.error("Erreur lors de la mise à jour de transaction: %s", str(e))
#             return {
#                 'success': False,
#                 'error': str(e)
#             }
    
#     @http.route('/api/orange_money/transactions/<int:partner_id>', type='http', auth='*', methods=['GET'], csrf=False)
#     def get_partner_transactions(self, partner_id, **kwargs):
#         """
#         Récupérer la liste des transactions d'un partenaire
#         """
#         try:
#             # Vérifier l'accès au partenaire
#             if not self._validate_partner_access(partner_id):
#                 return {
#                     'success': False,
#                     'error': 'Accès non autorisé'
#                 }
            
#             # Paramètres de pagination et filtrage
#             params = request.httprequest.args
#             limit = int(params.get('limit', 20))
#             offset = int(params.get('offset', 0))
#             status_filter = params.get('status')
#             date_from = params.get('date_from')
#             date_to = params.get('date_to')
            
#             # Construire le domaine de recherche
#             domain = []
            
#             # Filtrer par partenaire via les commandes liées
#             orders = request.env['sale.order'].sudo().search([('partner_id', '=', partner_id)])
#             if orders:
#                 domain.append(('order_id', 'in', orders.ids))
#             else:
#                 # Si pas de commandes, retourner une liste vide
#                 return {
#                     'success': True,
#                     'data': {
#                         'transactions': [],
#                         'total': 0,
#                         'limit': limit,
#                         'offset': offset
#                     }
#                 }
            
#             # Filtres additionnels
#             if status_filter:
#                 domain.append(('status', '=', status_filter))
            
#             if date_from:
#                 domain.append(('date', '>=', date_from))
            
#             if date_to:
#                 domain.append(('date', '<=', date_to))
            
#             # Récupérer les transactions
#             transactions = request.env['orange.money.transaction'].sudo().search(
#                 domain, 
#                 limit=limit, 
#                 offset=offset, 
#                 order='date desc'
#             )
            
#             # Compter le total
#             total = request.env['orange.money.transaction'].sudo().search_count(domain)
            
#             # Formater les données
#             transaction_data = []
#             for transaction in transactions:
#                 transaction_data.append({
#                     'id': transaction.id,
#                     'orange_id': transaction.orange_id,
#                     'amount': transaction.amount,
#                     'currency': transaction.currency,
#                     'phone': transaction.phone,
#                     'status': transaction.status,
#                     'reference': transaction.reference,
#                     'date': transaction.date.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if transaction.date else None,
#                     'created_at': transaction.created_at.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if transaction.created_at else None,
#                     'order_id': transaction.order_id.id if transaction.order_id else None,
#                     'order_name': transaction.order_id.name if transaction.order_id else None,
#                     'order_state': transaction.order_state,
#                     'customer_name': transaction.customer_id.name if transaction.customer_id else None
#                 })
            
#             return {
#                 'success': True,
#                 'data': {
#                     'transactions': transaction_data,
#                     'total': total,
#                     'limit': limit,
#                     'offset': offset
#                 }
#             }
            
#         except Exception as e:
#             _logger.error("Erreur lors de la récupération des transactions: %s", str(e))
#             return {
#                 'success': False,
#                 'error': str(e)
#             }
    
#     @http.route('/api/orange_money/transaction/<int:transaction_id>', type='http', auth='*', methods=['GET'], csrf=False)
#     def get_transaction(self, transaction_id, **kwargs):
#         """
#         Récupérer une transaction spécifique
#         """
#         try:
#             transaction = request.env['orange.money.transaction'].sudo().browse(transaction_id)
#             if not transaction.exists():
#                 return {
#                     'success': False,
#                     'error': 'Transaction non trouvée'
#                 }
            
#             # Vérifier l'accès
#             partner_id = transaction.order_id.partner_id.id if transaction.order_id else None
#             if partner_id and not self._validate_partner_access(partner_id):
#                 return {
#                     'success': False,
#                     'error': 'Accès non autorisé'
#                 }
            
#             return {
#                 'success': True,
#                 'data': {
#                     'id': transaction.id,
#                     'orange_id': transaction.orange_id,
#                     'amount': transaction.amount,
#                     'currency': transaction.currency,
#                     'phone': transaction.phone,
#                     'status': transaction.status,
#                     'reference': transaction.reference,
#                     'date': transaction.date.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if transaction.date else None,
#                     'created_at': transaction.created_at.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if transaction.created_at else None,
#                     'order_id': transaction.order_id.id if transaction.order_id else None,
#                     'order_name': transaction.order_id.name if transaction.order_id else None,
#                     'order_state': transaction.order_state,
#                     'customer_name': transaction.customer_id.name if transaction.customer_id else None,
#                     'callback_data': transaction.callback_data
#                 }
#             }
            
#         except Exception as e:
#             _logger.error("Erreur lors de la récupération de la transaction: %s", str(e))
#             return {
#                 'success': False,
#                 'error': str(e)
#             }
    
#     @http.route('/api/orange_money/transaction/status/<string:orange_id>', type='http', auth='*', methods=['GET'], csrf=False)
#     def check_transaction_status(self, orange_id, **kwargs):
#         """
#         Vérifier le statut d'une transaction via l'API Orange Money
#         """
#         try:
#             config = self._get_orange_config()
            
#             # Obtenir un token d'accès
#             token_response = self.get_orange_token()
#             if not token_response['success']:
#                 return token_response
            
#             token = token_response['data']['access_token']
            
#             # Vérifier le statut via l'API Orange Money
#             headers = {
#                 'Accept': 'application/json',
#                 'Authorization': f'Bearer {token}',
#                 'X-Api-Key': config['api_key']
#             }
            
#             response = requests.get(
#                 f"{config['base_url']}/api/eWallet/v1/transactions/{orange_id}/status",
#                 headers=headers,
#                 timeout=30
#             )
            
#             if response.status_code == 200:
#                 status_data = response.json()
#                 orange_status = status_data.get('status')
                
#                 # Mapper le statut
#                 status_mapping = {
#                     'SUCCESS': 'completed',
#                     'SUCCESSFUL': 'completed',
#                     'FAILED': 'failed',
#                     'CANCELLED': 'failed',
#                     'EXPIRED': 'failed',
#                     'PENDING': 'pending',
#                     'ACCEPTED': 'pending',
#                     'REJECTED': 'failed',
#                 }
                
#                 mapped_status = status_mapping.get(orange_status, 'pending')
                
#                 # Mettre à jour la transaction locale si elle existe
#                 transaction = request.env['orange.money.transaction'].sudo().search([
#                     ('orange_id', '=', orange_id)
#                 ], limit=1)
                
#                 if transaction and transaction.status != mapped_status:
#                     transaction.write({'status': mapped_status})
                
#                 return {
#                     'success': True,
#                     'data': {
#                         'orange_status': orange_status,
#                         'mapped_status': mapped_status,
#                         'transaction_id': orange_id,
#                         'updated_locally': bool(transaction)
#                     }
#                 }
#             else:
#                 return {
#                     'success': False,
#                     'error': f'Erreur de vérification: {response.status_code}'
#                 }
                
#         except Exception as e:
#             _logger.error("Erreur lors de la vérification du statut: %s", str(e))
#             return {
#                 'success': False,
#                 'error': str(e)
#             }
    
#     @http.route('/api/orange_money/stats/<int:partner_id>', type='http', auth='*', methods=['GET'], csrf=False)
#     def get_partner_stats(self, partner_id, **kwargs):
#         """
#         Récupérer les statistiques des transactions d'un partenaire
#         """
#         try:
#             # Vérifier l'accès au partenaire
#             if not self._validate_partner_access(partner_id):
#                 return {
#                     'success': False,
#                     'error': 'Accès non autorisé'
#                 }
            
#             # Récupérer les commandes du partenaire
#             orders = request.env['sale.order'].sudo().search([('partner_id', '=', partner_id)])
            
#             if not orders:
#                 return {
#                     'success': True,
#                     'data': {
#                         'total_transactions': 0,
#                         'total_amount': 0,
#                         'pending_count': 0,
#                         'completed_count': 0,
#                         'failed_count': 0,
#                         'pending_amount': 0,
#                         'completed_amount': 0,
#                         'failed_amount': 0
#                     }
#                 }
            
#             # Récupérer les transactions
#             transactions = request.env['orange.money.transaction'].sudo().search([
#                 ('order_id', 'in', orders.ids)
#             ])
            
#             # Calculer les statistiques
#             stats = {
#                 'total_transactions': len(transactions),
#                 'total_amount': sum(transactions.mapped('amount')),
#                 'pending_count': len(transactions.filtered(lambda t: t.status == 'pending')),
#                 'completed_count': len(transactions.filtered(lambda t: t.status == 'completed')),
#                 'failed_count': len(transactions.filtered(lambda t: t.status == 'failed')),
#                 'pending_amount': sum(transactions.filtered(lambda t: t.status == 'pending').mapped('amount')),
#                 'completed_amount': sum(transactions.filtered(lambda t: t.status == 'completed').mapped('amount')),
#                 'failed_amount': sum(transactions.filtered(lambda t: t.status == 'failed').mapped('amount'))
#             }
            
#             return {
#                 'success': True,
#                 'data': stats
#             }
            
#         except Exception as e:
#             _logger.error("Erreur lors de la récupération des statistiques: %s", str(e))
#             return {
#                 'success': False,
#                 'error': str(e)
#             }
    
#     @http.route('/api/orange_money/config', type='http', auth='*', methods=['GET'], csrf=False)
#     def get_config(self, **kwargs):
#         """
#         Récupérer la configuration publique Orange Money
#         """
#         try:
#             config = self._get_orange_config()
            
#             # Retourner seulement les informations publiques
#             public_config = {
#                 'merchant_name': config['merchant_name'],
#                 'merchant_code': config['merchant_code'],
#                 'callback_success_url': config['callback_success_url'],
#                 'callback_cancel_url': config['callback_cancel_url'],
#                 'currency': 'XOF',
#                 'default_validity': config['default_validity'],
#                 'max_validity': config['max_validity']
#             }
            
#             return {
#                 'success': True,
#                 'data': public_config
#             }
            
#         except Exception as e:
#             _logger.error("Erreur lors de la récupération de la configuration: %s", str(e))
#             return {
#                 'success': False,
#                 'error': str(e)
#             }

# -*- coding: utf-8 -*-
import json
import logging
import requests
from datetime import datetime, timedelta
from odoo import http, fields, _
from odoo.exceptions import ValidationError, UserError, AccessError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.http import request

_logger = logging.getLogger(__name__)

class OrangeMoneyAPI(http.Controller):
    
    def _make_response(self, data, status=200):
        """Créer une réponse HTTP JSON"""
        return request.make_response(
            json.dumps(data, ensure_ascii=False, indent=2),
            status=status,
            headers={
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With'
            }
        )
    
    def _get_orange_config(self):
        """Récupérer la configuration Orange Money"""
        try:
            # Utiliser sudo() pour éviter les problèmes de permissions
            IrConfigParameter = request.env['ir.config_parameter'].sudo()
            
            config = {
                'base_url': IrConfigParameter.get_param('orange_money.base_url', 'https://api.sandbox.orange-sonatel.com'),
                'client_id': IrConfigParameter.get_param('orange_money.client_id'),
                'client_secret': IrConfigParameter.get_param('orange_money.client_secret'),
                'api_key': IrConfigParameter.get_param('orange_money.api_key'),
                'merchant_code': IrConfigParameter.get_param('orange_money.merchant_code'),
                'merchant_name': IrConfigParameter.get_param('orange_money.merchant_name'),
                'callback_success_url': IrConfigParameter.get_param('orange_money.callback_success_url'),
                'callback_cancel_url': IrConfigParameter.get_param('orange_money.callback_cancel_url'),
            }
            
            return config
        except Exception as e:
            _logger.error("Erreur lors de la récupération de la configuration: %s", str(e))
            raise UserError(_('Configuration Orange Money non disponible: %s') % str(e))

    def _ensure_authenticated_env(self):
        """S'assurer que l'environnement est authentifié"""
        try:
            # Si pas d'utilisateur connecté, utiliser l'utilisateur admin
            if not request.env.user or request.env.user._is_public():
                admin_user = request.env.ref('base.user_admin')
                request.env = request.env(user=admin_user.id)
            return True
        except Exception as e:
            _logger.error("Erreur d'authentification: %s", str(e))
            return False

    def _validate_partner_access(self, partner_id):
        """Valider l'accès du partenaire - Version simplifiée"""
        try:
            partner = request.env['res.partner'].sudo().browse(partner_id)
            return partner.exists()
        except Exception as e:
            _logger.error("Erreur de validation d'accès: %s", str(e))
            return False

    @http.route('/api/orange_money/token', type='http', auth='public', methods=['POST'], csrf=False, cors='*')
    def get_orange_token_url(self, **kwargs):
        """Obtenir un token d'accès Orange Money"""
        try:
            # S'assurer de l'authentification
            self._ensure_authenticated_env()
            
            config = self._get_orange_config()
            
            if not all([config['client_id'], config['client_secret'], config['base_url']]):
                _logger.error("Configuration Orange Money incomplète")
                return self._make_response({
                    'success': False,
                    'error': 'Configuration Orange Money incomplète'
                }, 400)

            # Préparer les données d'authentification
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': config['client_id'],
                'client_secret': config['client_secret']
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            # Encoder les données
            form_data = '&'.join([f"{k}={v}" for k, v in auth_data.items()])
            
            # Faire la requête
            response = requests.post(
                f"{config['base_url']}/oauth/v1/token",
                data=form_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                return self._make_response({
                    'success': True,
                    'data': {
                        'access_token': token_data.get('access_token'),
                        'expires_in': token_data.get('expires_in', 3600),
                        'token_type': token_data.get('token_type', 'Bearer')
                    }
                })
            else:
                _logger.error("Erreur d'obtention du token Orange Money: %s", response.text)
                return self._make_response({
                    'success': False,
                    'error': f'Erreur d\'authentification: {response.status_code}'
                }, 400)

        except Exception as e:
            _logger.error("Erreur lors de l'obtention du token: %s", str(e))
            return self._make_response({
                'success': False,
                'error': str(e)
            }, 500)

    def get_orange_token(self):
        """Version interne pour obtenir un token"""
        try:
            config = self._get_orange_config()
            
            if not all([config.get('client_id'), config.get('client_secret'), config.get('base_url')]):
                return {
                    'success': False,
                    'error': 'Configuration Orange Money incomplète'
                }

            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': config['client_id'],
                'client_secret': config['client_secret']
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }

            form_data = '&'.join([f"{k}={v}" for k, v in auth_data.items()])

            response = requests.post(
                f"{config['base_url']}/oauth/v1/token",
                data=form_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                token_data = response.json()
                return {
                    'success': True,
                    'data': {
                        'access_token': token_data.get('access_token'),
                        'expires_in': token_data.get('expires_in', 3600),
                        'token_type': token_data.get('token_type', 'Bearer')
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur d'authentification: {response.status_code}"
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/orange_money/qrcode/generate', type='http', auth='public', methods=['POST'], csrf=False, cors='*')
    def generate_qr_code(self, **kwargs):
        """Générer un QR Code Orange Money"""
        try:
            # S'assurer de l'authentification
            self._ensure_authenticated_env()
            
            # Lire les données JSON
            try:
                if request.httprequest.data:
                    data = json.loads(request.httprequest.data.decode('utf-8'))
                else:
                    data = request.params
            except json.JSONDecodeError:
                return self._make_response({
                    'success': False,
                    'error': 'Données JSON invalides'
                }, 400)
            
            # Validation des paramètres
            required_fields = ['amount', 'description', 'partner_id']
            for field in required_fields:
                if field not in data:
                    return self._make_response({
                        'success': False,
                        'error': f'Champ requis manquant: {field}'
                    }, 400)

            # Vérifier l'accès au partenaire
            if not self._validate_partner_access(data['partner_id']):
                return self._make_response({
                    'success': False,
                    'error': 'Partenaire non trouvé'
                }, 404)

            # Récupérer la commande si fournie
            order = None
            order_id = data.get('order_id')
            if order_id:
                order = request.env['sale.order'].sudo().browse(order_id)
                if not order.exists():
                    return self._make_response({
                        'success': False,
                        'error': 'Commande non trouvée'
                    }, 404)

            # Récupérer le partenaire
            partner = request.env['res.partner'].sudo().browse(data['partner_id'])
            if not partner.exists():
                return self._make_response({
                    'success': False,
                    'error': 'Partenaire non trouvé'
                }, 404)

            # Obtenir la configuration
            config = self._get_orange_config()
            
            # Obtenir un token d'accès
            token_response = self.get_orange_token()
            if not token_response['success']:
                return self._make_response(token_response, 400)
            
            token = token_response['data']['access_token']
            
            # Préparer les données pour la génération du QR Code
            merchant_code = config['merchant_code']
            if merchant_code and len(merchant_code) > 6:
                merchant_code = merchant_code[:6]
            elif merchant_code and len(merchant_code) < 6:
                merchant_code = merchant_code.zfill(6)
            
            qr_data = {
                'amount': {
                    'unit': 'XOF',
                    'value': float(data['amount'])
                },
                'callbackCancelUrl': config['callback_cancel_url'],
                'callbackSuccessUrl': config['callback_success_url'],
                'code': merchant_code,
                'metadata': {
                    'description': data['description'],
                    'partner_id': str(data['partner_id']),
                    'commande': order.name if order else 'N/A',
                    'reference': f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                },
                'name': config['merchant_name'],
                'validity': min(int(data.get('validity', 300)), 86400)
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {token}',
                'X-Api-Key': config['api_key']
            }
            
            # Générer le QR Code
            response = requests.post(
                f"{config['base_url']}/api/eWallet/v4/qrcode",
                json=qr_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                qr_response = response.json()
                
                # Créer une transaction dans Odoo
                transaction_data = {
                    'orange_id': qr_response.get('transactionId', ''),
                    'amount': float(data['amount']),
                    'phone': partner.phone if partner else '',
                    'status': 'pending',
                    'reference': qr_data['metadata']['reference'],
                    'currency': 'XOF',
                    'callback_data': json.dumps(qr_response),
                    'date': fields.Datetime.now(),
                    'order_id': order.id if order else False,
                }

                transaction = request.env['orange.money.transaction'].sudo().create(transaction_data)

                return self._make_response({
                    'success': True,
                    'data': {
                        'qr_code': qr_response.get('qrCode'),
                        'transaction_id': qr_response.get('transactionId'),
                        'odoo_transaction_id': transaction.id,
                        'reference': qr_data['metadata']['reference'],
                        'validity': qr_data['validity'],
                        'amount': qr_data['amount'],
                        'deeplinks': qr_response.get('deeplinks', {})
                    }
                })
            else:
                _logger.error("Erreur de génération QR Code: %s", response.text)
                return self._make_response({
                    'success': False,
                    'error': f'Erreur de génération: {response.status_code}',
                    'details': response.text
                }, response.status_code)

        except Exception as e:
            _logger.error("Erreur lors de la génération du QR Code: %s", str(e))
            return self._make_response({
                'success': False,
                'error': str(e)
            }, 500)

    @http.route('/api/orange_money/transactions/<int:partner_id>', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_partner_transactions(self, partner_id, **kwargs):
        """Récupérer la liste des transactions d'un partenaire"""
        try:
            # S'assurer de l'authentification
            self._ensure_authenticated_env()
            
            # Vérifier l'accès au partenaire
            if not self._validate_partner_access(partner_id):
                return self._make_response({
                    'success': False,
                    'error': 'Partenaire non trouvé'
                }, 404)
            
            # Paramètres de pagination et filtrage
            params = request.httprequest.args
            limit = int(params.get('limit', 20))
            offset = int(params.get('offset', 0))
            status_filter = params.get('status')
            
            # Construire le domaine de recherche
            domain = []
            
            # Filtrer par partenaire via les commandes liées
            orders = request.env['sale.order'].sudo().search([('partner_id', '=', partner_id)])
            if orders:
                domain.append(('order_id', 'in', orders.ids))
            else:
                return self._make_response({
                    'success': True,
                    'data': {
                        'transactions': [],
                        'total': 0,
                        'limit': limit,
                        'offset': offset
                    }
                })
            
            # Filtres additionnels
            if status_filter:
                domain.append(('status', '=', status_filter))
            
            # Récupérer les transactions
            transactions = request.env['orange.money.transaction'].sudo().search(
                domain, 
                limit=limit, 
                offset=offset, 
                order='date desc'
            )
            
            # Compter le total
            total = request.env['orange.money.transaction'].sudo().search_count(domain)
            
            # Formater les données
            transaction_data = []
            for transaction in transactions:
                transaction_data.append({
                    'id': transaction.id,
                    'orange_id': transaction.orange_id,
                    'amount': transaction.amount,
                    'currency': transaction.currency,
                    'phone': transaction.phone,
                    'status': transaction.status,
                    'reference': transaction.reference,
                    'date': transaction.date.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if transaction.date else None,
                    'order_id': transaction.order_id.id if transaction.order_id else None,
                    'order_name': transaction.order_id.name if transaction.order_id else None,
                })
            
            return self._make_response({
                'success': True,
                'data': {
                    'transactions': transaction_data,
                    'total': total,
                    'limit': limit,
                    'offset': offset
                }
            })
            
        except Exception as e:
            _logger.error("Erreur lors de la récupération des transactions: %s", str(e))
            return self._make_response({
                'success': False,
                'error': str(e)
            }, 500)

    @http.route('/api/orange_money/config', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_config(self, **kwargs):
        """Récupérer la configuration publique Orange Money"""
        try:
            # S'assurer de l'authentification
            self._ensure_authenticated_env()
            
            config = self._get_orange_config()
            
            # Retourner seulement les informations publiques
            public_config = {
                'merchant_name': config.get('merchant_name', ''),
                'merchant_code': config.get('merchant_code', ''),
                'callback_success_url': config.get('callback_success_url', ''),
                'callback_cancel_url': config.get('callback_cancel_url', ''),
                'currency': 'XOF'
            }
            
            return self._make_response({
                'success': True,
                'data': public_config
            })
            
        except Exception as e:
            _logger.error("Erreur lors de la récupération de la configuration: %s", str(e))
            return self._make_response({
                'success': False,
                'error': str(e)
            }, 500)

    # Route OPTIONS pour CORS
    @http.route([
        '/api/orange_money/token',
        '/api/orange_money/qrcode/generate',
        '/api/orange_money/transactions/<int:partner_id>',
        '/api/orange_money/config'
    ], type='http', auth='public', methods=['OPTIONS'], csrf=False, cors='*')
    def options_handler(self, **kwargs):
        """Gérer les requêtes OPTIONS pour CORS"""
        return self._make_response({'success': True})

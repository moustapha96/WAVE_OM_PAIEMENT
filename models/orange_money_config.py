# # -*- coding: utf-8 -*-
# from odoo import models, fields, api, _
# from odoo.exceptions import UserError, ValidationError
# import requests
# import logging

# _logger = logging.getLogger(__name__)

# class OrangeMoneyConfig(models.Model):
#     _name = 'orange.money.config'
#     _description = 'Configuration Orange Money'
#     _rec_name = 'merchant_name'

#     # Informations générales
#     active = fields.Boolean(string='Actif', default=True)
#     merchant_name = fields.Char(string='Nom du Marchand', required=True, default='CCBM SHOP')
#     merchant_code = fields.Char(string='Code Marchand', required=True, size=6, default='123456')
#     test_mode = fields.Boolean(string='Mode Test', default=True)

#     # Configuration API Orange Money
#     orange_base_url = fields.Char(
#         string='URL de base Orange Money', 
#         required=True, 
#         default='https://api.sandbox.orange-sonatel.com'
#     )
#     orange_client_id = fields.Char(string='Client ID Orange Money')
#     orange_client_secret = fields.Char(string='Client Secret Orange Money')
#     orange_api_key = fields.Char(string='Clé API Orange Money')

#     # Configuration Webhook
#     webhook_url = fields.Char(string='URL du Webhook')
#     webhook_api_key = fields.Char(string='Clé API Webhook')

#     # URLs de callback
#     callback_success_url = fields.Char(
#         string='URL de succès', 
#         default='https://your-domain.com/payment/success'
#     )
#     callback_cancel_url = fields.Char(
#         string='URL d\'annulation', 
#         default='https://your-domain.com/payment/cancel'
#     )

#     # Paramètres de transaction
#     default_validity = fields.Integer(string='Validité par défaut (secondes)', default=300)
#     max_validity = fields.Integer(string='Validité maximale (secondes)', default=86400)

#     # Informations de test
#     last_test_date = fields.Datetime(string='Dernière date de test', readonly=True)
#     last_test_result = fields.Text(string='Résultat du dernier test', readonly=True)

#     # Contrainte SQL pour n'avoir qu'une seule configuration active
#     _sql_constraints = [
#         ('unique_active_config', 
#          'EXCLUDE (active WITH =) WHERE (active = true)', 
#          'Une seule configuration Orange Money peut être active à la fois!')
#     ]

#     @api.model
#     def create(self, vals):
#         """Surcharge pour gérer l'unicité de la configuration active"""
#         if vals.get('active', False):
#             # Désactiver toutes les autres configurations
#             existing_configs = self.search([('active', '=', True)])
#             if existing_configs:
#                 existing_configs.write({'active': False})
        
#         return super(OrangeMoneyConfig, self).create(vals)

#     def write(self, vals):
#         """Surcharge pour gérer l'unicité de la configuration active"""
#         if vals.get('active', False):
#             # Désactiver toutes les autres configurations
#             other_configs = self.search([('active', '=', True), ('id', 'not in', self.ids)])
#             if other_configs:
#                 other_configs.write({'active': False})
        
#         return super(OrangeMoneyConfig, self).write(vals)

#     def unlink(self):
#         """Permettre la suppression avec confirmation"""
#         for record in self:
#             if record.active:
#                 raise UserError(_(
#                     'Impossible de supprimer la configuration active "%s". '
#                     'Veuillez d\'abord la désactiver ou créer une nouvelle configuration active.'
#                 ) % record.merchant_name)
        
#         return super(OrangeMoneyConfig, self).unlink()

#     @api.constrains('active')
#     def _check_active_config(self):
#         """Vérifier qu'il y a au moins une configuration active"""
#         active_configs = self.search([('active', '=', True)])
#         if not active_configs:
#             raise ValidationError(_('Au moins une configuration Orange Money doit être active.'))

#     @api.constrains('orange_client_id', 'orange_client_secret', 'orange_api_key')
#     def _check_api_credentials(self):
#         """Vérifier que les identifiants API sont renseignés pour une config active"""
#         for record in self:
#             if record.active:
#                 if not record.orange_client_id:
#                     raise ValidationError(_('Le Client ID Orange Money est obligatoire pour une configuration active.'))
#                 if not record.orange_client_secret:
#                     raise ValidationError(_('Le Client Secret Orange Money est obligatoire pour une configuration active.'))
#                 if not record.orange_api_key:
#                     raise ValidationError(_('La Clé API Orange Money est obligatoire pour une configuration active.'))

#     @api.model
#     def get_config(self):
#         """Récupérer la configuration active"""
#         config = self.search([('active', '=', True)], limit=1)
#         if not config:
#             raise UserError(_('Aucune configuration Orange Money active trouvée.'))
#         return config

#     def action_activate(self):
#         """Action pour activer cette configuration"""
#         self.ensure_one()
#         if not self.active:
#             self.write({'active': True})
#         return {
#             'type': 'ir.actions.client',
#             'tag': 'display_notification',
#             'params': {
#                 'title': '✅ Configuration activée',
#                 'message': f'La configuration "{self.merchant_name}" est maintenant active.',
#                 'type': 'success',
#             }
#         }

#     def action_duplicate(self):
#         """Action pour dupliquer la configuration"""
#         self.ensure_one()
#         new_config = self.copy({
#             'merchant_name': f"{self.merchant_name} (Copie)",
#             'active': False,
#         })
#         return {
#             'type': 'ir.actions.act_window',
#             'name': 'Configuration dupliquée',
#             'res_model': 'orange.money.config',
#             'res_id': new_config.id,
#             'view_mode': 'form',
#             'target': 'current',
#         }

#     # Méthodes de test (inchangées)
#     def action_generate_test_token(self):
#         """Générer un token de test"""
#         self.ensure_one()
#         self._check_api_credentials()
        
#         try:
#             token = self._get_orange_access_token()

#             result = f"✅ TOKEN GÉNÉRÉ AVEC SUCCÈS\n"
#             result += f"Token: {token[:30]}...\n"
#             result += f"Date: {fields.Datetime.now()}\n"

#             self.write({
#                 'last_test_date': fields.Datetime.now(),
#                 'last_test_result': result
#             })

#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'display_notification',
#                 'params': {
#                     'title': '✅ Token généré',
#                     'message': 'Token d\'accès généré avec succès!',
#                     'type': 'success',
#                 }
#             }

#         except Exception as e:
#             error_result = f"❌ ERREUR GÉNÉRATION TOKEN\n"
#             error_result += f"Erreur: {str(e)}\n"
#             error_result += f"Date: {fields.Datetime.now()}\n"

#             self.write({
#                 'last_test_date': fields.Datetime.now(),
#                 'last_test_result': error_result
#             })

#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'display_notification',
#                 'params': {
#                     'title': '❌ Erreur Token',
#                     'message': str(e),
#                     'type': 'danger',
#                 }
#             }

#     def action_test_qr_generation(self):
#         """Tester la génération de QR code"""
#         self.ensure_one()
#         self._check_api_credentials()
        
#         try:
#             token = self._get_orange_access_token()
#             qr_result = self._test_qr_generation(token)

#             result = f"✅ QR CODE GÉNÉRÉ AVEC SUCCÈS\n"
#             result += f"Transaction ID: {qr_result['response'].get('transactionId', 'N/A')}\n"
#             result += f"Montant test: 100 XOF\n"
#             result += f"Date: {fields.Datetime.now()}\n"

#             self.write({
#                 'last_test_date': fields.Datetime.now(),
#                 'last_test_result': result
#             })

#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'display_notification',
#                 'params': {
#                     'title': '✅ QR Code généré',
#                     'message': 'QR Code de test généré avec succès!',
#                     'type': 'success',
#                 }
#             }

#         except Exception as e:
#             error_result = f"❌ ERREUR GÉNÉRATION QR CODE\n"
#             error_result += f"Erreur: {str(e)}\n"
#             error_result += f"Date: {fields.Datetime.now()}\n"

#             self.write({
#                 'last_test_date': fields.Datetime.now(),
#                 'last_test_result': error_result
#             })

#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'display_notification',
#                 'params': {
#                     'title': '❌ Erreur QR Code',
#                     'message': str(e),
#                     'type': 'danger',
#                 }
#             }

#     def action_test_configuration(self):
#         """Test complet de la configuration"""
#         self.ensure_one()
#         self._check_api_credentials()
        
#         try:
#             # Test 1: Token
#             token = self._get_orange_access_token()

#             # Test 2: QR Code
#             qr_result = self._test_qr_generation(token)

#             result = f"✅ TEST COMPLET RÉUSSI\n"
#             result += f"✓ Token généré: OK\n"
#             result += f"✓ QR Code généré: OK\n"
#             result += f"✓ Transaction ID: {qr_result['response'].get('transactionId', 'N/A')}\n"
#             result += f"Date: {fields.Datetime.now()}\n"

#             self.write({
#                 'last_test_date': fields.Datetime.now(),
#                 'last_test_result': result
#             })

#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'display_notification',
#                 'params': {
#                     'title': '✅ Test complet réussi',
#                     'message': 'Toute la configuration fonctionne correctement!',
#                     'type': 'success',
#                 }
#             }

#         except Exception as e:
#             error_result = f"❌ TEST COMPLET ÉCHOUÉ\n"
#             error_result += f"Erreur: {str(e)}\n"
#             error_result += f"Date: {fields.Datetime.now()}\n"

#             self.write({
#                 'last_test_date': fields.Datetime.now(),
#                 'last_test_result': error_result
#             })

#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'display_notification',
#                 'params': {
#                     'title': '❌ Test échoué',
#                     'message': str(e),
#                     'type': 'danger',
#                 }
#             }

#     def action_test_webhook(self):
#         """Tester le webhook"""
#         self.ensure_one()
#         if not self.webhook_url:
#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'display_notification',
#                 'params': {
#                     'title': '⚠️ Webhook non configuré',
#                     'message': 'Veuillez configurer l\'URL du webhook d\'abord.',
#                     'type': 'warning',
#                 }
#             }

#         try:
#             test_url = f"{self.webhook_url.rstrip('/')}/status"
#             response = requests.get(test_url, timeout=10)

#             if response.status_code == 200:
#                 result = f"✅ WEBHOOK ACCESSIBLE\n"
#                 result += f"URL: {test_url}\n"
#                 result += f"Status: {response.status_code}\n"
#                 result += f"Date: {fields.Datetime.now()}\n"

#                 self.write({
#                     'last_test_date': fields.Datetime.now(),
#                     'last_test_result': result
#                 })

#                 return {
#                     'type': 'ir.actions.client',
#                     'tag': 'display_notification',
#                     'params': {
#                         'title': '✅ Webhook OK',
#                         'message': 'Le webhook est accessible!',
#                         'type': 'success',
#                     }
#                 }
#             else:
#                 raise Exception(f'Status HTTP: {response.status_code}')

#         except Exception as e:
#             error_result = f"❌ WEBHOOK NON ACCESSIBLE\n"
#             error_result += f"URL: {self.webhook_url}\n"
#             error_result += f"Erreur: {str(e)}\n"
#             error_result += f"Date: {fields.Datetime.now()}\n"

#             self.write({
#                 'last_test_date': fields.Datetime.now(),
#                 'last_test_result': error_result
#             })

#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'display_notification',
#                 'params': {
#                     'title': '❌ Webhook inaccessible',
#                     'message': str(e),
#                     'type': 'danger',
#                 }
#             }

#     def action_clear_test_logs(self):
#         """Effacer les logs de test"""
#         self.ensure_one()
#         self.write({
#             'last_test_result': '',
#             'last_test_date': False
#         })
#         return {
#             'type': 'ir.actions.client',
#             'tag': 'display_notification',
#             'params': {
#                 'title': '🗑️ Logs effacés',
#                 'message': 'Les logs de test ont été effacés.',
#                 'type': 'info',
#             }
#         }

#     def _get_orange_access_token(self):
#         """Obtenir un token d'accès Orange Money"""
#         auth_data = {
#             'grant_type': 'client_credentials',
#             'client_id': self.orange_client_id,
#             'client_secret': self.orange_client_secret
#         }

#         headers = {
#             'Content-Type': 'application/x-www-form-urlencoded',
#             'Accept': 'application/json'
#         }

#         form_data = '&'.join([f"{k}={v}" for k, v in auth_data.items()])

#         response = requests.post(
#             f"{self.orange_base_url}/oauth/v1/token",
#             data=form_data,
#             headers=headers,
#             timeout=30
#         )

#         if response.status_code == 200:
#             token_data = response.json()
#             return token_data.get('access_token')
#         else:
#             raise Exception(f'Erreur d\'authentification: {response.status_code} - {response.text}')

#     def _test_qr_generation(self, token):
#         """Tester la génération d'un QR code"""
#         qr_data = {
#             'amount': {'unit': 'XOF', 'value': 100},
#             'callbackCancelUrl': self.callback_cancel_url,
#             'callbackSuccessUrl': self.callback_success_url,
#             'code': self.merchant_code,
#             'metadata': {
#                 'description': 'Test de configuration',
#                 'reference': f'TEST-{fields.Datetime.now().strftime("%Y%m%d%H%M%S")}'
#             },
#             'name': self.merchant_name,
#             'validity': 60
#         }

#         headers = {
#             'Content-Type': 'application/json',
#             'Accept': 'application/json',
#             'Authorization': f'Bearer {token}',
#             'X-Api-Key': self.orange_api_key
#         }

#         response = requests.post(
#             f"{self.orange_base_url}/api/eWallet/v4/qrcode",
#             json=qr_data,
#             headers=headers,
#             timeout=30
#         )

#         if response.status_code in [200, 201]:
#             return {
#                 'status': 'success',
#                 'message': 'Test de génération QR code réussi',
#                 'response': response.json()
#             }
#         else:
#             raise Exception(f'Erreur génération QR: {response.status_code} - {response.text}')
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import requests
import logging

_logger = logging.getLogger(__name__)

class OrangeMoneyConfig(models.Model):
    _name = 'orange.money.config'
    _description = 'Configuration Orange Money'
    _rec_name = 'merchant_name'

    # Informations générales
    active = fields.Boolean(string='Actif', default=False)  # Changé à False par défaut
    merchant_name = fields.Char(string='Nom du Marchand', required=True, default='CCBM SHOP')
    merchant_code = fields.Char(string='Code Marchand', required=True, size=6, default='123456')
    test_mode = fields.Boolean(string='Mode Test', default=True)

    # Configuration API Orange Money
    orange_base_url = fields.Char(
        string='URL de base Orange Money', 
        required=True, 
        default='https://api.sandbox.orange-sonatel.com'
    )
    orange_client_id = fields.Char(string='Client ID Orange Money')
    orange_client_secret = fields.Char(string='Client Secret Orange Money')
    orange_api_key = fields.Char(string='Clé API Orange Money')

    # Configuration Webhook
    webhook_url = fields.Char(string='URL du Webhook')
    webhook_api_key = fields.Char(string='Clé API Webhook')

    # URLs de callback
    callback_success_url = fields.Char(
        string='URL de succès', 
        default='https://your-domain.com/payment/success'
    )
    callback_cancel_url = fields.Char(
        string='URL d\'annulation', 
        default='https://your-domain.com/payment/cancel'
    )

    # Paramètres de transaction
    default_validity = fields.Integer(string='Validité par défaut (secondes)', default=300)
    max_validity = fields.Integer(string='Validité maximale (secondes)', default=86400)

    # Informations de test
    last_test_date = fields.Datetime(string='Dernière date de test', readonly=True)
    last_test_result = fields.Text(string='Résultat du dernier test', readonly=True)

    # SUPPRESSION de la contrainte SQL problématique
    # _sql_constraints = [
    #     ('unique_active_config', 
    #      'EXCLUDE (active WITH =) WHERE (active = true)', 
    #      'Une seule configuration Orange Money peut être active à la fois!')
    # ]

    @api.model
    def create(self, vals):
        """Surcharge pour gérer l'unicité de la configuration active"""
        if vals.get('active', False):
            # Vérifier s'il y a déjà une configuration active
            existing_active = self.search([('active', '=', True)], limit=1)
            if existing_active:
                # Désactiver l'ancienne configuration
                existing_active.write({'active': False})
                _logger.info(f"Configuration '{existing_active.merchant_name}' désactivée automatiquement")
        
        record = super(OrangeMoneyConfig, self).create(vals)
        _logger.info(f"Configuration '{record.merchant_name}' créée avec succès")
        return record

    def write(self, vals):
        """Surcharge pour gérer l'unicité de la configuration active"""
        if vals.get('active', False):
            # Si on active cette configuration, désactiver les autres
            other_configs = self.search([('active', '=', True), ('id', 'not in', self.ids)])
            if other_configs:
                other_configs.write({'active': False})
                for config in other_configs:
                    _logger.info(f"Configuration '{config.merchant_name}' désactivée automatiquement")
        
        result = super(OrangeMoneyConfig, self).write(vals)
        
        # Log des changements
        if 'active' in vals:
            for record in self:
                status = "activée" if vals['active'] else "désactivée"
                _logger.info(f"Configuration '{record.merchant_name}' {status}")
        
        return result

    def unlink(self):
        """Permettre la suppression avec vérifications"""
        for record in self:
            if record.active:
                # Vérifier s'il y a d'autres configurations
                other_configs = self.search([('id', '!=', record.id)])
                if not other_configs:
                    raise UserError(_(
                        'Impossible de supprimer la seule configuration existante. '
                        'Créez d\'abord une nouvelle configuration avant de supprimer celle-ci.'
                    ))
                else:
                    # Activer une autre configuration si disponible
                    inactive_config = other_configs.filtered(lambda c: not c.active)
                    if inactive_config:
                        inactive_config[0].write({'active': True})
                        _logger.info(f"Configuration '{inactive_config[0].merchant_name}' activée automatiquement")
        
        return super(OrangeMoneyConfig, self).unlink()

    @api.constrains('orange_client_id', 'orange_client_secret', 'orange_api_key')
    def _check_api_credentials(self):
        """Vérifier que les identifiants API sont renseignés pour une config active"""
        for record in self:
            if record.active:
                missing_fields = []
                if not record.orange_client_id:
                    missing_fields.append('Client ID Orange Money')
                if not record.orange_client_secret:
                    missing_fields.append('Client Secret Orange Money')
                if not record.orange_api_key:
                    missing_fields.append('Clé API Orange Money')
                
                if missing_fields:
                    raise ValidationError(_(
                        'Les champs suivants sont obligatoires pour une configuration active :\n%s'
                    ) % '\n'.join(f'• {field}' for field in missing_fields))

    @api.model
    def get_config(self):
        """Récupérer la configuration active"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            # Essayer d'activer la première configuration disponible
            first_config = self.search([], limit=1)
            if first_config:
                first_config.write({'active': True})
                return first_config
            else:
                raise UserError(_('Aucune configuration Orange Money trouvée. Veuillez en créer une.'))
        return config

    def action_activate(self):
        """Action pour activer cette configuration"""
        self.ensure_one()
        
        # Vérifier les champs obligatoires avant activation
        missing_fields = []
        if not self.orange_client_id:
            missing_fields.append('Client ID Orange Money')
        if not self.orange_client_secret:
            missing_fields.append('Client Secret Orange Money')
        if not self.orange_api_key:
            missing_fields.append('Clé API Orange Money')
        
        if missing_fields:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '⚠️ Champs manquants',
                    'message': f'Veuillez renseigner : {", ".join(missing_fields)}',
                    'type': 'warning',
                }
            }
        
        if not self.active:
            self.write({'active': True})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Configuration activée',
                'message': f'La configuration "{self.merchant_name}" est maintenant active.',
                'type': 'success',
            }
        }

    def action_deactivate(self):
        """Action pour désactiver cette configuration"""
        self.ensure_one()
        
        # Vérifier s'il y a d'autres configurations
        other_configs = self.search([('id', '!=', self.id)])
        if not other_configs:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '⚠️ Impossible de désactiver',
                    'message': 'Au moins une configuration doit rester active. Créez d\'abord une autre configuration.',
                    'type': 'warning',
                }
            }
        
        self.write({'active': False})
        
        # Activer une autre configuration si nécessaire
        if not self.search([('active', '=', True)]):
            other_configs[0].write({'active': True})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Configuration désactivée',
                'message': f'La configuration "{self.merchant_name}" a été désactivée.',
                'type': 'success',
            }
        }

    def action_duplicate(self):
        """Action pour dupliquer la configuration"""
        self.ensure_one()
        new_config = self.copy({
            'merchant_name': f"{self.merchant_name} (Copie)",
            'active': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Configuration dupliquée',
            'res_model': 'orange.money.config',
            'res_id': new_config.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_delete_config(self):
        """Action pour supprimer une configuration"""
        self.ensure_one()
        
        if self.active:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '⚠️ Impossible de supprimer',
                    'message': 'Impossible de supprimer la configuration active. Désactivez-la d\'abord.',
                    'type': 'warning',
                }
            }
        
        # Supprimer directement sans wizard pour simplifier
        config_name = self.merchant_name
        self.unlink()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '🗑️ Configuration supprimée',
                'message': f'La configuration "{config_name}" a été supprimée.',
                'type': 'success',
            }
        }

    # Méthodes de test (inchangées)
    def action_generate_test_token(self):
        """Générer un token de test"""
        self.ensure_one()
        
        try:
            token = self._get_orange_access_token()

            result = f"✅ TOKEN GÉNÉRÉ AVEC SUCCÈS\n"
            result += f"Token: {token[:30]}...\n"
            result += f"Date: {fields.Datetime.now()}\n"

            self.write({
                'last_test_date': fields.Datetime.now(),
                'last_test_result': result
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '✅ Token généré',
                    'message': 'Token d\'accès généré avec succès!',
                    'type': 'success',
                }
            }

        except Exception as e:
            error_result = f"❌ ERREUR GÉNÉRATION TOKEN\n"
            error_result += f"Erreur: {str(e)}\n"
            error_result += f"Date: {fields.Datetime.now()}\n"

            self.write({
                'last_test_date': fields.Datetime.now(),
                'last_test_result': error_result
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '❌ Erreur Token',
                    'message': str(e),
                    'type': 'danger',
                }
            }

    def action_test_qr_generation(self):
        """Tester la génération de QR code"""
        self.ensure_one()
        
        try:
            token = self._get_orange_access_token()
            qr_result = self._test_qr_generation(token)

            result = f"✅ QR CODE GÉNÉRÉ AVEC SUCCÈS\n"
            result += f"Transaction ID: {qr_result['response'].get('transactionId', 'N/A')}\n"
            result += f"Montant test: 100 XOF\n"
            result += f"Date: {fields.Datetime.now()}\n"

            self.write({
                'last_test_date': fields.Datetime.now(),
                'last_test_result': result
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '✅ QR Code généré',
                    'message': 'QR Code de test généré avec succès!',
                    'type': 'success',
                }
            }

        except Exception as e:
            error_result = f"❌ ERREUR GÉNÉRATION QR CODE\n"
            error_result += f"Erreur: {str(e)}\n"
            error_result += f"Date: {fields.Datetime.now()}\n"

            self.write({
                'last_test_date': fields.Datetime.now(),
                'last_test_result': error_result
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '❌ Erreur QR Code',
                    'message': str(e),
                    'type': 'danger',
                }
            }

    def action_test_configuration(self):
        """Test complet de la configuration"""
        self.ensure_one()
        
        try:
            # Test 1: Token
            token = self._get_orange_access_token()

            # Test 2: QR Code
            qr_result = self._test_qr_generation(token)

            result = f"✅ TEST COMPLET RÉUSSI\n"
            result += f"✓ Token généré: OK\n"
            result += f"✓ QR Code généré: OK\n"
            result += f"✓ Transaction ID: {qr_result['response'].get('transactionId', 'N/A')}\n"
            result += f"Date: {fields.Datetime.now()}\n"

            self.write({
                'last_test_date': fields.Datetime.now(),
                'last_test_result': result
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '✅ Test complet réussi',
                    'message': 'Toute la configuration fonctionne correctement!',
                    'type': 'success',
                }
            }

        except Exception as e:
            error_result = f"❌ TEST COMPLET ÉCHOUÉ\n"
            error_result += f"Erreur: {str(e)}\n"
            error_result += f"Date: {fields.Datetime.now()}\n"

            self.write({
                'last_test_date': fields.Datetime.now(),
                'last_test_result': error_result
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '❌ Test échoué',
                    'message': str(e),
                    'type': 'danger',
                }
            }

    def action_test_webhook(self):
        """Tester le webhook"""
        self.ensure_one()
        if not self.webhook_url:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '⚠️ Webhook non configuré',
                    'message': 'Veuillez configurer l\'URL du webhook d\'abord.',
                    'type': 'warning',
                }
            }

        try:
            test_url = f"{self.webhook_url.rstrip('/')}/status"
            response = requests.get(test_url, timeout=10)

            if response.status_code == 200:
                result = f"✅ WEBHOOK ACCESSIBLE\n"
                result += f"URL: {test_url}\n"
                result += f"Status: {response.status_code}\n"
                result += f"Date: {fields.Datetime.now()}\n"

                self.write({
                    'last_test_date': fields.Datetime.now(),
                    'last_test_result': result
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '✅ Webhook OK',
                        'message': 'Le webhook est accessible!',
                        'type': 'success',
                    }
                }
            else:
                raise Exception(f'Status HTTP: {response.status_code}')

        except Exception as e:
            error_result = f"❌ WEBHOOK NON ACCESSIBLE\n"
            error_result += f"URL: {self.webhook_url}\n"
            error_result += f"Erreur: {str(e)}\n"
            error_result += f"Date: {fields.Datetime.now()}\n"

            self.write({
                'last_test_date': fields.Datetime.now(),
                'last_test_result': error_result
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '❌ Webhook inaccessible',
                    'message': str(e),
                    'type': 'danger',
                }
            }

    def action_clear_test_logs(self):
        """Effacer les logs de test"""
        self.ensure_one()
        self.write({
            'last_test_result': '',
            'last_test_date': False
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '🗑️ Logs effacés',
                'message': 'Les logs de test ont été effacés.',
                'type': 'info',
            }
        }

    def _get_orange_access_token(self):
        """Obtenir un token d'accès Orange Money"""
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.orange_client_id,
            'client_secret': self.orange_client_secret
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }

        form_data = '&'.join([f"{k}={v}" for k, v in auth_data.items()])

        response = requests.post(
            f"{self.orange_base_url}/oauth/v1/token",
            data=form_data,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access_token')
        else:
            raise Exception(f'Erreur d\'authentification: {response.status_code} - {response.text}')

    def _test_qr_generation(self, token):
        """Tester la génération d'un QR code"""
        qr_data = {
            'amount': {'unit': 'XOF', 'value': 100},
            'callbackCancelUrl': self.callback_cancel_url,
            'callbackSuccessUrl': self.callback_success_url,
            'code': self.merchant_code,
            'metadata': {
                'description': 'Test de configuration',
                'reference': f'TEST-{fields.Datetime.now().strftime("%Y%m%d%H%M%S")}'
            },
            'name': self.merchant_name,
            'validity': 60
        }

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}',
            'X-Api-Key': self.orange_api_key
        }

        response = requests.post(
            f"{self.orange_base_url}/api/eWallet/v4/qrcode",
            json=qr_data,
            headers=headers,
            timeout=30
        )

        if response.status_code in [200, 201]:
            return {
                'status': 'success',
                'message': 'Test de génération QR code réussi',
                'response': response.json()
            }
        else:
            raise Exception(f'Erreur génération QR: {response.status_code} - {response.text}')
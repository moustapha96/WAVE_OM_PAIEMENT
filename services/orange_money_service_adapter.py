# -*- coding: utf-8 -*-
"""
Adaptateur pour utiliser la configuration Odoo au lieu des paramètres XML
"""
from odoo import api, SUPERUSER_ID


def get_orange_money_config(env):
    """Récupérer la configuration Orange Money active"""
    config = env['orange.money.config'].search([('active', '=', True)], limit=1)
    if not config:
        raise Exception('Aucune configuration Orange Money active trouvée')
    
    return {
        'base_url': config.orange_base_url,
        'client_id': config.orange_client_id,
        'client_secret': config.orange_client_secret,
        'api_key': config.orange_api_key,
        'merchant_code': config.merchant_code,
        'merchant_name': config.merchant_name,
        'callback_success_url': config.callback_success_url,
        'callback_cancel_url': config.callback_cancel_url,
        'webhook_url': config.webhook_url,
        'webhook_api_key': config.webhook_api_key,
        'default_validity': config.default_validity,
        'max_validity': config.max_validity,
    }


class OrangeMoneyConfigService:
    """Service pour gérer la configuration Orange Money"""
    
    @staticmethod
    def get_active_config(env):
        """Récupérer la configuration active"""
        return get_orange_money_config(env)
    
    @staticmethod
    def validate_config(config_data):
        """Valider une configuration"""
        required_fields = [
            'client_id', 'client_secret', 'api_key', 
            'merchant_code', 'merchant_name', 'base_url'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not config_data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            raise Exception(f'Champs manquants: {", ".join(missing_fields)}')
        
        return True
    
    @staticmethod
    def get_config_for_api(env):
        """Récupérer la configuration formatée pour l'API"""
        config = get_orange_money_config(env)
        
        # Valider la configuration
        OrangeMoneyConfigService.validate_config(config)
        
        return config

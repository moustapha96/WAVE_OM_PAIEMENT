# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class OrangeMoneyTransaction(models.Model):
    _name = 'orange.money.transaction'
    _description = 'Transaction Orange Money'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    orange_id = fields.Char(string="Orange Money ID", tracking=True)
    amount = fields.Float(string="Montant", tracking=True)
    phone = fields.Char(string="Téléphone", tracking=True)
    status = fields.Selection([
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
    ], default='pending', tracking=True)
    date = fields.Datetime(string="Date", default=fields.Datetime.now, tracking=True)
    created_at = fields.Datetime(string="Date de création", default=fields.Datetime.now)
    order_id = fields.Many2one('sale.order', string="Commande liée", tracking=True)
    
    # Champs additionnels pour plus d'informations
    reference = fields.Char(string="Référence", tracking=True)
    currency = fields.Char(string="Devise", default="XOF", tracking=True)
    callback_data = fields.Text(string="Données de callback", help="Données JSON reçues du webhook")
    # Champs calculés
    order_state = fields.Selection(related='order_id.state', string="État de la commande", readonly=True)
    customer_id = fields.Many2one(related='order_id.partner_id', string="Client", readonly=True, store=True)
    
    _sql_constraints = [
        ('orange_id_uniq', 'unique(orange_id)', 'L\'ID de transaction Orange Money doit être unique!')
    ]
    
    @api.model
    def create(self, vals):
        """Surcharge de la création pour ajouter des logs"""
        record = super(OrangeMoneyTransaction, self).create(vals)
        _logger.info("Transaction Orange Money créée: %s, Montant: %s, Statut: %s", 
                    record.orange_id, record.amount, record.status)
        return record
    
    def write(self, vals):
        """Surcharge de l'écriture pour ajouter des logs"""
        if 'status' in vals:
            for record in self:
                _logger.info("Mise à jour du statut de la transaction %s: %s -> %s", 
                            record.orange_id, record.status, vals['status'])
        return super(OrangeMoneyTransaction, self).write(vals)
    
    def action_confirm_manually(self):
        """Action pour confirmer manuellement une transaction"""
        for record in self:
            if record.status != 'completed':
                record.write({'status': 'completed'})
                if record.order_id and record.order_id.state in ['draft', 'sent']:
                    record.order_id.action_confirm()
                    message = _("Commande confirmée manuellement via transaction Orange Money %s") % record.orange_id
                    record.order_id.message_post(body=message)
    
    def action_mark_as_failed(self):
        """Action pour marquer une transaction comme échouée"""
        for record in self:
            if record.status != 'failed':
                record.write({'status': 'failed'})
                message = _("Transaction Orange Money %s marquée comme échouée manuellement") % record.orange_id
                if record.order_id:
                    record.order_id.message_post(body=message)
    
    def action_check_status(self):
        """Action pour vérifier le statut d'une transaction via l'API"""
        self.ensure_one()
        if not self.orange_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erreur'),
                    'message': _('Aucun ID de transaction Orange Money à vérifier'),
                    'type': 'danger',
                }
            }
        
        try:
            # Récupérer les paramètres de configuration
            IrConfigParameter = self.env['ir.config_parameter'].sudo()
            base_url = IrConfigParameter.get_param('orange_money.base_url')
            client_id = IrConfigParameter.get_param('orange_money.client_id')
            client_secret = IrConfigParameter.get_param('orange_money.client_secret')
            api_key = IrConfigParameter.get_param('orange_money.api_key')
            
            if not all([base_url, client_id, client_secret, api_key]):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erreur'),
                        'message': _('Configuration Orange Money incomplète'),
                        'type': 'danger',
                    }
                }
            
            # Obtenir un token d'accès
            import requests
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            form_data = '&'.join([f"{k}={v}" for k, v in auth_data.items()])
            
            auth_response = requests.post(
                f"{base_url}/oauth/v1/token",
                data=form_data,
                headers=headers,
                timeout=30
            )
            
            if auth_response.status_code != 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erreur d\'authentification'),
                        'message': auth_response.text,
                        'type': 'danger',
                    }
                }
            
            token = auth_response.json().get('access_token')
            
            # Vérifier le statut de la transaction
            status_headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {token}',
                'X-Api-Key': api_key
            }
            
            status_response = requests.get(
                f"{base_url}/api/eWallet/v1/transactions/{self.orange_id}/status",
                headers=status_headers,
                timeout=30
            )
            
            if status_response.status_code != 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erreur de vérification'),
                        'message': status_response.text,
                        'type': 'danger',
                    }
                }
            
            status_data = status_response.json()
            orange_status = status_data.get('status')
            
            # Mapper le statut Orange Money vers le statut du modèle
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
            
            new_status = status_mapping.get(orange_status, self.status)
            
            # Mettre à jour le statut
            if new_status != self.status:
                self.write({'status': new_status})
                
                # # Si complété et commande liée, confirmer la commande
                # if new_status == 'completed' and self.order_id and self.order_id.state in ['draft', 'sent']:
                #     self.order_id.action_confirm()
                #     message = _("Commande confirmée suite à la vérification du statut Orange Money")
                #     self.order_id.message_post(body=message)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Succès'),
                    'message': _('Statut mis à jour: %s') % new_status,
                    'type': 'success',
                }
            }
            
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erreur'),
                    'message': str(e),
                    'type': 'danger',
                }
            }

# from odoo import models, fields, api
# import json
# from odoo.exceptions import ValidationError

# class WaveTransaction(models.Model):
#     _name = 'wave.transaction'
#     _description = 'Transaction Wave Money'
#     _order = 'created_at desc'
#     _rec_name = 'reference'

#     # Identifiants
#     wave_id = fields.Char(
#         string="ID Wave", 
#         required=True,
#         index=True,
#         help="Identifiant unique de la transaction chez Wave"
#     )
#     transaction_id = fields.Char(
#         string="ID de transaction", 
#         required=True,
#         index=True,
#         help="Identifiant unique de la transaction dans Odoo"
#     )
    
#     reference = fields.Char(
#         string="Référence", 
#         required=True,
#         index=True,
#         help="Référence unique de la transaction côté client"
#     )

#     # Informations de paiement
#     amount = fields.Float(
#         string="Montant", 
#         required=True,
#         digits=(16, 2),
#         help="Montant de la transaction"
#     )
    
#     currency = fields.Selection([
#         ('XOF', 'Franc CFA (XOF)'),
#         ('USD', 'Dollar US (USD)'),
#         ('EUR', 'Euro (EUR)')
#     ], string='Devise', default='XOF', required=True)
    
#     phone = fields.Char(
#         string="Numéro de téléphone",
#         help="Numéro de téléphone du payeur"
#     )
    
#     description = fields.Text(
#         string="Description",
#         help="Description de la transaction"
#     )

#     # Statut et suivi
#     status = fields.Selection([
#         ('pending', 'En attente'),
#         ('completed', 'Complété'),
#         ('failed', 'Échoué'),
#         ('cancelled', 'Annulé'),
#         ('expired', 'Expiré')
#     ], string='Statut', default='pending', required=True, index=True)
    
#     # URLs et données
#     payment_link_url = fields.Char(
#         string="URL de paiement",
#         help="URL générée par Wave pour effectuer le paiement"
#     )
    
#     wave_response = fields.Text(
#         string="Réponse Wave",
#         help="Réponse complète de l'API Wave lors de la création"
#     )
    
#     webhook_data = fields.Text(
#         string="Données Webhook",
#         help="Dernières données reçues via webhook"
#     )

#     # Relations
#     order_id = fields.Many2one(
#         'sale.order', 
#         string="Commande liée",
#         help="Commande de vente associée à cette transaction"
#     )
    
#     partner_id = fields.Many2one(
#         'res.partner',
#         string="Client",
#         help="Client associé à cette transaction"
#     )

#     # Dates
#     created_at = fields.Datetime(
#         string="Date de création", 
#         default=fields.Datetime.now,
#         required=True,
#         readonly=True
#     )
    
#     updated_at = fields.Datetime(
#         string="Dernière mise à jour", 
#         default=fields.Datetime.now,
#         readonly=True
#     )
    
#     completed_at = fields.Datetime(
#         string="Date de completion",
#         readonly=True,
#         help="Date à laquelle la transaction a été complétée"
#     )

#     # Champs calculés
#     status_color = fields.Integer(
#         string="Couleur du statut",
#         compute='_compute_status_color',
#         store=False
#     )
    
#     formatted_amount = fields.Char(
#         string="Montant formaté",
#         compute='_compute_formatted_amount',
#         store=False
#     )

#     @api.depends('status')
#     def _compute_status_color(self):
#         """Calculer la couleur selon le statut"""
#         color_map = {
#             'pending': 4,    # Bleu
#             'completed': 10, # Vert
#             'failed': 1,     # Rouge
#             'cancelled': 3,  # Jaune
#             'expired': 8     # Gris
#         }
#         for record in self:
#             record.status_color = color_map.get(record.status, 0)

#     @api.depends('amount', 'currency')
#     def _compute_formatted_amount(self):
#         """Formater le montant avec la devise"""
#         for record in self:
#             if record.currency == 'XOF':
#                 record.formatted_amount = f"{record.amount:,.0f} FCFA"
#             else:
#                 record.formatted_amount = f"{record.amount:,.2f} {record.currency}"

#     @api.model
#     def create(self, vals):
#         """Surcharger create pour ajouter des validations"""
#         # Vérifier l'unicité de la référence
#         if vals.get('reference'):
#             existing = self.search([('reference', '=', vals['reference'])])
#             if existing:
#                 raise ValidationError(f"Une transaction avec la référence '{vals['reference']}' existe déjà.")
        
#         return super().create(vals)

#     def write(self, vals):
#         """Surcharger write pour mettre à jour la date de modification"""
#         vals['updated_at'] = fields.Datetime.now()
        
#         # Si le statut passe à 'completed', enregistrer la date
#         if vals.get('status') == 'completed' and self.status != 'completed':
#             vals['completed_at'] = fields.Datetime.now()
        
#         return super().write(vals)

#     def action_refresh_status(self):
#         """Action pour rafraîchir le statut depuis Wave"""
#         try:
#             config = self.env['wave.config'].search([('is_active', '=', True)], limit=1)
#             if not config:
#                 raise ValidationError("Aucune configuration Wave active trouvée.")

#             import requests
            
#             headers = {
#                 "Authorization": f"Bearer {config.api_key}",
#                 "Content-Type": "application/json",
#             }

#             response = requests.get(
#                 f"https://api.wave.com/v1/payments/{self.wave_id}",
#                 headers=headers,
#                 timeout=30
#             )

#             if response.status_code == 200:
#                 data = response.json()
#                 new_status = data.get('status', '').lower()
                
#                 if new_status != self.status:
#                     self.write({
#                         'status': new_status,
#                         'wave_response': json.dumps(data)
#                     })
                    
#                 return {
#                     'type': 'ir.actions.client',
#                     'tag': 'display_notification',
#                     'params': {
#                         'title': 'Statut mis à jour',
#                         'message': f'Le statut a été mis à jour: {new_status}',
#                         'type': 'success',
#                     }
#                 }
#             else:
#                 raise ValidationError(f"Erreur API Wave: {response.text}")

#         except Exception as e:
#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'display_notification',
#                 'params': {
#                     'title': 'Erreur',
#                     'message': f'Erreur lors de la mise à jour: {str(e)}',
#                     'type': 'danger',
#                 }
#             }

#     def action_view_payment_link(self):
#         """Action pour ouvrir le lien de paiement"""
#         if self.payment_link_url:
#             return {
#                 'type': 'ir.actions.act_url',
#                 'url': self.payment_link_url,
#                 'target': 'new',
#             }
#         else:
#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'display_notification',
#                 'params': {
#                     'title': 'Aucun lien',
#                     'message': 'Aucun lien de paiement disponible pour cette transaction.',
#                     'type': 'warning',
#                 }
#             }
        
#     def action_view_order(self):
#         """Action pour ouvrir la commande associée"""
#         if self.order_id:
#             return {
#                 'type': 'ir.actions.act_window',
#                 'name': 'Commande',
#                 'res_model': 'sale.order',
#                 'res_id': self.order_id.id,
#                 'view_mode': 'form',
#                 'target': 'current',
#             }
#         else:
#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'display_notification',
#                 'params': {
#                     'title': 'Aucune commande',
#                     'message': 'Aucune commande associée à cette transaction.',
#                     'type': 'warning',
#                 }
#             }


from odoo import models, fields, api
import json
from odoo.exceptions import ValidationError

class WaveTransaction(models.Model):
    _name = 'wave.transaction'
    _description = 'Transaction Wave Money'
    _order = 'created_at desc'
    _rec_name = 'reference'

    # Identifiants
    wave_id = fields.Char(
        string="ID Wave", 
        required=True,
        index=True,
        help="Identifiant unique de la transaction chez Wave"
    )

    transaction_id = fields.Char(
        string="ID de transaction", 
        required=True,
        index=True,
        help="Identifiant unique de la transaction dans Odoo"
    )
    
    reference = fields.Char(
        string="Référence", 
        required=True,
        index=True,
        help="Référence unique de la transaction côté client"
    )

    # Informations de paiement
    amount = fields.Float(
        string="Montant", 
        required=True,
        digits=(16, 2),
        help="Montant de la transaction"
    )
    
    currency = fields.Selection([
        ('XOF', 'Franc CFA (XOF)'),
        ('USD', 'Dollar US (USD)'),
        ('EUR', 'Euro (EUR)')
    ], string='Devise', default='XOF', required=True)
    
    phone = fields.Char(
        string="Numéro de téléphone",
        help="Numéro de téléphone du payeur"
    )
    
    description = fields.Text(
        string="Description",
        help="Description de la transaction"
    )

    # Statut et suivi
    status = fields.Selection([
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
        ('expired', 'Expiré'),
        ('refunded', 'Remboursé')
    ], string='Statut', default='pending', required=True, index=True)
    
    # URLs et données
    payment_link_url = fields.Char(
        string="URL de paiement",
        help="URL générée par Wave pour effectuer le paiement"
    )
    
    wave_response = fields.Text(
        string="Réponse Wave",
        help="Réponse complète de l'API Wave lors de la création"
    )
    
    webhook_data = fields.Text(
        string="Données Webhook",
        help="Dernières données reçues via webhook"
    )

    # Relations
    order_id = fields.Many2one(
        'sale.order', 
        string="Commande liée",
        help="Commande de vente associée à cette transaction"
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string="Client",
        help="Client associé à cette transaction"
    )

    # Dates
    created_at = fields.Datetime(
        string="Date de création", 
        default=fields.Datetime.now,
        required=True,
        readonly=True
    )
    
    updated_at = fields.Datetime(
        string="Dernière mise à jour", 
        default=fields.Datetime.now,
        readonly=True
    )
    
    completed_at = fields.Datetime(
        string="Date de completion",
        readonly=True,
        help="Date à laquelle la transaction a été complétée"
    )

    # Champs calculés
    status_color = fields.Integer(
        string="Couleur du statut",
        compute='_compute_status_color',
        store=False
    )
    
    formatted_amount = fields.Char(
        string="Montant formaté",
        compute='_compute_formatted_amount',
        store=False
    )

    @api.depends('status')
    def _compute_status_color(self):
        """Calculer la couleur selon le statut"""
        color_map = {
            'pending': 4,    # Bleu
            'completed': 10, # Vert
            'failed': 1,     # Rouge
            'cancelled': 3,  # Jaune
            'expired': 8,    # Gris
            'refunded': 9    # Violet
        }
        for record in self:
            record.status_color = color_map.get(record.status, 0)

    @api.depends('amount', 'currency')
    def _compute_formatted_amount(self):
        """Formater le montant avec la devise"""
        for record in self:
            if record.currency == 'XOF':
                record.formatted_amount = f"{record.amount:,.0f} FCFA"
            else:
                record.formatted_amount = f"{record.amount:,.2f} {record.currency}"

    @api.model
    def create(self, vals):
        """Surcharger create pour ajouter des validations"""
        # Vérifier l'unicité du transaction_id
        if vals.get('transaction_id'):
            existing = self.search([('transaction_id', '=', vals['transaction_id'])])
            if existing:
                raise ValidationError(f"Une transaction avec l'ID '{vals['transaction_id']}' existe déjà.")
        
        # Vérifier l'unicité de la référence
        if vals.get('reference'):
            existing = self.search([('reference', '=', vals['reference'])])
            if existing:
                raise ValidationError(f"Une transaction avec la référence '{vals['reference']}' existe déjà.")
        
        return super().create(vals)

    def write(self, vals):
        """Surcharger write pour mettre à jour la date de modification"""
        vals['updated_at'] = fields.Datetime.now()
        
        # Si le statut passe à 'completed', enregistrer la date
        if vals.get('status') == 'completed' and self.status != 'completed':
            vals['completed_at'] = fields.Datetime.now()
        
        return super().write(vals)

    def action_refresh_status(self):
        """Action pour rafraîchir le statut depuis Wave"""
        try:
            config = self.env['wave.config'].search([('is_active', '=', True)], limit=1)
            if not config:
                raise ValidationError("Aucune configuration Wave active trouvée.")

            # Utiliser la méthode du modèle pour récupérer la session
            session_data = config.get_session_by_id(self.wave_id)
            
            if session_data:
                wave_status = session_data.get('status', '').lower()
                # Mapper le statut Wave vers Odoo
                status_mapping = {
                    'completed': 'completed',
                    'succeeded': 'completed',
                    'failed': 'failed',
                    'cancelled': 'cancelled',
                    'canceled': 'cancelled',
                    'pending': 'pending',
                    'processing': 'pending',
                    'expired': 'expired'
                }
                new_status = status_mapping.get(wave_status, 'pending')
                
                if new_status != self.status:
                    self.write({
                        'status': new_status,
                        'wave_response': json.dumps(session_data)
                    })
                    
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Statut mis à jour',
                        'message': f'Le statut a été mis à jour: {new_status}',
                        'type': 'success',
                    }
                }
            else:
                raise ValidationError("Impossible de récupérer les données de la session Wave")

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Erreur',
                    'message': f'Erreur lors de la mise à jour: {str(e)}',
                    'type': 'danger',
                }
            }

    def action_view_payment_link(self):
        """Action pour ouvrir le lien de paiement"""
        if self.payment_link_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.payment_link_url,
                'target': 'new',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Aucun lien',
                    'message': 'Aucun lien de paiement disponible pour cette transaction.',
                    'type': 'warning',
                }
            }
        
    def action_view_order(self):
        """Action pour ouvrir la commande associée"""
        if self.order_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Commande',
                'res_model': 'sale.order',
                'res_id': self.order_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Aucune commande',
                    'message': 'Aucune commande associée à cette transaction.',
                    'type': 'warning',
                }
            }

    _sql_constraints = [
        ('transaction_id_unique', 'UNIQUE(transaction_id)', 'L\'ID de transaction doit être unique.'),
        ('reference_unique', 'UNIQUE(reference)', 'La référence doit être unique.'),
    ]

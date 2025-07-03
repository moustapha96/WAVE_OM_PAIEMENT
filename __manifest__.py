{
    'name': 'Wave & OM Payment',
    'version': '1.0',
    'summary': 'Intégration Wave et Orange Money pour les paiements',
    'description': 'Permet de générer des liens de paiement Wave et Orange Money et de suivre les transactions.',
    'category': 'CCBM/',
    # 'depends': ['base'],
    'depends': [
        'base',
        'sale',
        'account',
        'mail',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'images': ['static/description/icon.png'],
    'data': [
        'security/ir.model.access.csv',
        'data/orange_webhook_config.xml',
        'views/orange_money_transaction_views.xml',
    
        'views/orange_money_test.xml',
        'data/orange_money_demo_data.xml',

        'views/wave_config_views.xml',
        'views/wave_transaction_views.xml',
        'views/wave_menu.xml',
        'views/menu.xml',
    ],
    'demo': [
        'data/orange_money_demo_data.xml',
    ],
    'license': 'LGPL-3',
}

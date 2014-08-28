# -*- coding: utf-8 -*-

{
    'name': 'Moneris Payment Acquirer',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: Moneris Implementation',
    'version': '1.0',
    'description': """Moneris Payment Acquirer""",
    'author': 'xyenDev',
    'depends': ['payment'],
    'data': [
        'views/moneris.xml',
        'views/payment_acquirer.xml',
        'views/res_config_view.xml',
        'data/moneris.xml',
    ],
    'installable': True,
}

# -*- coding: utf-8 -*-
{
    'name': "Cloud Manager",

    'summary': """ Odoo SaaS Cloud Manager""",

    'description': """
		Create and manage Google Compute Engine VM and Digital Ocean Droplet (and similar vendor)
		 Odoo instances for an Odoo SaaS Company.
		Provide for "High Availability (HA)" and "Disaster recovery (DR)" via remote datacenter warm backup systems.
    """,

    'author': "Gary Wallis of Unixservice, LLC. for AdHoc SA",
    'website': "http://www.adhoc.com.ar",

    'category': 'Uncategorized',
    'version': '8.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/provider.xml',
        'views/server.xml',
        'views/serverstatus.xml',
        'views/zone.xml',
        'views/machinetype.xml',
        'views/image.xml',
	'data/provider.xml',
	#'data/serverstatus.csv',
	#'data/zone.csv',
	#'data/machinetype.csv',
	#'data/image.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}

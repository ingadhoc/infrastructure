# -*- coding: utf-8 -*-
{
    'name': "Cloud Manager",
    'summary': """
The Cloud Manager helps you create and manage a hybrid set of virtual
machines.""",
    'author': "ADHOC SA, Gary Wallis for Unixservice LLC.",
    'website': "www.adhoc.com.ar",
    'license': 'AGPL-3',
    'images': [
    ],
    'category': 'Uncategorized',
    'version': '8.0.1.0.0',
    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'board'
    ],
    # 'external_dependencies': {
    #     'python': ['requests']
    # },
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/cloudmanager.xml',
        'views/provider.xml',
        'views/server.xml',
        'views/serverstatus.xml',
        'views/zone.xml',
        'views/cloudmanager_machinetype.xml',
        'views/cloudmanager_image.xml',
        'views/deployvm.xml',
        # 'data/provider.xml',
        # 'data/serverstatus.xml',
        # 'data/machinetype.xml',
        # 'data/image.xml',
        # 'data/zone.xml',
        # 'data/server.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

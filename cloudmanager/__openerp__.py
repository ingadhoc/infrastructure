# -*- coding: utf-8 -*-
{
    'name': "Cloud Manager",
    'summary': """
The Cloud Manager helps you create and manage a multi vendor set of virtual
machines.""",
    'description':"""
Manage public cloud provider VM lifecycle. Supports Google Compute Engine VMs and Digital Ocean Droplets. Easily extensible
to other public and private cloud provider APIs like Rackspace, Amazon (AWS) and OpenStack. Provides optional DNS Automation.""",
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
        'board',
    ],
    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizards/cloudmanager_deployvm_view.xml',
        'views/cloudmanager.xml',
        'views/cloudmanager_provider_view.xml',
        'views/cloudmanager_server_view.xml',
        'views/cloudmanager_serverstatus_view.xml',
        'views/cloudmanager_zone_view.xml',
        'views/cloudmanager_machinetype_view.xml',
        'views/cloudmanager_image_view.xml',
        'data/cloudmanager_provider_data.xml',
        'data/cloudmanager_serverstatus_data.xml',
        'data/cloudmanager_machinetype_data.xml',
        'data/cloudmanager_image_data.xml',
        'data/cloudmanager_zone_cloudmanager.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/cloudmanager_server_demo.xml',
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

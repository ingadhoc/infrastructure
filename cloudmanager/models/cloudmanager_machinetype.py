# -*- coding: utf-8 -*-
from openerp import models, fields
# from openerp.exceptions import ValidationError


class CloudmanagerMachineType(models.Model):
    _name = 'cloudmanager.machinetype'
    _description = 'Cloud service provider server specification shorthand name'

    name = fields.Char(
        required=True,
        help="Provider name of the machine type or droplet size "
        "(server specification)",
    )
    notes = fields.Text(
        help="Freeform details regarding this machine type, droplet size or "
        "server specification",
    )
    provider_id = fields.Many2one(
        'cloudmanager.provider',
        string="Provider",
        help="The provider this machine type is valid for",
    )
    slug = fields.Text(
        string="fcSlug",
        help="Provider abbreviated name used in templates",
    )

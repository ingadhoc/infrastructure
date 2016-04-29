# -*- coding: utf-8 -*-
from openerp import models, fields
# from openerp.exceptions import ValidationError


class CloudmanagerImage(models.Model):
    _name = 'cloudmanager.image'
    _description = 'Cloud service provider OS image name'

    name = fields.Char(
        required=True,
        help="Provider name of the OS image",
    )
    notes = fields.Text(
        help="Freeform details regarding this OS image",
    )
    provider_id = fields.Many2one(
        'cloudmanager.provider',
        'Provider',
        help="The provider this image is valid for",
    )
    slug = fields.Text(
        help="Provider abbreviated name used in templates",
    )

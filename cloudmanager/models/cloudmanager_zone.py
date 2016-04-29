# -*- coding: utf-8 -*-
from openerp import models, fields
# from openerp.exceptions import ValidationError


class CloudmanagerZone(models.Model):
    _name = 'cloudmanager.zone'
    _description = 'Cloud service provider name of service region or zone'

    name = fields.Char(
        required=True,
        help="Provider name of the geographical region or zone that will "
        "host the server",
    )
    notes = fields.Text(
        help="Freeform details regarding this provider zone or region",
    )
    # TODO provider and slug should not be required?
    provider_id = fields.Many2one(
        'cloudmanager.provider',
        string="Provider",
        help="The provider this region is valid for",
    )
    slug = fields.Text(
        help="Provider abbreviated name used in templates",
    )

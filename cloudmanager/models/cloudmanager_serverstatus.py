# -*- coding: utf-8 -*-

from openerp import models, fields
# from openerp.exceptions import ValidationError


class ServerStatus(models.Model):
    _name = 'cloudmanager.serverstatus'
    _description = 'Cloud Manager server status'

    name = fields.Char(
        required=True,
        readonly=True,
        help="Server status name"
    )
    notes = fields.Text(
        help="Freeform details regarding this server status",
    )

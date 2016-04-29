# -*- coding: utf-8 -*-
from openerp import models, fields
# from openerp.exceptions import ValidationError


class CloudmanagerProvider(models.Model):
    _name = 'cloudmanager.provider'
    _description = 'Cloud service provider with all API required data'

    name = fields.Char(
        required=True,
        help="Name of the cloud provider organization",
    )
    creata_template = fields.Text(
        help="REST Create template",
    )
    delete_template = fields.Text(
        help="REST Delete template",
    )
    stop_template = fields.Text(
        help="REST Stop template",
    )
    start_template = fields.Text(
        help="REST Start template",
    )
    main_url = fields.Char(
        string="Main URL",
        help="Provider administrative web app URL",
    )
    api_url = fields.Char(
        string="API URL",
        help="Provider API URL",
    )
    api_user = fields.Char(
        string="API User",
        help="API login or username",
    )
    # for convention do not strip field names
    api_password = fields.Char(
        string="API Password",
        help="API password",
    )
    notes = fields.Text(
        help="Freeform details regarding this cloud provider",
    )

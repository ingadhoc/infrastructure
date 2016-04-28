# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError 
# from requests import requests
from string import Template
import json
import time


class Zone(models.Model):
    _name='cloudmanager.zone'
    _description='Cloud service provider name of service region or zone'
    name=fields.Char(required=True,
            help="Provider name of the geographical region or zone that will host the server")
    ftNotes=fields.Text( string="ftNotes",required=False,
            help="Freeform details regarding this provider zone or region")
    fm2oProvider=fields.Many2one('cloudmanager.provider',required=False,string="fm2oProvider",
            help="The provider this region is valid for")
    fcSlug=fields.Text( string="fcSlug",required=False,
            help="Provider abbreviated name used in templates")
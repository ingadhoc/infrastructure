# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError 
# from requests import requests
from string import Template
import json


class Image(models.Model):
    _name='cloudmanager.image'
    _description='Cloud service provider OS image name'
    name=fields.Char(required=True,
            help="Provider name of the OS image")
    ftNotes=fields.Text( string="ftNotes",required=False,
            help="Freeform details regarding this OS image")
    fm2oProvider=fields.Many2one('cloudmanager.provider',required=False,string="fm2oProvider",
            help="The provider this image is valid for")
    fcSlug=fields.Text( string="fcSlug",required=False,
            help="Provider abbreviated name used in templates")
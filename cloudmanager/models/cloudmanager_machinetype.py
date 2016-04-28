# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError 
# from requests import requests
from string import Template
import json
import time


class MachineType(models.Model):
    _name='cloudmanager.machinetype'
    _description='Cloud service provider server specification shorthand name'
    name=fields.Char(required=True,
            help="Provider name of the machine type or droplet size (server specification)")
    ftNotes=fields.Text( string="ftNotes",required=False,
            help="Freeform details regarding this machine type, droplet size or server specification")
    fm2oProvider=fields.Many2one('cloudmanager.provider',required=False,string="fm2oProvider",
            help="The provider this machine type is valid for")
    fcSlug=fields.Text( string="fcSlug",required=False,
            help="Provider abbreviated name used in templates")

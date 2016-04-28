# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError 
# from requests import requests
from string import Template
import json
import time


class ServerStatus(models.Model):
    _name='cloudmanager.serverstatus'
    _description='Cloud Manager server status'
    name=fields.Char(required=True,readonly=True,
            help="Server status name")
    ftNotes=fields.Text( string="ftNotes",required=False,
            help="Freeform details regarding this server status")
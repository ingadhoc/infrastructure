# -*- coding: utf-8 -*-
from openerp import models, fields
# from openerp.exceptions import ValidationError


class CloudmanagerProvider(models.Model):
    _name='cloudmanager.provider'
    _description='Cloud service provider with all API required data'
    name=fields.Char( required=True,
            help="Name of the cloud provider organization")
    ftCreateTemplate=fields.Text( string="ftCreateTemplate", required=False,
            help="REST Create template")
    ftDeleteTemplate=fields.Text( string="ftDeleteTemplate",required=False,
            help="REST Delete template")
    ftStopTemplate=fields.Text( string="ftStopTemplate", required=False,
            help="REST Stop template")
    ftStartTemplate=fields.Text( string="ftStartTemplate", required=False,
            help="REST Start template")
    fcMainURL=fields.Char( string="fcMainURL", required=False,
            help="Provider administrative web app URL")
    fcAPIURL=fields.Char( string="fcAPIURL", required=False,
            help="Provider API URL")
    fcAPIUser=fields.Char( string="fcAPIUser", required=False,
            help="API login or username")
    fcAPIPasswd=fields.Char( string="fcAPIPasswd", required=False,
            help="API password")
    ftNotes=fields.Text( string="ftNotes", required=False,
            help="Freeform details regarding this cloud provider")
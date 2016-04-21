# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Provider(models.Model):
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

class MachineType(models.Model):
    _name='cloudmanager.machinetype'
    _description='Cloud service provider server specification shorthand name'
    name=fields.Char(required=True,
            help="Provider name of the machine type or droplet size (server specification)")
    ftNotes=fields.Text( string="ftNotes",required=False,
            help="Freeform details regarding this machine type, droplet size or server specification")
    fm2oProvider=fields.Many2one('cloudmanager.provider',required=False,string="fm2oProvider",
            help="The provider this machine type is valid for")

class Image(models.Model):
    _name='cloudmanager.image'
    _description='Cloud service provider OS image name'
    name=fields.Char(required=True,
            help="Provider name of the OS image")
    ftNotes=fields.Text( string="ftNotes",required=False,
            help="Freeform details regarding this OS image")
    fm2oProvider=fields.Many2one('cloudmanager.provider',required=False,string="fm2oProvider",
            help="The provider this image is valid for")

class Zone(models.Model):
    _name='cloudmanager.zone'
    _description='Cloud service provider name of service region or zone'
    name=fields.Char(required=True,
            help="Provider name of the geographical region or zone that will host the server")
    ftNotes=fields.Text( string="ftNotes",required=False,
            help="Freeform details regarding this provider zone or region")
    fm2oProvider=fields.Many2one('cloudmanager.provider',required=False,string="fm2oProvider",
            help="The provider this region is valid for")

class ServerStatus(models.Model):
    _name='cloudmanager.serverstatus'
    _description='Cloud Manager server status'
    name=fields.Char(required=True,readonly=True,
            help="Server status name")
    ftNotes=fields.Text( string="ftNotes",required=False,
            help="Freeform details regarding this server status")

class Server(models.Model):
    _name='cloudmanager.server'
    _description='The server instance'
    name=fields.Char(required=True, readonly=True, states={'draft': [('readonly', False)]},
            help="Provider name of the instance/droplet or VM server")
    fcServerFQDN=fields.Char( string="fcServerFQDN", required=False,
            help="FQDN DNS name of the instance/droplet or VM server")
    fcDiskSize=fields.Char( string="fcDiskSize",required=False,
            help="Disk size, usually related to fcMachineType, also may include disk type like SSD. For informational purposes only.")
    fcRamSize=fields.Char( string="fcRamSize",required=False,
            help="Ram size, usually related to fcMachineType for informational purposes only.")
    fcTimeZone=fields.Char( string="fcTimeZone",required=False,
            help="Linux time zone name")
    ftNotes=fields.Text( string="ftNotes", required=False,
            help="Freeform details regarding this server")
    fm2oProvider=fields.Many2one('cloudmanager.provider',required=False,string="fm2oProvider",
            help="The provider this server is using")
    fm2oMachineType=fields.Many2one('cloudmanager.machinetype',required=False,string="fm2oMachineType",
            help="The machine type this server is using")
    fm2oImage=fields.Many2one('cloudmanager.image',required=False,string="fm2oImage",
            help="The OS image this server is using")
    fm2oZone=fields.Many2one('cloudmanager.zone',required=False,string="fm2oZone",
            help="The zone or geographical region this server is assigned to")
    fm2oServerStatus=fields.Many2one('cloudmanager.serverstatus',required=False,string="fm2oServerStatus",
            help="The status of the server")
    # se tiene que llamar state
    state = fields.Selection([
        ('draft', 'Draft'), ('deployed', 'Deployed')],
        string='State', required=True, default='draft',)

    _sql_constraints = [
        ('fcServerFQDN_unique', 'unique(fcServerFQDN)',
            'fcServerFQDN must be unique per server'),
    ]

    # @api.multi
    # @api.constrains('fm2oMachineType', 'fm2oProvider')
    # def check_machine_type(self):
    #     for server in self:
    #         if server.fm2oMachineType.fm2oProvider != server.fm2oProvider:
    #             raise Warning('Machine Type Provider must be of server provider')

    @api.one
    @api.constrains('fm2oMachineType', 'fm2oProvider')
    def check_machine_type(self):
        if self.fm2oMachineType.fm2oProvider != self.fm2oProvider:
            raise Warning('Machine Type Provider must be of selected server provider')

    @api.onchange('fm2oProvider')
    def onchange_provider(self):
        self.fm2oMachineType = False
        self.fm2oImage = False
        self.fm2oZone = False

    @api.multi
    def to_draft(self):
        self.write({'state': 'draft'})
        # en esta manera hay dos problemas:
        # 1. self tiene que ser un solo registro (no puede ser un listado)
        # 2. usando write puedo escribir varios campos a la vez
        # self.state = 'draft'

    @api.multi
    def deploy_server(self):
        self.write({'state': 'deployed'})

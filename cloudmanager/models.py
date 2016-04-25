# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError 
from requests import requests
from string import Template

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
    fcServerFQDN=fields.Char( string="fcServerFQDN", required=True,
            help="FQDN DNS name of the instance/droplet or VM server")
    fcDiskSize=fields.Char( string="fcDiskSize",required=True,
            help="Disk size, usually related to fcMachineType, also may include disk type like SSD. For informational purposes only.")
    fcRamSize=fields.Char( string="fcRamSize",required=True,
            help="Ram size, usually related to fm2oMachineType for informational purposes only.")
    fcTimeZone=fields.Char( string="fcTimeZone",required=True,
            help="Linux time zone name",default='EST5EDT')
    ftNotes=fields.Text( string="ftNotes", required=True,
            help="Freeform details regarding this server")
    fm2oProvider=fields.Many2one('cloudmanager.provider',required=True,string="fm2oProvider",
            help="The provider this server is using",default=1)
    fm2oMachineType=fields.Many2one('cloudmanager.machinetype',required=True,string="fm2oMachineType",
            help="The machine type this server is using")
    fm2oImage=fields.Many2one('cloudmanager.image',required=True,string="fm2oImage",
            help="The OS image this server is using")
    fm2oZone=fields.Many2one('cloudmanager.zone',required=True,string="fm2oZone",
            help="The zone or geographical region this server is assigned to")
    fm2oServerStatus=fields.Many2one('cloudmanager.serverstatus',required=True,string="fm2oServerStatus",
            help="The status of the server",default=1)
    fcProviderID=fields.Char( string="fcProviderID",required=False,readonly=True,
        help="Cloud provider ID assigned on VM creation")
    fcServerIPv4=fields.Char( string="fcServerIPv4",required=False,readonly=True,
        help="Cloud provider assigned public IPv4 number")
    # se tiene que llamar state
    state = fields.Selection([
        ('draft', 'Draft'), ('ready','Ready'), ('deployed','Deployed')],
        string='State', required=True, default='draft',)

    _sql_constraints = [
        ('fcServerFQDN_unique', 'UNIQUE(fcServerFQDN)', 'fcServerFQDN must be unique'),
        ('name', 'UNIQUE(name)', 'name must be unique'),
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
            raise ValidationError('Machine Type Provider must be of selected server provider')
        if self.fm2oImage.fm2oProvider != self.fm2oProvider:
            raise ValidationError('Image Provider must be of selected server provider')
        if self.fm2oZone.fm2oProvider != self.fm2oProvider:
            raise ValidationError('Image Provider must be of selected server provider')

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
    def to_ready(self):
        if self.state != 'draft':
            raise ValidationError('Can not change to ready VMs that are not in the workflow draft state')
        if not self.fm2oProvider.fcAPIPasswd:
            raise ValidationError('VM provider must have bearer token fcAPIPasswd defined')
        if not self.fm2oProvider.fcCreateTemplate:
            raise ValidationError('VM provider must have fcCreateTemplate defined')
        if not self.fm2oProvider.fcAPIURL:
            raise ValidationError('VM provider must have an API URL defined')
        if not self.name:
            raise ValidationError('VM must have a name')
        if not self.ftNotes:
            raise ValidationError('VM must have notes')
        if not self.fm2oProvider:
            raise ValidationError('VM must have provider')
        if not self.fm2oMachineType:
            raise ValidationError('VM must have machine type')
        if not self.fm2oImage:
            raise ValidationError('VM must have an OS image ')
        if not self.fm2oZone:
            raise ValidationError('VM must have a provider zone')
        if self.fm2oServerStatus.id != 1:
            raise ValidationError('VM must be at Initial Setup VM state')
        self.write({'state':'ready'})
        return True

    ##
    # deployvm
    #   uses cloud provider API to create a running VM
    #   uses DNS provider API to create an A record for VM
    # notes
    #   initial development: we need to find out when we get the IP number back
    #   from different cloud provider APIs
    @api.multi
    def deployvm(self):
        ##
        #Start Validate
        if self.state != 'ready':
            raise ValidationError('Can not deploy VMs that are not in workflow ready state')
        if not self.fm2oProvider.fcAPIPasswd:
            raise ValidationError('VM provider must have bearer token fcAPIPasswd defined')
        if not self.fm2oProvider.fcCreateTemplate:
            raise ValidationError('VM provider must have fcCreateTemplate defined')
        if not self.fm2oProvider.fcAPIURL:
            raise ValidationError('VM provider must have an API URL defined')
        if not self.ftNotes:
            raise ValidationError('VM must have notes')
        if not self.fm2oImage:
            raise ValidationError('VM must have an OS image ')
        if not self.fm2oZone:
            raise ValidationError('VM must have a provider zone')
        if not self.fm2oProvider:
            raise ValidationError('VM must have a provider')
        if not self.fm2oMachineType:
            raise ValidationError('VM must have a machine type')
        if self.fm2oServerStatus.id != 1:
            raise ValidationError('VM must be at Initial Setup VM status')
        #end Validate
        ##

        ##
        #Start request VM creation
        Authorization = "Bearer " + str(self.fm2oProvider.fcAPIPasswd)
        h = {"Content-Type": "application/json","Authorization": Authorization}
        t = Template(self.fm2oProvider.fcCreateTemplate)
        #this depends on provider and template, since we use safe sub we can use provider prefixed mapping
        #for API dependent name value pairs
        d = t.safe_substitute(name=self.fcServerFQDN,size=self.fcRamSize,image=self.fm2oImage.name,zone=self.fm2oZone.name);
        r = requests.post(self.fm2oProvider.fcAPIURL,headers=h,data=d)
        raise ValidationError(r.text)
        #get provider ID
        #if valid ID we can place server in waiting for deploy server status
        self.write({'state':'deployed','fm2oServerStatus':'4'})
        #end Start request VM creation
        ##


        #we must check later (depends on provider?) to change server status to active
        #schedule check creation and get IP number etc
        self.write({'state':'deployed','fm2oServerStatus':'4'})

        ##
        #start DNS API
        #post DNS A zone creation request
        #end DNS API
        ##
        return True

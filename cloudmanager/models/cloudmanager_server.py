# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError 
# from requests import requests
from string import Template
import json
import time


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
    fcIPv4=fields.Char( string="fcIPv4",required=False,readonly=True,
        help="Cloud provider assigned public IPv4 number")
    fcSSHPublicKey=fields.Char( string="fcSSHPublicKey",required=False,readonly=True,
        help="Optional public ssh key for use in create template")
    # se tiene que llamar state
    state = fields.Selection([
        ('draft', 'Draft'), ('ready','Ready'), ('deployedActive','Deployed Active'),('deployedStopped','Deployed Stopped')],
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
        if not self.fm2oProvider.ftCreateTemplate:
            raise ValidationError('VM provider must have ftCreateTemplate defined')
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
        if not self.fm2oProvider.id==2:
            raise ValidationError('VM provider '+self.fm2oProvider.name+' is not supported for deploy at this time')
        if not self.fm2oProvider.fcAPIPasswd:
            raise ValidationError('VM provider must have bearer token fcAPIPasswd defined')
        if not self.fm2oProvider.ftCreateTemplate:
            raise ValidationError('VM provider must have ftCreateTemplate defined')
        if not self.fm2oProvider.fcAPIURL:
            raise ValidationError('VM provider must have an API URL defined')
        if not self.ftNotes:
            raise ValidationError('VM must have notes')
        if not self.fm2oImage.fcSlug:
            raise ValidationError('VM must have an OS image ')
        if not self.fm2oZone.fcSlug:
            raise ValidationError('VM must have a provider zone')
        if not self.fm2oProvider:
            raise ValidationError('VM must have a provider')
        if not self.fm2oMachineType.fcSlug:
            raise ValidationError('VM must have a machine type')
        if self.fm2oServerStatus.id != 1:
            raise ValidationError('VM must be at Initial Setup VM status')
        #end Validate
        ##

        ##
        #request VM creation
        Authorization = "Bearer " + str(self.fm2oProvider.fcAPIPasswd)
        h = {"Content-Type": "application/json","Authorization": Authorization}
        t = Template(self.fm2oProvider.ftCreateTemplate)
        #this depends on provider and template, since we use safe sub we can use provider prefixed mapping
        #for API dependent name value pairs
        d = t.safe_substitute(name=self.fcServerFQDN,size=self.fm2oMachineType.fcSlug,
                                image=self.fm2oImage.fcSlug,zone=self.fm2oZone.fcSlug)
        #raise ValidationError(d)
        r = requests.post(self.fm2oProvider.fcAPIURL,headers=h,data=d)
        if r.status_code != 202 and r.status_code != 200:
            raise ValidationError("Error: "+str(r.status_code)+r.text)
        theJSON=json.loads(r.text)
        if self.fm2oProvider.id==2:
            if "id" in theJSON["droplet"]:
                vmid = theJSON["droplet"]["id"]
            if not vmid:
                raise ValidationError("Error no VM ID: "+theJSON["droplet"])
        else:
            raise ValidationError("Error unsupported provider: "+self.fm2oProvider.name)
        #get provider ID
        #if valid ID we can place server in waiting for deploy server status
        self.write({'state':'deployedActive','fm2oServerStatus':'4','fcProviderID':vmid})
        #end request VM creation
        ##

        #we must check later (depends on provider?) to change server status to active
        #schedule check creation and get IP number etc
        #DO only at this time
        time.sleep(30)
        vmidURL=self.fm2oProvider.fcAPIURL+str('/')+str(vmid)
        r = requests.get(vmidURL,headers=h)
        if r.status_code != 200:
            raise ValidationError("Error getting VM data: "+str(r.status_code)+r.text)
        theJSON=json.loads(r.text)
        if "networks" in theJSON["droplet"] and "v4" in theJSON["droplet"]["networks"]:
            for i in theJSON["droplet"]["networks"]["v4"]:
                cIPv4 = i["ip_address"]
                break
        if not cIPv4:
            raise ValidationError("Error no IPv4: "+theJSON["droplet"]["networks"])
        self.write({'fm2oServerStatus':'2','fcIPv4':cIPv4})

        ##
        #start DNS API
        #post DNS A zone creation request
        #end DNS API
        ##
        return True

    ##
    # destroyvm
    #   uses cloud provider API to destroy a VM
    @api.multi
    def destroyvm(self):
        ##
        #Start Validate
        if self.state != 'deployedActive' and self.state != 'deployedStopped':
            raise ValidationError('Can not destroy VMs that are not in  a workflow deployed state')
        if not self.fm2oProvider.id==2:
            raise ValidationError('VM provider '+self.fm2oProvider.name+' is not supported for destroy at this time')
        if not self.fm2oProvider.fcAPIPasswd:
            raise ValidationError('VM provider must have bearer token fcAPIPasswd defined')
        if not self.fcProviderID:
            raise ValidationError('Server must have a valid fcProviderID')
        if not self.fm2oProvider.fcAPIURL:
            raise ValidationError('VM provider must have an API URL defined')
        if self.fm2oServerStatus.id == 1:
            raise ValidationError('VM must not be at Initial Setup VM status')
        #end Validate
        ##

        ##
        #request VM destroy
        #DO only at this time
        Authorization = "Bearer " + str(self.fm2oProvider.fcAPIPasswd)
        h = {"Content-Type": "application/json","Authorization": Authorization}
        vmidURL=self.fm2oProvider.fcAPIURL+str('/')+self.fcProviderID
        r = requests.get(vmidURL,headers=h)
        if r.status_code != 200:
            raise ValidationError("Error getting VM data: "+str(r.status_code)+r.text)
        theJSON=json.loads(r.text)
        if "status" in theJSON["droplet"]:
            if theJSON["droplet"]["status"] != "active" and theJSON["droplet"]["status"] != "off":
                raise ValidationError("Error unexpected provider server status: "+theJSON["droplet"]["status"])
        r = requests.delete(vmidURL,headers=h)
        if r.status_code != 204:
            raise ValidationError("Error destroyvm: "+str(r.status_code)+r.text)
        #initial setup server status. ready state. remove IP and ID.
        self.write({'fm2oServerStatus':'1','fcProviderID':'','fcIPv4':'','state':'ready'})

        return True

    ##
    # stopvm
    #   uses cloud provider API to destroy a VM
    @api.multi
    def stopvm(self):
        ##
        #Start Validate
        if self.state != 'deployedActive':
            raise ValidationError('Can not stop VMs that are not in a workflow active deployed state')
        if not self.fm2oProvider.id==2:
            raise ValidationError('VM provider '+self.fm2oProvider.name+' is not supported for stop at this time')
        if not self.fm2oProvider.fcAPIPasswd:
            raise ValidationError('VM provider must have bearer token fcAPIPasswd defined')
        if not self.fcProviderID:
            raise ValidationError('Server must have a valid fcProviderID')
        if not self.fm2oProvider.ftStopTemplate:
            raise ValidationError('VM provider must have valid ftStopTemplate')
        if not self.fm2oProvider.fcAPIURL:
            raise ValidationError('VM provider must have an API URL defined')
        if self.fm2oServerStatus.id == 1:
            raise ValidationError('VM must not be at Initial Setup VM status')
        #end Validate
        ##

        ##
        #request VM stop
        #DO only at this time
        Authorization = "Bearer " + str(self.fm2oProvider.fcAPIPasswd)
        h = {"Content-Type": "application/json","Authorization": Authorization}
        vmidURL=self.fm2oProvider.fcAPIURL+str('/')+self.fcProviderID
        r = requests.get(vmidURL,headers=h)
        if r.status_code != 200:
            raise ValidationError("Error getting VM data: "+str(r.status_code)+r.text)
        theJSON=json.loads(r.text)
        if "status" in theJSON["droplet"]:
            if theJSON["droplet"]["status"] != "active":
                if theJSON["droplet"]["status"] == "off":
                    self.write({'fm2oServerStatus':'3','state':'deployedStopped'})
                    return True
                else:
                    raise ValidationError("Error unexpected provider server status: "+theJSON["droplet"]["status"])
        vmidURL=self.fm2oProvider.fcAPIURL+str('/')+self.fcProviderID+str('/actions')
        r = requests.post(vmidURL,headers=h,data=self.fm2oProvider.ftStopTemplate)
        if r.status_code != 201:
            raise ValidationError("Error stopvm: "+str(r.status_code)+r.text)
        #waiting for stop server status. deplyed stopped state.
        self.write({'fm2oServerStatus':'6','state':'deployedStopped'})
        #wait and check for status change, this is only for development testing
        time.sleep(30)
        vmidURL=self.fm2oProvider.fcAPIURL+str('/')+self.fcProviderID
        r = requests.get(vmidURL,headers=h)
        if r.status_code != 200:
            raise ValidationError("Error getting VM data: "+str(r.status_code)+r.text)
        theJSON=json.loads(r.text)
        if "status" in theJSON["droplet"]:
            if theJSON["droplet"]["status"] != "off":
                raise ValidationError("Error unexpected provider server status: "+theJSON["droplet"]["status"])
        #stopped
        self.write({'fm2oServerStatus':'3'})
        return True

    ##
    # startvm
    #   uses cloud provider API to destroy a VM
    @api.multi
    def startvm(self):
        ##
        #Start Validate
        if self.state != 'deployedStopped':
            raise ValidationError('Can not start VMs that are not in a workflow stopped deployed state')
        if not self.fm2oProvider.id==2:
            raise ValidationError('VM provider '+self.fm2oProvider.name+' is not supported for stop at this time')
        if not self.fm2oProvider.fcAPIPasswd:
            raise ValidationError('VM provider must have bearer token fcAPIPasswd defined')
        if not self.fcProviderID:
            raise ValidationError('Server must have a valid fcProviderID')
        if not self.fm2oProvider.ftStartTemplate:
            raise ValidationError('VM provider must have valid ftStartTemplate')
        if not self.fm2oProvider.fcAPIURL:
            raise ValidationError('VM provider must have an API URL defined')
        if self.fm2oServerStatus.id == 1:
            raise ValidationError('VM must not be at Initial Setup VM status')
        #end Validate
        ##

        ##
        #request VM start
        #DO only at this time
        Authorization = "Bearer " + str(self.fm2oProvider.fcAPIPasswd)
        h = {"Content-Type": "application/json","Authorization": Authorization}
        vmidURL=self.fm2oProvider.fcAPIURL+str('/')+self.fcProviderID
        r = requests.get(vmidURL,headers=h)
        if r.status_code != 200:
            raise ValidationError("Error getting VM data: "+str(r.status_code)+r.text)
        theJSON=json.loads(r.text)
        if "status" in theJSON["droplet"]:
            if theJSON["droplet"]["status"] != "off":
                raise ValidationError("Error unexpected provider server status: "+theJSON["droplet"]["status"])
        vmidURL=self.fm2oProvider.fcAPIURL+str('/')+self.fcProviderID+str('/actions')
        r = requests.post(vmidURL,headers=h,data=self.fm2oProvider.ftStartTemplate)
        if r.status_code != 201:
            raise ValidationError("Error startvm: "+str(r.status_code)+r.text)
        #waiting for start server/reboot status. deployed active state.
        self.write({'fm2oServerStatus':'8','state':'deployedActive'})
        #wait and check for status change, this is only for development testing
        time.sleep(30)
        vmidURL=self.fm2oProvider.fcAPIURL+str('/')+self.fcProviderID
        r = requests.get(vmidURL,headers=h)
        if r.status_code != 200:
            raise ValidationError("Error getting VM data: "+str(r.status_code)+r.text)
        theJSON=json.loads(r.text)
        if "status" in theJSON["droplet"]:
            if theJSON["droplet"]["status"] != "active":
                raise ValidationError("Error unexpected provider server status: "+theJSON["droplet"]["status"])
        #active
        self.write({'fm2oServerStatus':'2'})

        return True

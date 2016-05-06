# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
import requests
from string import Template
import json
import time
import constants
from oauth2client.service_account import ServiceAccountCredentials
from httplib2 import Http
import logging
_logger = logging.getLogger(__name__)


class CloudmanagerServer(models.Model):
    _name = 'cloudmanager.server'
    _description = 'The server instance'

    ##
    # Schema definitions
    #
    name = fields.Char(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Provider name of the instance/droplet or VM server",
    )
    server_fqdn = fields.Char(
        string="Server FQDN",
        required=True,
        help="FQDN DNS name of the instance/droplet or VM server",
    )
    disk_size = fields.Char(
        required=True,
        help="Disk size, usually related to fcMachineType, also may include "
        "disk type like SSD. For informational purposes only.",
    )
    ram_size = fields.Char(
        required=True,
        help="Ram size, usually related to machine_type_id for informational "
        "purposes only.",
    )
    time_zone = fields.Char(
        required=True,
        help="Linux time zone name",
        default='EST5EDT',
    )
    notes = fields.Text(
        required=True,
        help="Freeform details regarding this server",
    )
    provider_id = fields.Many2one(
        'cloudmanager.provider',
        required=True,
        string="Provider",
        help="The provider this server is using",
        default=constants.GOOGLE_COMPUTE_ENGINE
    )
    machine_type_id = fields.Many2one(
        'cloudmanager.machinetype',
        required=True,
        string="Machine Type",
        help="The machine type this server is using",
    )
    image_id = fields.Many2one(
        'cloudmanager.image',
        required=True,
        string="Image",
        help="The OS image this server is using",
    )
    zone_id = fields.Many2one(
        'cloudmanager.zone',
        required=True,
        string="Zone",
        help="The zone or geographical region this server is assigned to",
    )
    server_status_id = fields.Many2one(
        'cloudmanager.serverstatus',
        required=True,
        string="Server Status",
        help="The status of the server",
        default=constants.INITIAL_SETUP
    )
    providerID = fields.Char(
        string="ProviderID",
        readonly=True,
        help="ID assigned on VM creation/deploy by some public cloud providers",
    )
    ipv4 = fields.Char(
        string="IPv4",
        readonly=True,
        help="Cloud provider assigned public ipv4 number",
    )
    ssh_public_key = fields.Char(
        readonly=True,
        help="Optional public ssh key for use in create template",
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready'),
        ('deployedActive', 'Deployed Active'),
        ('deployedStopped', 'Deployed Stopped'),
    ],
        string='State',
        required=True,
        default='draft',
    )
    _sql_constraints = [
        ('server_fqdn_unique', 'UNIQUE(server_fqdn)',
            'Server FQDN must be unique'),
        ('name', 'UNIQUE(name)', 'name must be unique'),
    ]

    ##
    # Class Methods
    #   first schema and view/UI related later the important ones

    ##
    # check_machine_type
    #   force refresh for UX UI check assignment
    @api.one
    @api.constrains('machine_type_id', 'provider_id')
    def check_machine_type(self):
        if self.machine_type_id.provider_id != self.provider_id:
            raise ValidationError(_(
                'Machine Type Provider must be of selected server provider'))
        if self.image_id.provider_id != self.provider_id:
            raise ValidationError(_(
                'Image Provider must be of selected server provider'))
        if self.zone_id.provider_id != self.provider_id:
            raise ValidationError(_(
                'Image Provider must be of selected server provider'))


    ##
    # onchange_provider
    #   force refresh for UX UI
    @api.onchange('provider_id')
    def onchange_provider(self):
        self.machine_type_id = False
        self.image_id = False
        self.zone_id = False


    ##
    # to_draft
    #   change to draft as long as server is not deployed
    @api.multi
    def to_draft(self):
        if self.server_status_id.id != constants.INITIAL_SETUP:
            raise ValidationError(_('VM must be at Initial Setup VM state'))
        self.write({'state': 'draft'})


    ##
    # validate_server_fields
    #   common basic field sanity checks
    @api.multi
    def validate_server_fields(self):
        """
        validate_server_fields
            basic server field validation
        """
        if not self.name:
            raise ValidationError(_('VM must have a name'))
        if not self.notes:
            raise ValidationError(_('VM must have notes'))
        if not self.provider_id:
            raise ValidationError(_('VM must have provider'))
        if not self.machine_type_id:
            raise ValidationError(_('VM must have machine type'))
        if not self.image_id:
            raise ValidationError(_('VM must have an OS image '))
        if not self.zone_id:
            raise ValidationError(_('VM must have a provider zone'))
        return True


    ##
    # to_ready
    #   checks and if possible changes state to ready
    @api.multi
    def to_ready(self):

        self.validate_server_fields()

        if self.state != 'draft':
            raise ValidationError(_(
                'Can not change to ready VMs that are not in the workflow '
                'draft state'))
        if not self.provider_id.api_password:
            raise ValidationError(_(
                'VM provider must have api_password defined'))
        if not self.provider_id.create_template:
            raise ValidationError(_(
                'VM provider must have create_template defined'))
        if not self.provider_id.api_url:
            raise ValidationError(_(
                'VM provider must have an API URL defined'))
        if self.server_status_id.id != constants.INITIAL_SETUP:
            raise ValidationError(_('VM must be at Initial Setup VM state'))
        self.write({'state': 'ready'})
        return True

    ##
    # DigitalOcean__credentials
    #   Get a valid bearer token for Digital Ocean OAuth2
    #   And return request header
    def DigitalOcean_credentials(self):
        Authorization = "Bearer " + str(self.provider_id.api_password)
        Header = {
            "Content-Type": "application/json", "Authorization": Authorization
        }
        return Header

    ##
    # GoogleComputeEngine_credentials
    #   Get a valid bearer token for Google OAuth2
    #   And return request header
    def GoogleComputeEngine_credentials(self):
        scopes = ['https://www.googleapis.com/auth/compute']
        credentials = ServiceAccountCredentials.from_json_keyfile_name('/mnt/extra-addons/odoo-infrastructure/cloudmanager/gcekey.json', scopes=scopes)
        credentials.refresh_token = self.provider_id.api_password
        credentials.refresh(Http())
        Authorization = "Bearer " + str(credentials.access_token)
        Header = {
            "Content-Type": "application/json", "Authorization": Authorization
        }
        return Header


    ##
    # GoogleComputeEngine_deployvm
    #   Uses GCE v1 API to deploy a VM
    @api.multi
    def GoogleComputeEngine_deployvm(self):
        if not self.provider_id.api_user:
            raise ValidationError("Error deployvm: provider api_user is required for project name")
        h = self.GoogleComputeEngine_credentials()
        t = Template(self.provider_id.create_template)
        d = t.safe_substitute(
            name=self.name,
            size=self.machine_type_id.slug,
            image=self.image_id.slug,
            zone=self.zone_id.slug,
        )
        api_template = Template(self.provider_id.api_url)
        api_cooked = api_template.safe_substitute(
            zone=self.zone_id.slug,
            project=self.provider_id.api_user,
        )
        r = requests.post(api_cooked, headers=h, data=d)
        if r.status_code != 200:
            raise ValidationError(_("Error: " + str(r.status_code) + '\n' +
                    r.text + '\n' + str(h) + '\n' + str(d) +
                     '\n' + str(api_cooked)))
        theJSON = json.loads(r.text)
        vmid = False
        if "id" in theJSON:
            vmid = theJSON["id"]
        if not vmid:
            raise ValidationError(_("Error: No VM ID returned"))
        self.write({
            'state': 'deployedActive',
            'server_status_id': constants.WAITING_FOR_DEPLOYMENT,
            'providerID': vmid
        })
        return True


    ##
    # DigitalOcean_deployvm
    #   Uses Digitial Ocean v2 API to deploy a VM
    @api.multi
    def DigitalOcean_deployvm(self):
        h = self.DigitalOcean_credentials()
        t = Template(self.provider_id.create_template)
        d = t.safe_substitute(
            name=self.server_fqdn,
            size=self.machine_type_id.slug,
            image=self.image_id.slug,
            zone=self.zone_id.slug,
        )
        r = requests.post(self.provider_id.api_url, headers=h, data=d)
        if r.status_code != 202:
            raise ValidationError(_("Error: " + str(r.status_code) + '\n' +
                    r.text + '\n' + str(h) + '\n' + str(d) +
                     '\n' + self.provider_id.api_url))
        theJSON = json.loads(r.text)
        vmid = False
        if "id" in theJSON["droplet"]:
            vmid = theJSON["droplet"]["id"]
        if not vmid:
            raise ValidationError(_("Error: No droplet ID returned"))

        # if valid ID we can place server in waiting for deploy server status
        self.write({
            'state': 'deployedActive',
            'server_status_id': constants.WAITING_FOR_DEPLOYMENT,
            'providerID': vmid
        })
        # end request VM creation
        ##

        # THIS WILL BE CHANGED to use the Odoo automation scheduling table
        time.sleep(20)
        vmidURL = self.provider_id.api_url+ str('/') + str(vmid)
        r = requests.get(vmidURL, headers=h)
        if r.status_code != 200:
            raise ValidationError(_(
                "Error getting VM data: %s%s") % (r.status_code, r.text))
        theJSON = json.loads(r.text)
        if (
                "networks" in theJSON["droplet"] and
                "v4" in theJSON["droplet"]["networks"]):
            for i in theJSON["droplet"]["networks"]["v4"]:
                cipv4 = i["ip_address"]
                break
        if not cipv4:
            raise ValidationError(_("Error no ipv4: %s") % theJSON["droplet"]["networks"])
        self.write({
            'server_status_id': constants.ACTIVE,
            'ipv4': cipv4})
        return True


    ##
    # deployvm
    #   front end for future plugin architecture for deploy VM for 
    #   any cloud provider API
    @api.multi
    def deployvm(self):
        ##
        # Start Validate
        self.validate_server_fields()

        if self.state != 'ready':
            raise ValidationError(_(
                'Can not deploy VMs that are not in workflow ready state'))
        if not self.provider_id.api_password:
            raise ValidationError(_(
                'VM provider must have api_passwd defined'))
        if not self.provider_id.create_template:
            raise ValidationError(_(
                'VM provider must have create_template defined'))
        if not self.provider_id.api_url:
            raise ValidationError(_(
                'VM provider must have an API URL defined'))
        if self.server_status_id.id != constants.INITIAL_SETUP:
            raise ValidationError(_('VM must be at Initial Setup VM status'))
        # end Validate
        ##

        ##
        # request VM creation
        # notes

        if self.provider_id.id == constants.GOOGLE_COMPUTE_ENGINE:
            self.GoogleComputeEngine_deployvm()
        elif self.provider_id.id == constants.DIGITAL_OCEAN:
            self.DigitalOcean_deployvm()

        ##
        # start DNS API TODO
        # post DNS A zone creation request
        # end DNS API
        ##
        return True

    ##
    # DigitalOcean_HasServerDeployed
    #   check provider to see if VM is up and running
    #   if it is change status to active
    def DigitalOcean_HasServerDeployed(self):
        _logger.info('server id: ' + str(self.id))
        return True

    ##
    # GoogleComputeEngine_header2
    @api.multi
    def GoogleComputeEngine_header2(self):
        scopes = ['https://www.googleapis.com/auth/compute']
        credentials = ServiceAccountCredentials.from_json_keyfile_name('/mnt/extra-addons/odoo-infrastructure/cloudmanager/gcekey.json', scopes=scopes)
        credentials.refresh_token = self.provider_id.api_password
        credentials.refresh(Http())
        Authorization = "Bearer " + str(credentials.access_token)
        h = {
            "Content-Type": "application/json", "Authorization": Authorization
        }
        return h

    ##
    # GoogleComputeEngine_HasServerDeployed
    #   Provider specific status check to see if server has actually deployed
    def GoogleComputeEngine_HasServerDeployed(self):

        _logger.info('server id: ' + str(self.id))

        h = self.GoogleComputeEngine_header2

        api_template = Template(self.provider_id.api_url)
        api_cooked = api_template.safe_substitute(
            zone=self.zone_id.slug,
            project=self.provider_id.api_user,
        )
        vmidURL = api_cooked + str('/') + str(self.name)

        r = requests.get(vmidURL, headers=h)
        if r.status_code != 200:
            _logger.info('requests.get error: ' + str(r.status_code) + ' ' + str(r.text))
        theJSON = json.loads(r.text)
        cipv4 = False
        if "networkInterfaces" in theJSON:
            for i in theJSON["networkInterfaces"]:
                for j in i["accessConfigs"]:
                    cipv4 = j["natIP"]
                    break
        if not cipv4:
            _logger.info('No cipv4')
            return
        self.write({
            'server_status_id': constants.ACTIVE,
            'ipv4': cipv4})
        _logger.info('Ok ' + str(cipv4))
        return


    ##
    # HasServerDeployed
    #   This method is to be called from scheduled actions subsystem
    @api.model
    def HasServerDeployed(self):
        _logger.info('start HasServerDeployed')
        servers = self.search([('server_status_id', '=', constants.WAITING_FOR_DEPLOYMENT)])   
        for server in servers:
            if server.provider_id.id == constants.GOOGLE_COMPUTE_ENGINE:
                server.GoogleComputeEngine_HasServerDeployed()
            elif server.provider_id.id == constants.DIGITAL_OCEAN:
                server.DigitalOcean_HasServerDeployed()
        _logger.info('end HasServerDeployed')
        return True


    ##
    # GoogleComputeEngine_destroyvm
    #   uses GCE v1 API to remove/delete/destroy a VM
    @api.multi
    def GoogleComputeEngine_destroyvm(self):
        if not self.provider_id.api_user:
            raise ValidationError("Error destroyvm: provider api_user is required for project name")
        h = self.GoogleComputeEngine_credentials()
        api_template = Template(self.provider_id.api_url)
        api_cooked = api_template.safe_substitute(
            zone=self.zone_id.slug,
            project=self.provider_id.api_user,
        )
        vmidURL=api_cooked+str('/')+self.name
        r = requests.delete(vmidURL,headers=h)
        if r.status_code != 204 and r.status_code != 200:
            raise ValidationError("Error destroyvm: "+str(r.status_code)+r.text)
        # initial setup server status. ready state. remove IP and ID.
        self.write({'server_status_id':constants.INITIAL_SETUP, 'providerID': '', 'IPv4': '', 'state': 'ready'})
        return True


    ##
    # DigitalOcean_destroyvm
    #   uses Digital Ocean v2 API to remove/delete/destroy a VM
    @api.multi
    def DigitalOcean_destroyvm(self):
        h = self.DigitalOcean_credentials()
        vmidURL=self.provider_id.api_url+str('/')+self.providerID
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
        # initial setup server status. ready state. remove IP and ID.
        self.write({'server_status_id':constants.INITIAL_SETUP, 'providerID': '', 'IPv4': '', 'state': 'ready'})
        return True


    ##
    # GoogleComputeEngine_stopvm
    #   uses GCE v1 API to stop a VM
    @api.multi
    def GoogleComputeEngine_stopvm(self):
        if not self.provider_id.api_user:
            raise ValidationError("Error stopvm: provider api_user is required for project name")
        h = self.GoogleComputeEngine_credentials()
        api_template = Template(self.provider_id.api_url)
        api_cooked = api_template.safe_substitute(
            zone=self.zone_id.slug,
            project=self.provider_id.api_user,
        )
        vmidURL=api_cooked+str('/')+self.name+str('/stop')
        r = requests.post(vmidURL,headers=h)
        if r.status_code != 200:
            raise ValidationError("Error stopvm: "+str(r.status_code)+r.text)
        # initial setup server status. ready state. remove IP and ID.
        self.write({'server_status_id': constants.STOPPED,'state': 'deployedStopped'})
        return True


    ##
    # DigitalOcean_stopvm
    #   uses Digital Ocean v2 API to stop a VM
    @api.multi
    def DigitalOcean_stopvm(self):
        h = self.DigitalOcean_credentials()
        vmidURL=self.provider_id.api_url+str('/')+self.providerID
        r = requests.get(vmidURL,headers=h)
        if r.status_code != 200:
            raise ValidationError("Error getting VM data: "+str(r.status_code)+r.text)
        theJSON=json.loads(r.text)
        if "status" in theJSON["droplet"]:
            if theJSON["droplet"]["status"] != "active":
                if theJSON["droplet"]["status"] == "off":
                    self.write({'server_status_id':constants.STOPPED, 'state': 'deployedStopped'})
                    return True
                else:
                    raise ValidationError("Error unexpected provider server status: "+theJSON["droplet"]["status"])
        vmidURL=self.provider_id.api_url+str('/')+self.providerID+str('/actions')
        r = requests.post(vmidURL,headers=h,data=self.provider_id.stop_template)
        if r.status_code != 201:
            raise ValidationError("Error stopvm: "+str(r.status_code)+r.text)
        # waiting for stop server status. deplyed stopped state.
        self.write({'server_status_id':constants.WAITING_FOR_STOP, 'state': 'deployedStopped'})
        # wait and check for status change, this is only for development testing
        time.sleep(20)
        vmidURL=self.provider_id.api_url+str('/')+self.providerID
        r = requests.get(vmidURL,headers=h)
        if r.status_code != 200:
            raise ValidationError("Error getting VM data: "+str(r.status_code)+r.text)
        theJSON=json.loads(r.text)
        if "status" in theJSON["droplet"]:
            if theJSON["droplet"]["status"] != "off":
                raise ValidationError("Error unexpected provider server status: "+theJSON["droplet"]["status"])
        # stopped
        self.write({'server_status_id':constants.STOPPED})
        return True


    ##
    # GoogleComputeEngine_startvm
    #   start a stopped VM instance
    @api.multi
    def GoogleComputeEngine_startvm(self):
        if not self.provider_id.api_user:
            raise ValidationError("Error startvm: provider api_user is required for project name")
        h = self.GoogleComputeEngine_credentials()
        api_template = Template(self.provider_id.api_url)
        api_cooked = api_template.safe_substitute(
            zone=self.zone_id.slug,
            project=self.provider_id.api_user,
        )
        vmidURL=api_cooked+str('/')+self.name+str('/start')
        r = requests.post(vmidURL,headers=h)
        if r.status_code != 200:
            raise ValidationError("Error startvm: "+str(r.status_code)+r.text)
        # initial setup server status. ready state. remove IP and ID.
        self.write({'server_status_id': constants.ACTIVE,'state': 'deployedActive'})
        return True


    ##
    # DigitalOcean_startvm
    #   uses Digital Ocean 2.0 API to start a VM
    @api.multi
    def DigitalOcean_startvm(self):
        h = self.DigitalOcean_credentials()
        vmidURL=self.provider_id.api_url+str('/')+self.providerID
        r = requests.get(vmidURL,headers=h)
        if r.status_code != 200:
            raise ValidationError("Error getting VM data: "+str(r.status_code)+r.text)
        theJSON=json.loads(r.text)
        if "status" in theJSON["droplet"]:
            if theJSON["droplet"]["status"] != "off":
                raise ValidationError("Error unexpected provider server status: "+theJSON["droplet"]["status"])
        vmidURL=self.provider_id.api_url+str('/')+self.providerID+str('/actions')
        r = requests.post(vmidURL,headers=h,data=self.provider_id.start_template)
        if r.status_code != 201:
            raise ValidationError("Error startvm: "+str(r.status_code)+r.text)
        # waiting for start server/reboot status. deployed active state.
        self.write({'server_status_id':constants.WAITING_FOR_START, 'state': 'deployedActive'})
        # wait and check for status change, this is only for development testing
        time.sleep(20)
        vmidURL=self.provider_id.api_url+str('/')+self.providerID
        r = requests.get(vmidURL,headers=h)
        if r.status_code != 200:
            raise ValidationError("Error getting VM data: "+str(r.status_code)+r.text)
        theJSON=json.loads(r.text)
        if "status" in theJSON["droplet"]:
            if theJSON["droplet"]["status"] != "active":
                raise ValidationError("Error unexpected provider server status: "+theJSON["droplet"]["status"])
        # active
        self.write({'server_status_id': '2'})
        return True


    ##
    # destroyvm
    #   uses cloud provider API to destroy a VM
    @api.multi
    def destroyvm(self):
        ##
        # Start Validate
        if self.state != 'deployedActive' and self.state != 'deployedStopped':
            raise ValidationError('Can not destroy VMs that are not in  a workflow deployed state')
        if not self.provider_id.api_password:
            raise ValidationError('VM provider must have api_password defined')
        if not self.provider_id.api_url:
            raise ValidationError('VM provider must have a valid API URL defined')
        if self.server_status_id.id == constants.INITIAL_SETUP:
            raise ValidationError('VM must not be at Initial Setup VM status')
        # end Validate
        ##

        ##
        # request VM destroy
        if self.provider_id.id == constants.GOOGLE_COMPUTE_ENGINE:
            self.GoogleComputeEngine_destroyvm()
        elif self.provider_id.id == constants.DIGITAL_OCEAN:
            self.DigitalOcean_destroyvm()
        return True

    ##
    # stopvm
    #   uses cloud provider API to stop a VM
    @api.multi
    def stopvm(self):
        ##
        # Start Validate
        if self.state != 'deployedActive':
            raise ValidationError('Can not stop VMs that are not in a workflow active deployed state')
        if not self.provider_id.api_password:
            raise ValidationError('VM provider must have api_password defined')
        if not self.provider_id.stop_template:
            raise ValidationError('VM provider must have valid stop_template')
        if not self.provider_id.api_url:
            raise ValidationError('VM provider must have a valid API URL defined')
        if self.server_status_id.id == constants.INITIAL_SETUP:
            raise ValidationError('VM must not be at Initial Setup VM status')
        # end Validate
        ##

        ##
        # request VM stop
        if self.provider_id.id == constants.GOOGLE_COMPUTE_ENGINE:
            self.GoogleComputeEngine_stopvm()
        elif self.provider_id.id == constants.DIGITAL_OCEAN:
            self.DigitalOcean_stopvm()
        return True


    ##
    # startvm
    #   uses cloud provider API to start a VM
    @api.multi
    def startvm(self):
        ##
        # Start Validate
        if self.state != 'deployedStopped':
            raise ValidationError('Can not start VMs that are not in a workflow stopped deployed state')
        if not self.provider_id.api_password:
            raise ValidationError('VM provider must have api_password defined')
        if not self.provider_id.start_template:
            raise ValidationError('VM provider must have valid start_template')
        if not self.provider_id.api_url:
            raise ValidationError('VM provider must have a valid API URL defined')
        if self.server_status_id.id == constants.INITIAL_SETUP:
            raise ValidationError('VM must not be at Initial Setup VM status')
        # end Validate
        ##

        ##
        # request VM start
        if self.provider_id.id == constants.GOOGLE_COMPUTE_ENGINE:
            self.GoogleComputeEngine_startvm()
        elif self.provider_id.id == constants.DIGITAL_OCEAN:
            self.DigitalOcean_startvm()
        return True

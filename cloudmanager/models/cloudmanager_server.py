# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
import requests
from string import Template
import json
import time


class Server(models.Model):
    _name = 'cloudmanager.server'
    _description = 'The server instance'

    name = fields.Char(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Provider name of the instance/droplet or VM server",
    )
    server_FQDN = fields.Char(
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
        # TODO remove this, if we want a default we should use a function
        # that try to search one, because 1 coudl not exist
        # default=1
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
        string="server_status_id",
        help="The status of the server",
        # TODO remove this, if we want a default we should use a function
        # that try to search one, because 1 coudl not exist
        # default=1,
    )
    providerID = fields.Char(
        string="ProviderID",
        readonly=True,
        help="Cloud provider ID assigned on VM creation",
    )
    IPv4 = fields.Char(
        readonly=True,
        help="Cloud provider assigned public IPv4 number",
    )
    SSH_public_key = fields.Char(
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
        ('server_FQDN_unique', 'UNIQUE(server_FQDN)',
            'Server FQDN must be unique'),
        ('name', 'UNIQUE(name)', 'name must be unique'),
    ]

    # @api.multi
    # @api.constrains('machine_type_id', 'provider_id')
    # def check_machine_type(self):
    #     for server in self:
    #         if server.machine_type_id.provider_id != server.provider_id:
    #             raise Warning(
    #                 'Machine Type Provider must be of server provider')

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

    @api.onchange('provider_id')
    def onchange_provider(self):
        self.machine_type_id = False
        self.image_id = False
        self.zone_id = False

    @api.multi
    def to_draft(self):
        self.write({'state': 'draft'})
        # en esta manera hay dos problemas:
        # 1. self tiene que ser un solo registro (no puede ser un listado)
        # 2. usando write puedo escribir varios campos a la vez
        # self.state = 'draft'

    @api.multi
    def to_ready(self):
        # TODO borrar varias de las validaciones porque si los campos son
        # required ya no hace falta esta validación
        if self.state != 'draft':
            raise ValidationError(_(
                'Can not change to ready VMs that are not in the workflow '
                'draft state'))
        if not self.provider_id.fcAPIPasswd:
            raise ValidationError(_(
                'VM provider must have bearer token fcAPIPasswd defined'))
        if not self.provider_id.ftCreateTemplate:
            raise ValidationError(_(
                'VM provider must have ftCreateTemplate defined'))
        if not self.provider_id.fcAPIURL:
            raise ValidationError(_(
                'VM provider must have an API URL defined'))
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
        if self.server_status_id.id != 1:
            raise ValidationError('VM must be at Initial Setup VM state')
        self.write({'state': 'ready'})
        return True

    @api.multi
    def deployvm(self):
        """
        deployvm
            uses cloud provider API to create a running VM
            uses DNS provider API to create an A record for VM
        notes
            initial development: we need to find out when we get the IP number
                back
            from different cloud provider APIs
        """
        # Start Validate
        if self.state != 'ready':
            raise ValidationError(_(
                'Can not deploy VMs that are not in workflow ready state'))
        # TODO this check should be different and not to a related id
        # perhups we can check if start_template is set ond provider or
        # something else.
        # if not self.provider_id.id == 2:
        #     raise ValidationError(_(
        #         'VM provider %s is not supported for deploy yet') % (
        #         self.provider_id.name))
        if not self.provider_id.fcAPIPasswd:
            raise ValidationError(_(
                'VM provider must have bearer token fcAPIPasswd defined'))
        if not self.provider_id.ftCreateTemplate:
            raise ValidationError(_(
                'VM provider must have ftCreateTemplate defined'))
        if not self.provider_id.fcAPIURL:
            raise ValidationError(_(
                'VM provider must have an API URL defined'))
        if not self.notes:
            raise ValidationError(_('VM must have notes'))
        if not self.image_id.fcSlug:
            raise ValidationError(_('VM must have an OS image '))
        if not self.zone_id.fcSlug:
            raise ValidationError(_('VM must have a provider zone'))
        if not self.provider_id:
            raise ValidationError(_('VM must have a provider'))
        if not self.machine_type_id.fcSlug:
            raise ValidationError(_('VM must have a machine type'))
        if self.server_status_id.id != 1:
            raise ValidationError(_('VM must be at Initial Setup VM status'))
        # end Validate
        ##

        ##
        # r equest VM creation
        Authorization = "Bearer " + str(self.provider_id.fcAPIPasswd)
        h = {
            "Content-Type": "application/json", "Authorization": Authorization
        }
        t = Template(self.provider_id.ftCreateTemplate)
        # this depends on provider and template, since we use safe sub we can
        # use provider prefixed mapping for API dependent name value pairs
        d = t.safe_substitute(
            name=self.server_FQDN,
            size=self.machine_type_id.fcSlug,
            image=self.image_id.fcSlug,
            zone=self.zone_id.fcSlug,
        )
        # raise ValidationError(d)
        r = requests.post(self.provider_id.fcAPIURL, headers=h, data=d)
        if r.status_code != 202 and r.status_code != 200:
            # TODO use %
            raise ValidationError("Error: " + str(r.status_code) + r.text)
        theJSON = json.loads(r.text)
        # TODO this check should be different and not to a related id
        # we add this dumm id till fix
        vmid = False
        # if self.provider_id.id == 2:
        #     if "id" in theJSON["droplet"]:
        #         vmid = theJSON["droplet"]["id"]
        #     if not vmid:
        #         # TODO use %
        #         raise ValidationError("Error no VM ID: "+theJSON["droplet"])
        # else:
        #     # TODO use %
        #     raise ValidationError(
        #         "Error unsupported provider: "+self.provider_id.name)

        # get provider ID
        # if valid ID we can place server in waiting for deploy server status
        self.write({
            'state': 'deployedActive',
            # TODO we should get this status by other way, not id
            # 'server_status_id': '4',
            'providerID': vmid
        })
        # end request VM creation
        ##

        # we must check later (depends on provider?) to change server status
        # to active schedule check creation and get IP number etc
        # DO only at this time
        time.sleep(30)
        vmidURL = self.provider_id.fcAPIURL + str('/') + str(vmid)
        r = requests.get(vmidURL, headers=h)
        if r.status_code != 200:
            raise ValidationError(_(
                "Error getting VM data: %s%s") % (r.status_code, r.text))
        theJSON = json.loads(r.text)
        if (
                "networks" in theJSON["droplet"] and
                "v4" in theJSON["droplet"]["networks"]):
            for i in theJSON["droplet"]["networks"]["v4"]:
                cIPv4 = i["ip_address"]
                break
        if not cIPv4:
            raise ValidationError(_(
                "Error no IPv4: %s") % theJSON["droplet"]["networks"])
        self.write({
            # TODO we should get this status by other way, not id
            # 'server_status_id': '2',
            'fcIPv4': cIPv4})

        ##
        # start DNS API
        # post DNS A zone creation request
        # end DNS API
        ##
        return True

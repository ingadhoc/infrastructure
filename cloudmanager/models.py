# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Provider(models.Model):
	_name='cloudmanager.provider'
	fcName=fields.Char(string="fcName",
			required=True,
			help="Name of the cloud provider organization")
	fcImage=fields.Char(string="fcImage",
			required=True,
			help="VM image name formatted as required by provider API")
	fcMachineType=fields.Char(string="fcMachineType",
			required=True,
			help="VM machine or server type formatted as required by provider API")
	ftCreateTemplate=fields.Text(string="ftCreateTemplate",
			required=True,
			help="REST Create template")
	ftDeleteTemplate=fields.Text(string="fDeleteTemplate",
			required=True,
			help="REST Delete template")
	ftStopTemplate=fields.Text(string="ftStopTemplate",
			required=True,
			help="REST Stop template")
	ftStartTemplate=fields.Text(string="ftStartTemplate",
			required=True,
			help="REST Start template")
	fcMainURL=fields.Char(string="fcMainURL",
			required=True,
			help="Provider administrative web app URL")
	fcAPIURL=fields.Char(string="fcAPIURL",
			required=True,
			help="Provider API URL")
	fcAPIUser=fields.Char(string="fcAPIUser",
			required=True,
			help="API login or username")
	fcAPIPasswd=fields.Char(string="fcAPIPasswd",
			required=True,
			help="API password")
	ftNotes=fields.Text(string="ftNotes",
			required=False,
			help="Freeform details regarding this cloud provider")

class Server(models.Model):
	_name='cloudmanager.server'
	fcServer=fields.Char(string="fcServer",
			required=True,
			help="Provider name of the instance/droplet or VM server")
	fcServerFQDN=fields.Char(string="fcServerFQDN",
			required=True,
			help="FQDN DNS name of the instance/droplet or VM server")
	fcImage=fields.Char(string="fcImage",
			required=True,
			help="VM image name formatted as required by provider API")
	fcMachineType=fields.Char(string="fcMachineType",
			required=True,
			help="VM machine or server type formatted as required by provider API")
	fcDiskSize=fields.Char(string="fcDiskSize",
			required=True,
			help="Disk size, usually related to fcMachineType, also may include disk type like SSD. For informational purposes only.")
	fcRamSize=fields.Char(string="fcRamSize",
			required=True,
			help="Ram size, usually related to fcMachineType for informational purposes only.")
	fcZone=fields.Char(string="fcZone",
			required=True,
			help="Provider zone or region name")
	fcTimeZone=fields.Char(string="fcTimeZone",
			required=True,
			help="Provider time zone name")
	ftNotes=fields.Text(string="ftNotes",
			required=False,
			help="Freeform details regarding this cloud provider")


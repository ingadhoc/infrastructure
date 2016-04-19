from openerp import models, fields, api

class DeployVM(models.TransientModel):
	_name = 'cloudmanager.deployvm'

	def _default_session(self):
		return	self.env['cloudmanager.server'].browse(self._context.get('active_id'))

	session_id = fields.Many2one('cloudmanager.server',
	string="fcName", required=True, default=_default_session)

import logging
from openerp import models, fields, api

_logger = logging.getLogger(__name__)


class DeployVM(models.TransientModel):
    _name = 'cloudmanager.deployvm'

    def _default_session(self):
        return self.env['cloudmanager.server'].browse(self._context.get('active_id'))

    server_id = fields.Many2one('cloudmanager.server', string="fcName", required=True, default=_default_session)

    @api.multi
    def deployvm(self):
        print 'self.env.context', self.env.context
        print 'self.env.uid', self.env.uid
        print 'self.env.cr', self.env.cr
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            return True
        servers = self.env['cloudmanager.server'].browse(active_ids)
        for server in servers:
        #call the deploy method  in the ProviderAPI class
            _logger.error('server_id %s', server.id)
        return {}


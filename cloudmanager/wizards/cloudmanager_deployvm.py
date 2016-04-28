# -*- coding: utf-8 -*-
import logging
from openerp import models, api
_logger = logging.getLogger(__name__)


class DeployVM(models.TransientModel):
    _name = 'cloudmanager.deployvm'

    @api.multi
    def deployvm(self):
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            return True
        servers = self.env['cloudmanager.server'].browse(active_ids)
        for server in servers:
            # call the deploy method  in the ProviderAPI class
            # validate
            server.state = 'draft'
            # TODO we should remove some of this checks because some of them
            # are required fields
            if not server.name:
                return False
            if not server.notes:
                return False
            if not server.provider_id:
                return False
            if not server.machine_type_id:
                return False
            if not server.server_status_id:
                return False
            server.state = 'ready'
            _logger.info('server_id %s', server.id)
        return True

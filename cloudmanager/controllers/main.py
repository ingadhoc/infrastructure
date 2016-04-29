# -*- coding: utf-8 -*-
# from openerp import http


# class Wallis(http.Controller):
#     @http.route('/cloudmanager/cloudmanager/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cloudmanager/cloudmanager/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cloudmanager.listing', {
#             'root': '/cloudmanager/cloudmanager',
#             'objects': http.request.env[
#             'cloudmanager.cloudmanager'].search([]),
#         })

#     @http.route(
#         '/cloudmanager/cloudmanager/objects/'
#         '<model("cloudmanager.cloudmanager"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cloudmanager.object', {
#             'object': obj
#         })

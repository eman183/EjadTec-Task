# -*- coding: utf-8 -*-
# from odoo import http


# class EjadTask(http.Controller):
#     @http.route('/ejad_task/ejad_task', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ejad_task/ejad_task/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ejad_task.listing', {
#             'root': '/ejad_task/ejad_task',
#             'objects': http.request.env['ejad_task.ejad_task'].search([]),
#         })

#     @http.route('/ejad_task/ejad_task/objects/<model("ejad_task.ejad_task"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ejad_task.object', {
#             'object': obj
#         })


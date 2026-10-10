# -*- coding: utf-8 -*-
{
    'name': "ejad_task",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Eman Shalaby",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product','stock','point_of_sale','stock_delivery','website_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/menus.xml',
        'views/pos_config.xml',
        'views/product_rop_views.xml',
        'wizard/update_quantity_views.xml',
        'views/website_rop_templates.xml',
        'views/website_realtime_rop_templates.xml',
        'views/website_menus.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
'assets': {
    'point_of_sale._assets_pos': [
        'ejad_task/static/src/js/pos_rop_validation.js',
        'ejad_task/static/src/js/payment_screen.js',
        'ejad_task/static/src/js/cash_now_button.js',
        'ejad_task/static/src/xml/cash_now_button.xml',

    ],
    'web.assets_frontend': [
        'ejad_task/static/src/js/realtime_rop.js',
    ],
},
}


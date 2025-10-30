# -*- coding: utf-8 -*-
{
    'name': "Employee Portal",

    'summary': "Employee Portal | Employee can view their backend details",

    'author': "Irfan Ullah",
    'website': "https://www.youtube.com/@irfanullah",
    'category': 'Portal',
    'version': '19.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'portal', 'hr_holidays', 'planning'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'security/portal_user_group.xml',
        'views/new_menus_in_portal.xml',
        'views/employee_leave_template.xml',
        'views/weekly_schedule_template.xml',
    ],
    'images': ['static/description/banner.png'],


"license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
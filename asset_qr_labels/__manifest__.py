# -*- coding: utf-8 -*-
{
    "name": "Asset QR Labels",
    "version": "19.0.1.0.0",
    "summary": "Generate QR codes for account assets with name and date",
    "category": "Accounting/Assets",
    "author": "HIND",
    "depends": ["account_asset", "web"],
    "data": [
        "views/account_asset_views.xml",
        "reports/asset_qr_report.xml",
        "reports/asset_qr_templates.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
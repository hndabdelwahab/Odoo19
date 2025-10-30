# -*- coding: utf-8 -*-
{
    "name": "Product QR Labels",
    "version": "19.0.1.0.0",
    "summary": "Generate QR codes for products with name and serial number",
    "category": "Sales/Sales",
    "author": "HIND",
    "depends": ["product", "web"],
    "data": [
        "views/product_qr_views.xml",
        "reports/product_qr_report.xml",
        "reports/product_qr_templates.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
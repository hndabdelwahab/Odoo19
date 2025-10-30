# -*- coding: utf-8 -*-
import base64
from io import BytesIO
from urllib.parse import quote_plus

from odoo import api, fields, models
from odoo.exceptions import UserError

try:
    import qrcode  
except Exception:
    qrcode = None

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None


class ProductTemplate(models.Model):
    _inherit = "product.template"

    qr_payload = fields.Char(string="QR Payload", compute="_compute_qr_payload")
    qr_payload_esc = fields.Char(string="QR Payload (Escaped)", compute="_compute_qr_payload")
    qr_image = fields.Binary(string="QR Code Image", compute="_compute_qr_image", store=True)
    product_serial_number = fields.Char(string="Serial Number", compute="_compute_product_serial", store=False)

    def _compute_product_serial(self):
        for rec in self:
            if rec.id:
                rec.product_serial_number = f"PRD-{rec.id:05d}"
            else:
                rec.product_serial_number = ""

    @api.depends("name", "product_serial_number")  
    def _compute_qr_payload(self):
        for rec in self:
            if rec.name:
                payload = f"{rec.product_serial_number} | {rec.name}"
                rec.qr_payload = payload
                rec.qr_payload_esc = quote_plus(payload)
            else:
                rec.qr_payload = ""
                rec.qr_payload_esc = ""

    @api.depends("qr_payload")
    def _compute_qr_image(self):
        for rec in self:
            if qrcode and rec.qr_payload:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=5,
                    border=2,
                )
                qr.add_data(rec.qr_payload)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                buf = BytesIO()
                img.save(buf, format="PNG")
                rec.qr_image = base64.b64encode(buf.getvalue())
            else:
                rec.qr_image = False
    
    def action_generate_qr_code(self):
        for record in self:
            if not record.name:
                raise UserError("Please provide a product name before generating QR code.")
            if not qrcode:
                raise UserError("QR Code library not installed. Please install 'qrcode' Python package: pip install qrcode[pil]")
            record._compute_product_serial()
            record._compute_qr_payload()
            record._compute_qr_image()
        return True
    
    def action_print_qr_label(self):
        self.ensure_one()
        
        if not self.qr_image:
            self.action_generate_qr_code()
        
        if not self.qr_image:
            raise UserError("QR Code could not be generated. Please ensure the qrcode library is installed.")
        
        return self.env.ref('product_qr_labels.action_report_product_qr_label').report_action(self, config=False)
    
    def action_download_qr_code(self):
        self.ensure_one()
        
        if not self.qr_image:
            self.action_generate_qr_code()
        
        if not self.qr_image:
            raise UserError("QR Code could not be generated. Please ensure the qrcode library is installed.")
        
        filename = f"{self.product_serial_number}_qr_code.png"
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/qr_image?download=true&filename={filename}',
            'target': 'self',
        }


class ProductProduct(models.Model):
    _inherit = "product.product"

    qr_payload = fields.Char(string="QR Payload", compute="_compute_qr_payload", related='product_tmpl_id.qr_payload')
    qr_payload_esc = fields.Char(string="QR Payload (Escaped)", compute="_compute_qr_payload", related='product_tmpl_id.qr_payload_esc')
    qr_image = fields.Binary(string="QR Code Image", compute="_compute_qr_image", related='product_tmpl_id.qr_image')
    product_serial_number = fields.Char(string="Serial Number", related='product_tmpl_id.product_serial_number')
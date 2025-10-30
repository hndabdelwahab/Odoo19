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


class AccountAsset(models.Model):
    _inherit = "account.asset"

    qr_payload = fields.Char(string="QR Payload", compute="_compute_qr_payload")
    qr_payload_esc = fields.Char(string="QR Payload (Escaped)", compute="_compute_qr_payload")
    qr_image = fields.Binary(string="QR Code Image", compute="_compute_qr_image", store=True)
    asset_serial_number = fields.Char(string="Serial Number", compute="_compute_asset_serial", store=False)

    def _compute_asset_serial(self):
        for rec in self:
            if rec.id:
                rec.asset_serial_number = f"AST-{rec.id:05d}"
            else:
                rec.asset_serial_number = ""

    @api.depends("name", "acquisition_date", "asset_serial_number")  
    def _compute_qr_payload(self):
        for rec in self:
            if rec.name:
                date_str = rec.acquisition_date.strftime("%Y-%m-%d") if rec.acquisition_date else "No Date"
                payload = f"{rec.asset_serial_number} | {rec.name} | {date_str}"
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
                raise UserError("Please provide an asset name before generating QR code.")
            if not qrcode:
                raise UserError("QR Code library not installed. Please install 'qrcode' Python package: pip install qrcode[pil]")
            record._compute_asset_serial()
            record._compute_qr_payload()
            record._compute_qr_image()
        return True
    
    def action_print_qr_label(self):
        self.ensure_one()
        
        if not self.qr_image:
            self.action_generate_qr_code()
        
        if not self.qr_image:
            raise UserError("QR Code could not be generated. Please ensure the qrcode library is installed.")
        
        return self.env.ref('asset_qr_labels.action_report_qr_code_label').report_action(self, config=False)
    
    def action_download_qr_code(self):
        self.ensure_one()
        
        if not self.qr_image:
            self.action_generate_qr_code()
        
        if not self.qr_image:
            raise UserError("QR Code could not be generated. Please ensure the qrcode library is installed.")
        
        date_str = self.acquisition_date.strftime("%Y-%m-%d") if self.acquisition_date else "no-date"
        filename = f"{self.asset_serial_number}_{date_str}_qr_code.png"
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/qr_image?download=true&filename={filename}',
            'target': 'self',
        }
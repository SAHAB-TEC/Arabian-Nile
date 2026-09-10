# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    abco_po_ref = fields.Char(
        string='ABCO PO Ref',
        copy=False,
        readonly=True,
        tracking=True,
    )

    def _generate_abco_po_ref(self):
        self.ensure_one()
        if self.abco_po_ref:
            return self.abco_po_ref
        base = self.date_order or fields.Datetime.now()
        year = fields.Datetime.to_datetime(base).strftime('%y')
        seq_date = fields.Datetime.to_datetime(base).date()
        seq = self.env['ir.sequence'].with_context(
            ir_sequence_date=seq_date,
        ).next_by_code('purchase.order.abco.ref')
        if not seq:
            raise UserError(_(
                'ABCO purchase sequence is missing. Update module Sale Quotation Custom.'
            ))
        digits = ''.join(ch for ch in seq if ch.isdigit()) or seq
        digits = digits[-4:].zfill(4)
        return f'PO_AB-{year}{digits}'

    def button_confirm(self):
        for order in self:
            if not order.abco_po_ref:
                order.abco_po_ref = order._generate_abco_po_ref()
                # Use ABCO PO number as the document name after confirmation.
                if order.abco_po_ref and order.name != order.abco_po_ref:
                    order.name = order.abco_po_ref
        return super().button_confirm()

# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    abco_customer_code = fields.Char(
        string='ABCO Customer Code',
        size=4,
        copy=False,
        help='Short code used inside ABCO offer numbers (e.g. AG).',
    )
    customer_ref_label = fields.Char(
        string='Customer Ref Label',
        copy=False,
        help='Print label prefix for the customer offer reference '
             '(e.g. AGOCO → printed as "AGOCO Ref.").',
    )

    @api.constrains('abco_customer_code')
    def _check_abco_customer_code(self):
        for partner in self:
            code = (partner.abco_customer_code or '').strip()
            if not code:
                continue
            if not code.isalnum():
                raise ValidationError(
                    'ABCO Customer Code must contain letters/numbers only.'
                )
            if len(code) < 2:
                raise ValidationError(
                    'ABCO Customer Code must be at least 2 characters.'
                )

    @api.onchange('abco_customer_code')
    def _onchange_abco_customer_code(self):
        if self.abco_customer_code:
            self.abco_customer_code = self.abco_customer_code.strip().upper()

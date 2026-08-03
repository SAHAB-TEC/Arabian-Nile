# -*- coding: utf-8 -*-
from odoo import models, _


class ConstructionRaBilling(models.Model):
    _inherit = 'construction.ra.billing'

    def action_submit(self):
        for rec in self:
            self.env['rgb.ncr']._raise_if_frozen(
                rec.project_id.id,
                rec.partner_id.id,
                document_label=_('RA billing submission'),
            )
        return super().action_submit()

    def action_approve(self):
        for rec in self:
            self.env['rgb.ncr']._raise_if_frozen(
                rec.project_id.id,
                rec.partner_id.id,
                document_label=_('RA billing approval'),
            )
        return super().action_approve()

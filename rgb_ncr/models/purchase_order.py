# -*- coding: utf-8 -*-
from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        if self.construction_project_id:
            vals['construction_project_id'] = self.construction_project_id.id
        return vals

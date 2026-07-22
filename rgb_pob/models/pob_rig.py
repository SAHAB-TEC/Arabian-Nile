# -*- coding: utf-8 -*-
from odoo import fields, models


class PobRig(models.Model):
    _name = "pob.rig"
    _description = "POB Rig"
    _order = "name"
    _rec_name = "name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(translate=True)
    active = fields.Boolean(default=True)
    well_id = fields.Many2one("pob.well", string="Well", index=True)
    partner_id = fields.Many2one("res.partner", string="Partner")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=True,
    )
    note = fields.Text(string="Notes")

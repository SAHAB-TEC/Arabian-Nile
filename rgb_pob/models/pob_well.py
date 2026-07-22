# -*- coding: utf-8 -*-
from odoo import fields, models


class PobWell(models.Model):
    _name = "pob.well"
    _description = "POB Well"
    _order = "name"
    _rec_name = "name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(translate=True)
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one("res.partner", string="Partner")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=True,
    )
    rig_ids = fields.One2many("pob.rig", "well_id", string="Rigs")
    note = fields.Text(string="Notes")

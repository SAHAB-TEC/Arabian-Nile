# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # --- Auto / request-linked (defaults from requisition, still editable) ---
    ticket_company_id = fields.Many2one(
        "res.partner",
        string="Ticket Company",
        help="Company shown on the Delivery Ticket load section.",
    )
    ticket_shipped_from = fields.Char(string="Shipped From")
    ticket_shipped_to = fields.Char(string="Shipped To")
    ticket_delivery_time = fields.Datetime(string="Delivery Time")
    ticket_concession = fields.Char(string="Concession")
    ticket_status_color = fields.Selection(
        selection=[
            ("yellow", "Yellow"),
            ("orange", "Orange"),
            ("green", "Green"),
        ],
        string="Ticket Status Color",
        help="Filled from the material requisition request type.",
    )

    # --- Storekeeper ---
    ticket_storekeeper_signature = fields.Binary(string="Storekeeper Signature")
    ticket_storekeeper_name = fields.Char(string="Storekeeper Name")

    # --- Driver acknowledgment (manual) ---
    ticket_materials_ok = fields.Boolean(
        string="Materials Received in Good Condition",
        default=False,
    )
    ticket_driver_name = fields.Char(string="Receiving Driver")
    ticket_driver_card_no = fields.Char(string="Driver ID / Card No.")
    ticket_truck_no = fields.Char(string="Truck Number")
    ticket_driver_signature = fields.Binary(string="Driver Signature")

    # --- Final receipt footer (manual) ---
    ticket_received_company = fields.Char(string="Received Company Name")
    ticket_received_name = fields.Char(string="Received Name")
    ticket_received_signature = fields.Binary(string="Receiver Signature")
    ticket_received_date = fields.Date(string="Received Date")

    def _rgb_get_linked_requisition(self):
        self.ensure_one()
        if self.material_requisition_id:
            return self.material_requisition_id
        if not self.origin:
            return self.env["material.requisition"]
        return self.env["material.requisition"]._rgb_find_from_origin(self.origin)

    def _rgb_ticket_defaults_from_requisition(self):
        """Build editable defaults for Delivery Ticket fields from the request."""
        self.ensure_one()
        requisition = self._rgb_get_linked_requisition()
        vals = {}
        if requisition:
            if requisition.partner_id and not self.ticket_company_id:
                vals["ticket_company_id"] = requisition.partner_id.id
            if (
                requisition.request_type_id
                and requisition.request_type_id.ticket_status_color
                and not self.ticket_status_color
            ):
                vals["ticket_status_color"] = (
                    requisition.request_type_id.ticket_status_color
                )
            if not self.well_id and requisition.well_id:
                vals["well_id"] = requisition.well_id.id
            if not self.rig_id and requisition.rig_id:
                vals["rig_id"] = requisition.rig_id.id
        if not self.ticket_shipped_from and self.location_id:
            vals["ticket_shipped_from"] = self.location_id.display_name
        if not self.ticket_shipped_to and self.location_dest_id:
            vals["ticket_shipped_to"] = self.location_dest_id.display_name
        if not self.ticket_delivery_time:
            vals["ticket_delivery_time"] = self.date_done or self.scheduled_date
        if not self.ticket_company_id and self.partner_id and "ticket_company_id" not in vals:
            vals["ticket_company_id"] = self.partner_id.id
        return vals

    def action_rgb_fill_delivery_ticket(self):
        """Manual button: re-apply defaults from the linked requisition."""
        for picking in self:
            vals = picking._rgb_ticket_defaults_from_requisition()
            if vals:
                picking.write(vals)
        return True

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        for picking in pickings:
            defaults = picking._rgb_ticket_defaults_from_requisition()
            if defaults:
                picking.write(defaults)
        return pickings

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get("rgb_skip_ticket_autofill"):
            return res
        refresh_keys = {
            "material_requisition_id",
            "origin",
            "location_id",
            "location_dest_id",
            "scheduled_date",
            "date_done",
            "partner_id",
        }
        if refresh_keys & set(vals):
            for picking in self:
                defaults = picking._rgb_ticket_defaults_from_requisition()
                if defaults:
                    picking.with_context(rgb_skip_ticket_autofill=True).write(defaults)
        return res

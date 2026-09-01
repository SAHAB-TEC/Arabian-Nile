# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import models
from odoo.exceptions import ValidationError


class MaterialRequisitionFulfillmentWizard(models.TransientModel):
    _inherit = "material.requisition.fulfillment.wizard"

    def _create_internal_transfers(self):
        """Create one internal picking per (source, destination) with all product moves.

        Webkul default creates one picking per requisition line; group lines that share
        the same source and destination on a single transfer.
        """
        stock_picking = self.env["stock.picking"]
        rule = self.requisition_id.approval_rule_id
        self.requisition_id._ensure_destination_location(rule=rule)
        employee_location = self.requisition_id.location_id

        if not employee_location:
            raise ValidationError(
                "Destination location must be set on the requisition."
            )

        groups = defaultdict(lambda: self.env["material.requisition.line"])
        for line in self.line_ids:
            product = line.product_id
            source_location = line.stock_location_id

            if not source_location:
                available = line.all_stock_location_ids
                if not available:
                    raise ValidationError(
                        f"Product '{product.name}' has no stock in any location. "
                        f"Use 'Fulfill by Purchase Order' to procure it."
                    )
                raise ValidationError(
                    f"Product '{product.name}': please select a source location. "
                    f"Available locations with stock: "
                    f"{', '.join(available.mapped('complete_name'))}"
                )

            if source_location.usage != "internal":
                raise ValidationError(
                    "Source location must be an internal stock location."
                )

            if line.qty_remaining > line.quantity:
                raise ValidationError(
                    f"Product '{product.name}': transfer quantity ({line.qty_remaining}) "
                    f"cannot exceed requested quantity ({line.quantity})."
                )

            if line.qty_remaining < 1:
                raise ValidationError(
                    f"Product '{product.name}': transfer quantity must be at least 1 "
                    f"(current value: {line.qty_remaining})."
                )

            groups[(source_location.id, employee_location.id)] |= line

        for (source_id, dest_id), lines in groups.items():
            move_commands = []
            for line in lines:
                product = line.product_id
                move_commands.append(
                    (
                        0,
                        0,
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_uom_qty": line.qty_remaining,
                            "product_uom": product.uom_id.id,
                            "location_id": source_id,
                            "location_dest_id": dest_id,
                        },
                    )
                )

            picking_vals = {
                "partner_id": self.requisition_id._get_delivery_partner().id or False,
                "location_id": source_id,
                "location_dest_id": dest_id,
                "picking_type_id": self.env.ref("stock.picking_type_internal").id,
                "origin": self.requisition_id.name,
                "move_ids": move_commands,
            }
            if "material_requisition_id" in stock_picking._fields:
                picking_vals["material_requisition_id"] = self.requisition_id.id

            picking = stock_picking.create(picking_vals)

            if rule and rule.auto_create_dispatch:
                picking.action_confirm()
                picking.action_assign()
                if picking.state == "assigned":
                    picking.button_validate()
                else:
                    products = ", ".join(lines.mapped("product_id.display_name"))
                    source_name = lines[:1].stock_location_id.complete_name
                    raise ValidationError(
                        f"Insufficient stock at '{source_name}' to auto-complete the "
                        f"transfer for: {products}. Disable 'Auto Create Dispatch' on "
                        f"the approval rule or replenish the location first."
                    )
            elif rule and rule.require_stock_manager_dispatch:
                picking.action_confirm()
                picking.action_assign()

            for line in lines:
                line.picking_id = picking.id
                line.requisition_action = "transfer"

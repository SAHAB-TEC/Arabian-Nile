# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        check_company=True,
        tracking=True,
        copy=False,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help='Optional. Used for new lines and when you click Update Prices. '
             'You can clear it; it will not be filled in again unless you change the customer.',
    )
    has_sale_order = fields.Boolean(
        string='Has Sale Order',
        compute='_compute_has_sale_order',
    )
    show_update_pricelist = fields.Boolean(
        string='Show Update Pricelist',
        compute='_compute_show_update_pricelist',
    )

    @api.depends('invoice_line_ids.sale_line_ids')
    def _compute_has_sale_order(self):
        for move in self:
            move.has_sale_order = bool(move.invoice_line_ids.sale_line_ids)

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        if 'pricelist_id' not in fields_list or vals.get('pricelist_id'):
            return vals
        move_type = vals.get('move_type') or self.env.context.get('default_move_type')
        if move_type not in ('out_invoice', 'out_refund', 'out_receipt'):
            return vals
        partner_id = vals.get('partner_id') or self.env.context.get('default_partner_id')
        if not partner_id:
            return vals
        company_id = vals.get('company_id') or self.env.context.get('default_company_id') or self.env.company.id
        partner = self.env['res.partner'].browse(partner_id).with_company(company_id)
        if partner.property_product_pricelist:
            vals['pricelist_id'] = partner.property_product_pricelist.id
        return vals

    @api.onchange('partner_id')
    def _onchange_partner_id_pricelist(self):
        if self.move_type not in ('out_invoice', 'out_refund', 'out_receipt'):
            return
        if self.partner_id:
            self.pricelist_id = self.partner_id.with_company(self.company_id).property_product_pricelist
        else:
            self.pricelist_id = False

    @api.depends('pricelist_id', 'invoice_line_ids', 'has_sale_order', 'state')
    def _compute_show_update_pricelist(self):
        for move in self:
            move.show_update_pricelist = bool(
                move.state == 'draft'
                and move.pricelist_id
                and not move.has_sale_order
                and move.invoice_line_ids.filtered(
                    lambda line: line.display_type == 'product'
                    and line.product_id
                    and not line.sale_line_ids
                )
            )

    @api.onchange('pricelist_id')
    def _onchange_pricelist_id_set_currency(self):
        for move in self:
            if (
                move.move_type in ('out_invoice', 'out_refund', 'out_receipt')
                and move.state == 'draft'
                and not move.has_sale_order
                and move.pricelist_id.currency_id
            ):
                move.currency_id = move.pricelist_id.currency_id

    def write(self, vals):
        if 'pricelist_id' in vals:
            protected = self.filtered(lambda m: m.state != 'draft' or m.has_sale_order)
            if protected:
                raise UserError(_(
                    'You cannot change the pricelist of a posted invoice or an invoice created from a Sale Order.'
                ))
        return super().write(vals)

    def action_update_invoice_prices(self):
        self.ensure_one()
        if self.has_sale_order:
            raise UserError(_('You cannot update prices on an invoice created from a Sale Order.'))
        self.with_context(force_invoice_pricelist_price=True).invoice_line_ids._compute_price_unit()
        if self.pricelist_id:
            message = _(
                'Product prices have been recomputed according to pricelist %s.',
                self.pricelist_id._get_html_link(),
            )
        else:
            message = _('Product prices have been recomputed.')
        self.message_post(body=message)

    def _get_product_price_and_data(self, product):
        result = super()._get_product_price_and_data(product)
        if self._use_invoice_pricelist() and product:
            result['price'] = self.env['account.move.line']._get_price_from_invoice_pricelist(
                move=self,
                product=product,
                quantity=1.0,
                uom=product.uom_id,
            )
        return result

    def _update_order_line_info(self, product_id, quantity, **kwargs):
        price = super()._update_order_line_info(product_id, quantity, **kwargs)
        if self._use_invoice_pricelist():
            product = self.env['product.product'].browse(product_id)
            return self.env['account.move.line']._get_price_from_invoice_pricelist(
                move=self,
                product=product,
                quantity=quantity or 1.0,
                uom=product.uom_id,
            )
        return price

    def _use_invoice_pricelist(self):
        self.ensure_one()
        return bool(
            self.move_type in ('out_invoice', 'out_refund', 'out_receipt')
            and self.state == 'draft'
            and self.pricelist_id
            and not self.has_sale_order
            and not self.line_ids.sale_line_ids
        )

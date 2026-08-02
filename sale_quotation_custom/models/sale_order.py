# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_time_from = fields.Integer(
        string='Delivery From',
        help='Minimum delivery time in days.',
    )
    delivery_time_to = fields.Integer(
        string='Delivery To',
        help='Maximum delivery time in days.',
    )
    country_of_origin_id = fields.Many2one(
        'res.country',
        string='Country of Origin',
    )
    offer_validity = fields.Selection(
        [
            ('30', '30 Days'),
            ('60', '60 Days'),
            ('90', '90 Days'),
        ],
        string='Offer Validity',
        default='30',
    )
    offer_validity_date = fields.Date(
        string='Valid Until',
        compute='_compute_offer_validity_date',
        store=True,
    )
    show_taxes = fields.Boolean(
        string='Show Taxes',
        default=True,
        help='If disabled, tax column and tax totals are hidden on the quotation PDF.',
    )
    signatory_name = fields.Char(
        string='Signatory Name',
    )

    @api.depends('offer_validity', 'date_order')
    def _compute_offer_validity_date(self):
        for order in self:
            if not order.offer_validity or not order.date_order:
                order.offer_validity_date = False
                continue
            base_date = fields.Datetime.to_datetime(order.date_order).date()
            order.offer_validity_date = base_date + relativedelta(
                days=int(order.offer_validity),
            )

    @api.constrains('delivery_time_from', 'delivery_time_to')
    def _check_delivery_time(self):
        for order in self:
            if order.delivery_time_from and order.delivery_time_from < 0:
                raise ValidationError(_('Delivery From cannot be negative.'))
            if order.delivery_time_to and order.delivery_time_to < 0:
                raise ValidationError(_('Delivery To cannot be negative.'))
            if (
                order.delivery_time_from
                and order.delivery_time_to
                and order.delivery_time_from > order.delivery_time_to
            ):
                raise ValidationError(
                    _('Delivery From cannot be greater than Delivery To.')
                )

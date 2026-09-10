# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_DEFAULT_COVER_BODY = (
    "With reference to the above-mentioned subject, we are pleased to accompany "
    "our offer for your review and considerations.\n\n"
    "We would like to assure you that all the equipment mentioned in our offer is "
    "brand new, genuine, and according to API specification. We would also like "
    "to assure you that we accept all terms and conditions of the customer.\n\n"
    "We are confident that the attached offer will meet your professional "
    "requirements and we are looking forward to working with your esteemed company.\n\n"
    "We thank you for giving us the opportunity and look forward to doing business with you."
)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_time_from = fields.Integer(
        string='Delivery From',
        help='Minimum delivery time in weeks.',
    )
    delivery_time_to = fields.Integer(
        string='Delivery To',
        help='Maximum delivery time in weeks.',
    )
    country_of_origin_ids = fields.Many2many(
        'res.country',
        string='Countries of Origin',
        compute='_compute_country_of_origin_ids',
        store=True,
        readonly=True,
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
        help='If disabled, tax column and tax totals are hidden on the standard quotation PDF.',
    )
    signatory_name = fields.Char(
        string='Signatory Name',
        default='Walid Aldejawi',
    )
    signatory_title = fields.Char(
        string='Signatory Title',
        default='Supply and Sales Manager | ABCO',
    )

    # Customer tender / RFQ reference (manual)
    customer_offer_ref = fields.Char(
        string='Customer Offer Ref',
        copy=False,
        help='Manual reference received from the customer with their enquiry.',
    )
    customer_ref_label = fields.Char(
        related='partner_id.customer_ref_label',
        string='Customer Ref Label',
        store=True,
        readonly=True,
    )
    customer_ref_display_label = fields.Char(
        string='Customer Ref Print Label',
        compute='_compute_customer_ref_display_label',
    )

    # ABCO offer number (generated on confirm)
    abco_ref = fields.Char(
        string='ABCO Ref',
        copy=False,
        readonly=True,
        tracking=True,
    )
    abco_revision = fields.Integer(
        string='Revision',
        default=1,
        copy=False,
    )
    print_incoterm = fields.Char(
        string='Incoterm (Print)',
        help='Incoterm text printed on ABCO offers (e.g. FCA USA).',
    )
    print_payment = fields.Char(
        string='Payment (Print)',
        help='Payment text printed on ABCO offers (e.g. 100% USD CAD).',
    )

    # Editable cover letter
    cover_to = fields.Text(
        string='Cover Addressee',
        default='Department Manager, Supply Department',
    )
    cover_subject = fields.Char(
        string='Cover Subject',
    )
    cover_body = fields.Text(
        string='Cover Body',
        default=_DEFAULT_COVER_BODY,
    )

    @api.depends('order_line.country_of_origin_id')
    def _compute_country_of_origin_ids(self):
        for order in self:
            order.country_of_origin_ids = order.order_line.mapped('country_of_origin_id')

    @api.depends('partner_id', 'partner_id.customer_ref_label')
    def _compute_customer_ref_display_label(self):
        for order in self:
            label = (order.partner_id.customer_ref_label or '').strip()
            order.customer_ref_display_label = f'{label} Ref.' if label else 'Customer Ref.'

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

    def _get_abco_year_code(self):
        self.ensure_one()
        base = self.date_order or fields.Datetime.now()
        return fields.Datetime.to_datetime(base).strftime('%y')

    def _generate_abco_ref(self):
        self.ensure_one()
        if self.abco_ref:
            return self.abco_ref
        code = (self.partner_id.abco_customer_code or '').strip().upper()
        if not code:
            raise UserError(_(
                "Set ABCO Customer Code on customer %(customer)s before confirming.",
                customer=self.partner_id.display_name,
            ))
        year = self._get_abco_year_code()
        seq_date = fields.Datetime.to_datetime(self.date_order or fields.Datetime.now()).date()
        seq = self.env['ir.sequence'].with_context(
            ir_sequence_date=seq_date,
        ).next_by_code('sale.order.abco.ref')
        if not seq:
            raise UserError(_('ABCO offer sequence is missing. Update module Sale Quotation Custom.'))
        # next_by_code may return full prefixed value; keep digits only for safety
        digits = ''.join(ch for ch in seq if ch.isdigit()) or seq
        digits = digits[-4:].zfill(4)
        return f'O_AB-{code}-{year}{digits}'

    def action_confirm(self):
        for order in self:
            if not order.abco_ref:
                order.abco_ref = order._generate_abco_ref()
        return super().action_confirm()

    def _get_abco_delivery_print(self):
        self.ensure_one()
        if self.delivery_time_from and self.delivery_time_to:
            return f'{self.delivery_time_from}-{self.delivery_time_to} WEEKS'
        if self.delivery_time_from:
            return f'From {self.delivery_time_from} WEEKS'
        if self.delivery_time_to:
            return f'Up to {self.delivery_time_to} WEEKS'
        return ''

    def _get_abco_payment_print(self):
        self.ensure_one()
        if self.print_payment:
            return self.print_payment
        if self.payment_term_id:
            return self.payment_term_id.name
        return ''

    def _get_abco_validity_print(self):
        self.ensure_one()
        if self.offer_validity:
            return f'{self.offer_validity} days'
        return ''


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    country_of_origin_id = fields.Many2one(
        'res.country',
        string='Country of Origin',
        copy=True,
    )

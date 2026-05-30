# RGB Customer Invoice Pricelist

Pricelist-only extraction from `account_invoice_pricelist_18` for Arabian Nile.

## Features

- Pricelist on customer invoices (`out_invoice`, `out_refund`, `out_receipt`)
- Default pricelist from customer
- Currency follows pricelist on draft invoices
- **Update Prices** button recalculates line unit prices
- Prices from pricelist when adding products (catalog / lines)
- Pricelist copied from Sale Order to invoice

## Not included

- USD/LYD split (see `rgb_contract_management`)
- Discount account flag
- Custom invoice PDF layouts / transport fields

## Dependencies

- `account`, `sale`

## Install

Install **RGB Customer Invoice Pricelist** on the database. Users need the **Pricelists** group (`product.group_product_pricelist`).

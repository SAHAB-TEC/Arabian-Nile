# RGB Engineer Attendance

Monthly attendance grid for engineers at wells/rigs (Al-Abar).

## Features

- List view: engineer, well, rig, company, days count, product, period
- Form: month/year (defaults to today), checkboxes for days 1–31
- **Generate**: submit for approval + activities for approvers
- **Approve**: creates vendor bill (`in_invoice`) with quantity = number of checked days
- Chatter audit trail on all changes
- **Print → Attendance PDF** and **Action → Export Excel (CSV)**

## Security groups

| Group | Access |
|-------|--------|
| User | Create/edit draft sheets |
| Approver | Approve + submit workflow |
| Manager | Full access + reset to draft + accounting |

Assign **only** `Engineer Attendance / User` to users who must not see other apps (do not add Sales/Accounting groups unless needed).

## Dependencies

- `account`, `mail`, `product`, `rgb_workover_operations` (wells / rigs)

## Install

```bash
./odoo-bin -c _conf/abar.conf -d YOUR_DB -i rgb_engineer_attendance --stop-after-init
```

Engineer is selected from contacts marked **Is Engineer** (`is_engineer = True`).
Client company is selected from **companies** (`is_company = True`, not engineers).
Mark a contact as engineer from **ENG Attendance → Engineers** or on the partner form.

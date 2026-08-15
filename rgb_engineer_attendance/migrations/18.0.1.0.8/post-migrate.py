# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Copy engineer daily_rate from partner to linked employee contracts."""
    cr.execute(
        """
        UPDATE hr_contract AS c
           SET daily_rate = p.daily_rate
          FROM hr_employee AS e
          JOIN res_partner AS p ON p.id = e.work_contact_id
         WHERE c.employee_id = e.id
           AND COALESCE(c.daily_rate, 0) = 0
           AND COALESCE(p.daily_rate, 0) <> 0
        """
    )

# -*- coding: utf-8 -*-


def migrate(cr, version):
    cr.execute(
        """
        UPDATE workover_daily_report
           SET rig_summary_date_from = report_date,
               rig_summary_date_to = report_date
         WHERE rig_summary_date_from IS NULL
            OR rig_summary_date_to IS NULL
        """
    )

# -*- coding: utf-8 -*-
import base64
import csv
import io

from odoo import _, fields, models


class RgbAttendanceExportWizard(models.TransientModel):
    _name = "rgb.attendance.export.wizard"
    _description = "Export Attendance Sheets"

    file_data = fields.Binary(readonly=True)
    file_name = fields.Char(readonly=True)

    def action_export_excel_csv(self):
        sheets = self.env["rgb.attendance.sheet"].browse(self.env.context.get("active_ids", []))
        if not sheets:
            sheets = self.env["rgb.attendance.sheet"].search([])

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        header = [
            "Reference",
            "Engineer",
            "Well",
            "Rig",
            "Company",
            "Period",
            "Days",
            "Status",
        ] + [str(day) for day in range(1, 32)]
        writer.writerow(header)
        type_labels = dict(sheets._fields["day_1_type"].selection)
        for sheet in sheets:
            row = [
                sheet.name,
                sheet.engineer_id.display_name,
                sheet.well_id.name or "",
                sheet.rig_id.name if sheet.rig_id else "",
                sheet.partner_company_id.display_name,
                sheet.period_label,
                sheet.days_count,
                dict(sheet._fields["state"].selection).get(sheet.state, ""),
            ]
            for day in range(1, 32):
                if getattr(sheet, f"day_{day}", False):
                    code = getattr(sheet, f"day_{day}_type", False)
                    row.append(type_labels.get(code, ""))
                else:
                    row.append("")
            writer.writerow(row)

        content = buffer.getvalue().encode("utf-8-sig")
        self.write({
            "file_data": base64.b64encode(content),
            "file_name": "attendance_export.csv",
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
            "name": _("Download attendance export"),
        }

from odoo import models, fields
class RevenueReportWizard(models.TransientModel):
    _name = 'revenue.report.wizard'
    _description = 'Revenue Report Wizard'

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    def action_generate_revenue_report(self):
        # Gọi phương thức báo cáo
        report = self.env['booking.order'].get_revenue_report(self.start_date, self.end_date)

        # Tạo báo cáo hoặc hiển thị thông tin chi tiết
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'booking.order',
            'view_mode': 'tree',
            'domain': [
                ('payment_status', '=', 'paid'),
                ('check_in_date', '>=', self.start_date),
                ('check_out_date', '<=', self.end_date),
            ],
            'name': f"Revenue Report ({self.start_date} to {self.end_date})"
        }

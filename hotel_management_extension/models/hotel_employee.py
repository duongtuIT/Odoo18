from odoo import models, fields, api

class HotelManagement(models.Model):
    _inherit = "hotel.management"  # Kế thừa mô hình hotel.management

    # Thêm trường liên kết với nhân viên
    employee_ids = fields.One2many('hr.employee', 'hotel_id', string="Employees")

    @api.model
    def create(self, vals):
        # Tạo mới khách sạn và lấy danh sách nhân viên có job_id là 'Hotel_Employee'
        hotel = super(HotelManagement, self).create(vals)
        employee_ids = self.env['hr.employee'].search([('job_id.name', '=', 'Hotel_Employee')])
        for employee in employee_ids:
            employee.write({'hotel_id': hotel.id})
        return hotel


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    hotel_id = fields.Many2one('hotel.management', string="Hotel")

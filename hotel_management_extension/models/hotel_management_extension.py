from odoo import models, fields

class BookingHistory(models.Model):
    _name = 'booking.history'
    _description = 'Booking History'

    # Các trường trong bảng lịch sử đặt phòng
    customer_name = fields.Char(string="Customer Name", required=True)
    hotel_id = fields.Many2one('hotel.management', string="Hotel", required=True)
    room_code = fields.Char(string="Room Code", required=True)
    check_in_date = fields.Date(string="Check-in Date", required=True)
    check_out_date = fields.Date(string="Check-out Date", required=True)

class HotelManagement(models.Model):
    _inherit = 'hotel.management'
    # Quan hệ với bảng lịch sử đặt phòng
    booking_history_ids = fields.One2many(
        'booking.history', 'hotel_id', string="Booking History"
    )
    # Quan hệ One2many với booking.order
    booking_history_ids = fields.One2many(
        'booking.order', 'hotel_id', string="Booking History",
    )



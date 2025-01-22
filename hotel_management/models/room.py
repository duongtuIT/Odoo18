from odoo import models, fields, api
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)
class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'

    # Fields
    hotel_id = fields.Many2one('hotel.management', string="Hotel", ondelete="cascade", required=True)
    address = fields.Char(string="Hotel Address", related="hotel_id.address", store=True)
    room_code = fields.Char(string="Room Code", required=True)
    bed_type = fields.Selection([
        ('single', 'Single Bed'),
        ('double', 'Double Bed')
    ], string="Bed Type", required=True)
    weekday_price = fields.Float(string="Weekday Price", required=True)
    weekend_price = fields.Float(string="Weekend Price", required=True)
    description = fields.Text(string="Room Features")
    state = fields.Selection([
        ('available', 'Available'),
        ('booked', 'Booked')
    ], string="Room Status", default='available', required=True)
    last_booking_date = fields.Date(string="Last Booking Date")  # Thêm trường mới
    # Quan hệ với đặc điểm phòng
    feature_ids = fields.Many2many('room.feature', string="Room Features")

    # Ràng buộc mã phòng phải là duy nhất trong khách sạn
    _sql_constraints = [
        ('room_code_unique_per_hotel', 'unique(hotel_id, room_code)', 'Room code must be unique within a hotel.')
    ]
    taxes_id = fields.Many2many(
        'account.tax',
        string="Taxes",
        help="Specify the taxes to be applied to the room."
    )
    @api.model
    def check_unbooked_rooms(self):
        seven_days_ago = fields.Date.to_date(fields.Date.today() - timedelta(days=7))
        unbooked_rooms = self.search([('last_booking_date', '<=', seven_days_ago)])
        for room in unbooked_rooms:
            _logger.info(
                f"Room '{room.room_code}' in Hotel '{room.hotel_id.name}' has not been booked for over 7 days.")

    def get_available_rooms(self, start_date, end_date=None):
        end_date = end_date or start_date
        # Tìm các phòng không được đặt trong khoảng thời gian
        booked_rooms = self.env['booking.order'].search([
            ('check_in_date', '<=', end_date),
            ('check_out_date', '>=', start_date)
        ]).mapped('room_id')

        # Lọc ra các phòng trống
        available_rooms = self.search([('id', 'not in', booked_rooms.ids)])
        return available_rooms

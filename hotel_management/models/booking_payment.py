from odoo import models, fields, api

class BookingPaymentWizard(models.TransientModel):
    _name = 'booking.payment.wizard'
    _description = 'Booking Payment Wizard'

    booking_id = fields.Many2one('booking.order', string="Đơn đặt phòng", readonly=True)
    hotel_id = fields.Many2one('hotel.management', string="Khách sạn", readonly=True)
    room_id = fields.Many2one('hotel.room', string="Phòng", readonly=True)
    customer_name = fields.Char(string="Tên khách hàng", readonly=True)
    payment_amount = fields.Float(string="Số tiền thanh toán", readonly=True)
    service_total = fields.Float(string="Tổng dịch vụ", readonly=True)
    total_amount = fields.Float(string="Tổng phòng", readonly=True)
    room_code = fields.Char(string="Tên phòng", readonly=True)
    @api.model
    def default_get(self, fields):
        """ Tự động lấy thông tin từ booking_id khi mở wizard """
        res = super(BookingPaymentWizard, self).default_get(fields)
        booking_id = self.env.context.get('active_id')  # Lấy ID đơn đặt phòng từ context
        if booking_id:
            booking = self.env['booking.order'].browse(booking_id)
            res.update({
                'booking_id': booking.id,
                'hotel_id': booking.hotel_id.id,
                'room_id': booking.room_id.id,
                'room_code': booking.room_id.room_code,
                'customer_name': booking.customer_name,
                'payment_amount': booking.payment_amount,  # Giá trị thanh toán mặc định
                'service_total': booking.service_total,
                'total_amount': booking.total_amount,
            })
        return res

    @api.constrains('payment_amount')
    def _check_payment_amount(self):
        if self.payment_amount <= 0:
            raise models.ValidationError("Số tiền thanh toán phải lớn hơn 0.")

    def confirm_payment(self):
        self.booking_id.write({
            'payment_status': 'paid',
            'payment_date': fields.Datetime.now(),
            'payment_amount': self.payment_amount
        })



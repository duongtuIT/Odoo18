from odoo import models, fields, api

class BookingPaymentWizard(models.TransientModel):
    _name = 'booking.payment.wizard'
    _description = 'Booking Payment Wizard'

    booking_id = fields.Many2one('booking.order', string="Đơn đặt phòng", readonly=True)
    hotel_id = fields.Many2one('hotel.management', string="Khách sạn", readonly=True)
    room_id = fields.Many2one('hotel.room', string="Phòng", readonly=True)
    payment_amount = fields.Float(string="Số tiền thanh toán", required=True)

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

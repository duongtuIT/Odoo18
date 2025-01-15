from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError


class BookingOrder(models.Model):
    _name = 'booking.order'
    _description = 'Booking Order'

    # Fields
    booking_code = fields.Char(string="Booking Code", unique=True)
    customer_name = fields.Char(string="Customer Name", required=True)
    booking_date = fields.Date(string="Booking Date", default=date.today(), required=True)
    check_in_date = fields.Date(string="Check-in Date", required=True)
    check_out_date = fields.Date(string="Check-out Date", required=True)
    rental_days = fields.Integer(string="Số Đêm Thuê", compute="_compute_rental_days", store=True)
    hotel_id = fields.Many2one('hotel.management', string="Hotel", required=True)
    room_type = fields.Selection([
        ('single', 'Single Bed'),
        ('double', 'Double Bed')
    ], string="Room Type", required=True)
    room_id = fields.Many2one(
        'hotel.room',
        string="Room ID",
        required=True,
        domain="[('hotel_id', '=', hotel_id),('bed_type', '=', room_type)]"
    )
    room_price = fields.Float(related='room_id.price', string='Room Price', readonly=True)
    room_name = fields.Char(string="Room Name", related="room_id.room_code", store=True)
    state = fields.Selection([
        ('new', 'New'),
        ('confirmed', 'Confirmed')
    ], string="Booking Status", default='new', required=True)
    payment_status = fields.Selection(
        [('unpaid', 'Chưa thanh toán'), ('paid', 'Đã thanh toán')],
        string="Loại thanh toán",
        default='unpaid',
        readonly=True
    )
    payment_date = fields.Datetime(string="Ngày thanh toán", readonly=True)
    payment_amount = fields.Float(
        string="Số tiền thanh toán",
        readonly=True,
        compute='_compute_payment_amount',
        store=True)
    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_total_amount',
        store=True
    )

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)

    def action_confirm(self):
        self.state = 'confirmed'
    @api.model
    def create(self, vals):
        # Kiểm tra và tự động tạo hotel_code nếu không có
        if 'booking_code' not in vals:
            last_bill = self.search([], order='booking_code desc', limit=1)
            if last_bill:
                last_code = int(last_bill.booking_code)
                new_code = str(last_code + 1)
            else:
                new_code = '1'  # Nếu không có khách sạn nào, bắt đầu từ 1
            vals['booking_code'] = new_code
        # Cập nhật trạng thái phòng thành 'booked' khi tạo đơn đặt phòng
        room = self.env['hotel.room'].browse(vals['room_id'])
        if room:
            overlap_booking = self.env['booking.order'].search([
                ('room_id', '=', vals['room_id']),
                ('check_in_date', '<=', vals['check_out_date']),
                ('check_out_date', '>=', vals['check_in_date']),
              ])
            if overlap_booking:
                raise models.ValidationError("The room is already booked for the selected dates.")

        room.state = 'booked'  # Thay đổi trạng thái phòng thành 'booked'
        room.last_booking_date = vals.get('booking_date', fields.Date.today())  # Cập nhật ngày đặt gần nhất
        return super(BookingOrder, self).create(vals)

    # Constraints
    @api.constrains('check_in_date', 'check_out_date')
    def _check_dates(self):
        for record in self:
            if record.check_in_date > record.check_out_date:
                raise models.ValidationError("Check-in date cannot be later than check-out date.")

    @api.depends('room_id')
    def _compute_room_code(self):
        for record in self:
            if record.room_id:
                record.room_code = record.room_id.room_code

    def unlink(self):
        for record in self:
            if record.room_id:
                # Kiểm tra xem còn đơn đặt phòng nào khác liên quan đến phòng này không
                other_bookings = self.search([
                    ('room_id', '=', record.room_id.id),
                    ('id', '!=', record.id)  # Loại bỏ bản ghi hiện tại
                ])
                # Nếu không còn đơn đặt phòng nào khác, đặt trạng thái phòng là 'available'
                if not other_bookings:
                    record.room_id.state = 'available'
        return super(BookingOrder, self).unlink()

    def action_open_payment_wizard(self):
        return {
            'name': 'Thanh toán',
            'type': 'ir.actions.act_window',
            'res_model': 'booking.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_booking_id': self.id,
                'default_hotel_id': self.hotel_id.id,
                'default_room_id': self.room_id.id,
            }
        }

    def action_create_invoice(self):
        for record in self:
            # Check if payment has already been made
            if record.payment_status == 'paid':
                raise UserError("Payment has already been made for this booking.")
            # Check if a Sale Order already exists
            if record.sale_order_id:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Sale Order',
                    'view_mode': 'form',
                    'res_model': 'sale.order',
                    'res_id': record.sale_order_id.id,
                }
            # Search for the customer in res.partner
            partner = self.env['res.partner'].search([('name', '=', record.customer_name)], limit=1)

            # If no customer is found, create a new one
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': record.customer_name,
                })

            # Create Sale Order
            sale_order = self.env['sale.order'].create({
                'partner_id': partner.id,
                'origin': record.booking_code,
            })

            # Generate dynamic product name
            if record.room_id and record.check_in_date and record.check_out_date:
                checkin = fields.Date.to_string(record.check_in_date)
                checkout = fields.Date.to_string(record.check_out_date)
                sale_name = f"{record.room_id.room_code}: {checkin} - {checkout}"
            else:
                sale_name = "Room Booking"

            # Check if a product with the same name exists, otherwise create it
            product = self.env['product.product'].search([('name', '=', sale_name)], limit=1)
            if not product:
                product = self.env['product.product'].create({
                    'name': sale_name,
                    'type': 'service',
                    'list_price': record.total_amount,
                })

            # Calculate stay duration in days
            if record.check_in_date and record.check_out_date:
                duration = (record.check_out_date - record.check_in_date).days
                if duration <= 0:
                    raise UserError("Check-out date must be later than check-in date.")
            else:
                duration = 0

            # Create Sale Order Line
            self.env['sale.order.line'].create({
                'order_id': sale_order.id,
                'name': product.name,
                'product_uom_qty': duration or 1,  # Ensure at least 1 unit is billed
                'price_unit': record.room_price,
                'product_id': product.id,
            })

            # Link Sale Order to Booking and Mark Payment as Paid
            record.sale_order_id = sale_order.id
            record.payment_status = 'unpaid'

            return {
                'type': 'ir.actions.act_window',
                'name': 'Sale Order',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': sale_order.id,
            }

    @api.depends('check_in_date', 'check_out_date')
    def _compute_rental_days(self):
        for record in self:
            if record.check_in_date and record.check_out_date:
                delta = record.check_out_date - record.check_in_date
                record.rental_days = max(delta.days, 0)
            else:
                record.rental_days = 0

    @api.depends('check_in_date', 'check_out_date', 'room_price')
    def _compute_total_amount(self):
        for record in self:
            if record.rental_days < 1:
                record.total_amount = record.room_price  # If less than 1 day, charge the room price only
            else:
                record.total_amount = record.rental_days * record.room_price  # Otherwise, calculate by days

    @api.depends('total_amount', 'sale_order_id.amount_total')
    def _compute_payment_amount(self):
        for record in self:
            if record.sale_order_id:
                record.payment_amount = record.sale_order_id.amount_total
            else:
                record.payment_amount = record.total_amount if record.total_amount else 0.0










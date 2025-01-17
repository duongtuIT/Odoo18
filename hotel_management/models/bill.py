from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError, ValidationError
import random, string
class BookingOrder(models.Model):
    _name = 'booking.order'
    _description = 'Booking Order'

    # Fields
    booking_code = fields.Char(string="Booking Code",  readonly=True, default=lambda self: self._generate_booking_code())
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
    room_total = fields.Float(
        string="Room Total",
        compute="_compute_room_total",
        store=True,
        readonly=True,
    )
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
    tax_amount = fields.Float(
        string="Tax Amount",
        compute="_compute_tax_amount",
        store=True,
        readonly=True,
    )
    total_service_amount = fields.Float(string='Total Service Amount', compute='_compute_total_service_amount')
    service_line = fields.One2many(
        'custom.booking.service.line',  # Tên của mô hình con
        'booking_id',  # Trường liên kết ở mô hình con
        string="Service Lines"
    )

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)

    @api.depends('payment_amount', 'total_amount')
    def _compute_tax_amount(self):
        for record in self:
            record.tax_amount = record.payment_amount - record.total_amount if record.payment_amount and record.total_amount else 0.0
    @api.depends('room_price', 'rental_days')
    def _compute_room_total(self):
        for record in self:
            record.room_total = record.room_price * record.rental_days if record.room_price and record.rental_days else 0.0
    @api.depends('service_line.subtotal')
    def _compute_total_service_amount(self):
        for record in self:
            record.total_service_amount = sum(line.subtotal for line in record.service_line)

    @staticmethod
    def _generate_booking_code():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    @api.depends('check_in_date', 'check_out_date')
    def _compute_rental_days(self):
        for record in self:
            if record.check_in_date and record.check_out_date:
                delta = record.check_out_date - record.check_in_date
                record.rental_days = delta.days if delta.days > 0 else 0
            else:
                record.rental_days = 0

    @api.depends('rental_days', 'room_id', 'service_line')
    def _compute_total_amount(self):
        for record in self:
            room_cost = record.rental_days * record.room_id.price if record.room_id else 0
            service_cost = sum(line.subtotal for line in record.service_line)
            record.total_amount = room_cost + service_cost

    @api.constrains('check_in_date', 'check_out_date')
    def _check_date_order(self):
        for record in self:
            if record.check_in_date and record.check_out_date:
                if record.check_in_date > record.check_out_date:
                    raise ValidationError("Check-in date cannot be later than check-out date.")

    def action_confirm(self):
        self.state = 'confirmed'

    def unlink(self):
        for booking in self:
            if booking.room_id:
                booking.room_id.write({'state': 'available'})
        return super(BookingOrder, self).unlink()

    @api.model
    def create(self, vals):
        # Tạo Sale Order khi tạo booking
        if vals.get('sale_order_id', False):
            sale_order = self.env['sale.order'].browse(vals['sale_order_id'])
        else:
            # Lấy customer_name từ booking và tìm partner (khách hàng)
            customer_name = vals.get('customer_name')
            partner = self.env['res.partner'].search([('name', '=', customer_name)], limit=1)

            if not partner:
                # Nếu không tìm thấy partner, tạo partner mới
                if not customer_name:
                    raise ValidationError("Tên khách hàng không thể trống.")
                partner = self.env['res.partner'].create({
                    'name': customer_name,
                    # Có thể thêm các trường khác như email, phone, v.v.
                })

            # Tạo Sale Order với chi tiết từ booking
            sale_order = self.env['sale.order'].create({
                'partner_id': partner.id,
                'origin': vals.get('booking_code'),
            })
            vals['sale_order_id'] = sale_order.id

        # Chỉ gọi phương thức create của cha sau khi xử lý các logic cần thiết
        return super(BookingOrder, self).create(vals)

    def _get_room_price(self, room_id):
        room = self.env['hotel.room'].browse(room_id)
        return room.price if room else 0

    def action_create_inventory(self):
        for record in self:
            if record.payment_status == 'paid':
                raise UserError("Thanh toán cho booking này đã được thực hiện.")

            # Lấy hoặc tạo Sale Order từ booking
            sale_order = record.sale_order_id
            if not sale_order:
                raise UserError("Không tìm thấy Đơn bán hàng cho booking này.")

            # Tính toán số ngày thuê phòng
            duration = (record.check_out_date - record.check_in_date).days
            if duration <= 0:
                raise UserError("Ngày trả phòng phải lớn hơn ngày nhận phòng.")

            # Tạo sản phẩm phòng nếu chưa có
            sale_name = f"{record.room_id.room_code} {record.check_in_date} - {record.check_out_date}" if record.room_id else "Đặt phòng"

            room_product_template = self.env['product.template'].search([('name', '=', sale_name)], limit=1)
            if not room_product_template:
                room_product_template = self.env['product.template'].create({
                    'name': sale_name,
                    'list_price': record.total_amount,  # Giá trước thuế
                    'taxes_id': [(6, 0, self.env['account.tax'].search([('type_tax_use', '=', 'sale')]).ids)],
                })

            # Tạo hoặc lấy sản phẩm gắn với template
            room_product = self.env['product.product'].search([('product_tmpl_id', '=', room_product_template.id)],
                                                              limit=1)
            if not room_product:
                room_product = self.env['product.product'].create({
                    'product_tmpl_id': room_product_template.id,
                })

            # Cập nhật dòng sản phẩm phòng trong Sale Order
            order_line = sale_order.order_line.filtered(lambda l: l.product_id == room_product)
            if order_line:
                order_line.write({
                    'product_uom_qty': duration,
                    'price_unit': record.room_id.price,
                })
            else:
                self.env['sale.order.line'].create({
                    'order_id': sale_order.id,
                    'name': room_product.name,
                    'product_uom_qty': duration,
                    'price_unit': record.room_id.price,
                    'product_id': room_product.id,
                    'tax_id': [(6, 0, room_product.taxes_id.ids)],
                })

            # Thêm hoặc cập nhật dòng sản phẩm dịch vụ (nếu có)
            if record.service_line:
                for service in record.service_line:
                    self.env['sale.order.line'].create({
                        'order_id': sale_order.id,
                        'product_id': service.product_id.id,
                        'product_uom_qty': service.quantity,
                        'price_unit': service.price_unit,
                        'tax_id': [(6, 0, service.product_id.taxes_id.ids)],
                    })

            # Chỉ xác nhận đơn hàng nếu nó ở trạng thái dự thảo
            if sale_order.state == 'draft':
                sale_order.action_confirm()

            # Tính tổng tiền cho Sale Order
            sale_order.amount_total = sum(line.price_total for line in sale_order.order_line)

            # Cập nhật thông tin thanh toán
            record.payment_status = 'paid'
            record.payment_date = fields.Date.today()
            record.payment_amount = sale_order.amount_total

        return {
            'type': 'ir.actions.act_window',
            'name': 'Đơn Bán Hàng',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
        }

    def action_confirm_payment(self):
        self.ensure_one()
        if self.payment_status == 'paid':
            raise ValidationError("Payment has already been confirmed for this booking.")
        self.payment_status = 'paid'
        self.payment_date = fields.Date.today()  # You can also use fields.Datetime.today() if you need the exact timestamp

    @api.depends('total_amount')
    def _compute_total_with_tax(self):
        for record in self:
            if record.room_id:
                taxes = record.room_id.taxes_id.compute_all(
                    record.total_amount,
                    currency=record.env.company.currency_id,
                    quantity=1.0
                )
                record.payment_amount = taxes['total_included']
            else:
                record.payment_amount = record.total_amount

    @api.model
    def print_booking_report(self):
        return self.env.ref('your_module.action_booking_order_report').report_action(self)













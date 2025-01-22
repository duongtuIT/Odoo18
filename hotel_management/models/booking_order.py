from odoo import models, fields, api
from datetime import date, timedelta
from odoo.exceptions import UserError, ValidationError
import random, string
class BookingOrder(models.Model):
    _name = 'booking.order'
    _description = 'Booking Order'

    # Basic Information
    booking_code = fields.Char(
        string="Booking Code",
        readonly=True,
        default=lambda self: self._generate_booking_code()
    )
    customer_name = fields.Char(
        string="Customer Name",
        required=True
    )

    # Dates
    booking_date = fields.Date(
        string="Booking Date",
        default=date.today(),
        required=True
    )
    check_in_date = fields.Date(
        string="Check-in Date",
        required=True
    )
    check_out_date = fields.Date(
        string="Check-out Date",
        required=True
    )

    # Hotel and Room Information
    hotel_id = fields.Many2one(
        'hotel.management',
        string="Hotel",
        required=True
    )
    room_type = fields.Selection(
        [('single', 'Single Bed'),('double', 'Double Bed')],
        string="Room Type",
        required=True
    )
    room_id = fields.Many2one(
        'hotel.room',
        string="Room ID",
        required=True,
        domain="[('hotel_id', '=', hotel_id),('bed_type', '=', room_type)]"
    )
    room_name = fields.Char(
        string="Room Name",
        related="room_id.room_code",
        store=True
    )
    weekday_price = fields.Float(
        string="Weekday Price",
        related='room_id.weekday_price',
        readonly=True
    )
    weekend_price = fields.Float(
        string="Weekend Price",
        related='room_id.weekend_price',
        readonly=True
    )

    # Financial Information
    weekday_days = fields.Integer(
        string="Weekday Days",
        compute="_compute_days_and_amounts",
        store=True
    )
    weekend_days = fields.Integer(
        string="Weekend Days",
        compute="_compute_days_and_amounts",
        store=True
    )
    weekday_amount = fields.Float(
        string="Weekday Amount",
        compute="_compute_days_and_amounts",
        store=True
    )
    weekend_amount = fields.Float(
        string="Weekend Amount",
        compute="_compute_days_and_amounts",
        store=True
    )
    total_days = fields.Integer(
        string="Total Days",
        compute="_compute_days_and_amounts",
        store=True
    )
    room_total = fields.Float(
        string="Total Amount",
        compute="_compute_days_and_amounts",
        store=True
    )
    payment_amount = fields.Float(
        string="Số tiền thanh toán",
        readonly=True,
        compute='_compute_total_with_tax',
        store=True
    )
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
    total_service_amount = fields.Float(
        string='Total Service Amount',
        compute='_compute_total_service_amount'
    )

    # Status Fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string="Booking Status", default='draft', tracking=True)

    payment_status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid')
    ], string="Payment Status", default='unpaid', tracking=True)
    payment_date = fields.Datetime(
        string="Ngày thanh toán",
        readonly=True
    )

    # Relations
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        readonly=True
    )
    service_line = fields.One2many(
        'custom.booking.service.line',  # Tên của mô hình con
        'booking_id',  # Trường liên kết ở mô hình con
        string="Service Lines"
    )

    #Compute Methods
    @api.depends('payment_amount', 'total_amount')
    def _compute_tax_amount(self):
        for record in self:
            record.tax_amount = record.payment_amount - record.total_amount if record.payment_amount and record.total_amount else 0.0

    @api.depends('service_line.subtotal')
    def _compute_total_service_amount(self):
        for record in self:
            record.total_service_amount = sum(line.subtotal for line in record.service_line)

    @api.depends('check_in_date', 'check_out_date', 'room_id')
    def _compute_days_and_amounts(self):
        for record in self:
            if record.check_in_date and record.check_out_date and record.room_id:
                # Tính toán số ngày thuê
                days = (record.check_out_date - record.check_in_date).days
                total_weekday_days = 0
                total_weekend_days = 0
                weekday_amount = 0.0
                weekend_amount = 0.0

                for i in range(days):
                    current_date = record.check_in_date + timedelta(days=i)
                    if current_date.weekday() >= 5:  # Cuối tuần (Thứ 7 và CN)
                        total_weekend_days += 1
                        weekend_amount += record.room_id.weekend_price
                    else:  # Ngày trong tuần
                        total_weekday_days += 1
                        weekday_amount += record.room_id.weekday_price

                # Gán giá trị cho các trường
                record.weekday_days = total_weekday_days
                record.weekend_days = total_weekend_days
                record.weekday_amount = weekday_amount
                record.weekend_amount = weekend_amount
                record.total_days = total_weekday_days + total_weekend_days
                record.room_total = weekday_amount + weekend_amount
            else:
                # Gán giá trị mặc định khi không có thông tin
                record.weekday_days = 0
                record.weekend_days = 0
                record.weekday_amount = 0.0
                record.weekend_amount = 0.0
                record.total_days = 0
                record.room_total = 0.0

    @api.depends('total_amount', 'room_id.taxes_id')
    def _compute_total_amount(self):
        for record in self:
            # Tổng tiền thuê phòng = số tiền trong tuần + số tiền cuối tuần
            room_cost = record.weekday_amount + record.weekend_amount

            # Tổng tiền dịch vụ
            service_cost = record.total_service_amount

            # Tổng tiền toàn bộ = tiền phòng + tiền dịch vụ
            record.total_amount = room_cost + service_cost

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

    #Constrains Methods
    @api.constrains('check_in_date', 'check_out_date')
    def _check_date_order(self):
        for record in self:
            if record.check_in_date and record.check_out_date:
                if record.check_in_date > record.check_out_date:
                    raise ValidationError("Check-in date cannot be later than check-out date.")

    @api.constrains('check_in_date', 'check_out_date', 'room_id')
    def _check_booking_overlap(self):
        for record in self:
            # Tìm các đặt phòng trùng ngày
            overlapping_bookings = self.env['booking.order'].search([
                ('room_id', '=', record.room_id.id),
                ('id', '!=', record.id),  # Bỏ qua bản ghi hiện tại
                ('check_in_date', '<=', record.check_out_date),
                ('check_out_date', '>=', record.check_in_date)
            ])
            if overlapping_bookings:
                raise ValidationError(
                    f"The room '{record.room_id.name}' is already booked for the selected dates."
                )

    def unlink(self):
        for booking in self:
            if booking.room_id:
                booking.room_id.write({'state': 'available'})
        return super(BookingOrder, self).unlink()

    # action Method
    def action_confirm_booking(self):
        self.state = 'confirmed'
        self.room_id.state = 'booked'

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
            record.payment_status = 'unpaid'
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
        self.payment_status = 'paid'
        self.payment_date = fields.Date.today()
        # Kiểm tra nếu phòng có được sử dụng bởi các đơn đặt khác
        overlapping_bookings = self.env['booking.order'].sudo().search([
            ('room_id', '=', self.room_id.id),
            ('id', '!=', self.id),  # Loại trừ đơn hiện tại
            ('state', '=', 'confirmed'),  # Các trạng thái cho thấy phòng đang sử dụng
            ('check_in_date', '<=', self.check_out_date),  # Thời gian check-in nằm trong khoảng
            ('check_out_date', '>=', self.check_in_date)
        ])

        # Nếu không có đơn nào sử dụng phòng, đổi trạng thái phòng thành 'available'
        if not overlapping_bookings:
            self.room_id.state = 'available'

    @api.model
    def create(self, vals):
        room = self.env['hotel.room'].browse(vals['room_id'])
        if room:
            overlap_booking = self.env['booking.order'].search([
                ('room_id', '=', vals['room_id']),
                ('check_in_date', '<=', vals['check_out_date']),
                ('check_out_date', '>=', vals['check_in_date']),
            ])
            if overlap_booking:
                raise models.ValidationError("The room is already booked for the selected dates.")
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

    @staticmethod
    def _generate_booking_code():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def get_revenue_report(self, start_date, end_date):
        # Lọc các đơn đã thanh toán
        orders = self.search([
            ('payment_status', '=', 'paid'),  # Chỉ các đơn đã thanh toán
            ('check_in_date', '>=', start_date),
            ('check_out_date', '<=', end_date)
        ])

        # Tổng doanh thu
        total_revenue = sum(order.payment_amount for order in orders)

        # Doanh thu chi tiết
        detailed_revenue = [
            {
                'customer_name': order.customer_name,
                'room_id': order.room_id.room_code,
                'amount': order.payment_amount,
            }
            for order in orders
        ]

        return {
            'total_revenue': total_revenue,
            'detailed_revenue': detailed_revenue,
        }













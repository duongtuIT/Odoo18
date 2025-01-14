from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_discount = fields.Float(string="Discount", default=0.0, help="Direct discount on the unit price.")

    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        self.ensure_one()  # Đảm bảo rằng chỉ có một bản ghi
        price_unit_discount = self.price_unit - (self.x_discount or 0.0)  # Tính giá trị giảm giá của sản phẩm
        if price_unit_discount < 0:
            price_unit_discount = 0  # Nếu giá trị giảm giá nhỏ hơn 0, đặt lại giá trị này thành 0

        # Gọi super() để tiếp tục với logic của lớp cha, truyền giá trị price_unit đã điều chỉnh
        return super()._prepare_base_line_for_taxes_computation(**{
            'price_unit': price_unit_discount,
            **kwargs,
        })

    @api.depends('product_id', 'product_uom_qty', 'price_unit', 'x_discount', 'order_id.currency_id')
    def _compute_amount(self):
        for line in self:
            discount_price = line.price_unit - line.x_discount
            # Tính subtotal (trước thuế) sử dụng giá đã giảm giá
            line.price_subtotal = discount_price * line.product_uom_qty

            # Tính toán thuế sử dụng giá đã giảm giá
            taxes = line.tax_id.compute_all(
                discount_price,
                line.order_id.currency_id,
                line.product_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_id)

            # Cập nhật giá trị tổng cộng (bao gồm thuế)
            line.price_total = taxes['total_included']


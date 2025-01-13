from odoo import fields, models, api

class Hotel(models.Model):
    _name = "hotel.management"
    _description = "Hotel Management"


     # Fields
    hotel_ids = fields.Char(string="Hotel ID", unique=True, index=True)  # Mã khách sạn (duy nhất)
    name = fields.Char(string="Hotel Name", required=True)  # Tên khách sạn
    address = fields.Char(string="Hotel Address", required=True)  # Địa chỉ khách sạn
    floor_count = fields.Integer(string="Number of Floors", required=True)  # Số tầng
    room_count = fields.Integer(
        string="Number of Rooms",
        compute="_compute_room_count",
        store=True,
    )
    manager_id = fields.Many2one('hr.employee', string="Manager", domain="[('job_id', '=', 'Hotel_Manager')]")

    # Quan hệ với bảng room
    room_ids = fields.One2many(
        'hotel.room', 'hotel_id', string="Rooms"
    )  # Một khách sạn có nhiều phòng

    # Constraints
    _sql_constraints = [
    ('hotel_ids_unique', 'unique(hotel_ids)', 'Hotel id must be unique.')]

    @api.model
    def create(self, vals):
        # Kiểm tra và tự động tạo hotel_ids nếu không có
        if 'hotel_ids' not in vals:
            last_hotel = self.search([], order='hotel_ids desc', limit=1)
            if last_hotel:
                last_code = int(last_hotel.hotel_ids)
                new_code = str(last_code + 1)
            else:
                new_code = '1'  # Nếu không có khách sạn nào, bắt đầu từ 1
            vals['hotel_ids'] = new_code

        return super(Hotel, self).create(vals)

    @api.depends('room_ids')
    def _compute_room_count(self):
        for hotel in self:
            hotel.room_count = len(hotel.room_ids)
    
    @api.constrains('floor_count')
    def _onchange_floor_count(self):
        if self.floor_count < 1:
            raise models.ValidationError("Number of floors must be greater than 0.")



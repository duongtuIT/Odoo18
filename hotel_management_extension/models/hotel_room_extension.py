from odoo import models, fields

class HotelRoom(models.Model):
    _inherit = 'hotel.room'

    # Thêm các trường mới
    room_size = fields.Float(string="Room Size (m²)", required=True)
    max_people = fields.Integer(string="Maximum People", required=True)
    smoking_allowed = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], string="Smoking Allowed", required=True, default='no'
    )

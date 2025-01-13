from odoo import models, fields

class RoomFeature(models.Model):
    _name = 'room.feature'
    _description = 'Room Feature'

    # Fields
    name = fields.Char(string="Feature Name", required=True, unique=True)

    # Quan hệ với phòng
    room_ids = fields.Many2many('hotel.room', string="Rooms")


{
    'name': 'Hotel Management System',
    'version': '1.0',
    'summary': 'Module quản lý khách sạn và đặt phòng',
    'description': """
        Module quản lý khách sạn, phòng, đặc điểm phòng và đơn đặt phòng:
        - Quản lý khách sạn và danh sách phòng
        - Quản lý đặc điểm của phòng
        - Quản lý đơn đặt phòng
    """,
    'author': 'Duong Tu',
    'website': 'https://yourwebsite.com',
    'category': 'Management',
    'depends': ['base','hr'],
    'data': [
        'data/crons.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/record_rule_hotel.xml',
        'security/record_rule_room.xml',
        'security/record_rule_booking.xml',
        'views/hotel_view.xml',  # Views cho khách sạn
        'views/room_view.xml',  # Views cho phòng
        'views/room_feature.xml',  # Views cho đặc điểm phòng
        'views/bill_view.xml',  # Views cho đơn đặt phòng
        'views/booking_pending.xml', # Views cho đơn đặt phòng đang chờ
        'views/booking_payment.xml'
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'icon': '/hotel_management/static/description/icon_hotel.png',
}
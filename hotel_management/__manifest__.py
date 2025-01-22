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
    'depends': ['base','hr','sale','mail','account','website'],
    'data': [
        'data/crons.xml',

        'controllers/available_rooms_template.xml',
        'controllers/book_room_template.xml',
        'controllers/booking_success_template.xml',
        'controllers/booking_error_template.xml',

        'security/security.xml',
        'security/ir.model.access.csv',
        'security/record_rule_hotel.xml',
        'security/record_rule_room.xml',
        'security/record_rule_booking.xml',

        'views/hotel_view.xml',
        'views/room_view.xml',
        'views/room_feature.xml',
        'views/booking_order.xml',
        'views/booking_pending.xml',

        'views/wizard_booking_payment.xml',
        'views/wizard_revenue_booking.xml',
        'views/wizard_available_room.xml',

        'reports/action_report_booking.xml',
        'reports/report_booking_template.xml',
        'reports/action_report_available_room.xml',
        'reports/action_report_revenue_booking.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hotel_management/static/src/css/button.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'icon': '/hotel_management/static/description/icon_hotel.png',
}
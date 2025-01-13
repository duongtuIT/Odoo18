{
    'name': 'Hotel Room Extension',
    'version': '2.0',
    'author': 'Your Name',
    'category': 'Management',
    'summary': 'Add room details and booking history',
    'depends': ['base', 'hotel_management','hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hotel_management_extension_view.xml',
        'views/hotel_room_extension_view.xml',
        
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'icon': '/hotel_management_extension/static/description/icons.png',
}

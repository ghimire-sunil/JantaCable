{
    'name': "Sales API",
    'version': '1.0',
    'depends': ['auth_signup', 'sale','website'],
    'author': "InfoDevelopers Pvt. Ltd.",
    'category': 'Web',
    'description': """
    Provides API for Sales and Product configuration for custom applications
    """,
    'data': [
            # 'data/res_config_data.xml',
	        'security/ir.model.access.csv',
             'views/mobile_slider.xml',
             'views/product_minimum_quantity.xml',
            ],
    'demo': [],
}

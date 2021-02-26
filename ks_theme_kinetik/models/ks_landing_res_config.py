from odoo import fields, models, api


class KsResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def default_fitness_module(self):
        fitness_module = self.env['ir.module.module'].search([('name', '=', 'ks_fitness_page')])
        if fitness_module:
            return True
        else:
            return False

    def default_corporate_page(self):
        corporate_page = self.env['ir.module.module'].search([('name', '=', 'ks_corporate_page')])
        if corporate_page:
            return True
        else:
            return False

    def default_book_shop_page(self):
        book_shop_page = self.env['ir.module.module'].search([('name', '=', 'ks_book_shop_page')])
        if book_shop_page:
            return True
        else:
            return False

    def default_ks_christmas_page(self):
        ks_christmas_page = self.env['ir.module.module'].search([('name', '=', 'ks_christmas_page')])
        if ks_christmas_page:
            return True
        else:
            return False

    def default_ks_food_shop_page(self):
        ks_food_shop_page = self.env['ir.module.module'].search([('name', '=', 'ks_food_shop_page')])
        if ks_food_shop_page:
            return True
        else:
            return False

    def default_ks_furniture_page(self):
        ks_furniture_page = self.env['ir.module.module'].search([('name', '=', 'ks_furniture_page')])
        if ks_furniture_page:
            return True
        else:
            return False

    def default_ks_home_decor_page(self):
        ks_home_decor_page = self.env['ir.module.module'].search([('name', '=', 'ks_home_decor_page')])
        if ks_home_decor_page:
            return True
        else:
            return False

    def default_ks_hotel_page(self):
        ks_hotel_page = self.env['ir.module.module'].search([('name', '=', 'ks_hotel_page')])
        if ks_hotel_page:
            return True
        else:
            return False

    def default_ks_jewellery_page(self):
        ks_jewellery_page = self.env['ir.module.module'].search([('name', '=', 'ks_jewellery_page')])
        if ks_jewellery_page:
            return True
        else:
            return False

    def default_ks_new_year_page(self):
        ks_new_year_page = self.env['ir.module.module'].search([('name', '=', 'ks_new_year_page')])
        if ks_new_year_page:
            return True
        else:
            return False

    def default_ks_pet_shop_page(self):
        ks_pet_shop_page = self.env['ir.module.module'].search([('name', '=', 'ks_pet_shop_page')])
        if ks_pet_shop_page:
            return True
        else:
            return False

    module_ks_fitness_page = fields.Boolean(string='Fitness Page')
    module_ks_corporate_page = fields.Boolean(string='Corporate Page')
    module_ks_pet_shop_page = fields.Boolean(string='Pet Shop Page')
    module_ks_furniture_page = fields.Boolean(string='Furniture Page')
    module_ks_food_shop_page = fields.Boolean(string='Food Shop Page')
    module_ks_jewellery_page = fields.Boolean(string='Jewellery Page')
    module_ks_book_shop_page = fields.Boolean(string='Book Shop Page')
    module_ks_hotel_page = fields.Boolean(string='Hotel Page')
    module_ks_christmas_page = fields.Boolean(string='Christmas Page')
    module_ks_new_year_page = fields.Boolean(string='New Year Page')
    module_ks_home_decor_page = fields.Boolean(string='Home Decor Page')

    fitness_page = fields.Boolean(string='Fitness', default=default_fitness_module)
    corporate_page = fields.Boolean(string='Corporate', default=default_corporate_page)
    pet_shop_page = fields.Boolean(string='Pet Shop', default=default_ks_pet_shop_page)
    furniture_page = fields.Boolean(string='Furniture', default=default_ks_furniture_page)
    food_shop_page = fields.Boolean(string='Food Shop', default=default_ks_food_shop_page)
    jewellery_page = fields.Boolean(string='Jewellery', default=default_ks_jewellery_page)
    book_shop_page = fields.Boolean(string='Book Shop', default=default_book_shop_page)
    hotel_page = fields.Boolean(string='Hotel', default=default_ks_hotel_page)
    christmas_page = fields.Boolean(string='Christmas', default=default_ks_christmas_page)
    new_year_page = fields.Boolean(string='New Year', default=default_ks_new_year_page)
    home_decor_page = fields.Boolean(string='Home Decor', default=default_ks_home_decor_page)

    def get_values(self):
        res_value = super(KsResConfigSettings, self).get_values()
        res_value.update(
            module_ks_fitness_page=self.env['ir.config_parameter'].sudo().get_param('module_ks_fitness_page'),
            module_ks_corporate_page=self.env['ir.config_parameter'].sudo().get_param('module_ks_corporate_page'),
            module_ks_pet_shop_page=self.env['ir.config_parameter'].sudo().get_param('module_ks_pet_shop_page'),
            module_ks_furniture_page=self.env['ir.config_parameter'].sudo().get_param('module_ks_furniture_page'),
            module_ks_food_shop_page=self.env['ir.config_parameter'].sudo().get_param('module_ks_food_shop_page'),
            module_ks_jewellery_page=self.env['ir.config_parameter'].sudo().get_param('module_ks_jewellery_page'),
            module_ks_book_shop_page=self.env['ir.config_parameter'].sudo().get_param('module_ks_book_shop_page'),
            module_ks_hotel_page=self.env['ir.config_parameter'].sudo().get_param('module_ks_hotel_page'),
            module_ks_christmas_page=self.env['ir.config_parameter'].sudo().get_param('module_ks_christmas_page'),
            module_ks_new_year_page=self.env['ir.config_parameter'].sudo().get_param('module_ks_new_year_page'),
            module_ks_home_decor_page=self.env['ir.config_parameter'].sudo().get_param('module_ks_home_decor_page'),

        )
        return res_value

    def set_values(self):
        super(KsResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('module_ks_fitness_page', self.module_ks_fitness_page)
        self.env['ir.config_parameter'].sudo().set_param('module_ks_corporate_page', self.module_ks_corporate_page)
        self.env['ir.config_parameter'].sudo().set_param('module_ks_pet_shop_page', self.module_ks_pet_shop_page)
        self.env['ir.config_parameter'].sudo().set_param('module_ks_furniture_page', self.module_ks_furniture_page)
        self.env['ir.config_parameter'].sudo().set_param('module_ks_food_shop_page', self.module_ks_food_shop_page)
        self.env['ir.config_parameter'].sudo().set_param('module_ks_jewellery_page', self.module_ks_jewellery_page)
        self.env['ir.config_parameter'].sudo().set_param('module_ks_book_shop_page', self.module_ks_book_shop_page)
        self.env['ir.config_parameter'].sudo().set_param('module_ks_hotel_page', self.module_ks_hotel_page)
        self.env['ir.config_parameter'].sudo().set_param('module_ks_christmas_page', self.module_ks_christmas_page)
        self.env['ir.config_parameter'].sudo().set_param('module_ks_new_year_page', self.module_ks_new_year_page)
        self.env['ir.config_parameter'].sudo().set_param('module_ks_home_decor_page', self.module_ks_home_decor_page)


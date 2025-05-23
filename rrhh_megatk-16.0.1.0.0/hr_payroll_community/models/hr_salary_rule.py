# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp

class HrPayrollStructure(models.Model):
    """
    Salary structure used to defined
    - Basic
    - Allowances
    - Deductions
    """
    _name = 'hr.payroll.structure'
    _description = 'Salary Structure'

    @api.model
    def _get_parent(self):
        return self.env.ref('hr_payroll_community.structure_base', False)

    name = fields.Char(required=True)
    code = fields.Char(string='Referencia', required=True)
    company_id = fields.Many2one('res.company', string='Compañia', required=True,
        copy=False, default=lambda self: self.env['res.company']._company_default_get())
    note = fields.Text(string='Descripción')
    parent_id = fields.Many2one('hr.payroll.structure', string='Reglas padre', default=_get_parent)
    children_ids = fields.One2many('hr.payroll.structure', 'parent_id', string='Reglas hijas', copy=True)
    rule_ids = fields.Many2many('hr.salary.rule', 'hr_structure_salary_rule_rel', 'struct_id', 'rule_id', string='Reglas salariales')

    @api.constrains('parent_id')
    def _check_parent_id(self):

        if not self._check_recursion():
            raise ValidationError(_('No se puede crear una estructura salarial recursiva.'))

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):

        self.ensure_one()
        default = dict(default or {}, code=_("%s (copy)") % (self.code))
        return super(HrPayrollStructure, self).copy(default)

    def get_all_rules(self):

        """
        @return: devuelve una lista de tuplas (id, secuencia) de reglas que posiblemente se apliquen
        """
        all_rules = []
        for struct in self:
            all_rules += struct.rule_ids._recursive_search_of_rules()
        return all_rules

    def _get_parent_structure(self):

        parent = self.mapped('parent_id')
        if parent:
            parent = parent._get_parent_structure()
        return parent + self


class HrContributionRegister(models.Model):
    _name = 'hr.contribution.register'
    _description = 'Contribution Register'

    company_id = fields.Many2one('res.company', string='Compañia',
        default=lambda self: self.env['res.company']._company_default_get())
    partner_id = fields.Many2one('res.partner', string='Asociado')
    name = fields.Char(required=True)
    register_line_ids = fields.One2many('hr.payslip.line', 'register_id',
        string='Línea de registro', readonly=True)
    note = fields.Text(string='Descripción')


class HrSalaryRuleCategory(models.Model):
    _name = 'hr.salary.rule.category'
    _description = 'Salary Rule Category'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    parent_id = fields.Many2one('hr.salary.rule.category', string='Padre',
        help="La vinculación de una categoría salarial a su principal se utiliza únicamente con fines de generación de informes..")
    children_ids = fields.One2many('hr.salary.rule.category', 'parent_id', string='Hijo')
    note = fields.Text(string='Descripción')
    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env['res.company']._company_default_get())
    category_base = fields.Boolean('categoria base', default=False)
    active = fields.Boolean('activa', default=True)

    @api.constrains('parent_id')
    def _check_parent_id(self):

        if not self._check_recursion():
            raise ValidationError(_('¡Error! No se puede crear una jerarquía recursiva de categoría de regla salarial.'))
        
    def unlink(self):
        for category in self:
            if category.category_base:
                raise UserError(_('No se puede eliminar una categoria base, pongase en contacto con su administrador'))
            else:
                return super(HrSalaryRuleCategory, self).unlink()


class HrSalaryRule(models.Model):
    _name = 'hr.salary.rule'
    _order = 'sequence, id'
    _description = 'Salary Rule'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, help="El código que se puede utilizar en las reglas salariales.")
    sequence = fields.Integer(required=True, index=True, default=5,
        help='Usar para organizar la secuencia de cálculo')
    quantity = fields.Char(default='1.0',
        help="Se utiliza en el cálculo de porcentajes y cantidades fijas"
             "Por ejemplo, una regla para el vale de comida que tiene una cantidad fija de "
             u"100 LPS por día trabajado puede tener su cantidad definida en la expresión "
             "como días_trabajados.TRABAJO100.número_de_días.")
    category_id = fields.Many2one('hr.salary.rule.category', string='Categoria', required=True)
    rule_base = fields.Boolean('regla base', default=False)
    active = fields.Boolean(default=True,
        help="Si el campo activo se establece en falso, le permitirá ocultar la regla salarial sin eliminarla.")
    appears_on_payslip = fields.Boolean(string='Aparece en el recibo de sueldo', default=True,
        help="Se utiliza para mostrar la regla salarial en el recibo de nómina.")
    parent_rule_id = fields.Many2one('hr.salary.rule', string='Regla de salario de los padres', index=True)
    company_id = fields.Many2one('res.company', string='Compañia',
        default=lambda self: self.env['res.company']._company_default_get())
    condition_select = fields.Selection([
        ('none', 'Siempre verdadera'),
        ('range', 'Rango'),
    ], string="Condición basado en", default='none', required=True)
    condition_range = fields.Char(string='Rango basado en', default='contract.wage',)
    condition_python = fields.Text(string='Python Condición',
        help='Se aplicó esta regla para el cálculo si la condición es verdadera. Se puede especificar una condición como "básico > 1000"..')
    condition_range_min = fields.Float(string='Rango minimo', help="El importe mínimo, aplicado para esta regla.")
    condition_range_max = fields.Float(string='Rango maximo', help="El importe maximo, aplicado para esta regla.")
    amount_select = fields.Selection([
        ('percentage', 'Porcentage (%)'),
        ('fix', 'Cantidad Fija'), 
    ], string='Tipo de monto', index=True, required=True, default='fix', help="El método de cálculo para el monto de la regla.")
    amount_fix = fields.Float(string='Monto Fijo', digits=dp.get_precision('Payroll'))
    amount_percentage = fields.Float(string='Porcentaje (%)', digits=dp.get_precision('Payroll Rate'),
        help='Por ejemplo, ingrese 50.0 para aplicar un porcentaje del 50%')
    amount_python_compute = fields.Text(string='Código Python')
    amount_percentage_base = fields.Char(string='Porcentaje basado en', default='Sueldo', help='El resultado se verá afectado de forma variable')
    child_ids = fields.One2many('hr.salary.rule', 'parent_rule_id', string='Regla de salario infantil', copy=True)
    register_id = fields.Many2one('hr.contribution.register', string='Registro de contribuciones',
        help="Tercero eventual involucrado en el pago de salarios de los trabajadores.")
    input_ids = fields.One2many('hr.rule.input', 'input_id', string='Entradas', copy=True)
    note = fields.Text(string='Descripción')
    """en_base_a = fields.Selection([
        ('sueldo', 'Sueldo completo'),
        ('quincena', 'Quincena'),
    ], string='En base a:')"""

    @api.constrains('parent_rule_id')
    def _check_parent_rule_id(self):
        if not self._check_recursion(parent='parent_rule_id'):
            raise ValidationError(_('¡Error! No se puede crear una jerarquía recursiva de reglas salariales..'))

    def _recursive_search_of_rules(self):
        """
        @return: devuelve una lista de tuplas (id, secuencia) que son todos los hijos de los rule_ids pasados
        """
        children_rules = []
        for rule in self.filtered(lambda rule: rule.child_ids):
            children_rules += rule.child_ids._recursive_search_of_rules()
        return [(rule.id, rule.sequence) for rule in self] + children_rules

    #TODO should add some checks on the type of result (should be float)
    def _compute_rule(self, localdict):

        """
        :param localdict: diccionario que contiene el entorno en el que se calculará la regla
        :return: Devuelve una tupla construida como la base/cantidad calculada, la cantidad y la tasa.
        :rtype: (float, float, float)
        """
        self.ensure_one()
        if self.amount_select == 'fix':
            try:
                return self.amount_fix, float(safe_eval(self.quantity, localdict)), 100.0
            except:
                raise UserError(_('Cantidad incorrecta definida para la regla de salario %s (%s).') % (self.name, self.code))
        elif self.amount_select == 'percentage':
            try:
                return (float(safe_eval(self.amount_percentage_base, localdict)),
                        float(safe_eval(self.quantity, localdict)),
                        self.amount_percentage)
            except:
                raise UserError(_('Base porcentual incorrecta o cantidad definida para la regla salarial %s (%s).') % (self.name, self.code))
        else:
            try:
                safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
                return float(localdict['result']), 'result_qty' in localdict and localdict['result_qty'] or 1.0, 'result_rate' in localdict and localdict['result_rate'] or 100.0
            except:
                raise UserError(_('Código de Python incorrecto definido para la regla de salario %s (%s).') % (self.name, self.code))

    def _satisfy_condition(self, localdict):

        """
        @param contract_id: Identificación del contrato hr.contract que se va a probar
        @return: Devuelve Verdadero si la regla dada coincide con la condición del contrato dado. Devuelve Falso en caso contrario.
        """
        self.ensure_one()

        if self.condition_select == 'none':
            return True
        elif self.condition_select == 'range':
            try:
                result = safe_eval(self.condition_range, localdict)
                return self.condition_range_min <= result and result <= self.condition_range_max or False
            except:
                raise UserError(_('Condición de rango incorrecta definida para la regla de salario %s (%s).') % (self.name, self.code))
        else:  # python code
            try:
                safe_eval(self.condition_python, localdict, mode='exec', nocopy=True)
                return 'result' in localdict and localdict['result'] or False
            except:
                raise UserError(_('Condición de Python incorrecta definida para la regla de salario %s (%s).') % (self.name, self.code))
            
    def unlink(self):
        for rule in self:
            if rule.rule_base:
                raise UserError(_('No se puede eliminar una regla base, pongase en contacto con su administrador'))
            else:
                return super(HrSalaryRule, self).unlink()
        


class HrRuleInput(models.Model):
    _name = 'hr.rule.input'
    _description = 'Salary Rule Input'

    name = fields.Char(string='Descripción', required=True)
    code = fields.Char(required=True, help="El código que se puede utilizar en las reglas salariales")
    input_id = fields.Many2one('hr.salary.rule', string='Entrada de regla salarial', required=True)

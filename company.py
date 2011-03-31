# -*- coding: utf-8 -*-
#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
"Company"
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval

class Company(ModelSQL, ModelView):
    _name = 'company.company'

    budget = fields.Many2One('ekd.account.budget', 'Budget Company', ondelete="RESTRICT")

Company()

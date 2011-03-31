# -*- coding: utf-8 -*-
#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
{
    'name': 'General Budget System',
    'name_ru_RU': 'Бюджеты организации',
    'version': '1.8.0',
    'author': 'Dmitry Klimanov',
    'email': 'k-dmitry2@narod.ru',
    'website': 'http://www.tryton.org/',
    'description': '''Budget 
''',
    'description_ru_RU': '''Бюджеты организации
''',
    'depends': [
        'ir',
        'ekd_system',
        'ekd_company',
        'ekd_documents',
        'ekd_account',
    ],
    'xml': [
        'xml/ekd_budget.xml',
        'xml/ekd_budget_line.xml',
        'xml/ekd_budget_type.xml',
        'xml/ekd_budget_template.xml',
        'xml/ekd_doc_request_view.xml',
        'xml/ekd_budget_reports.xml',
        'xml/ekd_system.xml',
    ],
    'translation': [
        'ru_RU.csv',
    ],
}

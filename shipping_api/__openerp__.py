# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    'name': 'Shipping API',
    'version': '2.5',
    'category': 'Generic Modules/Others',
    'description': """
    """,
    'author': 'NovaPoint Group LLC',
    'website': ' http://www.novapointgroup.com',
    'depends': ['npg_delivery','account_analytic_default', 'purchase'],
    'data': [
        'stock_package_data.xml',
        'security/ir.model.access.csv',
        'views/shipping_view.xml',
        'views/stock_view.xml',
#        'views/sale_view.xml',
        'views/stock_package_view.xml',
        'views/email_template_view.xml',
        'views/purchase_view.xml',
        'report/shipping_report.xml',
    ],
    'demo': [],
    'test': ['test/shipping_api_updated.yml'],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

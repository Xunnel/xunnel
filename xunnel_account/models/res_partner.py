# -*- coding: utf-8 -*-
# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class ResPartner(models.Model):
    """ Creation of xml supplier """
    _inherit = 'res.partner'

    @api.model
    def create_partner(self, xml, ver, attr):
        """ It creates the supplier dictionary, getting data from the XML
        Receives an xml decode to read and returns a dictionary with data """
        def get_location(findby, val, model):
            """ It gets the location (country, state, city), wheter does not
            found the location, it makes a deeper research.
            Returns: ids location matches
            Receives: - Name or code or whatever (in case of code country)
            - What will be searched (city, state or country name)
            - Model where it will look """
            object_ids = self.env[model].search([(findby, 'ilike', val)])
            if len(object_ids) < 1 and val != '':
                object_ids = self.env['account.pre.invoice'].get_ids_search(
                    model, ['name'], val)
            return object_ids

        partner_dict = {
            'name': xml.Emisor.get(attr['nombre'][ver], False),
            'company_type': 'company',
            'vat': xml.Emisor.get(attr['rfc'][ver], False),
            'ref': xml.Emisor.get(attr['rfc'][ver], False),
            'supplier': True,
            'customer': False,
        }

        if ver == '3.2':
            if 'DomicilioFiscal' in xml.Emisor.__dict__.keys():
                country_by = 'name'
                if len(xml.Emisor.DomicilioFiscal.get('pais', 'None')) <= 2:
                    country_by = 'code'
                country_ids = get_location(
                    country_by, xml.Emisor.DomicilioFiscal.get(
                        'pais', None), 'res.country')
                state_ids = get_location(
                    'name', xml.Emisor.DomicilioFiscal.get(
                        'estado', None), 'res.country.state')

                state_id = country_id = False
                if country_ids:
                    country_id = country_ids[0].id
                if state_ids:
                    cutries = [cty.values()[0] for cty in country_ids.read(
                        ['id'])]
                    for stte in state_ids.read(['country_id']):
                        if stte['country_id'][0] in cutries:
                            state_id = stte['id']
                            country_id = stte['country_id'][0]
                            break

                partner_dict.update({
                    'street_name': xml.Emisor.DomicilioFiscal.get(
                        'calle', False),
                    'street_number': xml.Emisor.DomicilioFiscal.get(
                        'noExterior', False),
                    'street_number2': xml.Emisor.DomicilioFiscal.get(
                        'noInterior', False),
                    'zip': xml.Emisor.DomicilioFiscal.get(
                        'codigoPostal', False),
                    'street2': xml.Emisor.DomicilioFiscal.get(
                        'colonia', False),
                    'city': xml.Emisor.DomicilioFiscal.get('municipio', False),
                    'l10n_mx_locality': xml.Emisor.DomicilioFiscal.get(
                        'localidad', False),
                    'state_id': state_id,
                    'country_id': country_id,
                })
        return self.create(partner_dict)

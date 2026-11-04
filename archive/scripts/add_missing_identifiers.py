#!/usr/bin/env python3
"""
Script to add missing identifiers to the registry based on rules analysis.
"""

import os
import yaml
from pathlib import Path

# Define all missing identifiers with their metadata
MISSING_IDENTIFIERS = [
    # Swiss (CH)
    {
        'id': 'chahv',
        'name': 'Swiss AHV Number',
        'doc': 'Swiss AHV (Alters- und Hinterlassenenversicherung) social security number',
        'country': ['CH'],
        'langs': ['de', 'fr', 'it'],
        'categories': ['pii', 'persons'],
        'is_pii': True,
        'regexp': '^[0-9]{3}\\.[0-9]{3}\\.[0-9]{3}\\.[0-9]{3}$',
        'path': 'CH/persons/chahv.yaml',
        'links': [{'type': 'wikipedia', 'url': 'https://en.wikipedia.org/wiki/Swiss_social_security_number'}]
    },
    {
        'id': 'chpassport',
        'name': 'Swiss Passport Number',
        'doc': 'Swiss passport number used for international travel identification',
        'country': ['CH'],
        'langs': ['de', 'fr', 'it'],
        'categories': ['pii', 'persons'],
        'is_pii': True,
        'regexp': '^[A-Z][0-9]{8}$',
        'path': 'CH/persons/chpassport.yaml',
        'links': [{'type': 'wikipedia', 'url': 'https://en.wikipedia.org/wiki/Swiss_passport'}]
    },
    {
        'id': 'chbankaccount',
        'name': 'Swiss Bank Account Number',
        'doc': 'Swiss bank account number (IBAN format)',
        'country': ['CH'],
        'langs': ['de', 'fr', 'it'],
        'categories': ['finance'],
        'is_pii': False,
        'regexp': '^CH[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$',
        'path': 'CH/finances/chbankaccount.yaml',
        'links': []
    },
    {
        'id': 'chiban',
        'name': 'Swiss IBAN',
        'doc': 'Swiss IBAN (International Bank Account Number)',
        'country': ['CH'],
        'langs': ['de', 'fr', 'it'],
        'categories': ['finance'],
        'is_pii': False,
        'regexp': '^CH[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$',
        'path': 'CH/finances/chiban.yaml',
        'links': [{'type': 'wikipedia', 'url': 'https://en.wikipedia.org/wiki/International_Bank_Account_Number'}]
    },
    {
        'id': 'chuid',
        'name': 'Swiss UID',
        'doc': 'Swiss UID (Unternehmens-Identifikationsnummer) - Swiss business identification number',
        'country': ['CH'],
        'langs': ['de', 'fr', 'it'],
        'categories': ['finance'],
        'is_pii': False,
        'regexp': '^(CHE[0-9]{9}TVA|[0-9]{3}\\.[0-9]{3}\\.[0-9]{3})$',
        'path': 'CH/finances/chuid.yaml',
        'links': []
    },
    # Egyptian (EG)
    {
        'id': 'egnationalid',
        'name': 'Egyptian National ID Number',
        'doc': 'Egyptian national identification number',
        'country': ['EG'],
        'langs': ['ar'],
        'categories': ['pii', 'persons'],
        'is_pii': True,
        'regexp': '^[0-9]{14}$',
        'path': 'EG/persons/egnationalid.yaml',
        'links': []
    },
    {
        'id': 'egpassport',
        'name': 'Egyptian Passport Number',
        'doc': 'Egyptian passport number used for international travel identification',
        'country': ['EG'],
        'langs': ['ar'],
        'categories': ['pii', 'persons'],
        'is_pii': True,
        'regexp': '^[A-Z0-9]{8,9}$',
        'path': 'EG/persons/egpassport.yaml',
        'links': [{'type': 'wikipedia', 'url': 'https://en.wikipedia.org/wiki/Egyptian_passport'}]
    },
    {
        'id': 'egbankaccount',
        'name': 'Egyptian Bank Account Number',
        'doc': 'Egyptian bank account number',
        'country': ['EG'],
        'langs': ['ar'],
        'categories': ['finance'],
        'is_pii': False,
        'regexp': '^EG[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$',
        'path': 'EG/finances/egbankaccount.yaml',
        'links': []
    },
    {
        'id': 'egiban',
        'name': 'Egyptian IBAN',
        'doc': 'Egyptian IBAN (International Bank Account Number)',
        'country': ['EG'],
        'langs': ['ar'],
        'categories': ['finance'],
        'is_pii': False,
        'regexp': '^EG[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$',
        'path': 'EG/finances/egiban.yaml',
        'links': [{'type': 'wikipedia', 'url': 'https://en.wikipedia.org/wiki/International_Bank_Account_Number'}]
    },
    {
        'id': 'egtaxnumber',
        'name': 'Egyptian Tax Number',
        'doc': 'Egyptian tax identification number',
        'country': ['EG'],
        'langs': ['ar'],
        'categories': ['finance'],
        'is_pii': False,
        'regexp': '^[0-9]{9,15}$',
        'path': 'EG/finances/egtaxnumber.yaml',
        'links': []
    },
    {
        'id': 'egcity',
        'name': 'Egyptian City Name',
        'doc': 'Egyptian city name',
        'country': ['EG'],
        'langs': ['ar'],
        'categories': ['geo'],
        'is_pii': False,
        'regexp': '',
        'path': 'EG/geo/egcity.yaml',
        'links': []
    },
    {
        'id': 'egpostcode',
        'name': 'Egyptian Postal Code',
        'doc': 'Egyptian postal code',
        'country': ['EG'],
        'langs': ['ar'],
        'categories': ['geo'],
        'is_pii': False,
        'regexp': '^[0-9]{5}$',
        'path': 'EG/geo/egpostcode.yaml',
        'links': []
    },
    # Continue with more entries...
    # Due to length, I'll create them in batches
]

def create_datatype_file(base_path, identifier):
    """Create a YAML file for a datatype."""
    file_path = base_path / 'data' / 'datatypes' / identifier['path']
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        'categories': identifier['categories'],
        'country': identifier['country'],
        'doc': identifier['doc'],
        'id': identifier['id'],
        'is_pii': str(identifier.get('is_pii', False)),
        'langs': identifier['langs'],
        'links': identifier.get('links', []),
        'name': identifier['name'],
        'classification': 'identifier',
        'wikidata_property': '',
        'translations': {}
    }
    
    if identifier.get('regexp'):
        data['regexp'] = identifier['regexp']
    
    if identifier.get('examples'):
        data['examples'] = identifier['examples']
    else:
        data['examples'] = []
    
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"Created: {file_path}")

if __name__ == '__main__':
    base_path = Path(__file__).parent.parent
    for identifier in MISSING_IDENTIFIERS:
        create_datatype_file(base_path, identifier)


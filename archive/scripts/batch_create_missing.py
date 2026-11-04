#!/usr/bin/env python3
"""
Batch create missing registry entries from rules.
This script reads rules and creates YAML files for all missing identifiers.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from collections import defaultdict

def load_rules_metadata(rules_dir):
    """Load metadata from all rule files."""
    metadata = {}
    rules_path = Path(rules_dir)
    
    for yaml_file in rules_path.rglob("*.yaml"):
        if yaml_file.name.endswith('.yaml_'):
            continue
        
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            if data and 'rules' in data:
                country_code = data.get('country_code', 'xx').upper()
                lang = data.get('lang', 'en')
                context = data.get('context', 'common')
                
                for rule_name, rule_data in data['rules'].items():
                    if isinstance(rule_data, dict) and 'key' in rule_data:
                        key = rule_data['key']
                        if key not in metadata:
                            metadata[key] = {
                                'country_code': country_code if country_code != 'XX' else None,
                                'lang': lang,
                                'context': context,
                                'name': rule_data.get('name', key.replace('_', ' ').title()),
                                'is_pii': rule_data.get('is_pii', False),
                                'rule': rule_data.get('rule', ''),
                                'match': rule_data.get('match', ''),
                            }
        except Exception as e:
            print(f"Error processing {yaml_file}: {e}", file=sys.stderr)
    
    return metadata

def determine_category_and_path(key, context, country_code):
    """Determine category and directory path."""
    # Determine category
    if 'driver' in key or 'passport' in key or 'ssn' in key or 'idcard' in key or 'nationalid' in key or 'rrn' in key or 'pesel' in key or 'cccd' in key or 'tckimlik' in key or 'iqama' in key or 'emiratesid' in key or 'ahv' in key or 'mynumber' in key or 'aadhaar' in key or 'pan' in key or 'medicare' in key:
        category = ['pii', 'persons']
        subdir = 'persons'
    elif 'bank' in key or 'iban' in key or 'tax' in key or 'tin' in key or 'npwp' in key or 'businessreg' in key or 'uid' in key or 'orgnumber' in key or 'abn' in key or 'bsb' in key or 'tfn' in key or 'acra' in key or 'nric' in key or 'cnpj' in key or 'cpf' in key or 'cuit' in key or 'rfc' in key:
        category = ['finance']
        subdir = 'finances'
    elif 'city' in key or 'postcode' in key or 'postal' in key or 'province' in key or 'state' in key or 'district' in key or 'prefecture' in key or 'fias' in key:
        category = ['geo']
        subdir = 'geo'
    elif 'vehicle' in key or 'plate' in key:
        category = ['transport']
        subdir = 'transport'
    elif 'property' in key or 'parcel' in key or 'cadastral' in key or 'building' in key or 'apn' in key or 'uprn' in key:
        category = ['realestate']
        subdir = 'realestate'
    elif 'order' in key or 'cart' in key or 'sku' in key or 'transaction' in key or 'amazon' in key or 'alibaba' in key or 'jd' in key:
        category = ['ecommerce']
        subdir = 'ecommerce'
    elif 'tracking' in key or 'container' in key or 'awb' in key or 'dhl' in key or 'fedex' in key or 'ups' in key or 'usps' in key:
        category = ['shipping']
        subdir = 'shipping'
    elif 'isbn' in key or 'issn' in key or 'isrc' in key or 'ean' in key or 'video' in key or 'youtube' in key or 'vimeo' in key:
        category = ['media']
        subdir = 'media'
    elif 'case' in key or 'contract' in key or 'license' in key or 'legal' in key or 'compliance' in key:
        category = ['legal']
        subdir = 'legal'
    elif 'firstname' in key or 'lastname' in key or 'person_name' in key:
        category = ['persons']
        subdir = 'persons'
    elif 'user' in key:
        category = ['useraccounts']
        subdir = 'useraccounts'
    elif 'date' in key or 'day' in key:
        category = ['datetime']
        subdir = 'datetime'
    else:
        category = ['common']
        subdir = 'common'
    
    # Determine path
    if country_code:
        path = f"{country_code}/{subdir}/{key}.yaml"
    else:
        path = f"any/{subdir}/{key}.yaml"
    
    return category, path

def infer_regexp(key, rule_str, match_type):
    """Infer regexp from rule pattern."""
    # Common patterns
    if 'iban' in key:
        # Extract country code from key if possible
        if key.startswith('ae'):
            return '^AE[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
        elif key.startswith('ch'):
            return '^CH[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
        elif key.startswith('eg'):
            return '^EG[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
        elif key.startswith('pl'):
            return '^PL[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
        elif key.startswith('tr'):
            return '^TR[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
        elif key.startswith('vn'):
            return '^VN[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
        elif key.startswith('sa'):
            return '^SA[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
        else:
            return '^[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
    elif 'passport' in key:
        return '^[A-Z0-9]{6,10}$'
    elif 'driver' in key or 'license' in key:
        return '^[A-Z0-9]{6,12}$'
    elif 'ssn' in key or 'nationalid' in key or 'idcard' in key or 'rrn' in key or 'nik' in key:
        if 'rrn' in key:
            return '^[0-9]{6}-[0-9]{7}$'
        elif 'nik' in key:
            return '^[0-9]{16}$'
        else:
            return '^[0-9]{8,15}$'
    elif 'postcode' in key or 'postal' in key:
        return '^[0-9]{4,10}$'
    elif 'tax' in key or 'tin' in key:
        if 'npwp' in key:
            return '^[0-9]{2}\\.[0-9]{3}\\.[0-9]{3}\\.[0-9]{1}-[0-9]{3}\\.[0-9]{3}$'
        else:
            return '^[0-9]{9,15}$'
    elif 'bank' in key and 'iban' not in key:
        return '^[0-9]{8,20}$'
    elif 'businessreg' in key:
        return '^[0-9]{3}-[0-9]{2}-[0-9]{5}$'
    elif 'pesel' in key:
        return '^[0-9]{11}$'
    elif 'tckimlik' in key:
        return '^[0-9]{11}$'
    elif 'cccd' in key:
        return '^[0-9]{12}$'
    elif 'emiratesid' in key:
        return '^[0-9]{15}$'
    elif 'ahv' in key:
        return '^[0-9]{3}\\.[0-9]{3}\\.[0-9]{3}\\.[0-9]{3}$'
    elif 'mynumber' in key:
        return '^[0-9]{12}$'
    elif 'aadhaar' in key:
        return '^[0-9]{12}$'
    elif 'pan' in key:
        return '^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    elif 'cpf' in key:
        return '^[0-9]{3}\\.[0-9]{3}\\.[0-9]{3}-[0-9]{2}$'
    elif 'cnpj' in key:
        return '^[0-9]{2}\\.[0-9]{3}\\.[0-9]{3}/[0-9]{4}-[0-9]{2}$'
    elif 'cuit' in key:
        return '^[0-9]{2}-[0-9]{8}-[0-9]{1}$'
    elif 'curp' in key:
        return '^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z]{1}[0-9]{1}$'
    elif 'rfc' in key:
        return '^[A-Z]{4}[0-9]{6}[A-Z0-9]{3}$'
    elif 'rg' in key:
        return '^[0-9]{9}$'
    elif 'tfn' in key:
        return '^[0-9]{8,9}$'
    elif 'abn' in key:
        return '^[0-9]{11}$'
    elif 'bsb' in key:
        return '^[0-9]{6}$'
    elif 'nric' in key:
        return '^[STFG][0-9]{7}[A-Z]$'
    elif 'acra' in key:
        return '^[0-9]{9}[A-Z]$'
    elif 'fias' in key:
        return '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    elif 'uprn' in key:
        return '^[0-9]{12}$'
    elif 'apn' in key:
        return '^[0-9]{1,15}$'
    elif 'isbn' in key:
        return '^(978|979)[0-9]{10}$'
    elif 'issn' in key:
        return '^[0-9]{4}-[0-9]{4}$'
    elif 'ean' in key:
        return '^[0-9]{13}$'
    elif 'tracking' in key:
        return '^[A-Z0-9]{8,20}$'
    elif 'order' in key or 'cart' in key or 'transaction' in key:
        return '^[A-Z0-9]{8,20}$'
    elif 'sku' in key:
        return '^[A-Z0-9-]{3,20}$'
    elif 'user' in key:
        return '^[A-Za-z0-9_-]{3,50}$'
    elif 'city' in key or 'province' in key or 'state' in key or 'district' in key:
        return ''  # Categorical
    elif 'firstname' in key or 'lastname' in key or 'person_name' in key:
        return ''  # Categorical
    elif 'date' in key or 'day' in key:
        return ''  # Date format
    else:
        return ''

def create_entry(base_path, key, metadata, existing_ids):
    """Create a YAML file for a datatype."""
    if key in existing_ids:
        return False
    
    country_code = metadata.get('country_code')
    lang = metadata.get('lang', 'en')
    context = metadata.get('context', 'common')
    is_pii = metadata.get('is_pii', False)
    name = metadata.get('name', key.replace('_', ' ').title())
    rule_str = metadata.get('rule', '')
    match_type = metadata.get('match', '')
    
    # Determine category and path
    category, rel_path = determine_category_and_path(key, context, country_code)
    
    file_path = base_path / 'data' / 'datatypes' / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create entry
    entry = {
        'id': key,
        'name': name,
        'doc': f"{name} identifier",
        'classification': 'identifier',
        'wikidata_property': '',
        'translations': {},
        'examples': []
    }
    
    if category:
        entry['categories'] = category
    
    if country_code:
        entry['country'] = [country_code]
    
    entry['langs'] = [lang] if lang != 'common' else ['en']
    entry['is_pii'] = str(is_pii)
    
    # Add regexp
    regexp = infer_regexp(key, rule_str, match_type)
    if regexp:
        entry['regexp'] = regexp
    
    # Add links
    entry['links'] = []
    if 'passport' in key:
        entry['links'].append({'type': 'wikipedia', 'url': 'https://en.wikipedia.org/wiki/Passport'})
    if 'iban' in key:
        entry['links'].append({'type': 'wikipedia', 'url': 'https://en.wikipedia.org/wiki/International_Bank_Account_Number'})
    
    # Write file
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(entry, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"Created: {rel_path}")
    return True

def main():
    rules_dir = Path(__file__).parent.parent.parent / 'metacrafter-rules' / 'rules'
    registry_dir = Path(__file__).parent.parent
    registry_jsonl = registry_dir / 'data' / 'datatypes_latest.jsonl'
    registry_yaml = registry_dir / 'data' / 'datatypes'
    
    print("Loading rules metadata...")
    metadata = load_rules_metadata(rules_dir)
    
    print("Loading existing registry IDs...")
    existing_ids = set()
    # Load from JSONL
    if registry_jsonl.exists():
        with open(registry_jsonl, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if 'id' in data:
                            existing_ids.add(data['id'])
                    except:
                        pass
    # Load from YAML
    if registry_yaml.exists():
        for yaml_file in registry_yaml.rglob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and isinstance(data, dict) and 'id' in data:
                        existing_ids.add(data['id'])
            except:
                pass
    
    print(f"Found {len(existing_ids)} existing entries")
    print(f"Found {len(metadata)} rule keys")
    
    missing = set(metadata.keys()) - existing_ids
    print(f"\nCreating {len(missing)} missing entries...\n")
    
    created = 0
    for key in sorted(missing):
        if create_entry(registry_dir, key, metadata[key], existing_ids):
            created += 1
            existing_ids.add(key)
    
    print(f"\nCreated {created} new entries")

if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""
Generate missing registry entries from rules analysis.
Reads the missing keys and creates YAML files for them.

Every generated record has status: draft and contains only facts taken from the
rules (name, context, country, language, PII flag). Review and complete it, then
run `metacrafter-registry validate`.
"""

import os
import sys
import yaml
import json
from pathlib import Path
import subprocess

# Import the check script functionality
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'metacrafter-rules' / 'scripts'))
from check_missing_registry import load_all_rule_keys, load_registry_datatypes

# Mapping of rule keys to metadata (country, category, etc.)
# This will be populated from rules
def get_rule_metadata(rules_dir):
    """Extract metadata from rules to help create registry entries."""
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
                                'country_code': country_code,
                                'lang': lang,
                                'context': context,
                                'name': rule_data.get('name', ''),
                                'is_pii': rule_data.get('is_pii', False),
                                'files': []
                            }
                        metadata[key]['files'].append(str(yaml_file))
        except Exception as e:
            print(f"Error processing {yaml_file}: {e}", file=sys.stderr)
    
    return metadata

def determine_category(context, key):
    """Determine category from context and key."""
    category_map = {
        'pii': ['pii', 'persons'],
        'persons': ['persons'],
        'finances': ['finance'],
        'geo': ['geo'],
        'transport': ['transport'],
        'realestate': ['realestate'],
        'ecommerce': ['ecommerce'],
        'shipping': ['shipping'],
        'media': ['media'],
        'legal': ['legal'],
        'common': ['common'],
    }
    
    # Special cases
    if 'driver' in key or 'passport' in key or 'ssn' in key or 'idcard' in key or 'nationalid' in key:
        return ['pii', 'persons']
    if 'bank' in key or 'iban' in key or 'tax' in key or 'tin' in key:
        return ['finance']
    if 'city' in key or 'postcode' in key or 'postal' in key or 'province' in key or 'state' in key or 'district' in key:
        return ['geo']
    if 'vehicle' in key or 'plate' in key:
        return ['transport']
    if 'property' in key or 'parcel' in key or 'cadastral' in key or 'building' in key:
        return ['realestate']
    if 'order' in key or 'cart' in key or 'sku' in key or 'transaction' in key:
        return ['ecommerce']
    if 'tracking' in key or 'container' in key or 'awb' in key:
        return ['shipping']
    if 'isbn' in key or 'issn' in key or 'isrc' in key or 'ean' in key or 'video' in key:
        return ['media']
    if 'case' in key or 'contract' in key or 'license' in key or 'legal' in key:
        return ['legal']
    if 'firstname' in key or 'lastname' in key or 'person_name' in key:
        return ['persons']
    if 'user' in key:
        return ['useraccounts']
    if 'date' in key or 'day' in key:
        return ['datetime']
    
    return category_map.get(context, ['common'])

def determine_directory(key, country_code, category):
    """Determine the directory path for a datatype."""
    if country_code and country_code != 'XX':
        # Country-specific
        cat_dir = {
            'persons': 'persons',
            'pii': 'persons',
            'finance': 'finances',
            'geo': 'geo',
            'transport': 'transport',
            'realestate': 'realestate',
            'ecommerce': 'ecommerce',
            'shipping': 'shipping',
            'media': 'media',
            'legal': 'legal',
            'useraccounts': 'useraccounts',
            'datetime': 'datetime',
        }.get(category[0] if category else 'common', 'common')
        return f"{country_code}/{cat_dir}"
    else:
        # Common/any
        cat_dir = {
            'persons': 'persons',
            'pii': 'pii',
            'finance': 'finances',
            'geo': 'geo',
            'transport': 'transport',
            'realestate': 'realestate',
            'ecommerce': 'ecommerce',
            'shipping': 'shipping',
            'media': 'media',
            'legal': 'legal',
            'useraccounts': 'useraccounts',
            'datetime': 'datetime',
        }.get(category[0] if category else 'common', 'common')
        return f"any/{cat_dir}"

def create_datatype_entry(base_path, key, metadata, existing_ids):
    """Create a YAML file for a missing datatype."""
    if key in existing_ids:
        return False  # Already exists
    
    country_code = metadata.get('country_code', 'XX')
    lang = metadata.get('lang', 'en')
    context = metadata.get('context', 'common')
    is_pii = metadata.get('is_pii', False)
    name = metadata.get('name', key.replace('_', ' ').title())
    
    # Determine category
    category = determine_category(context, key)
    
    # Determine directory
    if country_code == 'XX':
        country_code = None
    
    if country_code:
        dir_path = determine_directory(key, country_code, category)
        country_list = [country_code.upper()]  # ISO 3166-1 alpha-2, uppercase
    else:
        dir_path = determine_directory(key, None, category)
        country_list = []
    
    file_path = base_path / 'data' / 'datatypes' / dir_path / f"{key}.yaml"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create the datatype entry (v2 record contract, see schema/datatype.schema.json).
    # Only facts known from the rules are written: no invented regexps, examples or
    # links. Generated records are always drafts until a human reviews them.
    entry = {
        'id': key,
        'name': name,
        'status': 'draft',
        'doc': f"{name}. Generated from the metacrafter-rules key '{key}' (context '{context}'); "
               "needs a reviewed description.",
    }
    if category:
        entry['categories'] = category
    if country_list:
        entry['country'] = country_list
    entry['langs'] = [lang] if lang != 'common' else ['common']
    entry['is_pii'] = bool(is_pii) and str(is_pii) != 'False'
    entry['classification'] = 'identifier'

    sys.path.insert(0, str(base_path / 'src'))
    from metacrafter_registry.migrate import dump_yaml

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(dump_yaml(entry))

    print(f"Created: {file_path}")
    return True

def main():
    rules_dir = Path(__file__).parent.parent.parent / 'metacrafter-rules' / 'rules'
    registry_dir = Path(__file__).parent.parent
    registry_jsonl = registry_dir / 'data' / 'datatypes_latest.jsonl'
    registry_yaml = registry_dir / 'data' / 'datatypes'
    
    print("Loading rules and registry...")
    rule_keys, rule_files = load_all_rule_keys(rules_dir)
    registry_ids = load_registry_datatypes(registry_jsonl, registry_yaml)
    metadata = get_rule_metadata(rules_dir)
    
    missing_keys = rule_keys - registry_ids
    print(f"\nFound {len(missing_keys)} missing keys")
    print("Generating entries...\n")
    
    created = 0
    for key in sorted(missing_keys):
        if key in metadata:
            if create_datatype_entry(registry_dir, key, metadata[key], registry_ids):
                created += 1
                registry_ids.add(key)  # Avoid duplicates
        else:
            print(f"Warning: No metadata for {key}, skipping")
    
    print(f"\nCreated {created} new datatype entries")

if __name__ == '__main__':
    main()


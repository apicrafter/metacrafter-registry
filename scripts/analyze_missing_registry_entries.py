#!/usr/bin/env python3
"""
Analyze all rules in metacrafter-rules and identify missing registry entries.
Generate a detailed report and optionally create registry YAML files.
"""

import os
import sys
import yaml
import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional, Any

# Paths
SCRIPT_DIR = Path(__file__).parent
REGISTRY_DIR = SCRIPT_DIR.parent
RULES_DIR = REGISTRY_DIR.parent / "metacrafter-rules" / "rules"
REGISTRY_DATATYPES_DIR = REGISTRY_DIR / "data" / "datatypes"
REGISTRY_JSONL = REGISTRY_DIR / "data" / "datatypes_latest.jsonl"
SCHEMA_FILE = REGISTRY_DIR / "data" / "schemes" / "datatype.json"


def load_rule_file(file_path: Path) -> Dict:
    """Load a rule YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}", file=sys.stderr)
        return {}


def load_datatype_file(file_path: Path) -> Dict:
    """Load a datatype YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}", file=sys.stderr)
        return {}


def get_all_rule_keys(rules_dir: Path = None) -> Tuple[Dict[str, Dict], Set[str]]:
    """
    Extract all unique keys from rule files with their metadata.
    Returns: (metadata_dict, keys_set)
    """
    if rules_dir is None:
        rules_dir = RULES_DIR
    
    metadata = {}
    keys = set()
    
    if not rules_dir.exists():
        print(f"Warning: Rules directory not found: {rules_dir}", file=sys.stderr)
        return metadata, keys
    
    for yaml_file in rules_dir.rglob("*.yaml"):
        if yaml_file.name.endswith('.yaml_'):
            continue
        
        rule_data = load_rule_file(yaml_file)
        if not rule_data or 'rules' not in rule_data:
            continue
        
        # Extract file-level metadata
        country_code = rule_data.get('country_code', 'xx').upper()
        lang = rule_data.get('lang', 'en')
        context = rule_data.get('context', 'common')
        
        # Determine country from file path if not in metadata
        file_path_parts = yaml_file.relative_to(rules_dir).parts
        if len(file_path_parts) > 0:
            first_part = file_path_parts[0].upper()
            # Check if it's a country code (2 letters)
            if len(first_part) == 2 and first_part.isalpha() and country_code == 'XX':
                country_code = first_part
        
        # Extract rule-level metadata
        for rule_name, rule_def in rule_data.get('rules', {}).items():
            if not isinstance(rule_def, dict) or 'key' not in rule_def:
                continue
            
            key = rule_def['key']
            keys.add(key)
            
            # Collect metadata for this key
            if key not in metadata:
                metadata[key] = {
                    'key': key,
                    'name': rule_def.get('name', key.replace('_', ' ').title()),
                    'is_pii': rule_def.get('is_pii', False),
                    'country_codes': set(),
                    'langs': set(),
                    'contexts': set(),
                    'rule_files': [],
                    'match_types': set(),
                    'rule_patterns': []
                }
            
            # Aggregate metadata
            meta = metadata[key]
            if country_code and country_code != 'XX':
                meta['country_codes'].add(country_code)
            if lang:
                meta['langs'].add(lang)
            if context:
                meta['contexts'].add(context)
            
            meta['rule_files'].append(str(yaml_file.relative_to(RULES_DIR)))
            if 'match' in rule_def:
                meta['match_types'].add(rule_def['match'])
            if 'rule' in rule_def:
                meta['rule_patterns'].append(rule_def['rule'])
    
    # Convert sets to lists for JSON serialization
    for key in metadata:
        meta = metadata[key]
        meta['country_codes'] = sorted(list(meta['country_codes']))
        meta['langs'] = sorted(list(meta['langs']))
        meta['contexts'] = sorted(list(meta['contexts']))
        meta['match_types'] = sorted(list(meta['match_types']))
    
    return metadata, keys


def get_all_registry_ids(registry_jsonl: Path = None, registry_datatypes_dir: Path = None) -> Set[str]:
    """Get all existing datatype IDs from registry."""
    if registry_jsonl is None:
        registry_jsonl = REGISTRY_JSONL
    if registry_datatypes_dir is None:
        registry_datatypes_dir = REGISTRY_DATATYPES_DIR
    
    registry_ids = set()
    
    # Load from JSONL if available
    if registry_jsonl.exists():
        try:
            with open(registry_jsonl, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if 'id' in data:
                                registry_ids.add(data['id'])
                        except:
                            pass
        except Exception as e:
            print(f"Error reading JSONL: {e}", file=sys.stderr)
    
    # Load from YAML files
    if registry_datatypes_dir.exists():
        for yaml_file in registry_datatypes_dir.rglob("*.yaml"):
            try:
                data = load_datatype_file(yaml_file)
                if data and isinstance(data, dict) and 'id' in data:
                    registry_ids.add(data['id'])
            except:
                pass
    
    return registry_ids


def map_context_to_category(context: str, key: str) -> Tuple[List[str], str]:
    """
    Map rule context to registry category and directory.
    Returns: (categories_list, subdirectory_name)
    """
    # Context to category mapping
    context_map = {
        'identifiers': ('identifiers', 'identifiers'),
        'geo': ('geo', 'geo'),
        'finance': ('finances', 'finances'),
        'finances': ('finances', 'finances'),
        'pii': ('pii', 'pii'),
        'software': ('software', 'software'),
        'transport': ('transport', 'transport'),
        'objects': ('objectids', 'objectids'),
        'objectids': ('objectids', 'objectids'),
        'persons': ('persons', 'persons'),
        'companies': ('companies', 'companies'),
        'legal': ('legal', 'legal'),
        'media': ('media', 'media'),
        'ecommerce': ('ecommerce', 'ecommerce'),
        'shipping': ('shipping', 'shipping'),
        'realestate': ('realestate', 'realestate'),
        'datetime': ('datetime', 'datetime'),
        'medical': ('medical', 'medical'),
        'science': ('science', 'science'),
        'useraccounts': ('useraccounts', 'useraccounts'),
        'values': ('values', 'values'),
        'texts': ('texts', 'texts'),
        'telecom': ('telecom', 'telecom'),
        'chemistry': ('chemistry', 'chemistry'),
        'environment': ('environment', 'environment'),
        'education': ('education', 'education'),
        'government': ('government', 'government'),
        'industry': ('industry', 'industry'),
        'gs1': ('gs1', 'gs1'),
        'cryptocurrency': ('cryptocurrency', 'cryptocurrency'),
        'cryptography': ('cryptography', 'cryptography'),
        'dublincore': ('dublincore', 'dublincore'),
        'common': ('common', 'common'),
    }
    
    # Try context mapping first
    if context in context_map:
        cat, subdir = context_map[context]
        return [cat], subdir
    
    # Fallback: infer from key name patterns
    key_lower = key.lower()
    
    if any(x in key_lower for x in ['driver', 'passport', 'ssn', 'idcard', 'nationalid', 'rrn', 
                                    'pesel', 'cccd', 'tckimlik', 'iqama', 'emiratesid', 'ahv', 
                                    'mynumber', 'aadhaar', 'pan', 'medicare', 'nik', 'curp']):
        return ['pii', 'persons'], 'persons'
    elif any(x in key_lower for x in ['bank', 'iban', 'tax', 'tin', 'npwp', 'businessreg', 'uid', 
                                      'orgnumber', 'abn', 'bsb', 'tfn', 'acra', 'nric', 'cnpj', 
                                      'cpf', 'cuit', 'rfc', 'ein', 'siret']):
        return ['finances'], 'finances'
    elif any(x in key_lower for x in ['city', 'postcode', 'postal', 'province', 'state', 'district', 
                                      'prefecture', 'fias', 'latitude', 'longitude', 'address', 
                                      'geopoint', 'country']):
        return ['geo'], 'geo'
    elif any(x in key_lower for x in ['vehicle', 'plate', 'imo', 'mmsi', 'iata', 'icao']):
        return ['transport'], 'transport'
    elif any(x in key_lower for x in ['property', 'parcel', 'cadastral', 'building', 'apn', 'uprn']):
        return ['realestate'], 'realestate'
    elif any(x in key_lower for x in ['order', 'cart', 'sku', 'transaction', 'amazon', 'alibaba', 'jd']):
        return ['ecommerce'], 'ecommerce'
    elif any(x in key_lower for x in ['tracking', 'container', 'awb', 'dhl', 'fedex', 'ups', 'usps']):
        return ['shipping'], 'shipping'
    elif any(x in key_lower for x in ['isbn', 'issn', 'isrc', 'ean', 'video', 'youtube', 'vimeo']):
        return ['media'], 'media'
    elif any(x in key_lower for x in ['case', 'contract', 'license', 'legal', 'compliance']):
        return ['legal'], 'legal'
    elif any(x in key_lower for x in ['firstname', 'lastname', 'person_name', 'surname', 'midname']):
        return ['persons'], 'persons'
    elif 'user' in key_lower:
        return ['useraccounts'], 'useraccounts'
    elif any(x in key_lower for x in ['date', 'day', 'time', 'month', 'year', 'birthday', 'age']):
        return ['datetime'], 'datetime'
    elif any(x in key_lower for x in ['hash', 'md5', 'sha', 'crc', 'imphash', 'authentihash']):
        return ['cryptography'], 'cryptography'
    elif any(x in key_lower for x in ['bitcoin', 'ethereum', 'wallet', 'address', 'crypto']):
        return ['cryptocurrency'], 'cryptocurrency'
    elif any(x in key_lower for x in ['email', 'url', 'domain', 'ip', 'mac', 'uri']):
        return ['internet'], 'internet'
    elif any(x in key_lower for x in ['uuid', 'guid', 'mongodbid', 'ulid', 'snowflake']):
        return ['identifiers'], 'identifiers'
    else:
        return ['common'], 'common'


def infer_regexp(key: str, rule_patterns: List[str], match_types: Set[str]) -> Optional[str]:
    """Infer regexp pattern from key name and rule patterns."""
    key_lower = key.lower()
    
    # Common patterns based on key name
    if 'iban' in key_lower:
        if key_lower.startswith('ae'):
            return '^AE[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
        elif key_lower.startswith('ch'):
            return '^CH[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
        elif key_lower.startswith('eg'):
            return '^EG[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
        elif key_lower.startswith('pl'):
            return '^PL[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
        elif key_lower.startswith('tr'):
            return '^TR[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
        elif key_lower.startswith('vn'):
            return '^VN[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
        elif key_lower.startswith('sa'):
            return '^SA[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
        else:
            return '^[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{16,24}$'
    elif 'passport' in key_lower:
        return '^[A-Z0-9]{6,10}$'
    elif 'driver' in key_lower or ('license' in key_lower and 'driver' in key_lower):
        return '^[A-Z0-9]{6,12}$'
    elif 'ssn' in key_lower or 'nationalid' in key_lower or 'idcard' in key_lower:
        if 'rrn' in key_lower:
            return '^[0-9]{6}-[0-9]{7}$'
        elif 'nik' in key_lower:
            return '^[0-9]{16}$'
        else:
            return '^[0-9]{8,15}$'
    elif 'postcode' in key_lower or 'postal' in key_lower:
        return '^[0-9]{4,10}$'
    elif 'tax' in key_lower or 'tin' in key_lower:
        if 'npwp' in key_lower:
            return '^[0-9]{2}\\.[0-9]{3}\\.[0-9]{3}\\.[0-9]{1}-[0-9]{3}\\.[0-9]{3}$'
        else:
            return '^[0-9]{9,15}$'
    elif 'bank' in key_lower and 'iban' not in key_lower:
        return '^[0-9]{8,20}$'
    elif 'uuid' in key_lower:
        return '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    elif 'guid' in key_lower:
        return '^\\{[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\\}$'
    elif 'email' in key_lower:
        return '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    elif 'mac' in key_lower and 'address' in key_lower:
        return '^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    elif 'isbn' in key_lower:
        return '^(978|979)[0-9]{10}$'
    elif 'issn' in key_lower:
        return '^[0-9]{4}-[0-9]{4}$'
    
    return None


def determine_registry_path(key: str, country_codes: List[str], category: str, subdir: str, 
                            registry_datatypes_dir: Path = None) -> Path:
    """Determine the registry file path for a datatype."""
    if registry_datatypes_dir is None:
        registry_datatypes_dir = REGISTRY_DATATYPES_DIR
    
    if country_codes:
        # Use first country code (most common)
        country_code = country_codes[0]
        return registry_datatypes_dir / country_code / subdir / f"{key}.yaml"
    else:
        return registry_datatypes_dir / "any" / subdir / f"{key}.yaml"


def generate_doc(key: str, name: str, category: str) -> str:
    """Generate documentation string for a datatype."""
    # Try to create a meaningful description
    if 'identifier' in name.lower() or 'id' in key.lower():
        return f"{name} identifier"
    elif 'code' in name.lower():
        return f"{name} code"
    elif 'number' in name.lower():
        return f"{name} number"
    else:
        return f"{name}"


def validate_entry(entry: Dict) -> Tuple[bool, List[str]]:
    """
    Validate a registry entry against the schema.
    Returns: (is_valid, list_of_errors)
    """
    try:
        from cerberus import Validator
    except ImportError:
        # If cerberus is not available, do basic validation
        errors = []
        if 'id' not in entry:
            errors.append("Missing required field: id")
        if 'name' not in entry:
            errors.append("Missing required field: name")
        if 'doc' not in entry:
            errors.append("Missing required field: doc")
        if 'langs' not in entry:
            errors.append("Missing required field: langs")
        elif not isinstance(entry['langs'], list) or len(entry['langs']) == 0:
            errors.append("langs must be a non-empty list")
        return len(errors) == 0, errors
    
    # Load schema
    if not SCHEMA_FILE.exists():
        return True, []  # Skip validation if schema not found
    
    try:
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except Exception as e:
        print(f"Warning: Could not load schema: {e}", file=sys.stderr)
        return True, []  # Skip validation if schema can't be loaded
    
    # Validate
    validator = Validator(schema)
    is_valid = validator.validate(entry)
    
    if is_valid:
        return True, []
    else:
        return False, [str(validator.errors)]


def check_duplicate_id(key: str, registry_path: Path, existing_ids: Set[str]) -> Tuple[bool, str]:
    """
    Check if an ID already exists in the registry.
    Returns: (is_duplicate, error_message)
    """
    if key in existing_ids:
        return True, f"ID '{key}' already exists in registry"
    
    # Also check if file already exists
    if registry_path.exists():
        try:
            existing_data = load_datatype_file(registry_path)
            if existing_data and existing_data.get('id') == key:
                return True, f"File {registry_path} already contains ID '{key}'"
        except:
            pass
    
    return False, ""


def create_registry_entry(key: str, metadata: Dict, category: List[str], subdir: str, 
                         registry_path: Path, existing_ids: Set[str], 
                         validate: bool = True) -> Tuple[bool, List[str]]:
    """
    Create a registry YAML file for a missing entry.
    Returns: (success, list_of_errors_or_warnings)
    """
    errors = []
    
    # Check for duplicates
    is_duplicate, dup_error = check_duplicate_id(key, registry_path, existing_ids)
    if is_duplicate:
        return False, [dup_error]
    
    # Determine country and language
    country_codes = metadata.get('country_codes', [])
    langs = metadata.get('langs', ['en'])
    
    # Normalize language codes
    normalized_langs = []
    for lang in langs:
        if lang == 'common':
            normalized_langs.append('en')
        else:
            normalized_langs.append(lang.lower())
    
    if not normalized_langs:
        normalized_langs = ['en']
    
    # Create entry
    entry = {
        'id': key,
        'name': metadata.get('name', key.replace('_', ' ').title()),
        'doc': generate_doc(key, metadata.get('name', key.replace('_', ' ').title()), category[0] if category else 'common'),
        'langs': normalized_langs,
    }
    
    # Add optional fields
    if category:
        entry['categories'] = category
    
    if country_codes:
        entry['country'] = country_codes
    
    if metadata.get('is_pii', False):
        entry['is_pii'] = 'True'
    else:
        entry['is_pii'] = 'False'
    
    # Infer regexp
    regexp = infer_regexp(key, metadata.get('rule_patterns', []), 
                          set(metadata.get('match_types', [])))
    if regexp:
        entry['regexp'] = regexp
    
    # Add classification
    entry['classification'] = 'identifier'
    
    # Initialize empty optional fields
    entry['translations'] = {}
    entry['examples'] = []
    entry['links'] = []
    
    # Validate entry
    if validate:
        is_valid, validation_errors = validate_entry(entry)
        if not is_valid:
            errors.extend(validation_errors)
            return False, errors
    
    # Create directory if needed
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write file
    try:
        with open(registry_path, 'w', encoding='utf-8') as f:
            yaml.dump(entry, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True, []
    except Exception as e:
        return False, [f"Error creating {registry_path}: {e}"]


def generate_report(rule_metadata: Dict[str, Dict], rule_keys: Set[str], 
                   registry_ids: Set[str], create_files: bool = False, 
                   validate: bool = True, registry_datatypes_dir: Path = None) -> None:
    """Generate detailed report of missing registry entries."""
    if registry_datatypes_dir is None:
        registry_datatypes_dir = REGISTRY_DATATYPES_DIR
    
    missing_keys = rule_keys - registry_ids
    existing_keys = rule_keys & registry_ids
    
    print("=" * 80)
    print("RULES TO REGISTRY ANALYSIS REPORT")
    print("=" * 80)
    print()
    
    print(f"Total unique rule keys found: {len(rule_keys)}")
    print(f"Existing registry entries: {len(existing_keys)}")
    print(f"Missing registry entries: {len(missing_keys)}")
    print()
    
    if not missing_keys:
        print("✓ All rule keys have corresponding registry entries!")
        return
    
    # Group missing entries by category/country
    grouped = defaultdict(lambda: defaultdict(list))
    
    for key in missing_keys:
        if key not in rule_metadata:
            continue
        
        meta = rule_metadata[key]
        contexts = meta.get('contexts', ['common'])
        country_codes = meta.get('country_codes', [])
        
        # Determine category
        primary_context = contexts[0] if contexts else 'common'
        categories, subdir = map_context_to_category(primary_context, key)
        category = categories[0] if categories else 'common'
        
        # Group by country (or 'any' if no country)
        country_key = country_codes[0] if country_codes else 'any'
        
        grouped[category][country_key].append({
            'key': key,
            'name': meta.get('name', key),
            'contexts': contexts,
            'country_codes': country_codes,
            'langs': meta.get('langs', ['en']),
            'is_pii': meta.get('is_pii', False),
            'subdir': subdir
        })
    
    # Print grouped report
    print("=" * 80)
    print("MISSING REGISTRY ENTRIES BY CATEGORY")
    print("=" * 80)
    print()
    
    total_to_create = 0
    created_count = 0
    
    for category in sorted(grouped.keys()):
        category_group = grouped[category]
        category_total = sum(len(entries) for entries in category_group.values())
        total_to_create += category_total
        
        print(f"\n{category.upper()} ({category_total} missing)")
        print("-" * 80)
        
        for country in sorted(category_group.keys()):
            entries = category_group[country]
            print(f"\n  {country.upper()}: {len(entries)} entries")
            
            for entry in entries[:10]:  # Show first 10
                key = entry['key']
                name = entry['name']
                subdir = entry['subdir']
                
                # Determine path
                country_codes = entry['country_codes']
                if country_codes:
                    rel_path = f"{country_codes[0]}/{subdir}/{key}.yaml"
                else:
                    rel_path = f"any/{subdir}/{key}.yaml"
                
                print(f"    - {key}: {name}")
                print(f"      Path: data/datatypes/{rel_path}")
                print(f"      Contexts: {', '.join(entry['contexts'])}")
                print(f"      Languages: {', '.join(entry['langs'])}")
                if entry['is_pii']:
                    print(f"      PII: True")
                
                # Create file if requested
                if create_files:
                    registry_path = registry_datatypes_dir / rel_path
                    success, errors = create_registry_entry(
                        key, rule_metadata[key], 
                        map_context_to_category(entry['contexts'][0] if entry['contexts'] else 'common', key)[0],
                        subdir, registry_path, registry_ids, validate=validate
                    )
                    if success:
                        created_count += 1
                        registry_ids.add(key)  # Update set to avoid duplicates
                        print(f"      ✓ Created: {rel_path}")
                    else:
                        print(f"      ✗ Failed: {rel_path}")
                        for error in errors:
                            print(f"        Error: {error}")
            
            if len(entries) > 10:
                print(f"    ... and {len(entries) - 10} more")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total missing entries: {total_to_create}")
    if create_files:
        print(f"Entries created: {created_count}")
        print(f"Entries skipped (already exist or errors): {total_to_create - created_count}")
    else:
        print(f"\nTo create these entries, run with --create flag")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze rules and identify missing registry entries'
    )
    parser.add_argument(
        '--create',
        action='store_true',
        help='Create registry YAML files for missing entries'
    )
    parser.add_argument(
        '--rules-dir',
        type=Path,
        default=RULES_DIR,
        help='Path to metacrafter-rules/rules directory'
    )
    parser.add_argument(
        '--registry-dir',
        type=Path,
        default=REGISTRY_DATATYPES_DIR,
        help='Path to registry datatypes directory'
    )
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip schema validation when creating entries'
    )
    
    args = parser.parse_args()
    
    print("Loading rules...")
    rule_metadata, rule_keys = get_all_rule_keys(rules_dir=args.rules_dir)
    print(f"Found {len(rule_keys)} unique rule keys")
    
    print("Loading registry entries...")
    # Determine JSONL path based on registry dir
    if args.registry_dir == REGISTRY_DATATYPES_DIR:
        registry_jsonl_path = REGISTRY_JSONL
    else:
        # Try to find JSONL in the same parent directory
        registry_jsonl_path = args.registry_dir.parent / "datatypes_latest.jsonl"
        if not registry_jsonl_path.exists():
            registry_jsonl_path = None
    
    registry_ids = get_all_registry_ids(
        registry_jsonl=registry_jsonl_path,
        registry_datatypes_dir=args.registry_dir
    )
    print(f"Found {len(registry_ids)} existing registry entries")
    
    print("\nAnalyzing...")
    generate_report(rule_metadata, rule_keys, registry_ids, 
                   create_files=args.create, validate=not args.no_validate,
                   registry_datatypes_dir=args.registry_dir)
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()


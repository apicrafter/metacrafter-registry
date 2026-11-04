#!/usr/bin/env python3
"""
Script to analyze datatypes in metacrafter-registry and identify missing rules in metacrafter-rules.
"""

import os
import yaml
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Paths
REGISTRY_DATATYPES_DIR = Path(__file__).parent.parent / "data" / "datatypes"
RULES_DIR = Path(__file__).parent.parent.parent / "metacrafter-rules" / "rules"


def load_datatype(file_path: Path) -> Dict:
    """Load a datatype YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}


def load_rule_file(file_path: Path) -> Dict:
    """Load a rule YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}


def get_all_datatypes() -> Dict[str, Dict]:
    """Get all datatypes from registry, organized by country/category."""
    datatypes = {}
    
    for country_dir in REGISTRY_DATATYPES_DIR.iterdir():
        if not country_dir.is_dir():
            continue
            
        country = country_dir.name
        
        # Handle nested structure (country/category/file.yaml)
        for category_dir in country_dir.iterdir():
            if not category_dir.is_dir():
                # Direct file in country directory
                if category_dir.suffix == '.yaml':
                    dt = load_datatype(category_dir)
                    if dt and 'id' in dt:
                        key = f"{country}/{category_dir.stem}"
                        datatypes[key] = dt
                continue
                
            category = category_dir.name
            for yaml_file in category_dir.glob("*.yaml"):
                dt = load_datatype(yaml_file)
                if dt and 'id' in dt:
                    key = f"{country}/{category}/{yaml_file.stem}"
                    datatypes[key] = dt
    
    return datatypes


def get_all_rules() -> Dict[str, Set[str]]:
    """Get all rule keys from rules directory, organized by country/language."""
    rules_by_key = defaultdict(set)
    
    for rule_file in RULES_DIR.rglob("*.yaml"):
        if rule_file.name.startswith('.'):
            continue
            
        rule_data = load_rule_file(rule_file)
        if not rule_data or 'rules' not in rule_data:
            continue
            
        # Determine country/lang from path
        parts = rule_file.relative_to(RULES_DIR).parts
        country = parts[0] if parts else "unknown"
        
        # Extract all keys from rules
        for rule_id, rule_def in rule_data.get('rules', {}).items():
            if 'key' in rule_def:
                key = rule_def['key']
                rules_by_key[key].add(str(rule_file.relative_to(RULES_DIR)))
    
    return rules_by_key


def analyze_missing_rules():
    """Analyze datatypes and identify missing rules."""
    print("Loading datatypes from registry...")
    datatypes = get_all_datatypes()
    print(f"Found {len(datatypes)} datatypes")
    
    print("\nLoading rules from rules directory...")
    rules_by_key = get_all_rules()
    print(f"Found {len(rules_by_key)} unique datatype keys in rules")
    
    # Organize datatypes by country and category
    by_country = defaultdict(lambda: defaultdict(list))
    missing_rules = defaultdict(lambda: defaultdict(list))
    
    for path, dt in datatypes.items():
        dt_id = dt.get('id', '')
        countries = dt.get('country', [])
        categories = dt.get('categories', [])
        langs = dt.get('langs', [])
        regexp = dt.get('regexp', '')
        is_pii = dt.get('is_pii', 'False') == 'True'
        
        # Check if rule exists
        has_rule = dt_id in rules_by_key
        
        for country in countries:
            for category in categories:
                by_country[country][category].append({
                    'id': dt_id,
                    'name': dt.get('name', ''),
                    'path': path,
                    'has_rule': has_rule,
                    'langs': langs,
                    'regexp': regexp,
                    'is_pii': is_pii,
                    'rule_files': list(rules_by_key.get(dt_id, []))
                })
                
                if not has_rule:
                    missing_rules[country][category].append({
                        'id': dt_id,
                        'name': dt.get('name', ''),
                        'path': path,
                        'langs': langs,
                        'regexp': regexp,
                        'is_pii': is_pii
                    })
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    total_with_rules = sum(1 for dt in datatypes.values() 
                          if dt.get('id', '') in rules_by_key)
    total_missing = len(datatypes) - total_with_rules
    
    print(f"\nTotal datatypes: {len(datatypes)}")
    print(f"Datatypes with rules: {total_with_rules}")
    print(f"Datatypes missing rules: {total_missing}")
    
    # Print missing rules by country
    print("\n" + "="*80)
    print("MISSING RULES BY COUNTRY")
    print("="*80)
    
    for country in sorted(missing_rules.keys()):
        country_missing = missing_rules[country]
        total_country_missing = sum(len(cat_list) for cat_list in country_missing.values())
        if total_country_missing == 0:
            continue
            
        print(f"\n{country}: {total_country_missing} missing rules")
        for category in sorted(country_missing.keys()):
            cat_list = country_missing[category]
            if cat_list:
                print(f"  {category}: {len(cat_list)} missing")
                for dt in cat_list[:5]:  # Show first 5
                    print(f"    - {dt['id']}: {dt['name']}")
                if len(cat_list) > 5:
                    print(f"    ... and {len(cat_list) - 5} more")
    
    # Generate suggestions
    print("\n" + "="*80)
    print("SUGGESTED RULES TO CREATE")
    print("="*80)
    
    suggestions = []
    
    for country in sorted(missing_rules.keys()):
        country_missing = missing_rules[country]
        for category in sorted(country_missing.keys()):
            cat_list = country_missing[category]
            if not cat_list:
                continue
                
            # Group by language
            by_lang = defaultdict(list)
            for dt in cat_list:
                for lang in dt.get('langs', ['en']):
                    by_lang[lang].append(dt)
            
            for lang, dt_list in by_lang.items():
                suggestions.append({
                    'country': country,
                    'category': category,
                    'lang': lang,
                    'datatypes': dt_list
                })
    
    # Print suggestions
    for sug in suggestions:
        country = sug['country']
        category = sug['category']
        lang = sug['lang']
        dt_list = sug['datatypes']
        
        print(f"\n{country}/{category} ({lang}): {len(dt_list)} rules needed")
        print(f"  Suggested file: rules/{country}/{country}_{category}.yaml")
        print(f"  Context: {category}")
        print(f"  Language: {lang}")
        print(f"  Country code: {country.lower()}")
        print(f"  Rules to add:")
        
        for dt in dt_list[:10]:  # Show first 10
            dt_id = dt['id']
            dt_name = dt['name']
            regexp = dt.get('regexp', '')
            is_pii = dt.get('is_pii', False)
            
            print(f"    - {dt_id}: {dt_name}")
            if regexp:
                print(f"      Pattern: {regexp}")
            if is_pii:
                print(f"      PII: True")
        
        if len(dt_list) > 10:
            print(f"    ... and {len(dt_list) - 10} more")
    
    return missing_rules, suggestions


if __name__ == "__main__":
    missing_rules, suggestions = analyze_missing_rules()
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


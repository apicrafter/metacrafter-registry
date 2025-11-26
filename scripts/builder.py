#!/usr/bin/env python
import yaml
import json
import logging
import argparse
from pprint import pprint
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '..', 'data')
FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def load_dict(filename):
    f = open(filename, 'r', encoding='utf8')
    data = yaml.load(f, Loader=Loader)
    f.close()
    out = {}
    for r in data:
        out[r['id']] = r['name']
    return out

def load_path(dirpath):
    subfolders = [f.path for f in os.scandir(dirpath) if f.is_dir()]
    all = []
    for root, dirs, files in os.walk(dirpath, topdown=False):
        for filename in files:
            if filename.lower().rsplit('.', 1)[-1] != 'yaml': continue
            logging.info('Load %s' % (filename))
            f = open(os.path.join(root, filename), 'r', encoding='utf8')
            all.append(yaml.load(f, Loader=Loader))
            f.close()
    return all

def load_json(filepath):
    f = open(filepath, 'r', encoding='utf8')
    data = json.load(f)
    f.close()
    return data


def update_by_dict(arr, adict):
    aindex = []

    for c in arr:
        name = adict.get(c)
        if name is None:
            logging.warning("Unknown key '%s' in mapping, skipping", c)
            continue
        aindex.append({'id': c, 'name': name})
    return aindex



def datatypes_yaml_to_jsonl():
    output = {}
    countries = load_dict(os.path.join(DATA_PATH, 'countries.yaml'))
    categories = load_dict(os.path.join(DATA_PATH, 'categories.yaml'))
    langs = load_dict(os.path.join(DATA_PATH, 'langs.yaml'))

    fjsonl = open(os.path.join(DATA_PATH, 'datatypes_latest.jsonl'), 'w', encoding='utf8')
    f = open(os.path.join(DATA_PATH, 'datatypes_latest.json'), 'w', encoding='utf8')

    pindex = {}
    dindex = {}
    patterns = {}


    datatypes = load_path(os.path.join(DATA_PATH, 'datatypes'))
    print('Loaded %d datatypes and patterns' % (len(datatypes)))
    for d in datatypes:
        if 'semantic_type' in d.keys():
            plist = pindex.get(d['semantic_type'], [])
            plist.append(d['id'])
            pindex[d['semantic_type']] = plist
            patterns[d['id']] = d
        else:
            dindex[d['id']] = d

    finallist = []
    for d in datatypes:
        if 'semantic_type' in d.keys():
            d['type'] = 'pattern'
            d['is_pii'] = True if dindex[d['semantic_type']]['is_pii'] == 'True' else False
            if 'classification' not in d.keys():
                if 'classification' in dindex[d['semantic_type']].keys():
                    d['classification'] = dindex[d['semantic_type']]['classification']
        else:
            d['type'] = 'datatype'        
            d['is_pii'] = True if d['is_pii'] == 'True' else False
        if 'categories' in d.keys():
            d['categories'] = update_by_dict(d['categories'], categories)
        if 'country' in d.keys():
            d['country'] = update_by_dict(d['country'], countries)
        if 'langs' in d.keys():
            d['langs'] = update_by_dict(d['langs'], langs)
        output[d['id']] = d        
        if d['id'] in pindex.keys():
            d['patterns'] = [] 
            for pid in pindex[d['id']]:
                d['patterns'].append(patterns[pid])
        finallist.append(d)
        fjsonl.write(json.dumps(d, ensure_ascii=False) + '\n')

    f.write(json.dumps(output, ensure_ascii=False))
    f.close()
    fjsonl.close()

def tools_yaml_to_jsonl():
    output = {}

    fjsonl = open(os.path.join(DATA_PATH, 'tools_latest.jsonl'), 'w', encoding='utf8')
    f = open(os.path.join(DATA_PATH, 'tools_latest.json'), 'w', encoding='utf8')

    tools = load_path(os.path.join(DATA_PATH, 'tools'))
    print('Loaded %d tools' % (len(tools)))
    for d in tools:
        d['num'] = len(d['supported_types'])
        fjsonl.write(json.dumps(d, ensure_ascii=False) + '\n')
        output[d['id']] = d
    f.write(json.dumps(output, ensure_ascii=False))
    f.close()
    fjsonl.close()



def calculate_stats():
    json_file = os.path.join(DATA_PATH, 'datatypes_latest.json')
    if not os.path.exists(json_file):
        print('Error: datatypes_latest.json not found.')
        print('Please run "python scripts/builder.py build" first to generate the required files.')
        return
    try:
        data = load_json(json_file)
    except Exception as e:
        print('Error loading datatypes_latest.json: %s' % str(e))
        return
    print('')
    total_types = 0
    total_pat = 0
    has_regexp = 0
    has_wikidata = 0
    has_links = 0
    has_trans = 0
    has_exam = 0
    has_classif = 0
    by_country = {}
    by_lang = {}
    for d in data.values():
        if d['type'] == 'datatype':
            total_types += 1
        elif d['type'] == 'pattern': total_pat += 1
        if 'regexp' in d.keys():
            has_regexp += 1
        if 'wikidata_property' in d.keys():
            has_wikidata += 1
        if 'links' in d.keys():
            has_links += 1
        if 'translations' in d.keys():
            has_trans += 1
        if 'examples' in d.keys():
            has_exam += 1
        if 'classification' in d.keys():
            has_classif += 1
        if 'country' in d.keys():
            for country in d['country']:
                v = by_country.get(country['id'], 0)
                by_country[country['id']] = v + 1
        else:
            country = 'any'
            v = by_country.get(country, 0)
            by_country[country] = v + 1 
        if 'langs' in d.keys():
            for lang in d['langs']:
                v = by_lang.get(lang['id'], 0)
                by_lang[lang['id']] = v + 1
        else:
            lang = 'any'
            v = by_lang.get(lang, 0)
            by_lang[lang] = v + 1             
    total_all = total_types + total_pat
    print('Total data types %d' % (total_types))
    print('Total patterns %d' % (total_pat))
    print('Total registered types %d' % (total_all))
    print('- with link %0.2f%% (%d)' % (has_links * 100.0 / total_all, has_links))
    print('- with regexp %0.2f%% (%d)' % (has_regexp * 100.0 / total_all, has_regexp))
    print('- with wikidata url %0.2f%% (%d)' % (has_wikidata * 100.0 / total_all, has_wikidata))
    print('- with translations %0.2f%% (%d)' % (has_trans * 100.0 / total_all, has_trans))
    print('- with examples %0.2f%% (%d)' % (has_exam * 100.0 / total_all, has_exam))
    print('- with classification %0.2f%% (%d)' % (has_classif * 100.0 / total_all, has_classif))
    print('Stats by country')
    for w in sorted(by_country, key=by_country.get, reverse=True):
        print('- %s: %d' % (w, by_country[w]))
    print('Stats by language')
    for w in sorted(by_lang, key=by_lang.get, reverse=True):
        print('- %s: %d' % (w, by_lang[w]))


def report():
    data = load_json(os.path.join(DATA_PATH, 'datatypes_latest.json'))
    print('')
    print('=' * 80)
    print('COMPLETENESS REPORT FOR SEMANTIC DATA TYPES')
    print('=' * 80)
    print('')
    
    # Define important fields for completeness scoring
    # Core required fields (must be present)
    core_fields = ['id', 'name', 'doc', 'langs']
    # Important optional fields (should ideally be present)
    important_fields = ['categories', 'country', 'regexp', 'classification', 'is_pii']
    # Enhancement fields (nice to have)
    enhancement_fields = ['wikidata_property', 'links', 'translations', 'examples']
    
    all_fields = core_fields + important_fields + enhancement_fields
    
    # Statistics tracking
    datatypes = []
    patterns = []
    field_missing_count = {field: 0 for field in all_fields}
    field_empty_count = {field: 0 for field in ['wikidata_property', 'links', 'translations']}
    completeness_scores = []
    completeness_by_category = {}
    completeness_by_country = {}
    
    for d in data.values():
        item_type = d.get('type', 'unknown')
        item_id = d.get('id', 'unknown')
        item_name = d.get('name', 'unknown')
        
        # Check field presence and quality
        missing_fields = []
        empty_fields = []
        present_fields = []
        
        # Check core fields
        for field in core_fields:
            if field not in d or d[field] is None:
                missing_fields.append(field)
                field_missing_count[field] += 1
            else:
                present_fields.append(field)
        
        # Check important fields
        for field in important_fields:
            if field not in d or d[field] is None:
                missing_fields.append(field)
                field_missing_count[field] += 1
            else:
                present_fields.append(field)
        
        # Check enhancement fields with special handling for empty values
        for field in enhancement_fields:
            if field not in d or d[field] is None:
                missing_fields.append(field)
                field_missing_count[field] += 1
            else:
                # Check for empty values
                if field == 'wikidata_property' and d[field] == '':
                    empty_fields.append(field)
                    field_empty_count[field] += 1
                elif field == 'links' and (not isinstance(d[field], list) or len(d[field]) == 0):
                    empty_fields.append(field)
                    field_empty_count[field] += 1
                elif field == 'translations' and (not isinstance(d[field], dict) or len(d[field]) == 0):
                    empty_fields.append(field)
                    field_empty_count[field] += 1
                elif field == 'examples' and (not isinstance(d[field], list) or len(d[field]) == 0):
                    empty_fields.append(field)
                else:
                    present_fields.append(field)
        
        # Calculate completeness score
        # Weight: core=3, important=2, enhancement=1
        total_weight = len(core_fields) * 3 + len(important_fields) * 2 + len(enhancement_fields) * 1
        score = 0
        for field in core_fields:
            if field in present_fields:
                score += 3
        for field in important_fields:
            if field in present_fields:
                score += 2
        for field in enhancement_fields:
            if field in present_fields and field not in empty_fields:
                score += 1
        
        completeness_pct = (score / total_weight) * 100 if total_weight > 0 else 0
        completeness_scores.append(completeness_pct)
        
        item_info = {
            'id': item_id,
            'name': item_name,
            'type': item_type,
            'completeness': completeness_pct,
            'missing': missing_fields,
            'empty': empty_fields,
            'present': present_fields
        }
        
        if item_type == 'datatype':
            datatypes.append(item_info)
        elif item_type == 'pattern':
            patterns.append(item_info)
        
        # Track by category
        categories = d.get('categories', [])
        if isinstance(categories, list) and len(categories) > 0:
            for cat in categories:
                if isinstance(cat, dict):
                    cat_id = cat.get('id', 'unknown')
                else:
                    cat_id = str(cat)
                if cat_id not in completeness_by_category:
                    completeness_by_category[cat_id] = []
                completeness_by_category[cat_id].append(completeness_pct)
        else:
            if 'uncategorized' not in completeness_by_category:
                completeness_by_category['uncategorized'] = []
            completeness_by_category['uncategorized'].append(completeness_pct)
        
        # Track by country
        countries = d.get('country', [])
        if isinstance(countries, list) and len(countries) > 0:
            for country in countries:
                if isinstance(country, dict):
                    country_id = country.get('id', 'any')
                else:
                    country_id = str(country)
                if country_id not in completeness_by_country:
                    completeness_by_country[country_id] = []
                completeness_by_country[country_id].append(completeness_pct)
        else:
            if 'any' not in completeness_by_country:
                completeness_by_country['any'] = []
            completeness_by_country['any'].append(completeness_pct)
    
    # Print summary statistics
    total_items = len(datatypes) + len(patterns)
    avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
    
    print('SUMMARY STATISTICS')
    print('-' * 80)
    print('Total datatypes: %d' % len(datatypes))
    print('Total patterns: %d' % len(patterns))
    print('Total items: %d' % total_items)
    print('Average completeness: %.1f%%' % avg_completeness)
    print('')
    
    # Completeness distribution
    print('COMPLETENESS DISTRIBUTION')
    print('-' * 80)
    ranges = [
        (0, 25, '0-25%'),
        (25, 50, '25-50%'),
        (50, 75, '50-75%'),
        (75, 90, '75-90%'),
        (90, 100, '90-100%'),
        (100, 101, '100%')
    ]
    for min_val, max_val, label in ranges:
        count = sum(1 for score in completeness_scores if min_val <= score < max_val)
        pct = (count / total_items * 100) if total_items > 0 else 0
        bar = '#' * int(pct / 2)
        print('%s: %d items (%.1f%%) %s' % (label.ljust(8), count, pct, bar))
    print('')
    
    # Most commonly missing fields
    print('MOST COMMONLY MISSING FIELDS')
    print('-' * 80)
    sorted_fields = sorted(field_missing_count.items(), key=lambda x: x[1], reverse=True)
    for field, count in sorted_fields:
        if count > 0:
            pct = (count / total_items * 100) if total_items > 0 else 0
            print('  %s: %d missing (%.1f%%)' % (field.ljust(25), count, pct))
    
    # Empty fields (present but empty)
    print('')
    print('EMPTY FIELDS (present but empty)')
    print('-' * 80)
    for field, count in field_empty_count.items():
        if count > 0:
            pct = (count / total_items * 100) if total_items > 0 else 0
            print('  %s: %d empty (%.1f%%)' % (field.ljust(25), count, pct))
    print('')
    
    # Completeness by category
    print('AVERAGE COMPLETENESS BY CATEGORY')
    print('-' * 80)
    category_avg = {cat: sum(scores) / len(scores) for cat, scores in completeness_by_category.items()}
    sorted_categories = sorted(category_avg.items(), key=lambda x: x[1])
    for cat, avg_score in sorted_categories:
        count = len(completeness_by_category[cat])
        print('  %s: %.1f%% (%d items)' % (cat.ljust(30), avg_score, count))
    print('')
    
    # Completeness by country
    print('AVERAGE COMPLETENESS BY COUNTRY')
    print('-' * 80)
    country_avg = {country: sum(scores) / len(scores) for country, scores in completeness_by_country.items()}
    sorted_countries = sorted(country_avg.items(), key=lambda x: x[1])
    for country, avg_score in sorted_countries:
        count = len(completeness_by_country[country])
        print('  %s: %.1f%% (%d items)' % (country.ljust(30), avg_score, count))
    print('')
    
    # Items with low completeness (below 50%)
    low_completeness = [item for item in datatypes + patterns if item['completeness'] < 50]
    if low_completeness:
        print('ITEMS WITH LOW COMPLETENESS (< 50%)')
        print('-' * 80)
        sorted_low = sorted(low_completeness, key=lambda x: x['completeness'])
        for item in sorted_low[:20]:  # Show top 20
            print('  [%s] %s / %s (%.1f%%)' % (
                item['type'].upper(),
                item['id'],
                item['name'],
                item['completeness']
            ))
            if item['missing']:
                print('    Missing: %s' % ', '.join(item['missing']))
            if item['empty']:
                print('    Empty: %s' % ', '.join(item['empty']))
        if len(low_completeness) > 20:
            print('  ... and %d more items with low completeness' % (len(low_completeness) - 20))
        print('')
    
    # Items missing critical fields
    print('ITEMS MISSING CRITICAL FIELDS')
    print('-' * 80)
    critical_missing = []
    for item in datatypes + patterns:
        missing_core = [f for f in item['missing'] if f in core_fields]
        if missing_core:
            critical_missing.append((item, missing_core))
    
    if critical_missing:
        for item, missing_core in critical_missing[:20]:  # Show top 20
            print('  [%s] %s / %s' % (
                item['type'].upper(),
                item['id'],
                item['name']
            ))
            print('    Missing core fields: %s' % ', '.join(missing_core))
        if len(critical_missing) > 20:
            print('  ... and %d more items with missing core fields' % (len(critical_missing) - 20))
    else:
        print('  All items have required core fields!')
    print('')
    
    print('=' * 80)


def validate():
    try:
        from cerberus import Validator
    except ImportError:
        print('Error: cerberus module is not installed.')
        print('Please install it with: pip install cerberus')
        return
    
    # Validate datatypes
    schema_file = os.path.join(DATA_PATH, 'schemes/datatype.json')
    if not os.path.exists(schema_file):
        print('Error: datatype schema file not found: %s' % schema_file)
        return
    
    try:
        with open(schema_file, 'r', encoding='utf8') as f:
            schema = json.load(f)
    except Exception as e:
        print('Error loading datatype schema: %s' % str(e))
        return
    
    datatypes = load_path(os.path.join(DATA_PATH, 'datatypes'))
    print('Loaded %d datatypes and patterns' % (len(datatypes)))
    
    v = Validator(schema)
    datatype_errors = []
    datatype_valid = 0
    
    for d in datatypes:
        if d:
            try:
                item_id = d.get('id', 'unknown')
                r = v.validate(d)
                if not r:
                    error_msg = '%s is not valid: %s' % (item_id, str(v.errors))
                    print(error_msg)
                    datatype_errors.append((item_id, v.errors))
                else:
                    datatype_valid += 1
            except Exception as e:
                item_id = d.get('id', 'unknown')
                error_msg = '%s error: %s' % (item_id, str(e))
                print(error_msg)
                datatype_errors.append((item_id, str(e)))
    
    # Validate tools
    tools_schema_file = os.path.join(DATA_PATH, 'schemes/tool.json')
    if not os.path.exists(tools_schema_file):
        print('Error: tool schema file not found: %s' % tools_schema_file)
        return
    
    try:
        with open(tools_schema_file, 'r', encoding='utf8') as f:
            tools_schema = json.load(f)
    except Exception as e:
        print('Error loading tool schema: %s' % str(e))
        return
    
    tools = load_path(os.path.join(DATA_PATH, 'tools'))
    print('Loaded %d tools' % (len(tools)))
    
    v_tools = Validator(tools_schema)
    tool_errors = []
    tool_valid = 0
    
    for d in tools:
        if d:
            try:
                item_id = d.get('id', 'unknown')
                r = v_tools.validate(d)
                if not r:
                    error_msg = '%s is not valid: %s' % (item_id, str(v_tools.errors))
                    print(error_msg)
                    tool_errors.append((item_id, v_tools.errors))
                else:
                    tool_valid += 1
            except Exception as e:
                item_id = d.get('id', 'unknown')
                error_msg = '%s error: %s' % (item_id, str(e))
                print(error_msg)
                tool_errors.append((item_id, str(e)))
    
    # Print summary
    print('')
    print('=' * 80)
    print('VALIDATION SUMMARY')
    print('=' * 80)
    print('Datatypes: %d valid, %d invalid' % (datatype_valid, len(datatype_errors)))
    print('Tools: %d valid, %d invalid' % (tool_valid, len(tool_errors)))
    total_valid = datatype_valid + tool_valid
    total_invalid = len(datatype_errors) + len(tool_errors)
    total_items = total_valid + total_invalid
    if total_items > 0:
        print('Overall: %d valid (%.1f%%), %d invalid (%.1f%%)' % (
            total_valid, 
            (total_valid * 100.0 / total_items),
            total_invalid,
            (total_invalid * 100.0 / total_items)
        ))
    print('=' * 80)


def build():
    datatypes_yaml_to_jsonl()
    print('Build new datatypes JSON and JSON lines files')
    tools_yaml_to_jsonl()
    print('Build new tools JSON and JSON lines files')


def stats():
    calculate_stats()


def main():
    parser = argparse.ArgumentParser(description="Metacrafter registry builder and validator")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("build", help="Build JSON and JSONL files from YAML datatypes and tools")
    subparsers.add_parser("stats", help="Calculate statistics for datatypes")
    subparsers.add_parser("report", help="Report missing fields for each datatype")
    subparsers.add_parser("validate", help="Validate datatypes and tools against JSON schemas")

    args = parser.parse_args()

    if args.command == "build":
        build()
    elif args.command == "stats":
        stats()
    elif args.command == "report":
        report()
    elif args.command == "validate":
        validate()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

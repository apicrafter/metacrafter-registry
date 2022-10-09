#!/usr/bin/env python
import yaml
import json
import logging
import typer
from pprint import pprint
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import csv
import os

DATA_PATH = '../data'
FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = typer.Typer()

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
        aindex.append({'id': c, 'name': adict[c]})
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
    typer.echo('Loaded %d datatypes and patterns' % (len(datatypes)))
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
    typer.echo('Loaded %d tools' % (len(tools)))
    for d in tools:
        d['num'] = len(d['supported_types'])
        fjsonl.write(json.dumps(d, ensure_ascii=False) + '\n')
        output[d['id']] = d
    f.write(json.dumps(output, ensure_ascii=False))
    f.close()
    fjsonl.close()



def export_to_datahub(filename):
    data = load_json(os.path.join(DATA_PATH, 'datatypes_latest.json'))
    output = {'version' : 1, 'source' : 'DataHub', 'owners' : {'users': ['datahub',]}, 'url' : 'https://registry.apicrafter.io'}
    nodes = []
    categories = {}
    for item in data.values():
       cat = item['categories'][0]['id']
       if cat not in categories:
           categories[cat] = [item]
       categories[cat].append(item)

    for cat in categories.keys():
        node = {'name' : cat.title(), 'description' : categories[cat][0]['categories'][0]['name']}
        terms = []
        for item in categories[cat]:
            term = {'name' : item['id'].strip(), 'description' : item['doc'], 'term_source' : 'EXTERNAL',
                    'source_ref' : 'METACRAFTER_REGISTRY',
                    'source_url' : 'https://registry.apicrafter.io/datatype/' + item['id'],
                    }

            term['inherits'] = []
            if 'parent' in item.keys():
                term['inherits'].append(data[item['parent']['type']]['categories'][0]['id'] + '.' + data[item['parent']['type']]['id'].strip())
            if 'semantic_type' in item.keys():
                key = data[item['semantic_type']]['categories'][0]['id'] + '.' + data[item['semantic_type']]['id'].strip()
                if key not in term['inherits']: term['inherits'].append(key)
            if 'patterns' in item.keys():
                term['contains'] = []
                for pat in item['patterns']:
                    term['contains'].append(pat['categories'][0]['id'] + '.' + pat['id'].strip())
            langs = []
            for lang in item['langs']:
                langs.append(lang['id'])
            item_categories = []
            for category in item['categories']:
                item_categories.append(category['id'])

            properties = {'metacrafter_id' : item['id'], 'is_pii' : item['is_pii'], 
                          'categories' : ','.join(item_categories), 'languages' : ','.join(langs)}
 
            if 'country' in item.keys(): 
                countries = []
                for country in item['country']:
                    countries.append(country['id'])
                properties['countries'] = ','.join(countries)
            if 'wikidata_property' in item.keys(): properties['wikidata_property'] = item['wikidata_property']
            if 'classification' in item.keys(): properties['classification'] = item['classification']
            if 'regexp' in item.keys(): properties['regexp'] = item['regexp']
            term['custom_properties'] = properties
            terms.append(term)
        node['terms'] = terms
        nodes.append(node)
    output['nodes'] = nodes
    f = open(filename, 'w', encoding='utf8')
    yaml.dump(output, f, Dumper=Dumper)
    f.close()
    

@app.command()
def datahub(filename: str):           
    export_to_datahub(filename)


if __name__ == "__main__":
    app()

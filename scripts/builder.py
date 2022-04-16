#!/usr/bin/env python
import yaml
import json
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import csv
import os
import pprint

DATA_PATH = '../data'

def load_dict(filename):
    f = open(filename, 'r', encoding='utf8')
    data = yaml.load(f, Loader=Loader)
    f.close()
    out = {}
    for r in data:
        out[r['id']] = r['name']
    return out

def load_path(dirpath):
    files = os.listdir(dirpath)
    all = []
    for filename in files:
        f = open(os.path.join(dirpath, filename), 'r', encoding='utf8')
        all.append(yaml.load(f, Loader=Loader))
        f.close()
    return all


def update_by_dict(arr, adict):
    aindex = []
    for c in arr:
        aindex.append({'id': c, 'name': adict[c]})
    return aindex



def yaml_to_jsonl():
    output = {}
    countries = load_dict(os.path.join(DATA_PATH, 'countries.yaml'))
    categories = load_dict(os.path.join(DATA_PATH, 'categories.yaml'))
    langs = load_dict(os.path.join(DATA_PATH, 'langs.yaml'))

    fjsonl = open(os.path.join(DATA_PATH, 'datatypes_latest.jsonl'), 'w', encoding='utf8')
    f = open(os.path.join(DATA_PATH, 'datatypes_latest.json'), 'w', encoding='utf8')

    patterns = load_path(os.path.join(DATA_PATH, 'patterns'))
    pindex = {}
    for p in patterns:
        p['type'] = 'pattern'
        if not p['semantic_type'] in pindex.keys():
            pindex[p['semantic_type']] = []
        if 'country' in p.keys():
            p['country'] = update_by_dict(p['country'], countries)
        if 'langs' in p.keys():
            p['langs'] = update_by_dict(p['langs'], langs)
        pindex[p['semantic_type']].append(p)
        output[p['id']] = p
        fjsonl.write(json.dumps(p, ensure_ascii=False) + '\n')

    datatypes = load_path(os.path.join(DATA_PATH, 'datatypes'))    
    for d in datatypes:
        d['type'] = 'datatype'
        d['is_pii'] = True if d['is_pii'] == 'True' else False
        if d['id'] in pindex.keys():
            d['patterns'] = pindex[d['id']]
        if 'categories' in d.keys():
            d['categories'] = update_by_dict(d['categories'], categories)
        if 'country' in d.keys():
            d['country'] = update_by_dict(d['country'], countries)
        if 'langs' in d.keys():
            d['langs'] = update_by_dict(d['langs'], langs)
        fjsonl.write(json.dumps(d, ensure_ascii=False) + '\n')
        output[d['id']] = d
    f.write(json.dumps(output, ensure_ascii=False))
    f.close()
    fjsonl.close()

def build_dataset():
    yaml_to_jsonl()


if __name__ == "__main__":
    build_dataset()
    print('Build new datatypes JSON and JSON lines files')
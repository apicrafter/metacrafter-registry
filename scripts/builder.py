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
    for subf in subfolders:
        files = os.listdir(subf)
        for filename in files:
            logging.info('Load %s' % (filename))
            f = open(os.path.join(subf, filename), 'r', encoding='utf8')
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

    patterns = load_path(os.path.join(DATA_PATH, 'patterns'))
    typer.echo('Loaded %d patterns' % (len(patterns)))
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
    typer.echo('Loaded %d datatypes' % (len(datatypes)))
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



def calculate_stats():
    data = load_json(os.path.join(DATA_PATH, 'datatypes_latest.json'))
    typer.echo('')
    total_types = 0
    total_pat = 0
    has_regexp = 0
    has_wikidata = 0
    has_links = 0
    has_trans = 0
    has_exam = 0
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
    total_all = total_types + total_pat
    typer.echo('Total data types %d' % (total_types))
    typer.echo('Total patterns %d' % (total_pat))
    typer.echo('Total registered types %d' % (total_all))
    typer.echo('- with link %0.2f%% (%d)' % (has_links * 100.0 / total_all, has_links))
    typer.echo('- with regexp %0.2f%% (%d)' % (has_regexp * 100.0 / total_all, has_regexp))
    typer.echo('- with wikidata url %0.2f%% (%d)' % (has_wikidata * 100.0 / total_all, has_wikidata))
    typer.echo('- with translations %0.2f%% (%d)' % (has_trans * 100.0 / total_all, has_trans))
    typer.echo('- with examples %0.2f%% (%d)' % (has_exam * 100.0 / total_all, has_exam))


@app.command()
def report():
    data = load_json(os.path.join(DATA_PATH, 'datatypes_latest.json'))
    typer.echo('')
    total_types = 0
    total_pat = 0
    has_regexp = 0
    has_wikidata = 0
    has_links = 0
    has_trans = 0
    has_exam = 0
    for d in data.values():     
        irep = []
        if 'regexp' not in d.keys():
            irep.append('no regexp')
        if 'wikidata_property' not in d.keys():
            irep.append('no wikidata property')
        if 'links' not in d.keys():
            irep.append('no links')
        if 'translations' not in d.keys():
            irep.append('no translations')
        if 'examples' not in d.keys():
            irep.append('no examples')
        if len(irep) > 0:
            print('%s / %s' % (d['id'], d['name']))
            for r in irep:
                print('- %s' % (r))


@app.command()
def validate():
    from cerberus import Validator
    schema_file = os.path.join(DATA_PATH, 'schemes/datatype.json')
    f = open(schema_file, 'r', encoding='utf8')
    schema = json.load(f)
    f.close()
    datatypes = load_path(os.path.join(DATA_PATH, 'datatypes'))
    typer.echo('Loaded %d datatypes' % (len(datatypes)))

    patterns = load_path(os.path.join(DATA_PATH, 'patterns'))
    typer.echo('Loaded %d patterns' % (len(patterns)))
    v = Validator(schema)
    for d in datatypes:
        if d:
            try:
                r = v.validate(d, schema)
                if not r:
                    print('%s is not valid %s' % (d['id'], str(v.errors)))
            except Exception as e:
                print('%s error %s' % (d['id'], str(e)))


    tools = load_path(os.path.join(DATA_PATH, 'tools'))
    schema_file = os.path.join(DATA_PATH, 'schemes/tool.json')
    f = open(schema_file, 'r', encoding='utf8')
    tools_schema = json.load(f)
    f.close()
    v = Validator(schema)
    for d in tools:
        if d:
            try:
                r = v.validate(d, tools_schema)
                if not r:
                    print('%s is not valid %s' % (d['id'], str(v.errors)))
            except Exception as e:
                print('%s error %s' % (d['id'], str(e)))


@app.command()
def build():
    datatypes_yaml_to_jsonl()
    typer.echo('Build new datatypes JSON and JSON lines files')
    tools_yaml_to_jsonl()
    typer.echo('Build new tools JSON and JSON lines files')

@app.command()
def stats():
    calculate_stats()


if __name__ == "__main__":
    app()

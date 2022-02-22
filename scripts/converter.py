#!/usr/bin/env python
import typer
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import csv

import pprint
DATA_FILE = '../data/entities.yaml'
headers = ['id', 'name', 'doc', 'is_pii', 'langs', 'contexts',
           'translations.ru.name', 'translations.ru.doc', 'links.url', 'links.type']


def tocsv():
    fout = open('entities.csv', 'w', encoding='utf8')
    f = open(DATA_FILE, 'r', encoding='utf8')
    data = yaml.load(f, Loader=Loader)
    keys = list(data.keys())
    keys.sort()
    print('\t'.join(headers))
    writer = csv.writer(fout, delimiter='\t')
    writer.writerow(headers)
    for key in keys:
        record = [key, data[key]['name'], data[key]['doc'], str(data[key]['is_pii']),','.join(data[key]['langs']), ','.join(data[key]['contexts']),
                  data[key]['translations']['ru']['name'], data[key]['translations']['ru']['doc'],
                  data[key]['links'][0]['url'] if len(data[key]['links']) > 0 else '',
                  data[key]['links'][0]['type'] if len(data[key]['links']) > 0 else '',
                  ]
        writer.writerow(record)
        print('\t'.join(record))
    pass
                    

if __name__ == "__main__":
    typer.run(tocsv)
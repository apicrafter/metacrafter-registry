from flask import Flask, json, jsonify, redirect, render_template, send_file, send_from_directory, request, url_for, flash, Response
import collections

DEBUG = False
SECRET_KEY = "dft5eycglbkj30i6tdfg,xfkxflgkdrfogkotg,/vxlf"
REGISTRY_HOST = '127.0.0.1'
REGISTRY_PORT = 8089
DATATYPES_DATA_PATH = '../data/datatypes_latest.json'
TOOLS_DATA_PATH = '../data/tools_latest.json'

def load_data(filename):
    f = open(filename, 'r', encoding='utf8')
    data = collections.OrderedDict(sorted(json.load(f).items()))
    f.close()
    return data

DATATYPES_GLOBAL = load_data(DATATYPES_DATA_PATH)    
TOOLS_GLOBAL = load_data(TOOLS_DATA_PATH)

def root_view():
    global DATATYPES_GLOBAL
    return render_template('datatype_list.tmpl', objects=DATATYPES_GLOBAL.values())

def datatype_view(slug):
    global DATATYPES_GLOBAL
    obj = DATATYPES_GLOBAL[slug]
    return render_template('datatype.tmpl', object=obj)

def datatype_view_json(slug):
    global DATATYPES_GLOBAL
    obj = DATATYPES_GLOBAL[slug]
    return jsonify(obj)

def tools_list_view():
    global TOOLS_GLOBAL
    return render_template('tool_list.tmpl', objects=TOOLS_GLOBAL.values())

def tool_view(slug):
    global TOOLS_GLOBAL
    obj = TOOLS_GLOBAL[slug]
    return render_template('tool.tmpl', object=obj)

def tool_view_json(slug):
    global TOOLS_GLOBAL
    obj = TOOLS_GLOBAL[slug]
    return jsonify(obj)


def registry_view_json():
    global DATATYPES_GLOBAL
    return jsonify(DATATYPES_GLOBAL)


def add_views_rules(app):
    app.add_url_rule('/', 'root', root_view)
    app.add_url_rule('/registry.json', '/registry.json', registry_view_json)
    app.add_url_rule('/datatype/<slug>', 'datatype/<slug>', datatype_view)
    app.add_url_rule('/datatype/<slug>.json', 'datatype/<slug>.json', datatype_view_json)
    app.add_url_rule('/tool', 'tool', tools_list_view)
    app.add_url_rule('/tool/<slug>', 'tool/<slug>', tool_view)
    app.add_url_rule('/tool/<slug>.json', 'tool/<slug>.json', tool_view_json)

def run_server():

    app = Flask("Metacrafter registry", static_url_path='/assets')
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['PROPAGATE_EXCEPTIONS'] = True

    add_views_rules(app)

    app.run(host=REGISTRY_HOST, port=REGISTRY_PORT, debug=DEBUG)


if __name__ == "__main__":
    run_server()

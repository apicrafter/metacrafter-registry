# metacrafter-registry
Registry of metadata identifier entities like UUID, GUID, person fullname, address and so on. Linked with other sources and to be converted to ontology in the future.

It's created from list of identifiers in [Metacrafter](https://github.com/apicrafter/metacrafter) tool  and list of data classes in [Datacrafter](https://datacrafter.ru/class) data catalog.

# Data

* data/datatypes/ - list of all known semantic data types as separate YAML files
* data/patterns/ - list of known patterns as separate YAML files
* data/categories.yaml - list of all data contexts. Categories used by Metacrafter tool to use only rules for certain situation/data/contexts set by user
* data/countries.yaml - list of all countries with available rules
* data/langs.yaml - list of all languages with available rules

## Semantic data type

Semantic data type is a primary data class with description of unique type of the data which is somehow defined identifier or commonly used data type.

Each semantic data type YAML file  objects have following structure.

- **id** - unique identifier of the entity
- **name** - name of the entity
- **category** - list of contexts associated with entity. 
- **country** - list of countries where this identifier used
- **doc** - English documentation/short description of this entity.
- **langs** - list of languages
- **is_pii** - true if this data is Personal identifiable information and false if not. PII could be detected also from contexts
- **links** - list of associated links with **type** as link type and **url** as url. Supported link types: wikipedia, wikidata, other
- **regexp** - regular expression that match this data type
- **wikidata_property** - property in Wikidata if applicable
- **examples** - list of examples with **value** and **description** for each one
- **parent_type** - name of the parent semantic type
- **translations** - name and doc translated to selected language.  

## Pattern

Patterns are extensions, additional helpers to identify certain ways to represent semantinc data types. They could be different by usage type, country, language and so on.
Patterns have no category since they inherit category from semantic data type

Each entity YAML file objects has following structure.

- **id** - unique identifier of the entity
- **name** - name of the entity
- **doc** - English documentation/short description of this entity.
- **country** - list of countries where this identifier used
- **langs** - list of languages
- **links** - list of associated links with **type** as link type and **url** as url. Supported link types: wikipedia, other
- **regexp** - regular expression that match this data type
- **wikidata_property** - property in Wikidata if applicable
- **examples** - list of examples with **value** and **description** for each one

## Tool

Tools are software libraries, open source or proprietary software with support of semantic data types.
Each entity YAML file objects has following structure.

- **id** - unique identifier of the entity
- **name** - name of the entity
- **category** - category of the tool. It could be one of: detector, pii, etl, other
- **doc** - English documentation/short description of this entity.
- **website** - URL of the primary web resource about this tool
- **supported_types** - array of strings with id of datatype or pattern for each string

## Identification rules

**Under development**

Identification rules are regex, other pattern matching algorithms and code that help to identify certain semantic data type directly or by pattern.

# Code

* scripts/ - list of scripts to convert and process data types and related registry data
* src/ - minimalistic server side code to run metadata server/

# Build registry

**Under development**

Current data update procedure:
1. Edit YAML files in data directory
2. Run builder.py script. It will to rebuild data/datatypes_latest.json and data/datatypes_latest.jsonl files from YAML files
3. Run src/registry.py to see changes locally https://127.0.0.1:8089 
4. Add, commit and push changed files

TODO: Add github actions for automatic registry build, version control, release and validation.

# Run server 
Server uses data/datatypes_latest.jsonl file to produce HTML for datatypes list
1. Go to "src" directory
2. Run "python registry.py"

# Contacts

Maintainer - Ivan Begtin (ivan@begtin.tech)

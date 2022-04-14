# metacrafter-registry
Registry of metadata identifier entities like UUID, GUID, person fullname, address and so on. Linked with other sources and to be converted to ontology in the future.

It's created from list of identifiers in [Metacrafter](https://github.com/apicrafter/metacrafter ) tool  and list of data classes in [Datacrafter](https://datacrafter.ru/class) data catalog.

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
- **links** - list of associated links with **type** as link type and **url** as url. Supported link types: wikipedia, other
- **parent_type** - name of the parent semantic type
- **translations** - name and doc translated to selected language.  

## Pattern

Patterns are extensions, additional helpers to identify certain ways to represent semantinc data types. They could be different by usage type, country, language and so on.
Patterns have no category since they inherit category from semantic data type

Each entity YAML file  objects have following structure.

- **id** - unique identifier of the entity
- **name** - name of the entity
- **doc** - English documentation/short description of this entity.
- **country** - list of countries where this identifier used
- **langs** - list of languages
- **links** - list of associated links with **type** as link type and **url** as url. Supported link types: wikipedia, other

## Identification rules

**Under development**

Identification rules are regex, other pattern matching algorithms and code that help to identify certain semantic data type directly or by pattern.





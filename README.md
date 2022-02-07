# metacrafter-registry
Registry of metadata identifier entities like UUID, GUID, person fullname, address and so on. Linked with other sources and to be converted to ontology in the future.

It's created from list of identifiers in [Metacrafter](https://github.com/apicrafter/metacrafter ) tool  and list of data classes in [Datacrafter](https://data.apicrafter.ru/class) data catalog.

# Data

* data/entities.yaml - list of all known identifiers
* data/contexts.yaml - list of all data contexts. Contexts used by Metacrafter tool to use only rules for certain situation/data
* data/langs.yaml - list of all languages with available rules

## Entities.yaml

Entities.yaml objects have following structure.

- **id** - unique identifier of the entity
- **name** - name of the entity
- **context** - list of contexts associated with entity. 
- **doc** - English documentation/short description of this entity.
- **langs** - list of languages
- **is_pii** - true if this data is Personal identifiable information and false if not. PII could be detected also from contexts
- **links** - list of associated links with **type** as link type and **url** as url. Supported link types: wikipedia, other
- **translations** - name and doc translated to selected language.  



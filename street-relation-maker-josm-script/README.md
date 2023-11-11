# Street Relation Maker JOSM Script

Script for [JOSM Scripting Plugin](https://gubaer.github.io/josm-scripting-plugin/) that creates [street relations](https://wiki.openstreetmap.org/wiki/Relation:street).

Use with GraalJS JavaScrip API V3.

## Usage

Select a street with `wikidata` tag and run the script. It will create a street relation, copy there all name* tags and move `wikidata`, `wikipedia` and `name:etymology:wikidata` tags.

# Script for syncing OSM ID in wikidata

This script retrieves all OSM features with `wikidata` tag and adds OSM reference claim to wikidata item referenced if it is missng.

## Requirements

Install [Deno](https://deno.com).

Script creates multiple references in a single wikidata entry if there are multiple objects in OSM with the same `wikidata` tag. Therefore it is more than recommended to first create `waterway`, `street`/`associatedStreet`, `railway` and other relations and move there `wikidata` tags.

## Running

Before running modify [main.ts](./main.ts) with your `cookie` header and `token`. To cover different area update `searchArea` in Overpass request.

```bash
./main.ts
```

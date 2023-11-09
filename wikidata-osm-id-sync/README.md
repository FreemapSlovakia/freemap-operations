# Script for syncing OSM ID in wikidata

This script retrieves all OSM features with `wikidata` tag and adds OSM reference claim to wikidata item referenced if it is missng.

## Requirements

[Deno](https://deno.com)

## Running

Before running modify [main.ts](./main.ts) with your `cookie` header and `token`. To cover different area update `searchArea` in Overpass request.

```bash
./main.ts
```

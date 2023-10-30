#!/usr/bin/env -S deno run --allow-net

async function fetchWikidataItems(offset = 0, limit = 1000) {
  const sparqlQuery = `
      SELECT ?item ?itemLabel ?coord WHERE {
          ?item wdt:P625 ?coord; wdt:P17 wd:Q214.
          SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
      }
      LIMIT ${limit}
      OFFSET ${offset}
  `;

  const url =
    "https://query.wikidata.org/sparql?query=" +
    encodeURIComponent(sparqlQuery) +
    "&format=json";

  const response = await fetch(url);
  const json = await response.json();

  return json.results.bindings;
}

async function getAllWikidataItems() {
  // return JSON.parse(await Deno.readTextFile("wiki.json"));

  const allItems = [];
  let offset = 0;
  const limit = 1000;
  while (true) {
    const items = await fetchWikidataItems(offset, limit);
    if (items.length === 0) break;
    allItems.push(...items);
    offset += limit;
  }
  return allItems;
}

async function fetchOSMItems() {
  const overpassQuery = `
      [out:json];
      area[name="Slovensko"]->.searchArea;
      nwr(area.searchArea)["wikidata"]; out;
  `;

  const url =
    "https://overpass-api.de/api/interpreter?data=" +
    encodeURIComponent(overpassQuery);

  const response = await fetch(url);
  const json = await response.json();

  return json.elements;
}

async function getFilteredItems() {
  const wikidataItems = await getAllWikidataItems();
  const osmItems = await fetchOSMItems();

  const osmWikidataIds = new Set(osmItems.map((item) => item.tags.wikidata));

  const filteredWikidataItems = wikidataItems.filter(
    (item) => !osmWikidataIds.has(item.item.value.replace("http://www.wikidata.org/entity/", ""))
  );

  return filteredWikidataItems;
}

function pointToArray(pointString: string) {
  const match = pointString.match(/Point\(([\d.-]+)\s([\d.-]+)\)/);
  if (match) {
    return [parseFloat(match[1]), parseFloat(match[2])];
  }
  throw new Error("Invalid Point format " + pointString);
}

getFilteredItems().then((a) =>
  console.log(
    JSON.stringify({
      type: "FeatureCollection",
      features: a
        .filter((item) => item.coord.type === "literal")
        .map((item) => ({
          type: "Feature",
          properties: {
            wikidata: item.item.value.replace("http://www.wikidata.org/entity/", ""),
            name: /^Q\d+$/.test(item.itemLabel.value)
              ? undefined
              : item.itemLabel.value,
          },
          geometry: {
            type: "Point",
            coordinates: pointToArray(item.coord.value),
          },
        })),
    })
  )
);

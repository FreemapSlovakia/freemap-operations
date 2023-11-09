#!/usr/bin/env -S deno run --allow-net

async function getOSMData(): Promise<any[]> {
  const response = await fetch("https://overpass-api.de/api/interpreter", {
    method: "POST",
    body: `[out:json][timeout:60];
        area["ISO3166-1"="SK"][boundary=administrative]->.searchArea;
        nwr["wikidata"](area.searchArea);
        out tags qt;
      `,
  });

  const data = await response.json();

  return data.elements;
}

async function addOSMReferenceToWikidata(
  wikidataId: string,
  property: string,
  osmId: number
) {
  const response = await fetch("https://www.wikidata.org/w/api.php", {
    method: "POST",
    headers: {
      "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
      cookie:
        "PUT_HERE_YOUR_OWN"
    },
    body: new URLSearchParams({
      action: "wbcreateclaim",
      format: "json",
      entity: wikidataId,
      property,
      snaktype: "value",
      value: JSON.stringify(String(osmId)),
      bot: "1",
      token: "PUT_HERE_YOUR_OWN",
    }).toString(),
  });

  if (!response.ok) {
    console.error(await response.text());

    Deno.exit(1);
  }

  const res = await response.json();

  if (res.error) {
    console.error(JSON.stringify(res.error));

    Deno.exit(1);
  }
}

const propMapping: Record<string, string> = {
  node: "P11693",
  way: "P10689",
  relation: "P402",
};

for (const item of await getOSMData()) {
  const { wikidata } = item.tags;

  const response = await fetch(
    `https://www.wikidata.org/wiki/Special:EntityData/${wikidata}.json`
  );

  const data = await response.json();

  const { claims = {} } = data.entities[wikidata];

  for (const [type, prop] of Object.entries(propMapping)) {
    if (item.type !== type) {
      if (claims[prop]) {
        console.warn("Reference type mismatch", item.type, item.id, wikidata);
      }
    } else {
      if (claims[prop]?.[0]) {
        if (claims[prop].length > 1) {
          throw new Error("Unexpected multiple claims for a prop. " + item.type + ":" + item.id);
        }

        if (claims[prop][0].mainsnak.datavalue.value === String(item.id)) {
          console.info("OKAY", item.type, item.id, wikidata);
        } else {
          console.warn("Reference ID mismatch", item.type, item.id, wikidata);
        }
      } else {
        console.info("CREATE", item.type, item.id, wikidata);

        await addOSMReferenceToWikidata(wikidata, prop, item.id);
      }
    }
  }
}

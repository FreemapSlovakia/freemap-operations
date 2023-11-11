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

      await wait();

      continue;
    }

    const res = await response.json();

    if (res.error) {
      console.error(JSON.stringify(res.error));

      await wait();

      continue;
    }

    break;
  }
}

const propMapping: Record<string, string> = {
  node: "P11693",
  way: "P10689",
  relation: "P402",
};

for (const item of await getOSMData()) {
  const { wikidata } = item.tags;

  if (!/^Q\d+$/.test(wikidata)) {
    console.log("Wrong wikidata", item);

    continue;
  }

  let data;

  for (;;) {
    const response = await fetch(
      `https://www.wikidata.org/wiki/Special:EntityData/${wikidata}.json`
    );

    if (response.ok) {
      data = await response.json();

      break;
    }

    console.error(await response.text());

    await wait();
  }

  if (!data.entities[wikidata]) {
    console.warn("No wikidata entry", item.type, item.id, wikidata);
    continue;
  }

  const { claims = {} } = data.entities[wikidata];

  for (const [type, prop] of Object.entries(propMapping)) {
    let create = true;

    if (item.type !== type) {
      if (claims[prop]) {
        console.warn("Reference type mismatch", item.type, item.id, wikidata);
      }
    } else {
      for (const items of claims[prop] ?? []) {
        if (items.mainsnak.datavalue.value === String(item.id)) {
          console.info("OKAY", item.type, item.id, wikidata);

          create = false;
        } else {
          console.warn("Reference ID mismatch", item.type, item.id, wikidata);
        }
      }

      if (create) {
        console.info("CREATE", item.type, item.id, wikidata);

        await addOSMReferenceToWikidata(wikidata, prop, item.id);
      }
    }
  }
}

async function wait() {
  console.log("Sleeping...");

  await new Promise((r) => setTimeout(r, 60000));
}

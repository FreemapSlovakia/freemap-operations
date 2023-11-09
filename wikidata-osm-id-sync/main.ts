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
        "GeoIP=SK:KI:Ko__ice:48.69:21.20:v4; wikidatawikimwuser-sessionId=a4817c5ac2252c59f881; wikidatawikiss0-UserID=6403112; wikidatawikiUserID=6403112; wikidatawikiss0-UserName=Martin%20%C5%BDdila; wikidatawikiUserName=Martin%20%C5%BDdila; centralauth_ss0-User=Martin%20%C5%BDdila; centralauth_User=Martin%20%C5%BDdila; centralauth_ss0-Token=95359c7c364d4f0ff20ce0f077959f3f; centralauth_Token=95359c7c364d4f0ff20ce0f077959f3f; loginnotify_prevlogins=2023-1l7ip7n-6lhsxabquwqphu0mwe4hrtg6fs3rtp5; ss0-wikidatawikiSession=d3j68e9r9k8t6jsckp3rtjmc20aq644u; ss0-centralauth_Session=b6c5ef3dbda7db2ba6c9ae066b046056; centralauth_Session=e438f95408e9b4425c75ea0f91873000; WMF-Last-Access=09-Nov-2023; WMF-Last-Access-Global=09-Nov-2023; NetworkProbeLimit=0.001; wikidatawikiSession=bht2oennp21d8f44crfk9r561bb18ngi"
    },
    body: new URLSearchParams({
      action: "wbcreateclaim",
      format: "json",
      entity: wikidataId,
      property,
      snaktype: "value",
      value: JSON.stringify(String(osmId)),
      bot: "1",
      token: "1e343b7afa808f8248e2622c943dd8b5654c8154+\\",
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

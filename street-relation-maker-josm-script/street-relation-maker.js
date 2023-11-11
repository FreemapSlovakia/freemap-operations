import josm from "josm";
import * as console from "josm/scriptingconsole";
import { buildChangeCommand, buildAddCommand } from "josm/command";
import { DataSetUtil, OsmPrimitiveType } from "josm/ds";
import { RelationBuilder } from "josm/builder";

function run() {
  const layer = josm.layers.activeLayer;

  const data = layer.data;

  const selected = data.getSelected();

  for (const s of selected) {
    const wikidata = s.get("wikidata");

    if (wikidata) {
      const members = [
        ...data.getPrimitives((p) => p.get("wikidata") === wikidata),
      ];

      const tags = { type: "street" };

      for (const member of members) {
        for (const [k, v] of member.getKeys()) {
          if (
            k === "name:etymology:wikidata" ||
            k === "wikidata" ||
            k === "wikipedia" ||
            /^(\w+_)?name(:\w+)?$/.test(k)
          ) {
            if (tags[k] && tags[k] !== v) {
              josm.alert("Mismatch: " + k + "=" + v + "/" + tags[k]);

              return;
            }

            tags[k] = v;
          }
        }
      }

      buildChangeCommand(...members, {
        tags: {
          wikidata: null,
          wikipedia: null,
          "name:etymology:wikidata": null,
        },
      }).applyTo(layer);

      const rel = RelationBuilder.withTags(tags)
        .withMembers(members.map((m) => RelationBuilder.member("street", m)))
        .create();

      buildAddCommand(rel).applyTo(layer);
    }
  }
}

run();

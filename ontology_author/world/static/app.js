const json = async (path) => {
  const response = await fetch(path);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || response.statusText);
  return payload;
};

const text = (value) => document.createTextNode(value == null ? "" : String(value));
const el = (tag, className, ...content) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.append(...content.filter((item) => item !== undefined));
  return node;
};

async function load() {
  const [overview, relations] = await Promise.all([
    json("/world/overview"),
    json("/world/schema"),
  ]);
  document.title = `Ontology Author · ${overview.world_id}`;
  document.querySelector("#title").append(text(`World: ${overview.world_id}`));
  document.querySelector("#identity").append(
    text(`revision ${overview.revision} · sealed semantic state`),
  );
  const summary = document.querySelector("#summary");
  for (const [label, value] of [
    ["relations", overview.relations],
    ["referents", overview.referents],
    ["assertions", overview.assertions],
    ["unresolved", overview.demand?.obligations ?? 0],
  ]) {
    summary.append(el("div", "metric", el("strong", null, text(value)), el("span", null, text(label))));
  }
  const target = document.querySelector("#schema");
  for (const relation of relations.relations) {
    const card = el("article", "relation");
    card.append(el("div", "relation-name", text(relation.name)));
    card.append(el("div", "muted", text(`${relation.mode} · ${relation.count} rows · ${relation.scope || "scope unavailable"}`)));
    const roles = el("div", "roles");
    for (const role of relation.roles) roles.append(el("span", "role", text(`${role.name}: ${role.type}`)));
    card.append(roles);
    target.append(card);
  }
}

load().catch((error) => { document.querySelector("#error").append(text(error.message)); });

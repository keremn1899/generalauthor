# Ontology Author inspector

This directory contains the source for the bundled, read-only World inspector.
It is built into `ontology_author/world/static/` and served by `author open`.

## Run

Build from this directory:

```bash
npm install
npm run build
```

For development, `npm run dev` serves the inspector and proxies `/world` to a
local World API. The normal user path is `author open [world]`, which requires
no frontend installation.

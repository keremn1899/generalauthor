# Bounded Graphauthor access

Use `python graphauthor_access.py OPERATION JSON_ARGUMENTS` against the frozen graph. The only exposed operations are actual Graphauthor `lookup`, `expand` (depth 1–3), and `path` (1–6 hops). `search`, raw Cypher, embeddings, content paging, summaries, inferred edges, inverse edges and source-fetch tools are unavailable. All graph edges are directed frozen facts; their labels are `predicate|evidence|relation_id`.

Examples: `python graphauthor_access.py lookup '{"references":["resource:redis-west"]}'`; `python graphauthor_access.py expand '{"node_ids":["resource:redis-west"],"direction":"incoming","depth":1}'`.

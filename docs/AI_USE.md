# AI use in this project

> DRAFT - Ayesha and Mrittika must edit this so it is true before submitting (rule 11).

We used AI coding assistants during Graph Hacks: **Claude Code (Claude Opus 5.5)**.

AI helped with:
- Backend first draft: Claude Code generated the initial backend (loader, Cypher queries,
  rules engine, FastAPI app, investigator, Claude Code hook, MCP server, evaluation, pytest
  tests, contract mocks) from our team playbook, which specified the graph model, rulebook,
  thresholds, safety design and API contract.
- Explaining FalkorDB/Cypher concepts and error messages
- Boilerplate: FastAPI setup, React scaffolding, CSS styling
- (Mrittika: add anything else, specifically)

We designed, reviewed and can explain ourselves:
- the graph data model and every Cypher query (playbook Sections 5 and 9)
- the verdict rules and their thresholds
- the hook, the investigator's safety design and the evaluation method
- the data curation from public reports
- the UI's data flow and the evidence graph view

Every AI suggestion was read and explained by one of us before merging.

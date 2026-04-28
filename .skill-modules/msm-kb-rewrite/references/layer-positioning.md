# Layer Positioning Reference

## Why this skill exists

`md-kb-rewrite` is positioned as an additional layer inside the markdown scaffolding skillset.
It is not a replacement for the existing lower-level markdown graph / ETL / scaffolding skills.

## Layer model

### Base structural layer
Existing markdown scaffolding skills handle:
- graph parsing
- graph traversal
- scaffolding design
- ETL
- frontmatter rollup
- RDF/OWL bridge
- vector search

### Maintenance / governance layer
`md-kb-rewrite` handles:
- rewrite candidate detection
- note drift diagnosis
- evidence lag checks
- semantic framing checks
- governance gating
- controlled rewrite drafting
- low-risk refactor decisions

## Why wrapper instead of embedding everything

Embedding governance/rewrite logic into every lower-level skill would blur responsibilities.
A wrapper layer keeps:
- structural skills focused on structure,
- retrieval skills focused on retrieval,
- and maintenance/governance concerns in one cross-cutting place.

## Practical stance

This skill should call or conceptually rely on lower-level markdown scaffolding skills when needed, but should remain primarily responsible for:
- deciding whether rewrite is needed,
- classifying rewrite type and risk,
- and preserving semantic integrity during maintenance.

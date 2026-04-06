---
name: md-kb-rewrite
description: Governed rewrite and maintenance wrapper for markdown knowledge bases. Use when KB notes, note clusters, article drafts, ontology notes, or team-share docs need rewrite candidate audit, controlled rewrite drafting, semantic framing checks, readability cleanup, evidence-lag review, or low-risk refactoring. Best for keeping a markdown KB from drifting or becoming hard to maintain; acts as a wrapper layer above markdown scaffolding / graph / ETL skills rather than replacing them.
---

# md-kb-rewrite

This skill is a **wrapper layer inside the markdown scaffolding skillset**.

It should be used when the task is not just “edit this markdown file,” but rather:
- detect which KB notes need rewriting,
- diagnose why they need rewriting,
- create controlled rewrite drafts,
- check semantic framing risk,
- and decide whether changes are safe to apply automatically or should stay in draft/review mode.

This skill is **not** the low-level graph/parser/ETL layer.
Those responsibilities remain with the existing markdown scaffolding skills.
This skill sits above them as a **maintenance + governance + rewrite orchestration layer**.

## Use this skill when

Use `md-kb-rewrite` for requests like:
- “이 노트 리팩토링해줘”
- “KB가 처지는 것 같은데 어디부터 정리해야 해?”
- “중복 note 후보 찾아줘”
- “이 article draft를 팀 공유용으로 다시 써줘”
- “evidence는 늘었는데 summary가 낡았는지 점검해줘”
- “semantic framing 리스크가 있는지 보면서 rewrite해줘”
- “low-risk cleanup만 적용해줘”

## Do not use this skill when

Do **not** use this skill for:
- simple one-line markdown edits,
- creating a brand-new graph/scaffolding structure from scratch,
- pure multihop retrieval without rewrite/maintenance intent,
- pure frontmatter rollups,
- RDF import/export,
- simple article drafting with no KB maintenance / governance angle.

Use the lower-level markdown scaffolding skills directly when the task is purely structural or retrieval-oriented.

## Core model

Think in this sequence:

1. **Detect** — identify rewrite candidates
2. **Diagnose** — classify the problem type
3. **Plan** — choose rewrite mode and risk level
4. **Draft** — produce controlled rewrite output
5. **Govern** — decide auto-apply vs draft-only vs human-review-required
6. **Record** — leave rationale and trace when the change is non-trivial

The goal is not aggressive rewriting.
The goal is to prevent KB entropy while protecting meaning.

## Rewrite heuristics to check

When auditing a note or note cluster, look for these signals:

### 1. Length / structure problems
- overly long notes
- heading depth that has become hard to read
- no summary despite heavy body growth
- scattered sections with weak hierarchy

### 2. Redundancy problems
- repeated claims across nearby notes
- article/study/context notes repeating the same logic
- concept notes polluted with example-heavy duplication

### 3. Drift problems
- ontology note behaving like an opinion note
- study note behaving like an article draft
- context note behaving like a long-term concept note

### 4. Link mismatch problems
- linked notes disagree in framing or definition
- article wording is stale relative to newer study/evidence notes
- ontology changed but adjacent explanatory notes did not

### 5. Evidence freshness problems
- new evidence exists but summary/conclusion is old
- verification note changed but article or concept did not
- note still speaks with stronger certainty than current evidence supports

### 6. Readability problems
- too dense for team sharing
- too much bolding / nested bullets / broken flow
- structurally correct but hard to read

### 7. Semantic framing risk
- single framing lock-in
- uncertainty collapse
- option collapse
- claim/evidence boundary blur
- premature ontology elevation

## Rewrite types

Classify the requested or detected rewrite into one or more of:
- **summary rewrite**
- **structure rewrite**
- **readability rewrite**
- **team-share rewrite**
- **evidence-integrating rewrite**
- **dedupe rewrite**
- **taxonomy rewrite**
- **framing rewrite**

If multiple apply, say so explicitly.

## Risk levels and authority

Always assign a rough risk level before changing content.

### Low risk
Safe-ish candidates for direct application:
- spacing / markdown cleanup
- heading normalization
- list cleanup
- obvious readability improvement without meaning change
- index refresh / lightweight consistency cleanup

### Medium risk
Usually draft-first:
- strong compression of long notes
- merging duplicated sections
- reorganizing sections while preserving meaning
- integrating recent evidence into an existing summary

### High risk
Usually human-review-required:
- ontology concept change
- principle/policy rewrite
- semantic framing change
- stronger/weaker claims than before
- concept elevation / abstraction change
- decision-support or governance notes with altered interpretation

If in doubt, escalate risk rather than forcing an apply.

## Semantic framing guardrails

This skill must preserve semantic integrity, not just readability.
Before finalizing a rewrite, check:

- Did the rewrite remove uncertainty too aggressively?
- Did it overcompress alternatives into a single framing?
- Did it blur evidence and interpretation?
- Did it make a concept sound more settled than the sources justify?
- Did it accidentally erase provenance or reviewability?

If yes, prefer a draft variant plus explanation over direct replacement.

## Output modes

Choose one of these output modes intentionally.

### 1. Audit only
Use when the user wants diagnosis first.
Output:
- candidate notes / files
- heuristic triggers
- rewrite type recommendation
- risk level
- suggested next action

### 2. Draft variant
Use when rewrite is non-trivial.
Output:
- rewritten draft in a new file or side-by-side block
- short rationale
- what changed / what stayed
- risk note

### 3. Low-risk direct apply
Use only when the change is low risk and clearly mechanical.
Still summarize the edits briefly.

## When to call other markdown scaffolding skills

This wrapper skill may rely on other skills when needed.

- Use **md-graph-multihop** when rewrite quality depends on linked-note context or N-hop structure.
- Use **md-scaffolding-design** when the real problem is missing/weak structure rather than text quality alone.
- Use **md-frontmatter-rollup** when stale parent note summaries come from missing rollup/aggregation.
- Use **md-data-analysis** when the note’s meaning depends on numeric/statistical interpretation.

Do not pretend to be those skills; delegate conceptually and use their outputs where relevant.

## Suggested response structure

For audit/rewrite work, prefer this structure:

### A. Diagnosis
- what is wrong
- which heuristics fired
- what rewrite type this is

### B. Risk
- low / medium / high
- why

### C. Action
- audit only / draft variant / direct apply

### D. Result
- rewritten note or concise rewrite summary

## File handling guidance

When the user explicitly asks for safety or the rewrite is medium/high risk:
- keep the original,
- create a variant or sidecar,
- and explain the delta.

When the user asks for direct cleanup and the risk is low:
- edit in place is acceptable.

## Design stance

This is not a “rewrite everything” skill.
It is a **governed KB maintenance wrapper**.

Its purpose is to keep a markdown KB usable over time by intervening:
- early,
- selectively,
- with semantic framing awareness,
- and with governance-aware caution.

If a change could improve readability but damage meaning, prefer meaning.
If a change could improve fluency but weaken traceability, prefer traceability.
If a rewrite could be helpful but is high-risk, produce a draft instead of silently applying it.

## References

Read the planning references when needed:
- `references/kb-heuristic-rewrite-loop.md` — core rewrite loop logic and heuristic taxonomy
- `references/layer-positioning.md` — why this skill is a wrapper layer inside the markdown scaffolding skillset

---

## Heuristic H-X: Connection Candidate (Karpathy "interesting connections")

> Added 2026-04-07. Distinct from H-A~H-G which detect problems in existing notes.
> H-X detects **missing nodes** — synthesis opportunities not yet written.

Signals:
- two or more notes share key concepts but are not wikilinked
- a concept appears across multiple evidence notes without a dedicated ontology node
- a cluster of notes implies a synthesis that doesn't yet exist
- a gap in the ontology is only visible when reading several notes together

**This is not a rewrite of existing notes.** It is a proposal for a new article or node.

Output mode: **audit only**, with a draft stub or outline.

When H-X fires:
1. Identify the candidate connection (Node A ↔ Node B, or "missing concept C")
2. Explain why the connection is non-trivial
3. Produce a stub or outline for the proposed new article
4. List which existing nodes it would link to

Triggers: "새 article 후보 찾아줘", "연결 안 된 개념 찾아줘", "KB에서 놓친 게 있나", "interesting connections 찾아줘", "synthesis 기회 찾아줘", "gap 분석해줘"

ollama_mcp 연동: `ollama_extract_concepts`로 여러 노드에서 개념 목록 추출 → Claude가 교차 분석해 gap 후보 도출.

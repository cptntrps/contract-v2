# Personal Knowledge Graph Design: A Research Synthesis

**Source:** Perplexity AI (Deep Research Report)
**Date:** February 23, 2026

---

## Executive Summary

For a single-user personal knowledge graph at a scale of thousands of entities, a lightweight, opinionated ontology combined with temporal edges, a hybrid entity resolution pipeline, and a Postgres-based adjacency list schema provides the optimal balance of expressiveness, maintainability, and cost. A two-stage extraction pipeline, where a local model (e.g., Qwen) performs the initial pass and a more powerful API-based model (e.g., Claude Sonnet) acts as a reviewer, is highly aligned with current best practices. This approach, particularly when combined with schema-first JSON prompting and the distillation of step-by-step rationales into the smaller local models, represents a robust and scalable architecture.

---

## 1. Core Schema for a Personal Knowledge Graph

### 1.1. Design Principles

Research in Personal Knowledge Graphs (PKGs), such as the agenda proposed by Kenter et al., emphasizes a focus on entities central to a user's life—people, tasks, documents, and events—over the generic web entities found in large-scale knowledge graphs. Practitioner experience from Obsidian-centric projects like ODIN and Cognee reinforces this, indicating that users derive the most value from a small, stable ontology where relationships can be more free-form. The Simple Graph Builder plugin for Obsidian exemplifies this by hard-coding ten core entity types and allowing relationships to be open-vocabulary verbs.

### 1.2. Recommended Ontology

Based on this, a practical and effective ontology for a personal OS would include the following:

**Entity Types:**

*   **PERSON:** Includes the user, family, colleagues, and other contacts.
*   **ORGANIZATION:** Companies, teams, and other groups.
*   **PLACE:** Cities, addresses, and virtual spaces.
*   **PROJECT:** Multi-step endeavors, aligned with productivity methodologies like PARA.
*   **EVENT:** Meetings, trips, and significant milestones.
*   **DOCUMENT:** Notes, PDFs, emails, and conversation threads.
*   **TECHNOLOGY / TOOL:** APIs, software, devices, and other tools.
*   **CONCEPT / TOPIC:** Abstract ideas and subjects of interest.
*   **TASK:** Atomic, actionable items.
*   **GOAL:** Mid- to long-term desired outcomes.

This schema makes `GOAL` and `TASK` first-class citizens, elevating them beyond simple action items.

**Relationship Types:**

Practical PKG systems avoid an explosion of relationship types by defining a small, canonical set for high-value semantics and allowing for flexibility elsewhere. The recommended approach is to use:

*   **A Core Set of Canonical Relations:** `works_at`, `lives_in`, `manages`, `reports_to`, `member_of`, `part_of` (for task/project/goal hierarchies), `authored_by`, `mentioned_in`, `depends_on`, and `uses`.
*   **Free-form Verbs:** For all other relationships, use an open vocabulary, as the current schema's `relation` field allows. This can be enhanced by adding a `relation_category` (e.g., structural, social, cognitive) to provide a layer of semantic grouping without sacrificing flexibility.

## 2. Temporal Modeling of Changing Facts

Personal knowledge is dynamic. To handle facts that change over time, such as a user moving from one city to another, temporal knowledge graphs store information as quadruples: `(subject, relation, object, time_interval)`. This approach is explicitly recommended in OpenAI’s documentation for “Temporal Agents with Knowledge Graphs” and is a consensus in the research community.

### 2.1. Representing Temporal Validity in Postgres

To implement this in a relational schema, the `facts` and `relationships` tables should be extended with temporal columns:

*   `valid_from` (timestamptz): The time when the fact became true in the real world.
*   `valid_to` (timestamptz, nullable): The time when the fact ceased to be true. A `NULL` value indicates the fact is still believed to be true.
*   `asserted_at` (timestamptz): The timestamp of when the fact was extracted and recorded in the database (i.e., transaction time).

This schema supports bitemporal queries, allowing one to ask not only what was true at a certain point in time, but also what the system *knew* at a certain point in time.

### 2.2. Handling Contradictions

When a new fact contradicts an old one (e.g., “I moved to NYC” contradicts “I live in Boston”), the old fact should not be overwritten. Instead, its validity interval should be closed. The correct procedure is:

1.  **Close the previous interval:** Set the `valid_to` timestamp on the old fact (the `lives_in` edge to Boston) to the `valid_from` timestamp of the new fact.
2.  **Insert the new fact:** Create a new `lives_in` edge to NYC with a `valid_from` of the move date and a `valid_to` of `NULL`.

This preserves a full history of the user's location. The extraction pipeline can be trained to recognize temporal trigger phrases like “moved to,” “used to,” or “no longer” as instructions to perform this interval-closing operation.

## 3. Entity Resolution & Deduplication

For a personal-scale graph, a multi-stage pipeline is the most effective and efficient approach to entity resolution. This mirrors practices in both healthcare and other personal knowledge graph implementations.

### 3.1. A Three-Stage Resolution Pipeline

1.  **Candidate Generation (Cheap):** This first pass aims to quickly find obvious matches. It involves normalizing the mentioned entity name (e.g., lowercasing, removing possessives and role descriptors like “my manager”) and performing exact or near-exact string matches against a canonical name and a list of aliases stored for each entity. This can be further constrained by entity type or other contextual clues.

2.  **Scoring (Rules + Embeddings):** For mentions that don’t have a clear match from the first stage, a score is computed. This score should be a weighted combination of lexical similarity (e.g., Levenshtein distance) and semantic similarity (cosine similarity of embeddings). Combining these two signals consistently outperforms either one alone in small-scale graphs. Structured signals, such as a shared email domain or location, can also be factored into the score.

3.  **Arbitration (LLM or Local Model):** If the score is below a certain confidence threshold or if there are multiple close candidates, the final decision is arbitrated by a more powerful model. The local Qwen model can propose a candidate, and if the confidence is low, Claude Sonnet can be asked to make the final call. The prompt should present the ambiguous candidates and ask for a definitive merge decision.

To maintain consistency over time, the resolved `entity_id` for each mention should be persisted.

---

## 4. Confidence, Provenance, and Staleness

### 4.1. Provenance Schema

Production knowledge graph systems emphasize strong provenance. For each extracted fact, the following metadata should be stored:

*   `source_type`: The origin of the data (e.g., `conversation`, `file`, `calendar`).
*   `source_id`: The specific ID of the source (e.g., `conversation_id`, `message_id`).
*   `source_model`: The model that performed the extraction (e.g., `qwen-7b`, `claude-3.5-sonnet`).
*   `extraction_pass`: The stage of extraction (e.g., `local`, `review`, `repair`).
*   `created_at`, `updated_at`: Standard database timestamps.

Additionally, storing a `schema_version` with each extraction allows for tracking and migrating data as the schema evolves.

### 4.2. Confidence & Decay

Best practice for temporal AI systems is to combine recency with frequency of mention, rather than using a simple age-based decay. A practical model for scoring facts at query time is:

`score = confidence * (1 + log(1 + mentions_count)) * recency_factor`

Here, `confidence` is the score from the extraction model, `mentions_count` tracks how many times the fact has been observed, and `recency_factor` is a function that decays after a certain window (e.g., 6-12 months) but has a floor so that old, stable facts never decay to zero. For explicit contradictions (e.g., "I no longer like X"), the validity interval should be closed, which effectively handles the decay.

## 5. Graph Storage Patterns in Postgres

Postgres can comfortably handle a graph of <100K nodes and several hundred thousand edges with a properly indexed adjacency list model and recursive CTEs. For a personal-scale system, this is often preferable to introducing the complexity of a dedicated graph database.

### 5.1. Recommended Relational Schema

The standard approach is to use two main tables:

*   `nodes(id, type, name, description, properties jsonb, ...)`
*   `edges(id, source_id, target_id, relation, relation_category, valid_from, valid_to, properties jsonb, ...)`

Proper indexing is key to performance. B-tree indexes should be created on node and edge types, names, and foreign keys (`source_id`, `target_id`). B-tree or BRIN indexes should be used on the temporal fields (`valid_from`, `valid_to`) to accelerate time-based queries. Graph traversal can be performed using recursive CTEs (`WITH RECURSIVE`), which is sufficient for the scale of this project.

### 5.2. The Role of Apache AGE

Apache AGE is a Postgres extension that adds an openCypher query layer on top of the relational model. This allows for more natural and ergonomic graph queries (e.g., `MATCH (u:Person)-[:LIVES_IN]->(c:City)`). While this is a “nice-to-have,” it is not strictly necessary. Given the project is migrating away from Neo4j, starting with a pure relational adjacency schema is the simplest path, with the option to add AGE later if query complexity becomes a bottleneck.

## 6. Extraction Prompt Engineering & Multi-Pass Strategies

Recent best practices from multiple sources (OpenAI, practitioner blogs, and schema-driven extraction frameworks like PARSE) converge on a set of stable patterns for robust structured data extraction from LLMs.

### 6.1. Schema-First JSON Prompting

The most reliable method is to treat the output schema as a contract. The system prompt should include:

*   A concise, natural-language description of each field.
*   A few positive and negative examples to demonstrate edge cases (e.g., how to handle missing information or avoid over-extraction).
*   Strict instructions to only output a single, valid JSON object with no explanatory text.

Format enforcers (e.g., `lm-format-enforcer` or Pydantic validators) should be used to programmatically validate and, if possible, repair the LLM’s output.

### 6.2. Multi-Pass Extraction

A two-pass system (local model → validator model) is a robust pattern. The workflow is as follows:

1.  **Local Pass (Qwen):** The local model performs the initial extraction, generating the full JSON output. It should also be prompted to include a `needs_review` flag and a brief rationale for its confidence on each major object.

2.  **Validator Pass (Claude):** For extractions flagged as `needs_review` or having low confidence, the more powerful model is invoked. Its role is not to re-extract but to validate and repair. The prompt to the validator should include the original text, the local model’s JSON output, and a list of any schema validation errors. This “repair with error list” pattern is highly effective.

This tiered approach allows the system to keep costs down by only using the expensive API-based model for the most difficult or high-stakes extractions.

## 7. Distilling Claude into Local Qwen Models

For structured extraction tasks, Supervised Fine-Tuning (SFT) on high-quality teacher outputs is empirically more effective than more complex reinforcement learning setups.

### 7.1. Data and Objectives

The training data consists of pairs where the input is the conversation text and the target is the Claude-corrected JSON. An optional but highly effective addition is to also distill the step-by-step *rationale* from the teacher model. Research from Google has shown that training smaller models to generate both a rationale and the final answer improves performance with less data.

### 7.2. SFT vs. DPO

*   **SFT** is the ideal starting point. It is well-suited for this task because there is a single “gold” JSON output from Claude for each input text.
*   **DPO** (Direct Preference Optimization) is more useful later on, for refining the model on more subtle trade-offs where there isn’t a single correct answer (e.g., choosing between a slightly over-extractive vs. under-extractive output). For the initial goal of matching Claude’s schema and accuracy, SFT is the more direct path.

---

## 8. Additional Categories Worth Modeling

Beyond the current schema, several other categories of knowledge are highlighted in PKG literature as being highly valuable for personalization and retrieval.

*   **Goals & Projects:** Making `GOAL` a first-class entity type and explicitly linking tasks and projects to goals enables powerful queries about progress and alignment.
*   **Habits, Routines, and Schedules:** Extracting recurring behaviors (e.g., “weekly review on Sunday”) provides strong contextual clues for surfacing relevant information at the right time.
*   **Emotional and Motivational Context:** Adding an `emotional_state` to events and decisions, and tracking `satisfaction` or `regret` for past decisions, allows for deeper insights into the user’s patterns.
*   **Social Graph & Tie Strength:** Augmenting relationships with a `relationship_type` (e.g., friend, colleague, mentor) and a numerical `tie_strength` (approximated from frequency and recency of mentions) creates a much richer social graph.
*   **Skills & Capabilities:** Tracking the user’s skills and their proficiency level, and linking them to the projects where they are being developed, is powerful for personal and professional development queries.

## 9. Recommended Local Models by Task

For a 4090 GPU, a tiered approach with different models for different tasks is recommended:

| Task | Recommended Model(s) | Rationale |
|---|---|---|
| **First-Pass Structured Extraction** | Qwen2.5-Instruct 7B (or 14B for higher accuracy) | Strong performance on structured data and JSON output; well-supported in Ollama. |
| **Entity Resolution & Contradiction Handling** | DeepSeek-R1 14B or Qwen2.5-Instruct 14B | 14B models are a sweet spot for reasoning-intensive tasks like disambiguation and temporal updates. |
| **Policy / Routing Model** | Qwen2.5-Instruct 1.5B or 3B | Very fast and efficient for simple classification tasks like deciding whether an extraction needs review. |
| **Summarization & User-Facing UX** | Llama 3.1 8B Instruct or Gemma 2 9B | Good general-purpose assistant models for summarizing graph content into natural language. |

This three-tier stack (tiny router → 7B extractor → 14B disambiguator) allows for an efficient pipeline where the majority of the workload is handled by the fast 7B model, with more powerful models reserved for more difficult tasks.

# Optimal Knowledge Graph Schema & Extraction Strategy for Personal AI Systems

**Author:** Manus AI  
**Date:** February 23, 2026  
**Project:** LivingOS — Personal Knowledge OS

---

## Introduction

This report synthesizes research across eight critical domains for building a personal knowledge OS that ingests AI conversations and maintains a persistent, structured knowledge graph. The system described — nightly ingestion, local LLM first-pass extraction (Qwen 3B/7B), Claude Sonnet review and correction, and mismatch-driven training — represents a sophisticated architecture that sits at the intersection of knowledge representation, information extraction, and continual learning. The findings below draw on academic papers, open-source project documentation, and practitioner accounts to provide actionable guidance for each component of this system.

---

## 1. Schema Design for Personal Knowledge Graphs

### 1.1. Entity and Relationship Ontology

The most important design decision in a personal knowledge graph is choosing entity types and relationship predicates that are expressive enough to be useful but constrained enough to remain consistent. Research into existing systems reveals a convergence around a core set of entity types. The PersonaBench paper, which benchmarks LLM understanding of personal information, identifies the following categories as most salient for personal profiles: **demographics** (age, location, occupation), **interests and hobbies**, **values and beliefs**, **life experiences**, **social relationships**, **daily routines**, **goals and aspirations**, and **health and wellness** [1]. These map well to a graph schema where entities are the nouns and relationships are the verbs of a user's life.

The Zep/Graphiti architecture, which is the most thoroughly documented open-source personal knowledge graph system, uses a **three-layer graph model** [2]:

| Layer | Node Type | Description |
|---|---|---|
| Episodic | `EpisodicNode` | Raw source data — a single conversation, message, or document chunk. Preserves full context. |
| Semantic | `EntityNode` | Extracted real-world entities (people, places, organizations, concepts). One node per real-world referent. |
| Community | `CommunityNode` | Higher-order clusters of related entities, generated periodically to summarize patterns. |

Edges in this model are similarly typed: `EpisodicEdge` connects raw episodes to the entities they mention, while `EntityEdge` represents a relationship between two entities and stores the extracted fact as a property. This dual-layer approach — preserving raw source data while also maintaining a clean semantic layer — is a key architectural insight. It means that the semantic layer can be corrected or re-extracted without losing the original source data.

### 1.2. Standard Ontologies: FOAF, Schema.org, and Beyond

The Friend of a Friend (FOAF) vocabulary and Schema.org's `Person` schema provide well-tested foundations for the people-centric parts of a personal knowledge graph. Schema.org's `Person` type, for instance, includes properties like `affiliation`, `alumniOf`, `knows`, `worksFor`, `homeLocation`, and `hasOccupation`, which cover a large fraction of the facts that would be extracted from personal conversations [3]. Using these as a baseline avoids reinventing the wheel for common entity types.

However, standard ontologies are insufficient on their own. They are designed for public, machine-readable data and lack the vocabulary for personal, subjective knowledge — preferences, emotional context, and behavioral patterns. The recommended approach is a **hybrid schema**: use Schema.org/FOAF types for the structural backbone (Person, Organization, Place, Event, CreativeWork), and extend with custom entity types and relationship predicates for personal knowledge (e.g., `PREFERS`, `DECIDED_TO`, `STRUGGLES_WITH`, `ASPIRES_TO`).

### 1.3. Insights from Existing Systems

The open-source landscape offers several reference implementations. **Graphiti** (github.com/getzep/graphiti) is the most directly relevant: it is a Python library for building temporally-aware knowledge graphs from conversations, with a schema designed for AI agent memory [2]. **Khoj** (github.com/khoj-ai/khoj) is an open-source personal AI that indexes documents and notes and uses a simpler, document-centric schema. **Basic Memory** (github.com/basicmachines-co/basic-memory) uses a Markdown-based schema that maps closely to Obsidian's note structure, making it a good reference for integrating with existing note-taking workflows. The **AriGraph** paper, which inspired Graphiti's episodic/semantic split, demonstrates that this two-layer architecture significantly outperforms flat fact storage in complex reasoning tasks [4].

---

## 2. Entity Resolution and Deduplication

### 2.1. The Core Challenge

Entity resolution — determining that "John," "John Smith," and "my manager John" all refer to the same person — is one of the hardest problems in knowledge graph construction. Unlike enterprise systems that have canonical identifiers (employee IDs, email addresses), a personal knowledge graph built from unstructured conversations has no such anchors. The same entity may appear hundreds of times across thousands of conversations, with varying levels of specificity and context.

### 2.2. A Three-Stage Hybrid Pipeline

Research and practitioner experience converge on a three-stage hybrid pipeline as the most effective approach at personal scale (thousands to tens of thousands of entities):

**Stage 1 — Blocking and Exact Matching:** Before any expensive semantic comparison, a blocking step narrows the candidate set. This involves normalizing entity names (lowercasing, removing punctuation, expanding abbreviations) and performing exact-match lookups. This is cheap and catches a large fraction of duplicates. The Zep system performs a full-text search on existing entity names and summaries as its first step [2].

**Stage 2 — Embedding-Based Similarity:** For entities that pass the blocking step without an exact match, embedding-based similarity search identifies candidates that are semantically similar. The entity name and its summary are embedded, and the top-K most similar existing entities are retrieved. This is the workhorse of the deduplication pipeline and handles cases like "John" vs. "John Smith" or "Google" vs. "Alphabet Inc."

**Stage 3 — LLM-Based Resolution:** The final stage passes the candidate pairs to an LLM, which makes the definitive determination. The LLM is given the name, type, and summary of both the new entity and the candidate existing entity, and is asked to determine if they refer to the same real-world referent. If they do, the LLM also synthesizes a new, merged summary. This stage is the most expensive but is only invoked for the small fraction of cases that pass the embedding similarity threshold.

The Zep blog post on scaling LLM data extraction documents the evolution of their deduplication prompt from a complex batch operation to a simple, per-entity binary classification task [5]. The key insight is that **simplifying the LLM's task to a single yes/no question with a merged summary** dramatically improves consistency and allows for parallel execution.

### 2.3. Practical Considerations at Small Scale

At the scale of thousands of entities (not millions), the primary concern is not throughput but accuracy. The Reddit post on building a knowledge graph memory system with 10M+ nodes provides a cautionary tale: at large scale, even a small error rate in entity resolution compounds into a graph that is riddled with duplicates and incorrect merges [6]. The author recommends **asynchronous resolution** — performing deduplication in a background process rather than inline with ingestion — to avoid blocking the pipeline and to allow for human review of uncertain cases.

For a single-user system, a confidence threshold for automatic merging is advisable. Pairs with similarity above a high threshold (e.g., 0.95) are merged automatically; pairs in a middle band (e.g., 0.75–0.95) are queued for human review; pairs below the threshold are kept as separate entities.

---

## 3. Temporal Knowledge Modeling

### 3.1. The Problem of Changing Facts

A personal knowledge graph must handle the reality that facts change over time. "I live in Boston" may be true for two years and then become false when the user moves to New York. Simply overwriting the old fact loses valuable historical information. The challenge is to model temporal validity in a way that is both expressive and queryable.

### 3.2. Bitemporal Modeling

The most principled approach to temporal knowledge is **bitemporal modeling**, which tracks two independent time dimensions [7]:

*   **Valid Time (`t_valid` to `t_invalid`):** The period during which a fact is true in the real world. For the Boston example, `t_valid` would be the date the user moved to Boston, and `t_invalid` would be the date they moved to New York.
*   **Transaction Time (`created_at`):** The time when the fact was recorded in the database. This is always the current time and is set automatically.

The Zep paper implements this model directly on graph edges [2]. Each `EntityEdge` has four temporal fields: `created_at`, `expired_at`, `valid_at`, and `invalid_at`. This allows the system to answer both "what is currently true?" and "what was true at a specific point in the past?" as well as "what did the system know at a specific point in time?"

| Temporal Field | Meaning | Set By |
|---|---|---|
| `created_at` | When this edge was added to the database | System (always now) |
| `expired_at` | When this edge was superseded in the database | System (when a contradiction is found) |
| `valid_at` | When this fact became true in the real world | LLM extraction (from text) |
| `invalid_at` | When this fact stopped being true in the real world | LLM extraction (from text) |

### 3.3. Contradiction Detection and Edge Invalidation

When a new fact is extracted that contradicts an existing one, the system must invalidate the old fact rather than deleting it. The Zep architecture uses a dedicated **edge invalidation prompt** that is given the new fact and a set of candidate existing facts, and is asked to identify any that are contradicted [2]. For each identified contradiction, the `invalid_at` timestamp of the old edge is set to the `valid_at` timestamp of the new edge, creating a seamless temporal chain.

The OpenAI cookbook on temporal agents with knowledge graphs describes a similar "invalidation agent" pattern, where a separate LLM call is responsible for detecting and marking outdated triplets [8]. This separation of concerns — extraction and invalidation as distinct tasks — is a key design principle for maintaining a clean temporal graph.

---

## 4. Confidence and Provenance Tracking

### 4.1. Provenance as a First-Class Citizen

Every fact in the knowledge graph should be traceable back to its source. This is not merely a nice-to-have; it is essential for debugging extraction errors, understanding the basis for a belief, and implementing confidence decay. The recommended schema for provenance includes the following fields on every extracted fact:

*   `source_conversation_id`: The identifier of the conversation from which the fact was extracted.
*   `source_message_id`: The specific message or turn within the conversation.
*   `source_date`: The date of the source conversation.
*   `extracted_by`: The model that performed the extraction (e.g., `qwen-7b`, `claude-sonnet-3-5`).
*   `reviewed_by`: If the extraction was reviewed and corrected, the model that performed the review.
*   `extraction_timestamp`: When the extraction was performed.

The Zep architecture stores this provenance on the `EpisodicEdge` that connects a raw episode to an extracted entity or fact [2]. This means that every semantic fact can be traced back to the raw conversation that produced it.

### 4.2. Confidence Scoring and Weighting

A multi-factor confidence score is more robust than a single LLM-provided score. The following factors should be combined:

**Extraction Confidence:** The LLM performing the extraction can be asked to provide a confidence score (high/medium/low) for each extracted fact. This is already part of the current schema for preferences, and it should be extended to all fact types. Research suggests that LLMs are reasonably well-calibrated for this task when the prompt explicitly asks for uncertainty.

**Repetition Weighting:** A fact mentioned in five different conversations over six months should have higher confidence than a fact mentioned once. A simple count of supporting episodes, combined with a logarithmic scaling function, provides a robust repetition signal.

**Source Recency:** More recent sources should generally be weighted more heavily, especially for facts about the user's current state (location, job, preferences).

**User Feedback:** The user should be able to explicitly confirm or deny facts. A confirmed fact should receive a maximum confidence boost; a denied fact should be marked as invalid.

### 4.3. Confidence Decay

For facts that are likely to change over time (location, job, relationship status, preferences), confidence should decay as a function of time since the last supporting evidence. A simple exponential decay function works well: `confidence(t) = confidence_0 * exp(-λ * Δt)`, where `λ` is a decay rate that varies by fact type. Facts about stable attributes (birth year, nationality) should have a very low decay rate, while facts about dynamic attributes (current project, current city) should have a higher decay rate.

---

## 5. Graph Storage in Postgres

### 5.1. Viability at Personal Scale

For a personal knowledge graph with fewer than 100,000 nodes and edges, Postgres is a fully viable storage backend. The common concern that Postgres is "not a graph database" is largely a performance concern that only manifests at enterprise scale. At personal scale, the primary advantages of Postgres — ACID compliance, mature tooling, a rich query language, and a unified storage layer for all application data — outweigh the performance advantages of a dedicated graph database.

### 5.2. Schema Patterns for Graph Storage in Postgres

The most common and practical pattern for storing a knowledge graph in Postgres is the **adjacency list model**, where nodes and edges are stored in separate tables:

```sql
-- Nodes table
CREATE TABLE kg_nodes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,  -- 'Person', 'Organization', 'Project', etc.
    summary     TEXT,
    embedding   vector(1536),   -- pgvector for semantic search
    created_at  TIMESTAMPTZ DEFAULT now(),
    metadata    JSONB
);

-- Edges table (with bitemporal fields)
CREATE TABLE kg_edges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id       UUID REFERENCES kg_nodes(id),
    target_id       UUID REFERENCES kg_nodes(id),
    relation        TEXT NOT NULL,  -- 'WORKS_AT', 'KNOWS', 'PREFERS', etc.
    fact            TEXT,           -- Human-readable statement of the fact
    created_at      TIMESTAMPTZ DEFAULT now(),
    expired_at      TIMESTAMPTZ,
    valid_at        TIMESTAMPTZ,
    invalid_at      TIMESTAMPTZ,
    confidence      FLOAT DEFAULT 0.8,
    source_episode  UUID,           -- FK to episodes table
    metadata        JSONB
);

-- Episodic nodes (raw source data)
CREATE TABLE kg_episodes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content         TEXT NOT NULL,
    source          TEXT,           -- 'claude', 'chatgpt', 'gemini'
    conversation_id TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

This schema, combined with the `pgvector` extension for embedding-based similarity search, provides all the capabilities needed for a personal knowledge graph. Recursive CTEs can handle graph traversal queries (e.g., "find all people connected to John within 2 hops"), and the `JSONB` metadata field provides flexibility for storing additional attributes without schema migrations.

### 5.3. Extensions Worth Evaluating

**Apache AGE** (github.com/apache/age) is a Postgres extension that adds a full Cypher query interface on top of Postgres. It is worth evaluating if the team is already familiar with Cypher from Neo4j, as it would allow a direct migration path. However, AGE adds complexity and is not necessary for a personal-scale graph.

**pgvector** is essential for the embedding-based similarity search required for entity resolution and semantic retrieval. It is mature, well-maintained, and integrates seamlessly with the adjacency list schema.

The Supabase article on using Postgres as a graph database with pgRouting demonstrates that recursive CTEs and specialized extensions can handle graph traversal workloads that would previously have required a dedicated graph database [9]. For a personal-scale graph, the performance is more than adequate.

---

## 6. Extraction Prompt Engineering

### 6.1. The Evolution from Mega-Prompts to Modular Pipelines

The most important lesson from the Graphiti team's experience is that **a single, complex extraction prompt does not scale** [5]. Their initial "mega-prompt" — which included the full graph summary, the last three episodes, and 35 guidelines — worked well enough to prove the concept but was slow, expensive, and produced inconsistent results with smaller models. The solution was to decompose the extraction task into a series of focused, single-purpose prompts that can be executed in parallel.

The Graphiti pipeline now consists of at least six separate prompts: entity extraction, entity deduplication (one per new entity), fact extraction, fact deduplication, temporal fact dating, and edge invalidation [5]. Each prompt is small, focused, and produces a simple, predictable output. This decomposition is the single most impactful change for improving extraction quality with smaller models.

### 6.2. Common Failure Modes

The article on LLM failures in knowledge graph extraction identifies several failure modes that are particularly relevant for personal knowledge graphs [10]:

**Coreference Collapse:** The LLM extracts "Party A," "the plaintiff," and "the aforementioned party" as three separate entities when they all refer to the same entity. This is the most common failure mode and is best addressed by providing recent conversation context in the extraction prompt so the LLM can resolve pronouns and references.

**Over-Extraction:** The LLM extracts relationships that are implied by the text but not explicitly stated. For example, if the user says "I'm meeting with Sarah from Google tomorrow," the LLM might extract `Sarah WORKS_AT Google` as a fact, even though this was not explicitly stated. Prompt guidelines should instruct the LLM to only extract explicitly stated facts.

**Vague Entities:** The LLM extracts entities like "the project" or "the meeting" that have no canonical identity. Guidelines should instruct the LLM to use the most specific name available and to avoid extracting entities that cannot be uniquely identified.

**Temporal Hallucination:** The LLM infers temporal information (start dates, end dates) that is not explicitly stated in the text. The Graphiti team found this to be a significant problem and added explicit guidelines: "ONLY set a timestamp if a specific time is explicitly mentioned in the text. If no time is mentioned, use null." [5]

### 6.3. Chain-of-Thought vs. Direct JSON Output

The choice between chain-of-thought (CoT) reasoning and direct JSON output depends on the complexity of the extraction task and the capability of the model. For simple, well-defined extraction tasks (entity extraction, binary deduplication), direct JSON output with a well-defined schema is faster and more reliable. For complex tasks that require reasoning (temporal dating, contradiction detection), a brief CoT step before the JSON output can significantly improve accuracy.

The NER distillation paper found that CoT prompting improved GPT-4's annotation quality on NER tasks, which in turn improved the quality of the distilled training data for smaller models [11]. For the local Qwen model, which has less reasoning capacity, CoT prompting is likely to be even more beneficial.

### 6.4. Recommended Prompt Architecture

Based on the research, the following multi-stage extraction pipeline is recommended:

| Stage | Task | Model | Output |
|---|---|---|---|
| 1 | Entity extraction from current message | Local (Qwen 7B) | `{entities: [{name, type, summary}]}` |
| 2 | Entity deduplication (per entity, parallel) | Local (Qwen 7B) | `{is_duplicate, existing_id, merged_summary}` |
| 3 | Fact/relationship extraction | Local (Qwen 7B) | `{facts: [{source, target, relation, fact, valid_at}]}` |
| 4 | Fact deduplication and invalidation | Local (Qwen 7B) | `{duplicates: [...], invalidations: [...]}` |
| 5 | Review and correction of uncertain cases | Claude Sonnet | Corrected JSON from stages 1–4 |

---

## 7. Training Local Models from LLM Extractions

### 7.1. Knowledge Distillation for Structured Extraction

The architecture described in the project — local model first pass, Claude Sonnet review, mismatches become training pairs — is a textbook implementation of **output-based knowledge distillation**. The large model (teacher) provides high-quality labeled data; the small model (student) is trained to replicate the teacher's outputs. This approach has been validated for NER and relation extraction tasks in the academic literature.

The paper "Distilling Large Language Models into Tiny Models for Named Entity Recognition" demonstrates a three-phase strategy that is directly applicable [11]:

**Phase 1 — Teacher Annotation:** The teacher model (GPT-4 in the paper, Claude Sonnet in this system) annotates a subset of the data. For this system, this is already happening: every conversation that Claude reviews produces a high-quality labeled example.

**Phase 2 — Mixed Training:** The student model is trained on a mix of teacher-annotated data and any available ground-truth data. The paper found that training first on the distilled data and then on the original data ("Simple Mix" strategy) outperformed training on either dataset alone.

**Phase 3 — Data Blending Optimization:** More sophisticated data blending techniques (sigmoid decay, power decay functions) can further improve performance by gradually shifting the training distribution from distilled to original data over the course of training.

### 7.2. SFT vs. DPO: Which to Use

For this specific use case — training a local model to produce structured JSON extraction outputs that match Claude Sonnet's quality — the recommended approach is **SFT first, then DPO for refinement**:

**Supervised Fine-Tuning (SFT)** is the right tool for teaching the model the target output format and schema. The training data consists of `(conversation_text, correct_json_extraction)` pairs, where the correct JSON comes from Claude Sonnet's review. SFT is highly effective for this task because the target output is deterministic and well-defined. A Qwen 3B model fine-tuned on even a few hundred high-quality examples can learn to produce well-formed JSON in the correct schema reliably.

**Direct Preference Optimization (DPO)** is the right tool for the second phase, where the goal is to reduce the specific types of errors the local model makes. The mismatch pairs — `(conversation_text, local_model_output, claude_corrected_output)` — are perfect DPO training data. The local model's output is the "rejected" response; Claude's corrected output is the "chosen" response. DPO training on these pairs teaches the model to avoid its specific failure modes without requiring a reward model.

A common production pattern is: SFT to establish the output format, then DPO to polish behavior and reduce unwanted tendencies [12]. For a continual learning system, new mismatch pairs should be accumulated and used for periodic DPO updates.

### 7.3. Curriculum and Data Strategies

Several strategies can accelerate the training process and improve final model quality:

**Curriculum Learning:** Start with simpler extraction tasks (single-entity conversations, clear explicit facts) and gradually introduce more complex ones (multi-entity conversations, implicit relationships, temporal facts). This mirrors how the distillation paper found that training on distilled data first (which tends to be cleaner) and then on original data improved performance [11].

**Selective Sampling:** Not all mismatch pairs are equally informative. Prioritize training examples where the local model's error is systematic (e.g., consistently hallucinating temporal information) over random errors. Clustering the mismatch pairs by error type and sampling proportionally from each cluster ensures broad coverage.

**Data Augmentation:** Paraphrase the source conversations to generate additional training examples. This is particularly valuable for rare entity types or relationship predicates that appear infrequently in the natural data.

---

## 8. Missing Knowledge Categories

### 8.1. Beyond the Current Schema

The current schema (entities, relationships, preferences, facts, decisions, action items) covers the most salient categories for a personal knowledge graph. However, research into personal AI systems and the PersonaBench taxonomy reveals several additional categories that have proven valuable for downstream retrieval and personalization.

### 8.2. Goals and Aspirations

Goals are distinct from decisions and action items. A decision is a past choice; an action item is a near-term task. A goal is a desired future state that may span months or years. Tracking goals explicitly allows the AI to connect daily activities and decisions back to the user's larger aspirations and to surface relevant past information when the user is working toward a goal. The recommended schema is: `{goal, category (career/health/financial/personal/learning), horizon (short/medium/long), status (active/achieved/abandoned), created_at}`.

### 8.3. Emotional and Psychological Context

Emotional context is one of the most underutilized categories in personal AI systems. The sentiment and emotional tone of a conversation provide crucial context for interpreting the facts and decisions extracted from it. A decision made in a moment of frustration has different weight than one made after careful deliberation. The recommended approach is to extract a sentiment score and dominant emotion for each conversation, stored as metadata on the episodic node, rather than as a separate entity type. This avoids polluting the semantic graph with ephemeral emotional states while still preserving the context.

### 8.4. Skills and Competencies

Tracking the user's skills and areas of expertise enables the AI to provide more relevant recommendations and to understand the user's capacity to execute on plans. Skills can be extracted from conversations about work, learning, and projects, and should be linked to the entities (projects, organizations) where they were developed. The recommended schema is: `{skill, proficiency (novice/intermediate/expert), context (where/how it was developed), last_evidenced_at}`.

### 8.5. Habits and Behavioral Patterns

Habits are recurring behaviors that are not explicitly stated as preferences but emerge from patterns across many conversations. For example, if the user mentions going for a run every Monday morning across dozens of conversations, this is a habit worth capturing. Habits are best extracted by a periodic batch process that analyzes patterns across the episodic graph, rather than by per-conversation extraction. The recommended schema is: `{behavior, frequency, context, first_observed_at, last_observed_at, confidence}`.

### 8.6. Social Graph Dynamics

The current schema captures the existence of relationships between people but not their strength or nature. Social graph dynamics — how frequently the user interacts with a person, the emotional valence of those interactions, the context of the relationship — are valuable for prioritization and personalization. A simple relationship strength score, updated each time a person is mentioned in a conversation, provides a useful signal for ranking people by relevance.

### 8.7. Summary Table of Recommended Knowledge Categories

| Category | Current Schema | Recommended Addition |
|---|---|---|
| Entities | name, type, description | Add `embedding`, `confidence`, `first_seen`, `last_seen` |
| Relationships | source, target, relation, context | Add `valid_at`, `invalid_at`, `confidence`, `source_episode` |
| Preferences | subject, preference, confidence, reason | Extend to include `category` and `last_evidenced_at` |
| Facts | statement, source_context | Add `valid_at`, `invalid_at`, `confidence`, `extracted_by` |
| Decisions | decision, context, category | Add `outcome` (if known), `emotional_context` |
| Action Items | task, due_date, priority | Add `status`, `completed_at` |
| **Goals** | — | goal, category, horizon, status, created_at |
| **Emotional Context** | — | sentiment, dominant_emotion (on EpisodicNode) |
| **Skills** | — | skill, proficiency, context, last_evidenced_at |
| **Habits** | — | behavior, frequency, context, confidence |
| **Social Strength** | — | relationship_strength score on EntityEdge |

---

## 9. Recommendations and Implementation Roadmap

### 9.1. Immediate Priorities

The most impactful changes to the current system, in order of priority, are:

**Adopt Bitemporal Modeling on Facts and Relationships.** Adding `valid_at` and `invalid_at` fields to the facts and relationships tables is the single most important schema change. It enables temporal queries, prevents information loss when facts change, and creates the foundation for the edge invalidation pipeline. This is a schema migration that can be done incrementally.

**Decompose the Extraction Prompt into Modular Stages.** If the current system uses a single extraction prompt, decomposing it into separate entity extraction, deduplication, and fact extraction prompts will immediately improve quality and enable parallel execution. The Graphiti codebase (github.com/getzep/graphiti) is an excellent reference implementation.

**Implement a Three-Stage Deduplication Pipeline.** The combination of exact matching, embedding similarity, and LLM-based resolution will significantly reduce duplicate entities in the graph. The embedding-based stage requires `pgvector` to be installed and entity embeddings to be computed at ingestion time.

### 9.2. Medium-Term Enhancements

**Add Goals, Skills, and Habits as First-Class Categories.** These categories have the highest return on investment for downstream personalization and retrieval. Goals in particular are easy to extract and have immediate utility.

**Begin SFT Training on Accumulated Mismatch Pairs.** Once a few hundred mismatch pairs have been accumulated (the current 1,200 conversations should already provide this), a first round of SFT fine-tuning on the local Qwen model is warranted. The goal is to reduce the mismatch rate from its current level to below 10%, at which point DPO becomes the more appropriate tool.

**Implement Confidence Decay.** Adding a scheduled job that applies decay functions to fact confidence scores based on their age and type will improve the quality of the knowledge graph over time by surfacing stale information for review.

---

## References

[1] Jang, S., et al. (2025). *PersonaBench: Evaluating AI Models on Understanding Personal Information through Conversations*. arXiv. https://arxiv.org/html/2502.20616v2

[2] Rasmussen, P., Paliychuk, P., Beauvais, T., Ryan, J., & Chalef, D. (2025). *Zep: A Temporal Knowledge Graph Architecture for Agent Memory*. arXiv. https://arxiv.org/html/2501.13956v1

[3] Schema.org. (n.d.). *Person*. Schema.org. https://schema.org/Person

[4] Anokhin, P., et al. (2024). *AriGraph: Learning Knowledge Graph World Models with Episodic Memory for LLM Agents*. arXiv. https://arxiv.org/abs/2407.04363

[5] Rasmussen, P. (2024, September 12). *Scaling LLM Data Extraction: Challenges, Design decisions, and Solutions*. Zep Blog. https://blog.getzep.com/llm-rag-knowledge-graphs-faster-and-more-dynamic/

[6] mate_0107. (2025, October 26). *Lessons from building a knowledge graph memory system with 10M+ nodes*. Reddit r/singularity. https://www.reddit.com/r/singularity/comments/1pn803k/lessons_from_building_a_knowledge_graph_memory/

[7] Pavlyshyn, V. (2024, September 2). *Time-Aware Personal Knowledge Graphs*. Medium. https://volodymyrpavlyshyn.medium.com/time-aware-personal-knowledge-graphs-b5c5c752e71e

[8] OpenAI. (2025). *Temporal Agents with Knowledge Graphs*. OpenAI Cookbook. https://developers.openai.com/cookbook/examples/partners/temporal_agents_with_knowledge_graphs/temporal_agents/

[9] Supabase. (2024). *Postgres as a Graph Database: Using pgRouting*. Supabase Blog. https://supabase.com/blog/pgrouting-postgres-graph-database

[10] Yáñez Romero, F. (2026, January 15). *Why LLMs Fail at Knowledge Graph Extraction (And What Works Instead)*. Towards AI. https://pub.towardsai.net/why-llms-fail-at-knowledge-graph-extraction-and-what-works-instead-dcb029f35f5b

[11] Huang, Y., Tang, K., & Chen, M. (2024). *Distilling Large Language Models into Tiny Models for Named Entity Recognition*. arXiv. https://arxiv.org/html/2402.09282v3

[12] Davlatova, S. (2026, February 6). *SFT vs DPO: Fine-Tuning Strategies for LLMs*. LinkedIn. https://www.linkedin.com/posts/shahzodadavlatova_dpo-vs-sft-fine-tuning-when-people-say-fine-tuning-activity-7425577728902561792-yRl5

[13] Shereshevsky, A. (2026, January 21). *Entity Resolution at Scale: Deduplication Strategies for Knowledge Graph Construction*. Medium. https://medium.com/graph-praxis/entity-resolution-at-scale-deduplication-strategies-for-knowledge-graph-construction-7499a60a97c3

[14] Mem0. (n.d.). *Memory Types*. Mem0 Documentation. https://docs.mem0.ai/core-concepts/memory-types

[15] Weave, D. (2025, December 11). *GraphRAG on Postgres: A Builder's Guide*. Medium. https://medium.com/@duckweave/graphrag-on-postgres-a-builders-guide-1c6d2ecf2eed

[16] Getzep. (2024). *Graphiti: A Python library for building and querying temporally-aware knowledge graphs*. GitHub. https://github.com/getzep/graphiti

[17] Polat, F., et al. (2023). *Testing Prompt Engineering Methods for Knowledge Graph Extraction*. Semantic Web Journal. https://www.semantic-web-journal.net/system/files/swj3606.pdf

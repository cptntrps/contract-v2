# Synthesis of Research on Personal Knowledge Graph Systems

**Author:** Manus AI
**Date:** February 23, 2026

---

## 1. Introduction

This document synthesizes the findings from two independent research reports on the design and implementation of a personal knowledge graph (PKG) system. The goal is to provide a single, unified set of recommendations that integrates the overlapping consensus and highlights the unique insights from each report. The core architecture—a local-first, two-stage extraction pipeline with a powerful API-based model reviewing the outputs of a smaller local model—is strongly validated by both research streams. This synthesis provides a consolidated, actionable roadmap for building a robust and scalable personal knowledge OS.

---

## 2. Synthesized Schema and Ontology Design

There is a strong consensus on the principles of schema design for a personal knowledge graph. Both reports advocate for a small, stable, and opinionated core ontology, extended with flexibility for user-specific concepts.

### 2.1. Unified Core Ontology

Combining the recommendations, the following unified ontology represents a best-practice starting point:

*   **Core Entity Types:** PERSON, ORGANIZATION, PLACE, PROJECT, EVENT, DOCUMENT, TECHNOLOGY/TOOL, CONCEPT/TOPIC, TASK, GOAL.
*   **Core Relationship Predicates:** A small, canonical set including `works_at`, `lives_in`, `manages`, `part_of`, `authored_by`, `depends_on`, and `uses`.
*   **Flexible Relationships:** For all other connections, use a free-form verb as the `relation`, but add a `relation_category` (e.g., `social`, `structural`, `cognitive`) for semantic grouping, as suggested by the Perplexity report.

### 2.2. The Three-Layer Graph Model

The Manus AI report, drawing from the Zep/Graphiti architecture, recommends a three-layer model that is a critical architectural insight:

1.  **Episodic Layer:** Stores raw, immutable source data (e.g., a conversation transcript) as an `EpisodicNode`.
2.  **Semantic Layer:** Stores the clean, deduplicated, and structured knowledge (e.g., `EntityNode`s and `EntityEdge`s) extracted from the episodic layer.
3.  **Community Layer:** Higher-order clusters of related entities, generated periodically to summarize patterns.

This layered approach is crucial because it separates the raw data from the extracted knowledge, allowing the semantic layer to be rebuilt or corrected without losing the original source material.

---

## 3. Consolidated Temporal Modeling Strategy

Both reports are in complete agreement on the necessity and implementation of temporal modeling.

*   **Bitemporal Edges:** The consensus is to implement bitemporal modeling directly on the graph edges. Every fact or relationship should have four temporal fields: `valid_from`, `valid_to`, `asserted_at` (transaction time), and `expired_at` (for database-level invalidation).
*   **Contradiction Handling:** When a new fact contradicts an old one, the system must **never delete** the old fact. Instead, it should close the validity interval of the old fact by setting its `valid_to` timestamp to the `valid_from` timestamp of the new, superseding fact. This preserves a complete and queryable history.
*   **Dedicated Invalidation Pipeline:** The process of detecting and handling contradictions should be a separate, dedicated stage in the extraction pipeline, triggered after new facts are extracted.

---

## 4. Unified Entity Resolution and Deduplication Pipeline

Both reports recommend an identical, three-stage hybrid pipeline for entity resolution, which is the clear industry best practice for this scale.

1.  **Stage 1: Candidate Generation (Blocking):** Use normalized string matching on names and aliases to find cheap, exact matches.
2.  **Stage 2: Scoring (Embeddings + Rules):** For remaining candidates, combine semantic similarity from embeddings (via `pgvector`) with lexical similarity (e.g., Levenshtein) and structured rules (e.g., shared location or organization).
3.  **Stage 3: Arbitration (LLM):** For ambiguous cases that fall within a certain confidence band, use a powerful LLM (Claude Sonnet) to make the final binary decision (`is_duplicate: true/false`) and synthesize a merged summary.

Both reports also emphasize that this process should be run **asynchronously** to avoid blocking the ingestion pipeline.

---

## 5. Integrated Recommendations for Extraction and Training

### 5.1. Multi-Pass, Modular Prompting

There is a strong consensus against using a single, monolithic extraction prompt. The recommended architecture is a multi-pass pipeline of small, single-purpose prompts:

1.  **Entity Extraction:** Extract all potential entities from the text.
2.  **Entity Deduplication:** For each new entity, run the three-stage resolution pipeline.
3.  **Fact/Relationship Extraction:** Extract relationships between the now-resolved entities.
4.  **Temporal Dating & Invalidation:** Identify temporal triggers and close out old fact intervals.

### 5.2. Schema-First, Validated JSON Output

Both reports highlight the importance of treating the JSON schema as a strict contract. The prompts must be “schema-first,” providing the LLM with both a natural language description and examples. The output must then be programmatically validated against a JSON Schema (using a library like Pydantic). The Perplexity report adds a crucial step: if validation fails, the validator model should be re-invoked with the original text, the invalid JSON, and the specific validation errors, and asked to repair it.

### 5.3. SFT First, then DPO for Distillation

Both reports agree on the fine-tuning strategy:

*   **Supervised Fine-Tuning (SFT):** This is the primary method. The local model should be fine-tuned on `(conversation_text, claude_corrected_json)` pairs. This is the most direct way to teach the model the correct output format and schema.
*   **Direct Preference Optimization (DPO):** This should be used as a secondary step to refine the model. The mismatch pairs `(conversation_text, local_model_output, claude_corrected_output)` are perfect for DPO, teaching the model to prefer the corrected version.

The Perplexity report adds the valuable insight of **rationale distillation**: training the local model to generate not just the final JSON, but also a brief step-by-step rationale for its extractions. This has been shown to improve performance and interpretability.

---

## 6. Comprehensive List of Additional Knowledge Categories

By combining the recommendations from both reports, a comprehensive list of high-value knowledge categories to add to the schema emerges:

*   **Goals & Aspirations:** A first-class entity type to track the user’s long-term objectives.
*   **Habits & Routines:** Recurring behaviors, likely extracted via periodic batch analysis rather than per-conversation.
*   **Skills & Competencies:** The user’s skills, proficiency levels, and the projects where they are applied.
*   **Emotional & Motivational Context:** The emotional tone of conversations and the satisfaction/regret associated with past decisions.
*   **Social Graph Dynamics:** The type and strength of relationships between people.

---

## 7. Final Recommendations on Storage and Models

*   **Storage:** Both reports unequivocally recommend **Postgres with an adjacency list model** for this scale. The combination of `pgvector` for similarity search and recursive CTEs for graph traversal is sufficient. The complexity of a dedicated graph database is not warranted.
*   **Local Models:** The Perplexity report provides a more detailed, tiered recommendation for local models that is highly practical: a **Qwen2.5-7B** model for fast, first-pass extraction; a more powerful **14B model (Qwen or DeepSeek)** for the reasoning-intensive tasks of disambiguation and temporal updates; and a tiny **1.5B/3B model** for simple routing and classification tasks. A **Llama 3.1 8B** model is recommended for the user-facing summarization layer.

This synthesized roadmap provides a clear, actionable, and research-backed path forward for the development of the LivingOS personal knowledge graph.

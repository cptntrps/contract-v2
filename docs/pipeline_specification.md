# Prescriptive Specification: Personal Knowledge Graph Extraction Pipeline

**Version:** 1.0
**Author:** Manus AI
**Date:** February 23, 2026

---

## 1. Overview

This document provides a prescriptive, implementation-ready specification for an 8-stage asynchronous pipeline to extract structured knowledge from AI conversations and populate a personal knowledge graph stored in Postgres. This specification is intended to be used by an AI developer (e.g., Claude) to construct the Python code for the system.

The pipeline is designed to be modular, robust, and cost-effective, leveraging small, local LLMs for the majority of the workload and a powerful, API-based LLM for review and arbitration of ambiguous cases.

---

## 2. Core Data Models

All data structures should be implemented using Pydantic for schema validation.

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from datetime import datetime
import uuid

# --- Database Models ---

class KGNode(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    type: str
    summary: str
    embedding: List[float]
    aliases: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = Field(default_factory=dict)

class KGEdge(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_id: uuid.UUID
    target_id: uuid.UUID
    relation: str
    fact: str
    confidence: float = 0.8
    source_episode_id: uuid.UUID
    is_inferred: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expired_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    metadata: Dict = Field(default_factory=dict)

# --- Extraction Payload Models ---

class ExtractedEntity(BaseModel):
    local_id: str # e.g., "e1", "e2"
    name: str
    type: Literal['PERSON', 'ORGANIZATION', 'PLACE', 'PROJECT', 'EVENT', 'DOCUMENT', 'TECHNOLOGY', 'CONCEPT', 'TASK', 'GOAL']
    description: str
    source_span: str

class ExtractedRelationship(BaseModel):
    source_local_id: str
    target_local_id: str
    relation: str
    fact: str
    is_inferred: bool = False
    source_span: str

class FullExtractionPayload(BaseModel):
    schema_version: str = "1.0"
    entities: List[ExtractedEntity]
    relationships: List[ExtractedRelationship]
    # ... other categories like preferences, decisions, etc.
    needs_review: bool = False
    review_reason: Optional[str] = None
```

---

## 3. Pipeline Stages

### Stage 1: Segmentation

**Purpose:** To break down a raw conversation transcript into logically coherent, processable chunks called "episodes."

*   **Input:** Raw conversation text (e.g., from Claude, ChatGPT).
*   **Process:**
    1.  Identify the boundaries between user and assistant turns.
    2.  Group turns into sessions based on time. A new session begins if there is a gap of more than 60 minutes between turns.
    3.  Each session becomes a single `Episode` to be processed by the pipeline.
    4.  Store the raw episode text in an `episodes` table in Postgres, which will be referenced by `source_episode_id` in the `KGEdge` model.
*   **Output:** A list of `Episode` objects, each containing the text and metadata (e.g., `conversation_id`, `timestamps`).

---

### Stage 2: Entity Extraction

**Purpose:** To identify all potential entities mentioned in an episode.

*   **Input:** The text of a single `Episode`.
*   **Process:**
    1.  Construct a prompt for the local LLM (Qwen2.5-7B) that instructs it to extract all entities according to the `ExtractedEntity` Pydantic model.
    2.  The prompt must explicitly state the 10 allowed entity types and instruct the model to assign a `local_id` (e.g., "e1", "e2") to each unique entity within the text.
    3.  The prompt must include a rule: "Only extract entities that have a proper name or a stable, unique identifier. Do not extract vague references like 'my friend' or 'the project' unless they are given a specific name."
    4.  Execute the LLM call.
*   **Output:** A list of `ExtractedEntity` objects.

    *   **Example:** `[ExtractedEntity(local_id="e1", name="John", type="PERSON", ...), ExtractedEntity(local_id="e2", name="Acme Corp", type="ORGANIZATION", ...)]`

`
      ...)]`

---

### Stage 3: Entity Deduplication

**Purpose:** To resolve each extracted candidate entity to a canonical node in the knowledge graph, either by matching it to an existing node or creating a new one.

*   **Input:** The list of `ExtractedEntity` objects from Stage 2.
*   **Process:**
    1.  This stage **must be executed in parallel** for each `ExtractedEntity` in the input list.
    2.  For each entity, perform the following three-step resolution process:
        *   **Step A: Candidate Generation (Embedding Search):**
            *   Generate an embedding for the entity's `name` and `description`.
            *   Query the `kg_nodes` table in Postgres using `pgvector` to find the top 5 most similar nodes of the same `type`.
        *   **Step B: Decision by Threshold:**
            *   Let `max_similarity` be the similarity score of the top candidate from Step A.
            *   If `max_similarity >= 0.95`, consider it an **automatic match**. The entity is resolved to this existing node's ID.
            *   If `max_similarity < 0.75`, consider it a **new entity**. A new node will be created.
            *   If `0.75 <= max_similarity < 0.95`, the match is **ambiguous**. Proceed to Step C.
        *   **Step C: LLM Arbitration (for ambiguous cases only):**
            *   Construct a prompt for the arbitration LLM (Qwen2.5-14B or Claude Sonnet) containing the `name` and `description` of the new entity and the `name` and `summary` of the candidate existing entity.
            *   The prompt must ask for a JSON output: `{ "is_duplicate": true/false, "existing_id": "...", "merged_summary": "..." }`.
            *   If `is_duplicate` is true, the entity is resolved to the `existing_id`. The node's `summary` in the database should be updated with the `merged_summary`.
*   **Output:** A dictionary mapping each `local_id` from Stage 2 to a canonical `uuid.UUID` from the `kg_nodes` table. This is the **Resolved Entity Map**.

    *   **Example:** `{"e1": UUID('...'), "e2": UUID('...')}`

---

### Stage 4: Fact & Relationship Extraction

**Purpose:** To extract the relationships *between* the now-resolved entities.

*   **Input:**
    1.  The original `Episode` text.
    2.  The **Resolved Entity Map** from Stage 3.
*   **Process:**
    1.  Construct a prompt for the local LLM (Qwen2.5-7B).
    2.  The prompt must include the full episode text and the full Resolved Entity Map.
    3.  The core instruction is: "Extract all relationships explicitly stated in the text that connect the entities listed in the resolved map. Use their canonical IDs. Do not invent relationships that are not directly stated."
    4.  The prompt must request output conforming to the `ExtractedRelationship` Pydantic model, using the `local_id`s for `source_local_id` and `target_local_id`.
    5.  This stage can be run in parallel with the extraction of other categories like `preferences`, `decisions`, and `action_items`, as they all depend on the same inputs.
*   **Output:** A list of `ExtractedRelationship` objects.

---

### Stage 5: Temporal Dating

**Purpose:** To assign temporal validity (`valid_from`, `valid_to`) to all extracted facts and relationships.

*   **Input:** The list of `ExtractedRelationship` and other fact-based objects from Stage 4.
*   **Process:**
    1.  Construct a prompt for the local LLM (Qwen2.5-7B).
    2.  The prompt includes the original episode text and the extracted facts.
    3.  The instruction is: "For each fact, identify if a specific date or time is mentioned. If so, populate the `valid_from` field. If the text indicates a fact is no longer true (e.g., 'I used to work at...'), populate the `valid_to` field. If no temporal information is present, leave the fields as null."
*   **Output:** The same list of fact/relationship objects, but with temporal fields populated where applicable.

---

### Stage 6: Contradiction & Invalidation

**Purpose:** To identify and mark existing knowledge in the graph that is contradicted by the new extractions.

*   **Input:** The temporally-dated facts from Stage 5.
*   **Process:**
    1.  For each new fact that has a `valid_from` date, query the `kg_edges` table for existing facts with the same `source_id` and `relation` that are currently active (`valid_to IS NULL`).
    2.  If a potential conflict is found, construct a prompt for the arbitration LLM (Qwen2.5-14B) with the old fact and the new fact.
    3.  The prompt asks: "Does the new fact contradict and supersede the old fact? Return JSON: `{"is_contradiction": true/false}`.
    4.  If `is_contradiction` is true, add the `id` of the old edge to a list of edges to be invalidated.
*   **Output:** A list of `uuid.UUID`s corresponding to the `KGEdge`s that need to be updated.

---

### Stage 7: Schema Validation & Repair

**Purpose:** To ensure the final extracted payload is 100% schema-conformant before writing to the database.

*   **Input:** The complete `FullExtractionPayload` object containing all entities, relationships, and other extracted data.
*   **Process:**
    1.  Attempt to parse the entire JSON payload using the `FullExtractionPayload` Pydantic model.
    2.  **If validation succeeds:** Proceed to Stage 8.
    3.  **If validation fails:**
        *   Construct a prompt for the repair LLM (Claude Sonnet).
        *   The prompt must include: the original episode text, the invalid JSON produced by the local models, and the specific validation error message from Pydantic.
        *   The instruction is: "Repair the provided JSON to make it conform to the schema, using the original text as context. Do not add or remove information unless it is necessary to fix the error."
        *   Use the repaired JSON as the final output.
*   **Output:** A single, validated `FullExtractionPayload` object.

---

### Stage 8: Upsert to Postgres

**Purpose:** To atomically write the final, validated knowledge to the database.

*   **Input:**
    1.  The validated `FullExtractionPayload`.
    2.  The list of edge IDs to invalidate from Stage 6.
*   **Process:**
    1.  Open a single database transaction.
    2.  For each new entity that was created in Stage 3, insert a new row into the `kg_nodes` table.
    3.  For each resolved entity that was merged, update its `summary` and `aliases` in the `kg_nodes` table.
    4.  For each `ExtractedRelationship`, insert a new row into the `kg_edges` table, using the canonical IDs from the Resolved Entity Map.
    5.  For each edge ID in the invalidation list, update its `valid_to` field to the `valid_from` of the new, superseding edge.
    6.  Commit the transaction.
*   **Output:** A successfully populated and consistent knowledge graph.

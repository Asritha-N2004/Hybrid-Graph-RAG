# Research architecture

See [the system diagram](../docs/system_architecture.md) for the implemented pipeline. The research hypothesis is that combining independently scored lexical, vector and relational evidence can improve retrieval for product constraints while preserving an auditable connection between answers and sources.

The experimental system separates retrieval quality from source support. A high source-support fraction cannot establish answer relevance, completeness, real-world truth, or semantic understanding. Ten agents are executable task functions coordinated by LangGraph; they are not ten independently trained language models. Query understanding and reasoning are deterministic constraint processing unless the optional LLM selection stage is configured.

The graph exposes a one-hop product neighborhood and explicit similarity links. Multi-hop free-form Cypher planning is not implemented. Product schema entities are resolved by exact ID and known name; general entity linking remains future work.

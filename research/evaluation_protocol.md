# Evaluation protocol

The Evaluation Center runs 20 executions: keyword, vector, graph and hybrid methods, each over five queries, K=5. Ground truth is all synthetic product IDs meeting the category and numeric/exact requirements stated for each case. Queries include RAM/storage, machine-learning GPU-memory heuristic, smartphone RAM, headphone battery, and price constraints.

Precision@K is relevant retrieved products / K. Recall@K is relevant retrieved products / all relevant products. MRR is the reciprocal rank of the first relevant product, zero if absent. Results are macro averaged per method. Product IDs are deduplicated before scoring; canonical evidence added to substantiate a product does not inflate product counts.

Context precision and recall are explicitly **product-level relevance proxies**, using the same relevant-product labels. They are not RAGAS chunk-level judgments. Evidence coverage is the supported rendered claim fraction checked against source identity and value. It is not completeness or a confidence probability.

Retrieval latency sums node execution durations for graph/vector/keyword/fusion; because branches run in parallel this is work duration, not critical-path wall-clock latency. Response latency is wall-clock elapsed time through the workflow. No synthetic latency is displayed.

Faithfulness and answer relevance remain null with a `not_run` explanation unless an independent evaluator is implemented and configured. `requirements-ai.txt` includes RAGAS as an optional research dependency; installing it does not automatically produce valid evaluations. Human-reviewed references, a separate judge configuration, budget controls, and recorded evaluator versions are needed for that extension.

Do not use this intentionally small benchmark to prove hybrid superiority. Structured filtering is applied consistently to every retriever and makes constraint satisfaction easy. Extend with unseen products, aliases, negative constraints, unstructured contradictory sources, paraphrases, hard negatives, graded relevance and independent human judgments. Freeze data and query sets, retain individual results, and bootstrap confidence intervals for comparative reporting.

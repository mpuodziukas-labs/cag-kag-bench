### Test-split results

Corpus: 60 docs. Questions: 50 dev, 50 test (seeded 50/50 split). Only the 50 test questions are reported. RAG parameters were tuned on dev only: top_k=8, k1=0.9, b=0.4 (dev exact match 34/50).

Exact match, with Wilson 95% intervals in brackets:

| method | overall | single-hop | multi-hop | 1-hop | 2-hop | 3-hop |
|---|---|---|---|---|---|---|
| RAG | 0.6200 [0.4815, 0.7414] (31/50) | 1.0000 [0.8865, 1.0000] (30/30) | 0.0500 [0.0089, 0.2361] (1/20) | 1.0000 [0.8865, 1.0000] (30/30) | 0.0909 [0.0162, 0.3774] (1/11) | 0.0000 [0.0000, 0.2992] (0/9) |
| CAG | 1.0000 [0.9286, 1.0000] (50/50) | 1.0000 [0.8865, 1.0000] (30/30) | 1.0000 [0.8389, 1.0000] (20/20) | 1.0000 [0.8865, 1.0000] (30/30) | 1.0000 [0.7412, 1.0000] (11/11) | 1.0000 [0.7008, 1.0000] (9/9) |
| KAG | 1.0000 [0.9286, 1.0000] (50/50) | 1.0000 [0.8865, 1.0000] (30/30) | 1.0000 [0.8389, 1.0000] (20/20) | 1.0000 [0.8865, 1.0000] (30/30) | 1.0000 [0.7412, 1.0000] (11/11) | 1.0000 [0.7008, 1.0000] (9/9) |

Evidence: supporting-doc recall is the share of gold supporting docs the method surfaced to its answerer (RAG: retrieved docs; CAG: docs packed into the context; KAG: docs behind the edges it walked).

| method | supporting-doc recall | mean context tokens | refused |
|---|---|---|---|
| RAG | 0.8067 | 122.8 | 19 |
| CAG | 1.0000 | 990.0 | 0 |
| KAG | 1.0000 | 24.0 | 0 |

CAG context budget 4000 whitespace tokens, 60 of 60 docs packed. Answer cache hit rate: cold pass 0.0000, warm pass 1.0000, overall 0.5000. Per-query wall time is printed by bench.py and not stored, because it is not deterministic.

What the numbers say:

- multi-hop test: KAG 1.0000 vs RAG 0.0500; KAG higher; 95% intervals do not overlap.
- single-hop test: KAG 1.0000 vs RAG 1.0000; equal; 95% intervals overlap.
- Expected KAG above RAG on multi-hop: HELD.
- Expected RAG matching KAG on single-hop (intervals overlap): HELD.

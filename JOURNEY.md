
# PCC — The Journey

**Alejandro Garay | July 2025**

---

## Context & Mandate

When GDPR/CCPA case classification at Spotify was a brittle SQL query, I was tasked not just with automating, but with architecting a robust, auditable, and extensible system. The goal: bridge legal, technical, and operational worlds, and deliver a solution that would stand up to scrutiny from both compliance and engineering.

---

## Architecture: Building for Trust

PCC is a modular, testable pipeline—ingestion, preprocessing, inference, postprocessing, monitoring—each stage designed for transparency and swappability. Every assumption is explicit; every output is schema-validated and versioned. The design is documented in detail in the [PCC Blueprint](Documentation/PCC.pdf), which serves as both a technical and organizational contract.

---

## Communication: Legal Analogies & Stakeholder Buy-In

To win trust, I used analogies: “Think of the model as a legal triage nurse—screening, not judging.” This framing, detailed in the [Legal Analogy documentation](Documentation/PCC_Legal%20Analogy.pdf), helped legal and ops teams understand and challenge the system constructively. The [FAISS Analogy](Documentation/Weak%20Labeling_FAISS%20Analogy.pdf) further demystified semantic search for non-technical audiences, likening it to an omniscient librarian who can find and relate every case in the corpus.

---

## Technical Challenges & Solutions

- **Data Scarcity:** With few labeled cases, I used SMOTE, semantic filtering, and weak labeling (see [Weak Labeling documentation](Documentation/PCC_Weak%20Labeling.pdf)) to build a meaningful training set. Clustering and semantic retrieval (via FAISS) made manual labeling more efficient and improved recall.
- **Auditability:** Every prediction is schema-compliant, logged, and versioned—no black boxes. The [Taxonomy documentation](Documentation/PCC_Taxonomy.pdf) brought operational clarity to ambiguous privacy-themed support cases.
- **Performance:** Even the MVP, trained on ~230 organic cases, achieved high recall and robust separation (see [Dev Results](Documentation/Dev_v0.1%20Results.pdf)).

---

## Results & Milestones

- **MVP Pipeline:** End-to-end, from BigQuery ingestion to schema-validated output, with Dockerized reproducibility and CI/CD foundations.
- **Model Performance:** ROC-AUC 0.998, F1 0.97 (see [model_analysis.ipynb](../docs/model_analysis.ipynb)).
- **Stakeholder Trust:** Regular demos, feedback loops, and living documentation. Each PDF in the Documentation folder is a snapshot of both technical and organizational learning.

---

## Learnings

- **Ownership:** Building ML infra means owning data, code, deployment, and comms.
- **Empathy:** The best solutions come from listening—analogies matter.
- **Iteration:** Progress is non-linear; breakthroughs follow setbacks.

---

## What’s Next

- Real data integration
- Embedding generation in-pipeline
- Orchestration, monitoring, and continuous delivery

---

*For more, see the Documentation folder:*
- **PCC.pdf:** Project overview and feasibility
- **Legal Analogy.pdf:** Non-technical system explanation
- **Dev_v0.1 Results.pdf:** MVP model results
- **Taxonomy, Weak Labeling, FAISS Analogy:** Deep dives into data and modeling strategies

---

**The journey is ongoing. The code is just the artifact.**

 
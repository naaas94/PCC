---
noteId: "55ee44405cc011f09e2863a97b2b4200"
tags: []

---

# PCC — The Journey

**Alejandro Garay | July 2025**

---

## Context

At Spotify, the “solution” for GDPR/CCPA case classification was a SQL query. It worked, but it was brittle, manual, and opaque. When the problem landed on my desk, I saw an opportunity: not just to automate, but to design something robust, transparent, and extensible — from scratch.

I wasn’t handed a blueprint. I had to envision the system, build it, and prove its value — technically and organizationally.

---

## The Build

- **From zero:** No pre-existing infra, no labeled data pipeline, no “ML platform” to lean on. Just a business problem and a blank slate.
- **Design:** I architected the Privacy Case Classifier (PCC) as a modular, testable pipeline: ingestion, preprocessing, inference, postprocessing, output, monitoring. Every assumption explicit, every component swappable.
- **Iteration:** The first version was simple — but every run, every failure, every edge case made it stronger. I learned to love the process, not just the result.

---

## Communication & Stakeholders

- **Bridging worlds:** Most stakeholders weren’t technical. I had to translate ML concepts into legal analogies for the head counsel and DPO, and make the case for why this mattered — not just for compliance, but for customer trust.
- **Storytelling:** I learned that a good analogy can open doors that technical specs never will. “Think of the model as a legal triage nurse — not a judge, but a first filter.”
- **Feedback loops:** Every demo, every question, every “what if?” from legal or ops made the system better. I learned to listen, not just explain.

---

## Technical Challenges

- **Data scarcity:** Labeled privacy cases were rare. I had to get creative: SMOTE for balancing, leveraging metadata, experimenting with meta-models, and even using FAISS for semantic search.
- **Validation:** Every prediction had to be auditable, every output schema-compliant. No black boxes.
- **Performance:** Early on, the model was already reliable for some subtypes (erasure, access/portability). That was a breakthrough — and a sign that the architecture was sound.

---

## Emotional Highs & Lows

- **Frustration:** There were days when nothing worked. When the data didn’t make sense, or the model failed silently. But every bug was a lesson.
- **Breakthrough:** The first wet run — seeing real predictions written to BigQuery, knowing they’d be used downstream — was pure adrenaline. I felt like a king.
- **Pride:** Not just in the code, but in the system: something only I could have envisioned, now running, making an impact.

---

## What I Learned

- **Ownership:** Building ML infra from scratch means owning every layer — data, code, deployment, and communication.
- **Empathy:** The best solutions come from listening, not just building.
- **Iteration:** Progress isn’t linear. The best breakthroughs come after the worst days.
- **Joy:** There’s nothing like seeing your vision, your system, up and running — and knowing it matters.

---

## What’s Next

- Real data integration
- Embedding generation as a pipeline step
- Orchestration, monitoring, and continuous delivery
- More learning, more building, more sharing

---

**This is the journey. The code is just the artifact.**

 
noteId: "80095e305cbc11f09e2863a97b2b4200"
tags: []

---

 
noteId: "80095e305cbc11f09e2863a97b2b4200"
tags: []

---

 
noteId: "80095e305cbc11f09e2863a97b2b4200"
tags: []

---

 
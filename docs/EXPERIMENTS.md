# Named experiments

Run `bash scripts/run_demo.sh` after cloning. To print the list without starting models, use `bash scripts/run_demo.sh --list`. Select **1** for preparation and **2** for the board report. Every implemented lab has a direct numbered entry; no letter or tour submenu is needed.

| Number | Experiment | Requirements |
|---|---|---|
| 3 | Offline Conversation Assistant | Core setup |
| 4 | Ask the Local Language Model | Core setup |
| 5 | Tokenization Microscope | Core setup |
| 6 | Structured Information Extraction | Core setup |
| 7 | Calculator Tool Assistant | Core setup |
| 8 | Class Notes Retrieval and Grounded Answers | Local text documents |
| 9 | Persistent Memory Assistant | Explicit fictional facts saved locally |
| 10 | TinyStories Generator | Core setup |
| 11 | Language Model Performance Benchmark | Core setup |
| 12 | Reproducible Prompt Evaluation | User-provided JSONL dataset |
| 13 | Camera Perception Lab | Compatible camera; includes vision installation |
| 14 | Sampling Playground | Compare greedy and two seeded creative outputs |
| 15 | Mission Control: Tool-Planning Assistant | Core setup |
| 16 | Document Detective: Answers with Evidence | Bundled fictional exhibit brief |
| 17 | Story Director: Audience-Controlled Fiction | Core setup |
| 18 | Scene Memory Detective | Prepared camera, fixed position |
| 19 | AI Visual Scavenger Hunt | Prepared camera and ordinary objects |
| 20 | Camera Change Journal | Prepared camera, fixed position |
| 22 | Prompt Design Studio | Compare minimal and audience-specific instructions |
| 23 | Few-Shot Pattern Learner | Compare zero examples with four examples |
| 24 | Message Triage Desk | JSON schema and validated category routing |
| 25 | Summary Fact Checker | Source, summary, and a separate model critique |
| 26 | Prompt Injection Defense Lab | Compare unprotected and separated instructions |
| 27 | Answer or Abstain | Known answer and deliberately missing evidence |
| 28 | Context Memory Challenge | Recall under increasing distractor text |
| 29 | Socratic Study Partner | A guided text conversation with follow-up questions |
| 30 | Mystery Character Interview | Interview a fictional character and guess the profession |

**21** runs the prepared student demonstrations in sequence. **0** exits. Ctrl+C cancels an active demo.

There are 27 named experiment entries, plus the optional sequence. The active scope is Nano plus optional camera only: no microphone, speaker, external GPU, training, cloud API, or power meter. The old 72-topic catalogue is a historical ideas reference; unsupported topics are excluded rather than presented as working demos. See [presentation coverage](CATALOGUE-COVERAGE.md) for the remaining implementation gaps and external-hardware requirements. No physical Nano validation has been performed here.

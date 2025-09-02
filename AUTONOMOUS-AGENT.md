# Building Autonomous AI Agents — README

This README captures the core content for the webinar **“Building Autonomous AI Agents”**.

---

## 1) What is an AI Agent?

An **AI agent** is a software system that **perceives** an environment (inputs/events), **reasons and plans** over internal state and goals, and **acts** through tools/APIs to change the environment. Modern agent stacks are typically LLM-centric with added planning, memory, tool-use, and feedback loops.

**Core capabilities**

- **Perception & state**: ingest events, documents, structured data; maintain short/long‑term memory.
- **Reasoning & planning**: goal decomposition, search, reflection, self‑critique, re‑planning.
- **Action & tools**: call tools/APIs, run code, query retrieval systems, operate browsers, etc.
- **Autonomy**: choose next actions without explicit step‑by‑step human prompts.
- **Learning/Adaptation**: update plans/memory and refine policies from feedback.

**Useful background**

- ReAct (Reason + Act) prompting: [https://arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629)
- Intelligent agents (foundations): [https://en.wikipedia.org/wiki/Intelligent_agent](https://en.wikipedia.org/wiki/Intelligent_agent)

---

## 2) Agents vs. Workflows (and when to use each)

**High‑level distinctions (body text)**

- **Agents** are **goal‑driven**, **stateful**, and **adaptive**. They handle ambiguity and open‑ended tasks with multi‑step reasoning and variable tool calls.
- **Workflows** are **deterministic graphs** (DAGs/state machines). They excel at compliance, scale, and repeatability for well‑specified processes.
- **Hybrid patterns** combine both: workflows provide guardrails, SLAs, and auditability; agents fill the reasoning/decision‑making gaps within nodes.

**Quick reference (phrases only)**

| Aspect         | AI Agent                                  | Workflow                      |
| -------------- | ----------------------------------------- | ----------------------------- |
| Decision       | Autonomous planning                       | Predefined path               |
| Flexibility    | Adapts to novel inputs                    | Rigid / versioned             |
| Explainability | Chain‑of‑thought & traces (often noisy) | Explicit steps / logs         |
| Best for       | Open‑ended; long‑horizon; R&D           | High‑volume, well‑specified |

**Rule of thumb**

- Use **agents** for **ambiguous** problems, evolving context, and tool orchestration with uncertain branches.
- Use **workflows** for **repeatable** tasks, SLAs, compliance, and when failure modes must be tightly bounded.
- Use **hybrids** for **mission‑critical** systems: put the agent *inside* workflow nodes; keep observability, rate limits, and circuit breakers at the workflow layer.

---

## 3) Deep Agents

**Idea**: Architect agents for **long‑horizon, multi‑stage** tasks by making planning and state *first‑class*.

**Key ingredients**

- **System role & contract**: concise “who am I / what are my powers / what are my boundaries”.
- **Planner**: explicit task graph (sub‑goals, milestones, dependencies); revise plans as evidence changes.
- **Sub‑agents** (see next section): delegate specialist subtasks; parallelize where safe.
- **Persistent memory**: task files, artifacts, scratchpads, episodic logs; retrieval‑augmented context.
- **Self‑monitoring**: reflection, test‑time feedback, and success criteria checks.

**Patterns that help**

- ReAct / ToT / Reflexion / Planner‑Executor loops.
- Cached tool schemas, typed arguments, and structured outputs (JSON/JSON‑Schema).
- Checkpointing (save/restore partial progress).

---

## 4) Sub‑Agents & Multi‑Agent Systems

**Sub‑agents** are specialised agents **supervised** by a coordinator/supervisor agent. They enable **specialisation**, **parallelism**, and **modularity**.

**Common topologies**

- **Supervisor ⇄ Specialists**: one coordinator decomposes goals and aggregates results.
- **Peer network**: agents negotiate and critique each other (debate / consensus).
- **Pipelines**: writer → reviewer → executor (explicit hand‑off contracts).
- **Graph orchestration**: an agent graph (with memory edges) built using a framework (e.g., LangGraph).

**Design notes**

- Define **roles**, **SLAs**, **handoff contracts**, and **termination criteria**.
- Enforce **isolation** (tool scopes, credentials, quotas) per sub‑agent.
- Add **traces**: capture messages, tool IO, and artifacts for later replay / audits.

---

## 5) Generative AI vs. AI Agent vs. Agentic AI

| Dimension     | Generative AI               | AI Agent                | Agentic AI (Systems)                           |
| ------------- | --------------------------- | ----------------------- | ---------------------------------------------- |
| Scope         | One‑shot output            | Single task with tools  | Multi‑agent**workflows** / end‑to‑end |
| Autonomy      | Low (prompt‑bound)         | Medium (plan + tools)   | High (coordinated teams of agents)             |
| Memory        | Context window only         | Short/long‑term memory | Shared memories & artifacts                    |
| Orchestration | None                        | Planner/Executor        | Scheduler/Coordinator + messaging              |
| Examples      | Prompt → answer/image/code | Researcher w/ tools     | Supervisor + specialists + evaluators          |

---

## 6) Architecture blueprint (practical)

**A. Interfaces**

- **Inputs**: user goal, constraints, existing artifacts, corpora, telemetry.
- **Outputs**: artifacts (docs/code), decisions, structured reports, traces.

**B. Core runtime**

- **Planner** (task graph), **Executor** (tool router), **Critic** (self‑check), **Memory** (RAG + scratchpads), **Policy** (guardrails).

**C. Tools layer**

- Retrieval/search, web/browse, data wrangling, code‑exec/sandboxes, connectors (Git/Jira/Notion/etc.), evaluation harnesses.

**D. Persistence & observability**

- Vector/SQL stores, artifact FS, run registry; traces, metrics (latency, cost, success@k), dashboards.

**E. Governance**

- Identity & scopes, rate limits and budgets, escalation paths, human‑in‑the‑loop check‑points.

---

## 7) Evaluation & Observability

- **Task success**: exact‑match or graded rubrics; pass@k, BLEU/ROUGE for text when appropriate.
- **Process metrics**: steps taken, tool accuracy, correction rate, re‑plan frequency.
- **Cost & latency**: tokens, tool calls, wall‑clock; regressions over time.
- **Safety**: jailbreak checks, data‑leakage probes, policy violations; red‑team suites.
- **A/B & canaries**: compare planners/policies/LLMs; maintain golden test sets and fixtures.

---

## 8) Safety & Guardrails (must‑haves)

- **Least‑privilege tool scopes**; rotate keys; sandbox code exec.
- **Deterministic containment** for workflow edges (timeouts, retries, circuit breakers).
- **Content & data policies** (PII handling, compliance); redact/segment memory.
- **Human‑in‑the‑loop** for critical actions; require approvals on spend or external effects.
- **Transparent traces** for audits; protect logs and artifacts.

---

## 9) Choosing a Framework / Stack

Well‑supported, production‑ready options to consider (pick 1–2 and go deep):

- **LangGraph (LangChain)** — typed agent graphs, supervisors, checkpoints, and persistence.[https://langchain-ai.github.io/langgraph/](https://langchain-ai.github.io/langgraph/)
- **AutoGen (Microsoft)** — multi‑agent conversation + tool usage; research‑friendly.[https://microsoft.github.io/autogen/](https://microsoft.github.io/autogen/)
- **CrewAI** — opinionated “crew” (roles/tasks/tools) abstraction for multi‑agent setups.[https://docs.crewai.com/](https://docs.crewai.com/)
- **LlamaIndex** — strong RAG/memory layer with agent abstractions.
  [https://docs.llamaindex.ai/en/stable/understanding/agent/](https://docs.llamaindex.ai/en/stable/understanding/agent/)

**Classic papers & patterns**

- ReAct (actions interleaved with reasoning): [https://arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629)
- Reflexion (test‑time self‑improvement): [https://arxiv.org/abs/2303.11366](https://arxiv.org/abs/2303.11366)
- Tree‑of‑Thought (structured search/planning): [https://arxiv.org/abs/2305.10601](https://arxiv.org/abs/2305.10601)

---

## 10) Implementation checklist (quick)

- [ ] Define **goal**, **constraints**, **KPIs**, and **fail‑safes**.
- [ ] Choose framework; **scaffold** planner/executor/critic; add **memory**.
- [ ] Model/tool **contracts** (JSON schemas) and **typed** tool adapters.
- [ ] Add **sub‑agents** where specialization yields clear wins; define SLAs.
- [ ] Wire **observability** (traces, metrics, run registry).
- [ ] Build **eval harness** + golden tasks; add canaries.
- [ ] Introduce **guardrails** (limits, approvals, sandboxing).
- [ ] Run **canary pilots**; iterate on plans, memories, and tool quality.

---

## 11) References & Further Reading

- LangGraph (multi‑agent graphs): [https://langchain-ai.github.io/langgraph/](https://langchain-ai.github.io/langgraph/)
- AutoGen framework: [https://microsoft.github.io/autogen/](https://microsoft.github.io/autogen/)
- CrewAI docs: [https://docs.crewai.com/](https://docs.crewai.com/)
- LlamaIndex agents: [https://docs.llamaindex.ai/en/stable/understanding/agent/](https://docs.llamaindex.ai/en/stable/understanding/agent/)
- ReAct: [https://arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629)
- Reflexion: [https://arxiv.org/abs/2303.11366](https://arxiv.org/abs/2303.11366)
- Tree‑of‑Thought: [https://arxiv.org/abs/2305.10601](https://arxiv.org/abs/2305.10601)
- AutoGPT (historical): [https://github.com/Significant-Gravitas/AutoGPT](https://github.com/Significant-Gravitas/AutoGPT)
- BabyAGI (historical): [https://github.com/yoheinakajima/babyagi](https://github.com/yoheinakajima/babyagi)

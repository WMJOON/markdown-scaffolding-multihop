## Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers

Pengfei Du1 1 Hong Kong Research Institute of Technology, HongKong, China E-mail: lldpf1234@gmail.com

# arXiv:2603.07670v1[cs.AI]8 Mar 2026

### Abstract

Large language model (LLM) agents increasingly operate in settings where a single context window is far too small to capture what has happened, what was learned, and what should not be repeated. Memory—the ability to persist, organize, and selectively recall information across interactions—is what turns a stateless text generator into a genuinely adaptive agent. This survey offers a structured account of how memory is designed, implemented, and evaluated in modern LLM-based agents, covering work from 2022 through early 2026. We formalize agent memory as a write–manage–read loop tightly coupled with perception and action, then introduce a threedimensional taxonomy spanning temporal scope, representational substrate, and control policy. Five mechanism families are examined in depth: context-resident compression, retrieval-augmented stores, reflective self-improvement, hierarchical virtual context, and policy-learned management. On the evaluation side, we trace the shift from static recall benchmarks to multi-session agentic tests that interleave memory with decision-making, analyzing four recent benchmarks that expose stubborn gaps in current systems. We also survey applications where memory is the differentiating factor—personal assistants, coding agents, open-world games, scientific reasoning, and multi-agent teamworkand address the engineering realities of write-path filtering, contradiction handling, latency budgets, and privacy governance. The paper closes with open challenges: continual consolidation, causally grounded retrieval, trustworthy reflection, learned forgetting, and multimodal embodied memory.

Keywords: large language model agents; agent memory; long-term memory; retrieval-augmented generation; continual adaptation; agent evaluation

### 1 Introduction

Scaling large language models has unlocked a new class of autonomous software agents—systems that perceive environments, reason about goals, wield tools, and take action over extended time horizons [Brown et al., 2020, Achiam et al., 2023, Touvron et al., 2023]. What separates these agents from a vanilla chatbot is not merely bigger models; it is the expectation that they learn from experience. A coding assistant should remember that a particular API is flaky, a game-playing agent should recall which crafting recipes it already mastered, and a personal scheduler should never ask

a user’s birthday twice. All of this demands memory.

#### 1.1 What goes wrong without it

Picture a debugging assistant that works on a large codebase across a week of sessions. Without memory, every Monday morning it rediscovers the directory layout, re-reads the same README, and—worst of all—retries the exact fix that crashed the build on Friday. Equip the same agent with even a modest memory module and the dynamic shifts: it arrives already knowing the hotspots, skips the dead ends, and gradually distills project-specific heuristics.

This is not a marginal improvement; it is a qualitative change. Memory transforms a stateless LLM into a selfevolving agent [Zhang et al., 2024a] that can (i) accumulate factual knowledge and user preferences, (ii) develop behavioral patterns grounded in prior experience, (iii) avoid repeating costly mistakes, and (iv) continuously improve through interaction.

#### 1.2 A brief history of neural memory

The ambition to give neural networks external storage dates back over a decade. Memory Networks [Weston et al., 2015] and their end-to-end variant [Sukhbaatar et al., 2015] introduced differentiable read-write access to external slots for question answering. Neural Turing Machines [Graves et al., 2014] and Differentiable Neural Computers [Graves et al., 2016] pushed further, supporting both content-based and location-based addressing over a memory matrix. Memorizing Transformers [Wu et al., 2022] and Recurrent Memory Transformers [Bulatov et al., 2022] later integrated explicit memory layers directly into the Transformer backbone.

A parallel thread focused on retrieval. RAG [Lewis et al., 2020] married a pre-trained generator with a dense document retriever, and RETRO [Borgeaud et al., 2022] showed that pulling from a trillion-token corpus at inference time could match much larger models at a fraction of the parameter count. These systems proved a crucial point: external knowledge stores can be queried dynamically during generation without retraining.

The leap from retrieval-augmented models to memoryaugmented agents happened quickly. ReAct [Yao et al., 2022] interleaved reasoning traces with environment actions, producing an interpretable trajectory that doubles as short-horizon memory. Reflexion [Shinn et al., 2023] took this further by storing verbal self-critiques after task attempts—essentially giving the agent a post-mortem journal. Then came the Generative Agents paper [Park et al.,

- 2023], whose simulated town of 25 characters demonstrated that a simple observation–reflection–planning loop could produce months of coherent social behavior. Since 2023, the design space has exploded: hierarchical virtual memory inspired by operating systems [Packer et al., 2024], evergrowing skill libraries in Minecraft [Wang et al., 2023a], SQL databases as symbolic memory [Hu et al., 2023], andmost recently—end-to-end learned memory management via reinforcement learning [Yu et al., 2026].


#### 1.3 Why another survey?

Several broad agent surveys already exist [Xi et al., 2023, Wang et al., 2024a], and Zhang et al. [Zhang et al., 2024a] published a memory-focused review in 2024. However, the landscape has shifted considerably since then. A wave of 2025–2026 contributions—Agentic Memory [Yu et al., 2026], MemBench [Tan et al., 2025], MemoryAgentBench [Hu et al., 2025], MemoryArena [He et al., 2026]has introduced learned memory control, richer evaluation dimensions, and agentic benchmarks that tightly couple memory with action.

This survey zooms in on the memory module and asks three questions:

- RQ1 How should memory in LLM agents be decomposed and formalized?
- RQ2 What mechanisms exist, and what trade-offs do they impose?
- RQ3 How should memory be evaluated when the ultimate test is downstream agent performance?


Contributions. We formalize agent memory as a write– manage–read loop within a POMDP-style agent cycle (Section 2), propose a three-dimensional taxonomy that unifies disparate designs (Section 3), provide deep mechanism reviews with concrete system comparisons (Section 4), survey benchmarks alongside a practical metric stack (Section 5), map applications where memory is the differentiating factor (Section 6), discuss engineering realities and architecture patterns (Section 7), position relative to prior surveys (Section 8), and chart open research directions (Section 9).

- 2 Problem Formulation and Design Objectives


#### 2.1 The agent loop, seen through memory

At each discrete step t, an agent receives input xt—a user message, a sensor reading, or a tool return value—and must produce an action at. Between these two events, it consults its accumulated memory. We write:

at = πθ xt, R(Mt,xt), gt , (1) Mt+1 = U Mt,xt,at,ot,rt , (2)

where πθ is the policy (typically a prompted or partially fine-tuned LLM), R reads from memory, U writes to and

manages memory, gt encodes active goals, ot is environment feedback, and rt is any reward-like signal.

Two aspects deserve emphasis. First, U is not a simple append operation. In a well-designed system it summarizes, deduplicates, scores priority, resolves contradictions, andwhen appropriate—deletes. Second, πθ and (R,U ) form a feedback loop: the agent’s decisions determine what gets written, and what is written shapes future decisions. This recursive dependence is what makes memory both powerful and brittle—one bad write can pollute the store for many steps downstream.

#### 2.2 Connection to POMDPs

Cast formally, the setup above is a partially observable Markov decision process. Memory Mt plays the role of the agent’s belief state: an internal summary of history that stands in for the unobservable true state of the world. Classical POMDP solvers update beliefs via Bayesian filtering; LLM agents do something analogous—albeit messierthrough natural language compression, vector indexing, or structured storage.

The analogy clarifies an important point: agent memory is not merely a database lookup problem. It is about maintaining a sufficient statistic of the interaction history for good action selection, subject to hard computational and storage budgets.

#### 2.3 Five design objectives and their tensions

Across the systems we review, memory mechanisms are pulled along five axes:

- • Utility – Does memory actually improve task outcomes?
- • Efficiency – What is the token, latency, and storage cost per unit of utility gained?
- • Adaptivity – Can the system update incrementally from interaction feedback without a full retrain?
- • Faithfulness – Is recalled information accurate and current? Stale or hallucinated recall can be worse than no recall at all.
- • Governance – Does the system respect privacy, support deletion requests, and comply with organizational policy?


These objectives tug in opposite directions. Maximizing utility tempts you to store everything, which bloats storage and creates governance headaches. Aggressive compression improves efficiency but silently discards the one rare fact that turns out to be critical three weeks later. Any real deployment must navigate these trade-offs deliberately, and the “right” balance point shifts with the application. A medical triage agent, where a missed allergy record could be lifethreatening, operates under a very different faithfulness– efficiency frontier than a casual recipe recommender. Understanding these tensions is not merely academic—it directly shapes architectural choices, as we discuss in subsequent sections.

#### 2.4 Memory as a differentiator: an empiricalperspective

The practical importance of memory design is perhaps best illustrated by ablation results reported across recent systems. In the Generative Agents experiment [Park et al., 2023], removing the reflection component caused agent behavior to degenerate from coherent multi-day planning to repetitive, context-free responses within 48 simulated hours. Voyager [Wang et al., 2023a] without its skill library lost 15.3× in tech-tree milestone speed—the skill library was the performance. And in MemoryArena [He et al., 2026], swapping an active memory agent for a long-context-only baseline dropped task completion from over 80% to roughly 45% on interdependent multi-session tasks.

These numbers underscore a recurring theme: the gap between “has memory” and “does not have memory” is often larger than the gap between different LLM backbones. Investing in memory architecture can yield returns that rivalor exceed—model scaling.

3 A Unified Taxonomy of Agent Memory

Cognitive scientists have long distinguished multiple memory systems in the human brain [Atkinson and Shiffrin, 1968, Tulving, 1972, Baddeley, 2000, Squire, 2004]. Agent designers—often unconsciously—mirror that structure. We organize the space along three orthogonal dimensions.

#### 3.1 Temporal scope

Working memory. Whatever fits inside the current context window constitutes the agent’s working memory. Baddeley’s central executive plus buffer model [Baddeley, 2000] maps neatly: the LLM is the executive, the context window is the buffer, and both share the same bottleneck—limited capacity.

Episodic memory. Records of concrete experiences: individual tool calls, conversation turns, environment observations. In the Generative Agents world [Park et al., 2023], every observation—“Isabella saw Klaus painting in the park at 3pm”—lands in the episodic stream with a timestamp, an importance score, and an embedding for later retrieval.

Semantic memory. Abstracted, de-contextualized knowledge. An episodic fact like “the user corrected the date format on Jan 5, Jan 12, and Feb 1” may consolidate into the semantic record “user prefers DD/MM/YYYY.” This consolidation is rarely automatic; most current systems require explicit prompting or heuristic triggers.

Procedural memory. Reusable skills and executable plans. Voyager’s skill library [Wang et al., 2023a] is the clearest example: every verified Minecraft routine is stored as runnable JavaScript, indexed by a natural language description, and composed on the fly for novel tasks.

In practice, most agents blend at least two of these. The hard question is the transition policy: when does an episodic record graduate to semantic status, and when does a semantic fact get instantiated back into working memory for a specific task?

To illustrate the interplay, consider a customer-support agent handling returns. Each return request constitutes an episodic record. After processing hundreds of similar requests, the agent might consolidate the pattern into a semantic rule: “customers who received damaged items within 7 days are eligible for express replacement.” When a new request arrives, this semantic rule is loaded into working memory alongside the specific episodic details of the current case. If the agent also has stored scripts for processing returns (procedural memory), the four memory types form a complete reasoning stack: the procedure says how, semantic memory says what the policy is, episodic memory says what happened, and working memory holds the live reasoning context.

This four-layer integration is the aspiration; most current systems implement only two layers well and handle the transitions between layers via crude heuristics. The consolidation step—where episodes become semantic knowledgeis particularly underserved: it typically requires either explicit developer rules or periodic LLM-driven summarization, both of which are fragile and hard to validate.

#### 3.2 Representational substrate

How memory is physically stored constrains what the agent can efficiently do with it.

Context-resident text—summaries, scratchpads, chainof-thought traces [Wei et al., 2022]—is the simplest substrate. Fully transparent, zero infrastructure, but ruthlessly capacity-limited.

Vector-indexed stores encode records as dense embeddings and support approximate nearest-neighbor search [Karpukhin et al., 2020, Johnson et al., 2021]. They scale gracefully to millions of records but lose structured relationships: you can ask “what’s most similar?” but not “what caused what?”

Structured stores—SQL databases [Hu et al., 2023], key–value maps, knowledge graphs [Ji et al., 2022]preserve relational structure and support complex queries (“all API failures involving service X in the last 7 days”), at the cost of upfront schema design.

Executable repositories—code libraries, tool definitions, plan templates [Wang et al., 2023a]—let the agent invoke stored skills directly, sidestepping regeneration and the errors it introduces.

Hybrid stores are the norm in production. MemGPT [Packer et al., 2024], for instance, layers a context-window “main memory” over a searchable recall database and a vector-indexed archive—each tier with different access patterns and eviction rules.

#### 3.3 Control policy

Perhaps the most consequential—and least discusseddimension is who decides what to store, what to retrieve, and what to discard.

Heuristic control hard-codes rules: top-k retrieval, summarize every n turns, expire records older than d days. Predictable, easy to debug, but blind to context.

Prompted self-control exposes memory operations as tool calls and lets the LLM decide when to invoke them. MemGPT’s core_memory_append and

archival_memory_search are canonical examples [Packer et al., 2024]. Quality here hinges on the LLM’s instruction-following ability and on how well the memory API is documented in the system prompt.

Learned control treats memory operations as policy actions optimized end-to-end. Agentic Memory [Yu et al., 2026] trains store, retrieve, update, summarize, and discard as callable tools via a three-stage RL pipeline with step-wise GRPO. The payoff is substantial—learned policies discover non-obvious strategies such as preemptive summarization before the context is full—but so is the training cost.

#### 3.4 Representative systems at a glance

- Table 1 plots key systems and benchmarks on a timeline.


- 4 Core Memory Mechanisms


We now examine each mechanism family in detail, grounding the discussion in concrete system designs and their empirical trade-offs.

#### 4.1 Context-resident memory and compres-sion

The most straightforward way to give an agent memory is to keep relevant information in the prompt. System messages, recent conversation turns, scratchpad notes—everything the LLM “sees” on every call functions as working memory with perfect in-window recall.

The trouble starts when history outgrows the window. Several compression strategies have emerged: (i) sliding windows that retain the n most recent turns and drop the rest; (ii) rolling summaries that periodically condense older history into a shorter precis; (iii) hierarchical summaries operating at turn, session, and topic granularities; (iv) taskconditioned compression, where the current query decides which parts of history keep full detail. The Self-Controlled Memory system [Liang et al., 2023] hands this decision to the agent itself, letting it choose which segments deserve verbatim retention versus aggressive condensation.

Context-resident memory is transparent and infrastructure-free, but it carries a well-known pathology: summarization drift. Each compression pass silently discards low-frequency details. After enough passes, the agent “remembers” a sanitized, generic version of history—precisely the kind of memory that fails on edge cases. Extending context windows to 100k+ tokens [Chen

- et al., 2023] delays the problem but cannot eliminate it, and longer contexts incur quadratic cost increases in attention.


To make this concrete: consider an agent that processes 50 user interactions per day. After one week of rolling summarization, the raw 350-turn history has been compressed through at least three summary cycles. A rare but critical instruction from day one—say, “never call the production database directly”—may survive the first compression but is exactly the kind of low-frequency, high-importance detail that tends to vanish by the third pass. The agent then proceeds to call the production database, with predictable consequences.

This is not a hypothetical failure mode; it mirrors reported issues in deployed long-running chatbots and coding assistants. The implication is clear: for any agent expected to run for more than a handful of sessions, contextresident memory should be supplemented—not replaced, but supplemented—with an external store that preserves raw records at full fidelity.

A less obvious but equally important limitation of context-resident memory is attentional dilution. Even within a sufficiently large window, the LLM’s attention mechanism must distribute capacity across all tokens. As more memory content is injected, the model’s ability to focus on any single piece degrades—a phenomenon empirically documented in the “lost in the middle” literature, where information placed in the center of a long context is recalled less reliably than information at the beginning or end. This suggests that simply making the window bigger is not a complete solution; the agent must also curate what enters the window, which brings us back to the fundamental need for retrieval and filtering mechanisms.

#### 4.2 Retrieval-augmented memory stores

RAG [Lewis et al., 2020] demonstrated that pairing a generator with a non-parametric retrieval index produces strong results on knowledge-intensive tasks. In agent settings, the store is populated not with encyclopedia articles but with living interaction records: tool call logs, environment observations, user corrections, partial plans, and verbal reflections.

Indexing granularity. Fine-grained indexing (individual tool calls or single sentences) gives precise recall but can fragment multi-step reasoning into meaningless shards. Coarse-grained indexing (full sessions or long passages) preserves context but drowns the signal in noise. The practical sweet spot is multi-granularity indexing, where the retriever adaptively selects the right resolution. Dense passage retrieval [Karpukhin et al., 2020] via learned encoders, typically backed by FAISS-style approximate nearest-neighbor search [Johnson et al., 2021], remains the default implementation, often augmented with sparse BM25 and metadata filters (timestamps, tool types, task tags).

Query formulation. A subtlety that many systems gloss over: the agent’s immediate input xt is often a poor retrieval query. A user asking “Why did that crash?” needs the agent to retrieve the crash log from two sessions ago, not the most semantically similar sentence. Strategies include LLM-reformulated queries, multi-query fan-out with result fusion, and using the current subgoal as an additional retrieval signal. Self-RAG [Asai et al., 2024] goes one step further and teaches the model to decide whether retrieval is warranted at all—a simple gate that substantially cuts unnecessary latency.

Scale. RETRO [Borgeaud et al., 2022] and follow-up work on trillion-token datastores [Raad et al., 2024] suggest that retrieval memory can scale to years of interaction history without architectural changes. The bottleneck shifts decisively from storage to relevance: ensuring that the most useful—not merely the most similar—records are returned.

Read-write memory. RET-LLM [Sun et al., 2024] bridges free-form retrieval and structured storage by letting the agent write structured triplets at storage time while

Table 1: Representative memory systems and benchmarks for LLM agents (2020–2026).

System Year Memory Category Distinguishing Feature

RAG [Lewis et al., 2020]

2020 Non-parametric retrieval

First to couple a seq2seq generator with a dense document retriever at NeurIPS 2020.

RETRO [Borgeaud

- et al., 2022]

2022 Retrieval at scale Chunks retrieved from a 2-trillion-token corpus; 7.5Bparameter model rivals 175B Jurassic-1 on 10/16 benchmarks.

ReAct [Yao et al.,

- 2022]

2022 Trajectory traces Reasoning-and-acting traces double as short-horizon working memory; 34% absolute gain on ALFWorld.

Reflexion [Shinn et al., 2023]

2023 Reflective episodic Verbal self-critiques stored as episodic memory; 91% pass@1 on HumanEval (vs. 80% GPT-4 baseline).

Generative Agents [Park et al.,

- 2023]


- et al., 2024]

2024 Long-term with forgetting

Ebbinghaus-curve decay applied to chatbot memory; published at AAAI 2024.

LoCoMo [Maharana

- et al., 2024]

2024 Benchmark Up to 35 sessions, 300+ turns, 9k–16k tokens per conver-

sation; humans still far ahead. MemBench [Tan

- et al., 2025]

2025 Benchmark Separates factual vs. reflective memory; participation vs. observation modes; ACL 2025 Findings.

MemoryAgentBench [Hu et al., 2025]

2025 Benchmark Tests four cognitive competencies; no current system masters all four.

Agentic Memory [Yu et al., 2026]

2026 Unified STM/LTM policy

Memory ops trained as RL actions via step-wise GRPO; outperforms all memory-augmented baselines on five benchmarks.

MemoryArena [He

- et al., 2026]




2023 Episodic + reflective 25 simulated characters autonomously organize a Valentine’s party via observation–reflection–planning cycles.

Voyager [Wang et al., 2023a]

2023 Procedural skill library

3.3× more unique items and 15.3× faster tech-tree progression than prior Minecraft agents.

LongMem [Wang

- et al., 2023b]

2023 Long-form external Frozen backbone + residual side-network; memory bank

scales to 65k tokens. ChatDB [Hu et al.,

- 2023]

2023 Structured symbolic SQL databases as agent memory; supports precise IN-

SERT/SELECT queries over interaction records. ExpeL [Zhao et al.,

- 2024]


2024 Experiential learning Systematically extracts success/failure “rules of thumb”

from trajectory comparisons. MemGPT [Packer

- et al., 2024]


2024 Hierarchical virtual OS-inspired paging across main context, recall DB, and

archival vector store. MemoryBank [Zhong

2026 Benchmark Multi-session interdependent tasks in four domains; nearsaturated LoCoMo models drop to 40–60% here.

querying them via natural language. This is a pragmatic compromise: schema at write time, flexibility at read time.

#### 4.3 Reflective and self-improving memory

Reflexion [Shinn et al., 2023] introduced a deceptively simple idea: after failing a task, have the agent write a natural language post-mortem, then prepend it to the prompt on the next attempt. No gradient updates, no reward model—just a text file of self-critiques. The results were striking: 91% pass@1 on HumanEval, versus 80% for GPT-4 without reflection.

Generative Agents [Park et al., 2023] built a richer pipeline. Raw observations accumulate in an episodic stream. Periodically, the agent clusters related observations and synthesizes higher-order reflections—e.g., “Klaus has been eating alone and seems withdrawn.” Retrieval scores memories by a weighted mix of recency (exponential decay), relevance (embedding similarity), and importance (a self-assessed integer). This multi-signal scoring is a substantial improvement over pure cosine similarity and remains influential in later designs.

ExpeL [Zhao et al., 2024] pushes the paradigm further by systematically contrasting successful and failed trajectories, extracting discriminative “rules of thumb,” and storing them as reusable heuristics. Think-in-Memory [Liu et al., 2024a] separates retrieval from reasoning: the agent first recalls, then performs a dedicated thinking step over the recalled content before generating a response.

The central risk of reflective memory is self-reinforcing error. If the agent incorrectly concludes “API X always returns errors with parameter Y,” it will avoid that call path forever, never collecting evidence to overturn the false belief. Over-generalization is the sibling risk: a lesson learned in one context applied blindly in another. Quality gates—confidence scores, contradiction checking against other memories, periodic expiration—are necessary but still underdeveloped.

The problem becomes more acute at scale. A single incorrect reflection in a short-lived agent causes limited damage; the same incorrect reflection persisting in a long-running production agent—potentially influencing thousands of downstream decisions over weeks—can be catastrophic. The severity of the reflective memory failure

mode scales with agent lifetime, making it particularly dangerous in exactly the settings where memory is most needed.

One mitigation strategy explored in recent work is reflection grounding: requiring the agent to cite specific episodic evidence for each reflection it generates. If the reflection “API X is unreliable” must point to three concrete failure instances, the agent is less likely to generate baseless generalizations. This does not fully solve the problem—the cited evidence may itself be unrepresentative—but it provides an auditable trail that can be reviewed by human operators.

#### 4.4 Hierarchical memory and virtual contextmanagement

MemGPT [Packer et al., 2024] borrows an idea that operating system designers perfected decades ago: virtual memory. An OS gives each process the illusion of vast, contiguous memory by transparently paging data between RAM and disk. MemGPT does the same for the LLM’s context window:

- • Main context (RAM): the active window holding system prompt, recent messages, and currently relevant records.
- • Recall storage (disk): a searchable database of all past messages.
- • Archival storage (cold storage): a vector-indexed store for documents and long-term knowledge.


The agent moves data between tiers by calling memory management “functions”—archival_memory_search, core_memory_append, and so on. An interrupt mechanism passes control to the agent on each user message or timer event, letting it perform multiple internal memory operations before responding.

JARVIS-1 [Wang et al., 2024b] extends the hierarchical principle to multimodal settings, with separate stores for visual observations, textual plans, and executable skills. Cognitive Architectures for Language Agents [Sumers et al.,

- 2024] propose a generalized blueprint where working, episodic, semantic, and procedural stores interact through a central executive (the LLM), directly echoing Baddeley’s model [Baddeley, 2000].


The Achilles’ heel of hierarchical memory is orchestration. Page the wrong things in and you waste precious context tokens; archive too aggressively and you create “memory blindness”—the agent simply does not know that the critical fact exists somewhere in cold storage. This tension motivates the next mechanism family.

It is worth noting that orchestration failures in hierarchical memory tend to be silent. Unlike a crashed API call, which produces an error message, a paging decision that evicts the wrong record simply results in a slightly worse responseno exception, no log entry, no obvious signal that something went wrong. Over time, these silent failures compound. Diagnosing them requires detailed memory operation logs and retrospective analysis—an engineering investment that few current systems make but that is essential for productiongrade deployments.

#### 4.5 Policy-learned memory management

Heuristics and prompted self-control are not optimized for the agent’s end task. A k-nearest-neighbor retriever does not know whether the retrieved record will actually help; a fixed summarization schedule does not care whether the material being compressed is important.

Agentic Memory (AgeMem) [Yu et al., 2026] addresses this by treating five memory operations—store, retrieve, update, summarize, discard—as callable tools within the agent’s policy, then optimizing the entire pipeline with reinforcement learning. Training proceeds in three stages: supervised warm-up on memory demonstrations, task-level RL with outcome rewards, and finally step-level GRPO that provides denser credit assignment for individual memory actions. Across five long-horizon benchmarks, AgeMem consistently outperforms strong baselines, and the learned policy surfaces non-obvious tactics: proactively summarizing intermediate results before the context fills up, and selectively discarding records that are semantically similar to existing ones but add no new information.

Open concerns remain. RL training over long horizons is expensive. Learned forgetting could delete safety-critical information. Policies trained on one task distribution may fail to transfer. And it is hard to explain why the agent chose a particular memory action—interpretability lags behind capability.

#### 4.6 Parametric memory and weight-basedadaptation

All of the above treat memory as external to the model’s weights. An alternative family embeds memory inside the parameters through fine-tuning or adapter modules. MemLLM [Modarressi et al., 2024] fine-tunes the LLM to interact with an explicit read-write memory module, tightly coupling parametric and non-parametric knowledge. Joint training of retrieval and generation [Zhong et al., 2022] yields better memory utilization than frozen-retriever baselines.

Parametric memory offers seamless integration—the model just “knows” things. But it is hard to audit (where exactly in the weights is the user’s birthday stored?), hard to delete from (machine unlearning is still immature), and expensive to update (each new fact requires fine-tuning). For these reasons, most deployed agents favor non-parametric, inspectable stores.

### 5 Evaluation: From Recall to Agentic Utility

#### 5.1 Why classical retrieval metrics fall short

Precision@k and nDCG tell you whether the right document was retrieved. They say nothing about whether the agent used that document correctly—or whether retrieving it was even worth the latency. Agent memory evaluation must jointly assess memory quality and decision quality, along with concerns that classical IR ignores entirely: staleness, contradiction, forgetting quality, and governance compliance.

#### 5.2 The new benchmark landscape

Four recent benchmarks push evaluation in complementary directions.

LoCoMo [Maharana et al., 2024] tests very long-term conversational memory: up to 35 sessions, 300+ turns, and 9k–16k tokens per conversation. Three evaluation tasks—factual QA, event summarization, and dialogue generation—probe different memory demands. The headline result: even RAG-augmented LLMs lag far behind humans, especially on temporal and causal dynamics.

MemBench [Tan et al., 2025] distinguishes factual from reflective memory and tests each in both participation and observation modes. Metrics span three dimensions: effectiveness (accuracy), efficiency (number of memory operations), and capacity (performance degradation as the memory store grows).

MemoryAgentBench [Hu et al., 2025] grounds evaluation in cognitive science, probing four competencies: accurate retrieval, test-time learning, long-range understanding, and selective forgetting. Long-context datasets are reformatted into incremental multi-turn interactions to simulate realistic accumulation. No current system masters all four competencies; most fail conspicuously on selective forgetting.

MemoryArena [He et al., 2026] embeds memory evaluation inside complete agentic tasks—web navigation, preference-constrained planning, progressive information search, and sequential formal reasoning—where later subtasks depend on what the agent learned from earlier ones. The most striking finding: models that score near-perfectly on LoCoMo plummet to 40–60% in MemoryArena, exposing a deep gap between passive recall and active, decisionrelevant memory use.

#### 5.3 Benchmark comparison

- Table 2 summarizes design differences across these four benchmarks.


#### 5.4 A practical metric stack

Deployment demands more nuance than any single benchmark provides. We propose a four-layer evaluation stack:

##### Layer 1—Task effectiveness: success rate, factual cor-

rectness, plan completion rate.

##### Layer 2—Memory quality: retrieved-record preci-

sion/recall, contradiction rate, staleness distribution, coverage of task-relevant facts.

###### Layer 3—Efficiency: latency per memory operation,

prompt tokens consumed by memory content, retrieval calls per step, storage growth over time.

###### Layer 4—Governance: privacy leakage rate, deletion

compliance, access-scope violations.

Ablation studies should isolate the write policy, the retrieval strategy, and the compression module to attribute gains to specific components rather than the overall pipeline.

#### 5.5 Cross-cutting lessons from the bench-marks

Aggregating results across these four evaluations, several patterns stand out.

Long context is not memory. Despite context windows stretching to 200k tokens [Chen et al., 2023], long-context models consistently underperform purpose-built memory systems on tasks requiring selective retrieval and active management. MemoryArena makes this starkest: passive recall aces are poor memory agents.

RAG helps, but the gap to humans is wide. RAG-based agents beat pure long-context baselines across the board, yet the primary bottleneck is no longer storage—it is retrieval quality. Agents routinely surface plausible but stale or offtopic records [Maharana et al., 2024].

Nobody evaluates forgetting well. Only MemoryAgentBench tests selective forgetting explicitly. Yet in any longrunning deployment, the inability to discard outdated information gradually poisons retrieval precision.

Cross-session coherence is underexplored. Most benchmarks measure within-session performance. MemoryArena’s multi-session design reveals that maintaining consistent knowledge and behavior across sessions separated by hours or days is a distinct—and largely unsolvedchallenge.

The parametric–non-parametric gap is real. Systems with parametric memory (fine-tuned weights) and nonparametric memory (external stores) show different failure profiles. Parametric memory excels at seamless knowledge integration but fails at targeted deletion and auditing. Nonparametric memory supports inspection and governance but can feel “bolted on”—the agent sometimes ignores retrieved records or uses them inconsistently. The optimal balance between these two approaches, and how to combine them effectively, remains an open empirical question.

Evaluation must include cost. A memory system that achieves 5% higher accuracy but triples latency and storage cost may not be an improvement in practice. None of the current benchmarks systematically report efficiency metrics alongside effectiveness, making it difficult to assess whether reported gains are “free” or come at significant operational expense. Future evaluations should mandate reporting of at least token consumption and latency overhead alongside accuracy numbers.

6 Where Memory Makes or Breaks the Agent

Memory is not uniformly important. A one-shot translation tool barely needs it; a month-long project collaborator cannot function without it. Below we examine domains where memory is the differentiating factor.

#### 6.1 Personal assistants and conversationalagents

A personal assistant that forgets your dietary restrictions or re-asks your timezone every session is, at best, annoying. MemoryBank [Zhong et al., 2024] models memory decay

Table 2: Feature comparison of recent agent memory benchmarks.

Benchmark Year Multi-session Multi-turn Agentic tasks Forgetting Multimodal

LoCoMo 2024 ✓ ✓ – – ✓ MemBench 2025 – ✓ – – – MemoryAgentBench 2025 – ✓ – ✓ – MemoryArena 2026 ✓ ✓ ✓ – –

via Ebbinghaus forgetting curves [Ebbinghaus, 1885]: frequently accessed, high-importance memories are reinforced, while neglected ones fade. MemGPT [Packer et al., 2024] demonstrates multi-session chat with evolving user models. The core tension in this domain is personalization without overstepping—the agent must remember enough to be genuinely helpful without surfacing information the user considers private or forgotten.

#### 6.2 Software engineering agents

Coding agents assist with generation, debugging, review, and project management across codebases that may contain millions of lines [Qian et al., 2024, Hong et al., 2024]. Memory requirements are steep: retain architecture decisions, track bug report histories, remember code-style preferences, and maintain a library of verified solutions. ChatDev [Qian

- et al., 2024] equips role-playing agents (CEO, CTO, programmer, tester) with shared memory to keep a project coherent across development phases. MetaGPT [Hong et al., 2024] structures this shared memory as standardized documents—PRDs, design specs, code modules—that persist and evolve.


The distinguishing challenge here is structural scale: the memory system must index and retrieve relevant portions of a codebase that may span thousands of files, not just conversations.

#### 6.3 Open-world game agents

Minecraft and similar sandboxes are popular testbeds precisely because they demand long-horizon planning and compositional skill reuse. Voyager [Wang et al., 2023a] showed that an ever-growing skill library enables lifelong learning: 3.3× more unique items and 15.3× faster milestone progression than prior agents. JARVIS-1 [Wang et al., 2024b] extends this with multimodal memory spanning visual observations and textual plans. Ghost in the Minecraft [Zhu et al., 2023] uses text-based knowledge and memory for generally capable open-world agents.

The key challenge is compositional skill reuse: the agent must not only recall individual skills but chain them creatively to solve novel problems.

#### 6.4 Scientific reasoning and discovery

Scientific agents must track hypotheses, record experimental outcomes, digest literature, and revise beliefs as evidence accumulates. Memory here acts as a hypothesis ledger and evidence accumulator. The distinctive challenge is uncertainty-aware memory: the agent must maintain not just facts but confidence levels, and update them correctly as

new data arrives—something most current memory systems handle poorly or not at all.

#### 6.5 Multi-agent collaboration

When multiple agents work together, memory becomes a coordination mechanism. AutoGen [Wu et al., 2023] lets agents build on each other’s contributions through shared context. CAMEL [Li et al., 2024] explores role-aware communicative agents that must remember prior agreements and collaborative history. ProAgent [Zhang et al., 2024b] builds proactive teammates that anticipate needs based on memory of past interactions.

Two challenges dominate: shared vs. private memory boundaries—what should be visible to whom?—and consistency under concurrent writes—what happens when two agents update shared memory simultaneously? Current multi-agent frameworks handle shared memory in one of two ways: either all memory is shared (simple but leaks private information) or each agent maintains its own store with no cross-agent access (isolated but prevents knowledge transfer). Neither extreme is satisfactory. A principled middle ground would define role-based access controls over a shared memory substrate, allowing a project manager agent to see high-level summaries from a developer agent without accessing the raw code diffs. Database-style access control lists, adapted for natural language records, are a natural but unexplored solution.

#### 6.6 Tool use and API orchestration

Tool-using agents [Schick et al., 2024] interact with APIs, databases, and web services. Memory must track which tools exist, how to call them, what parameters worked last time, and which sequences of calls have been verified. AgentBench [Liu et al., 2023] evaluates agents across eight environments; agents that lose track of their command history show sharp performance drops in multi-step tasks. DERA [Nair et al., 2023] uses dialog-turn memory to refine tool-use strategies iteratively.

A practical hazard unique to this setting is schema drift: when an API updates its interface, stored usage patterns become invalid. Version tracking and schema validation on stored tool-use records are essential but rarely implemented. In fast-moving API ecosystems, a tool-use memory system that does not handle schema drift will accumulate an increasing fraction of invalid records, progressively degrading the agent’s ability to reuse past experience.

The broader point here is that tool-use memory is not just about storing “what worked”; it is about maintaining a living, versioned catalog of tool capabilities that degrades gracefully as the external world changes. This connects to

the software engineering concept of dependency management: just as a build system must track library versions, a tool-using agent must track API versions in its memory store.

#### 6.7 Cross-domain memory transfer

An emerging direction is transferring memory across domains—e.g., debugging heuristics learned in Python reused for Java, or time-management strategies from one user applied to another. Tree of Thoughts [Yao et al., 2024] provides a framework for deliberate problem-solving that could benefit from cross-domain procedural memory. The open question is how to identify which memories generalize and which are hopelessly context-specific.

#### 6.8 Summary: where different memory typesmatter most

The application survey reveals a clear pattern: different domains stress different memory types. Personal assistants depend most on semantic memory (user preferences and profiles). Software engineering agents lean heavily on procedural memory (verified code patterns and architecture decisions). Game agents need tight integration of episodic and procedural memory (what happened + what to do about it). Scientific agents require semantic memory with explicit uncertainty tracking. Multi-agent systems add a coordination layer that no single-agent memory design currently handles well.

No existing system provides strong support across all these profiles simultaneously, which suggests that the next leap in agent memory may come from more modular, pluggable architectures where memory components can be composed and configured per deployment rather than baked into a monolithic design.

### 7 Engineering Realities

#### 7.1 The write path

Storing every interaction verbatim is tempting and almost always wrong. Noise—small talk, redundant confirmations, repeated greetings—degrades retrieval precision. A welldesigned write path includes: filtering to reject low-signal records, canonicalization to normalize dates, names, and quantities, deduplication to merge overlapping entries, priority scoring to rank records by task relevance and novelty, and metadata tagging (timestamp, source, task label, confidence) to support structured queries downstream.

The optimal filtering threshold is application-specific. A medical agent cannot afford false negatives (missing a drug allergy mention); a casual chat assistant can tolerate them. Between these extremes lies a spectrum: enterprise customer-support bots typically prioritize high recall for contractual commitments but accept lower recall for casual preferences, while financial advisory agents demand near-perfect recall for regulatory disclosures but can afford to forget informal chit-chat. The write-path design should be informed by a risk analysis that maps memory failure modes to their downstream consequences in the target domain.

#### 7.2 The read path

Not every step needs retrieval, and not every retrieval needs the full pipeline. Practical read-path optimizations include: two-stage retrieval (fast BM25 or metadata filter → slower cross-encoder reranker), retrieval-or-not gating [Asai et al., 2024], token budgeting that dynamically allocates context space between memory and current task, and cache layers for high-frequency records like user preferences.

#### 7.3 Staleness, contradictions, and drift

A personal assistant that sends a birthday card to a user’s expartner at the old address is not just unhelpful—it is harmful. Long-lived memory stores accumulate stale records, and without explicit mechanisms the agent has no way to distinguish the 2024 address from the 2022 one.

Robust systems need temporal versioning (prefer the newest record), source attribution (user statement > agent inference), contradiction detection (flag conflicts for resolution), and periodic consolidation (scheduled sweeps that merge duplicates and retire stale entries).

#### 7.4 Latency and cost

Users expect sub-second responses for simple queries. Retrieval pipelines can easily add 200–500ms. Common mitigations: asynchronous writes (defer storage until after the response), progressive retrieval (start generating while retrieval runs in parallel), and dynamic routing (skip retrieval for straightforward requests, engage the full pipeline only when ambiguity is high).

Xu et al. [Xu et al., 2024] show that retrieving a handful of highly relevant passages into a moderate-length context often beats both pure long-context and pure retrieval approaches—a useful guideline for tuning the latency– quality tradeoff.

#### 7.5 Privacy, compliance, and deletion

Agent memory can harbor sensitive data: health details, financial records, private conversations. Deployments must provide encryption at rest and in transit, per-user access scoping, automated PII redaction, configurable retention policies, and auditable deletion that removes data from every tier—including vector index entries and backup snapshots.

When memories have leaked into fine-tuned weights, external deletion is insufficient. Machine unlearning [Bourtoule et al., 2021, Liu et al., 2024b] is the only path, and it remains far from production-ready. The intersection of agent memory governance and machine unlearning is an urgent open problem.

#### 7.6 Three architecture patterns

In practice, agent memory systems cluster into three recurring patterns:

Pattern A: Monolithic context. All memory lives inside the prompt. Zero infrastructure, fully transparent, but capacity-capped and prone to summarization drift. Suitable for short-lived agents or rapid prototyping.

##### Pattern B: Context + retrieval store. Working mem-

ory in the context window; long-term records in an external vector or structured store. A retrieval pipeline injects relevant records each step. This is the workhorse pattern behind most production agents today: coding assistants, customerservice bots, enterprise copilots. The engineering burden is manageable; the main challenge is retrieval quality.

##### Pattern C: Tiered memory with learned control.

Multiple tiers—context, structured DB, vector store, cold archive—managed by a learned or prompted controller. MemGPT [Packer et al., 2024] and AgeMem [Yu et al., 2026] are exemplars. This pattern offers the most headroom but demands the most sophisticated engineering and training.

Our recommendation: start with Pattern B, instrument it thoroughly, and graduate to Pattern C only when empirical data shows that learned control meaningfully improves your target workload.

#### 7.7 Observability and debugging

Memory systems are notoriously difficult to debug. When an agent gives a wrong answer, was the problem in retrieval (wrong records surfaced), in the write path (relevant information never stored), in compression (detail lost during summarization), or in the LLM’s reasoning over correctly retrieved content?

Production deployments benefit from comprehensive memory operation logging: every write, read, update, and delete should be recorded with timestamps, triggering context, and the records involved. Replay tools that let developers re-run a failed interaction with modified memory content are invaluable for root-cause analysis. Some teams have found that a simple “memory diff”—showing what changed in the memory store between two conversation turns—provides more diagnostic value than traditional log analysis.

This observability infrastructure is rarely discussed in research papers, but its absence is one of the primary reasons that impressive demo-stage memory systems fail to make the transition to reliable production deployments.

Beyond debugging, memory observability also supports continuous improvement. By analyzing patterns in memory operations—which types of records are retrieved most often, which are written but never read, which retrieval queries consistently return empty results—teams can identify bottlenecks and calibrate their memory systems over time. This feedback loop is standard in database engineering (query performance monitoring, index optimization) but is almost entirely absent in agent memory practice. Borrowing these techniques, even in simplified form, would significantly improve the reliability of deployed memory-augmented agents.

A related concern is regression testing for memory behavior. When a memory system is updated—say, a new embedding model is deployed for the vector store—the effects on retrieval quality are unpredictable and potentially subtle. Without a suite of regression tests that verify expected memory behavior on representative scenarios, changes to the memory subsystem become a source of untracked risk. Building such test suites requires ground-truth annotations of “which memories should be retrieved for which queries,” an investment that pays dividends in system stability.

### 8 Positioning Relative to Prior Sur-veys

Xi et al. [Xi et al., 2023] and Wang et al. [Wang et al., 2024a] offer broad agent surveys in which memory is one module among many. Zhang et al. [Zhang et al., 2024a] focus specifically on memory and organize their review around write– manage–read operations; our work updates their coverage with 2025–2026 systems (AgeMem, MemBench, MemoryAgentBench, MemoryArena), adds a POMDP-grounded formulation, and extends the discussion to applications, engineering patterns, and governance.

Gao et al. [Gao et al., 2024] survey RAG comprehensively, but their scope is the retrieval–generation pipeline, not agent-specific memory needs. Sumers et al. [Sumers et al., 2024] propose a cognitive architecture blueprint for language agents; our taxonomy is complementary, sharing the cognitive science terminology but extending the analysis to representational substrates and control policies.

A question often raised is whether expanding context windows—from 4k in early GPT models to 200k+ today [Chen et al., 2023]—makes external memory obsolete. The evidence says no. Longer context enlarges working memory but does not provide persistent cross-session storage, structured knowledge organization, selective retrieval from months of history, or governance mechanisms like deletion and access control. Moreover, inference cost scales quadratically with context length, and Xu et al. [Xu et al., 2024] show empirically that a modest context augmented with targeted retrieval outperforms brute-force long context on many tasks.

### 9 Open Challenges

#### 9.1 Principled consolidation

Current systems oscillate between hoarding (store everything, drown in noise) and amnesia (compress aggressively, lose rare but vital facts). Neuroscience offers a suggestive model: during sleep, the hippocampus replays recent experiences, strengthening important traces and pruning the rest [Squire, 2004]. An analogous “offline consolidation” process—scheduled during idle periods—could provide a principled balance. Open questions: how to estimate memory importance without future-sight, how to detect when consolidation is needed, and how to guarantee that safetycritical records survive the process.

One concrete approach worth exploring is dual-buffer consolidation, where newly formed memories reside in a “hot” buffer during a probation period and are promoted to long-term storage only after passing quality checks—reverification, deduplication, and importance scoring. This mirrors the hippocampal-to-neocortical transfer observed in biological memory [Squire, 2004], where new memories are initially hippocampus-dependent and gradually become independent through repeated reactivation. Implementing this in an agent system would require defining the probation period, the promotion criteria, and the fallback behavior when the hot buffer overflows before promotion occurs.

#### 9.2 Causally grounded retrieval

Semantic similarity answers “what looks like this?” but not “what caused this?” When an agent debugs a system failure, the relevant memory may be temporally distant and semantically dissimilar to the current error message yet causally upstream. Hybrid retrievers blending semantic similarity, temporal ordering, causal graph traversal, and counterfactual relevance remain largely unexplored. Building them will require integrating causal discovery techniques with memory indexing—technically challenging but potentially transformative for complex reasoning tasks.

A concrete starting point would be to augment the standard vector index with a lightweight causal metadata layer. When storing a memory record, the agent could annotate it with an estimated causal parent—the earlier record or event that precipitated it. At retrieval time, the system would traverse these causal links alongside the standard similarity search, surfacing records that are semantically distant but causally relevant. Such a system need not perform full causal inference; even approximate causal annotations, generated by the LLM at write time, could substantially improve retrieval for reasoning-heavy tasks like root cause analysis, counterfactual planning, and multi-step debugging.

#### 9.3 Trustworthy reflection

Self-reflection is a powerful adaptation mechanism that can also entrench mistakes. If the agent falsely concludes that “approach A always fails,” it will never test approach A again—a classic confirmation bias. Future systems need external validation (check reflections against ground truth when available), uncertainty quantification (decay confidence over time without confirming evidence), adversarial probing (periodically challenge stored beliefs with counterexamples), and expiration policies (retire unvalidated reflections after a set period).

#### 9.4 Learning to forget

Forgetting is not a bug; it is a feature—essential for robustness, privacy, and efficiency. Yet current systems handle it crudely: hard time-based expiration, storage-limit eviction, or nothing at all. The research problem is to learn selective forgetting policies that maximize long-term utility under safety and compliance constraints. Connections to machine unlearning [Bourtoule et al., 2021, Liu et al., 2024b] are critical when memories have influenced model behavior through in-context learning or fine-tuning.

#### 9.5 Multimodal and embodied memory

As agents move into robotics and mixed-reality, memory must fuse text, vision, audio, proprioception, and tool state. JARVIS-1 [Wang et al., 2024b] provides an early example in Minecraft, but real-world embodied settings add spatial memory, real-time latency constraints, and the thorny problem of cross-modal retrieval—finding a visual memory via a textual query, or vice versa.

#### 9.6 Multi-agent memory governance

Multi-agent systems raise questions that single-agent memory never encounters: access control over shared stores, consensus protocols for concurrent writes, and knowledge transfer mechanisms between agents with different specializations. Current approaches rely on shared conversation logs or document stores; more sophisticated designs—distributed memory with merge semantics, hierarchical shared memory with per-agent caches—remain wide open.

#### 9.7 Toward memory-efficient architectures

Memory-augmented agents are expensive: large context windows, multiple retrieval calls per step, ever-growing stores. Sparse retrieval (activating a tiny fraction of the store per step), compressed session vectors, memorynative architectures like Recurrent Memory Transformers [Bulatov et al., 2022], and retrieval-free injection via adapters [Modarressi et al., 2024] all point toward cheaper alternatives, though none has yet demonstrated strong agentlevel performance.

#### 9.8 Deeper neuroscience integration

Current agent memory borrows cognitive science labels; deeper engagement could yield better mechanisms. Spreading activation [Anderson, 1983]—where accessing one memory primes related ones—could improve retrieval beyond direct similarity. Memory reconsolidation theory—retrieval renders a memory labile and subject to revision—could inform update mechanisms. Ebbinghaus curves [Ebbinghaus, 1885], already used in MemoryBank [Zhong et al., 2024], could be extended with spaced repetition to optimize reinforcement timing.

#### 9.9 Foundation models for memory manage-ment

A longer-term vision: a foundation model for memory control, trained across diverse agent tasks to perform write, retrieve, summarize, forget, and consolidate operations with general competence—much as instruction-tuned LLMs [Ouyang et al., 2022] provide general language capabilities. AgeMem [Yu et al., 2026] takes a first step by learning memory management as a policy, but the vision of a truly task-agnostic memory controller remains unrealized.

Such a foundation model would need to handle a diverse distribution of memory challenges: short-term conversational tracking, long-term user profiling, high-frequency tool-use logging, rare but safety-critical information retention, and graceful degradation when storage budgets are exhausted. The training data requirements are daunting—the model would need exposure to thousands of agent trajectories across dozens of domains, with ground-truth labels for memory operation quality. Generating this training data synthetically, perhaps by having advanced LLMs retrospectively annotate which memory operations in historical traces were helpful or harmful, could bootstrap the process.

#### 9.10 Standardized evaluation

The field still lacks a community-standard evaluation harness. Each benchmark uses its own datasets, metrics, and protocols, making cross-paper comparison unreliable. A GLUE-style shared leaderboard for agent memoryspanning conversational, agentic, and multi-session tracks, with standardized metrics from our four-layer stack—would substantially accelerate progress and reduce duplicated effort.

### 10 Conclusion

Memory has moved from a peripheral add-on to the central engineering and research challenge for LLM-based agents. The field has traversed three generations in rapid succession: prompt-level compression, retrieval-augmented external stores, and end-to-end learned memory policies. Evaluation has evolved in tandem—from static recall tests to multisession agentic benchmarks that expose the gap between remembering a fact and actually using it.

This survey has offered a POMDP-grounded formalization, a three-axis taxonomy, a deep dive into five mechanism families, a structured benchmark comparison, an application-level analysis, and a practical engineering playbook. But the hardest problems remain ahead: how to consolidate without catastrophic loss, how to retrieve by cause rather than similarity, how to reflect without entrenching errors, and how to forget safely. Solving these will determine whether the next generation of agents is merely impressive or genuinely reliable.

If there is one takeaway from this survey, it is that memory deserves the same level of engineering investment as the LLM itself. Model selection gets months of careful benchmarking; memory architecture often gets an afternoon. The evidence reviewed here suggests that flipping this prioritytreating memory as a first-class system component worthy of dedicated design, testing, and optimization—may be the single highest-leverage intervention available to agent builders today.

### Acknowledgments

This manuscript targets Advanced Intelligent Systems. Author, funding, and ethics metadata should be finalized before submission.

### Conflict of Interest

The authors declare no conflict of interest.

### Data Availability Statement

No primary data were generated in this study. All referenced works are publicly available as cited.

### References

Tom Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah, Jared D. Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda Askell, et al. Language models are few-shot learners. Advances in Neural Information Processing Systems (NeurIPS), 2020.

Josh Achiam, Steven Adler, Sandhini Agarwal, Lama Ahmad, Ilge Akkaya, Florencia Leoni Aleman, Diogo Almeida, Janko Altenschmidt, Sam Altman, Shyamal Anadkat, et al. GPT-4 technical report. arXiv preprint arXiv:2303.08774, 2023.

Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, et al. LLaMA: Open and efficient foundation language models. arXiv preprint arXiv:2302.13971, 2023.

Zeyu Zhang, Xiaohe Bo, Chen Ma, Rui Li, Xu Chen, Quanyu Dai, Jieming Zhu, Zhenhua Dong, and JiRong Wen. A survey on the memory mechanism of large language model based agents. arXiv preprint arXiv:2404.13501, 2024a.

Jason Weston, Sumit Chopra, and Antoine Bordes. Memory networks. arXiv preprint arXiv:1410.3916, 2015.

Sainbayar Sukhbaatar, Arthur Szlam, Jason Weston, and Rob Fergus. End-to-end memory networks. Advances in Neural Information Processing Systems (NeurIPS), 2015.

Alex Graves, Greg Wayne, and Ivo Danihelka. Neural turing machines. arXiv preprint arXiv:1410.5401, 2014.

Alex Graves, Greg Wayne, Malcolm Reynolds, Tim Harley, Ivo Danihelka, Agnieszka Grabska-Barwi´nska, Sergio Gómez Colmenarejo, Edward Grefenstette, Tiago Ramalho, John Agapiou, et al. Hybrid computing using a neural network with dynamic external memory. Nature, 538:471–476, 2016.

Yuhuai Wu, Markus N. Rabe, DeLesley Hutchins, and Christian Szegedy. Memorizing transformers. arXiv preprint arXiv:2203.08913, 2022.

Aydar Bulatov, Yuri Kuratov, and Mikhail Burtsev. Recurrent memory transformer. Advances in Neural Information Processing Systems (NeurIPS), 2022.

Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen tau Yih, Tim Rocktäschel, Sebastian Riedel, and Douwe Kiela. Retrieval-augmented generation for knowledge-intensive NLP tasks. In Advances in Neural Information Processing Systems (NeurIPS), 2020.

Sebastian Borgeaud, Arthur Mensch, Jordan Hoffmann, Trevor Cai, Eliza Rutherford, Katie Millican, George van den Driessche, Jean-Baptiste Lespiau, Bogdan Damoc, Aidan Clark, Diego de Las Casas, et al. Improving language models by retrieving from trillions of tokens. In Proceedings of the 39th International Conference on Machine Learning (ICML), 2022.

Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, and Yuan Cao. ReAct: Synergizing reasoning and acting in language models. arXiv preprint arXiv:2210.03629, 2022.

Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik Narasimhan, and Shunyu Yao. Reflexion: Language agents with verbal reinforcement learning. arXiv preprint arXiv:2303.11366, 2023.

Joon Sung Park, Joseph C. O’Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, and Michael S. Bernstein. Generative agents: Interactive simulacra of human behavior. In Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology (UIST), 2023.

Charles Packer, Sarah Wooders, Kevin Lin, Vivian Fang, Shishir G. Patil, Ion Stoica, and Joseph E. Gonzalez. MemGPT: Towards LLMs as operating systems. arXiv preprint arXiv:2310.08560, 2024.

Guanzhi Wang, Yuqi Xie, Yunfan Jiang, Ajay Mandlekar, Chaowei Xiao, Yuke Zhu, Linxi Fan, and Anima Anandkumar. Voyager: An open-ended embodied agent with large language models. arXiv preprint arXiv:2305.16291, 2023a.

Chenxu Hu, Jie Fu, Chenzhuang Du, Simian Luo, Junbo Zhao, and Hang Zhao. ChatDB: Augmenting LLMs with databases as their symbolic memory. arXiv preprint arXiv:2306.03901, 2023.

Yi Yu, Liuyi Yao, Yuexiang Xie, Qingquan Tan, Jiaqi Feng, Yaliang Li, and Libing Wu. Agentic memory: Learning unified long-term and short-term memory management for large language model agents. arXiv preprint arXiv:2601.01885, 2026.

Zhiheng Xi, Wenxiang Chen, Xin Guo, Wei He, Yiwen Ding, Boyang Hong, Ming Zhang, Junzhe Wang, Senjie Jin, Enyu Zhou, et al. The rise and potential of large language model based agents: A survey. arXiv preprint arXiv:2309.07864, 2023.

Lei Wang, Chen Ma, Xueyang Feng, Zeyu Zhang, Hao Yang, Jingsen Zhang, Zhiyuan Chen, Jiakai Tang, Xu Chen, Yankai Lin, Wayne Xin Zhao, Zhewei Wei, and Ji-Rong Wen. A survey on large language model based autonomous agents. Frontiers of Computer Science, 18 (6):186345, 2024a.

Haoran Tan, Zeyu Zhang, Chen Ma, Xu Chen, Quanyu Dai, and Zhenhua Dong. MemBench: Towards more comprehensive evaluation on the memory of LLM-based agents. arXiv preprint arXiv:2506.21605, 2025.

Yuanzhe Hu, Yu Wang, and Julian McAuley. Evaluating memory in LLM agents via incremental multi-turn interactions. arXiv preprint arXiv:2507.05257, 2025.

Zexue He, Yu Wang, Churan Zhi, Yuanzhe Hu, Tzu-Ping Chen, Lang Yin, Ze Chen, Tong Arthur Wu, Siru Ouyang,

- Zihan Wang, Jiaxin Pei, Julian McAuley, Yejin Choi, and Alex Pentland. MemoryArena: Benchmarking agent memory in interdependent multi-session agentic tasks. arXiv preprint arXiv:2602.16313, 2026.


Richard C. Atkinson and Richard M. Shiffrin. Human memory: A proposed system and its control processes. Psychology of Learning and Motivation, 2:89–195, 1968.

Endel Tulving. Episodic and semantic memory. Organization of Memory, pages 381–403, 1972.

Alan Baddeley. The episodic buffer: A new component of working memory? Trends in Cognitive Sciences, 4(11): 417–423, 2000.

Larry R. Squire. Memory systems of the brain: A brief history and current perspective. Neurobiology of Learning and Memory, 82(3):171–177, 2004.

Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei Xia, Ed Chi, Quoc V. Le, and Denny Zhou. Chain-of-thought prompting elicits reasoning in large language models. Advances in Neural Information Processing Systems (NeurIPS), 2022.

Vladimir Karpukhin, Barlas O˘guz, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi Chen, and Wen tau Yih. Dense passage retrieval for open-domain question answering. arXiv preprint arXiv:2004.04906, 2020.

Jeff Johnson, Matthijs Douze, and Hervé Jégou. Billionscale similarity search with GPUs. IEEE Transactions on Big Data, 7(3):535–547, 2021.

Shaoxiong Ji, Shirui Pan, Erik Cambria, Pekka Marttinen, and Philip S. Yu. A survey on knowledge graphs: Representation, acquisition, and applications. IEEE Transactions on Neural Networks and Learning Systems, 33(2): 494–514, 2022.

Weizhi Wang, Li Dong, Hao Cheng, Xiaodong Liu, Xifeng Yan, Jianfeng Gao, and Furu Wei. Augmenting language models with long-term memory. In Advances in Neural Information Processing Systems (NeurIPS), 2023b.

Andrew Zhao, Daniel Huang, Quentin Xu, Matthieu Lin, Yong-Jin Liu, and Gao Huang. ExpeL: LLM agents are experiential learners. Proceedings of the AAAI Conference on Artificial Intelligence, 38, 2024.

Wanjun Zhong, Lianghong Guo, Qiqi Gao, He Ye, and Yanlin Wang. MemoryBank: Enhancing large language models with long-term memory. Proceedings of the AAAI Conference on Artificial Intelligence, 38, 2024.

Adyasha Maharana, Dong-Ho Lee, Sergey Tulyakov, Mohit Bansal, Francesco Barbieri, and Yuwei Fang. Evaluating very long-term conversational memory of LLM agents. arXiv preprint arXiv:2402.17753, 2024.

Xinnian Liang, Bing Wang, Hui Huang, Shuangzhi Wu, Peihao Wu, Lu Lu, Zejun Ma, and Zhoujun Li. Unleashing infinite-length input capacity for large-scale language models with self-controlled memory system. arXiv preprint arXiv:2304.13343, 2023.

Shouyuan Chen, Sherman Wong, Liangjian Chen, and Yuandong Tian. Extending context window of large language models via positional interpolation. arXiv preprint arXiv:2306.15595, 2023.

Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, and Hannaneh Hajishirzi. Self-RAG: Learning to retrieve, generate, and critique through self-reflection. arXiv preprint arXiv:2310.11511, 2024.

Jad Raad, Xian Li, Peter West, and Yejin Choi. Scaling retrieval-based language models with a trillion-token datastore. arXiv preprint arXiv:2407.12854, 2024.

Jianlv Sun, Zihao Shi, Simeng Han, Chuang Gan, and Yilun Du. RET-LLM: Towards a general read-write memory for large language models. arXiv preprint arXiv:2305.14322, 2024.

Lei Liu, Xiaoyan Yang, Yue Shen, Binbin Hu, Zhiqiang Zhang, Jinjie Gu, and Jun Zhou. Think-in-memory: Recalling and post-thinking enable LLMs with long-term memory. arXiv preprint arXiv:2311.08719, 2024a.

- Zihao Wang, Shaofei Cai, Anji Liu, Yonggang Jin, Jinbing Hou, Bowei Zhang, Haowei Lin, Zhaofeng He, Zilong Zheng, Yaodong Yang, Xiaojian Ma, and Yitao Liang. JARVIS-1: Open-world multi-task agents with memoryaugmented multimodal language models. arXiv preprint arXiv:2311.05997, 2024b.


Theodore R. Sumers, Shunyu Yao, Karthik Narasimhan, and Thomas L. Griffiths. Cognitive architectures for language agents. Transactions on Machine Learning Research, 2024.

Ali Modarressi, Aber Rizvi, Mehdi Rezagholizadeh, and Pascal Poupart. MemLLM: Finetuning LLMs to use an explicit read-write memory. arXiv preprint arXiv:2404.11672, 2024.

Wanjun Zhong, Lianghong Guo, Qiqi Gao, He Ye, and Yanlin Wang. Training language models with memory augmentation. arXiv preprint arXiv:2205.12674, 2022.

Hermann Ebbinghaus. Über das gedächtnis: Untersuchungen zur experimentellen psychologie. Leipzig: Duncker & Humblot, 1885.

Chen Qian, Xin Cong, Cheng Yang, Weize Chen, Yusheng Su, Juyuan Xu, Zhiyuan Liu, and Maosong Sun. ChatDev: Communicative agents for software development. arXiv preprint arXiv:2307.07924, 2024.

Sirui Hong, Mingchen Zhuge, Jonathan Chen, Xiawu Zheng, Yuheng Cheng, Ceyao Zhang, Jinlin Wang, Zili Wang, Steven Ka Shing Yau, Zijuan Lin, et al. MetaGPT: Meta programming for a multi-agent collaborative framework. arXiv preprint arXiv:2308.00352, 2024.

Xizhou Zhu, Yuntao Chen, Hao Tian, Chenxin Tao, Weijie Su, Chenyu Yang, Gao Huang, Bin Li, Lewei Lu, Xiaogang Wang, Yu Qiao, Zhaoxiang Zhang, and Jifeng Dai. Ghost in the minecraft: Generally capable agents for open-world environments via large language models with text-based knowledge and memory. arXiv preprint arXiv:2305.17144, 2023.

Qingyun Wu, Gagan Bansal, Jieyu Zhang, Yiran Wu, Beibin Li, Erkang Zhu, Li Jiang, Xiaoyun Zhang, Shaokun Zhang, Jiale Liu, et al. AutoGen: Enabling next-gen LLM

applications via multi-agent conversation. arXiv preprint arXiv:2308.08155, 2023.

Guohao Li, Hasan Abed Al Kader Hammoud, Hani Itani, Dmitrii Khizbullin, and Bernard Ghanem. CAMEL: Communicative agents for “mind” exploration of large language model society. Advances in Neural Information Processing Systems (NeurIPS), 2024.

Ceyao Zhang, Kaijie Yang, Siyi Du, Xuewei Guo, Yulin Chen, Yao Huang, Haonan Li, Kunlun Zhu, Zhe Zheng, Haoqi Fan, Jiaqi Li, Yu Song, Yiwen Sun, and Sirui Hong. ProAgent: Building proactive cooperative agents with large language models. Proceedings of the AAAI Conference on Artificial Intelligence, 38, 2024b.

Timo Schick, Jane Dwivedi-Yu, Roberto Dessì, Roberta Raileanu, Maria Lomeli, Luke Zettlemoyer, Nicola Cancedda, and Thomas Scialom. Toolformer: Language models can teach themselves to use tools. Advances in Neural Information Processing Systems (NeurIPS), 2024.

Xiao Liu, Hao Yu, Hanchen Zhang, Yifan Xu, Xuanyu Lei, Hanyu Lai, Yu Gu, Hangliang Ding, Kaiwen Men, Kejuan Yang, et al. AgentBench: Evaluating LLMs as agents. arXiv preprint arXiv:2308.03688, 2023.

Varun Nair, Elliot Schumacher, Geoffrey Tso, and Anitha Kannan. DERA: Enhancing large language model completions with dialog-enabled resolving agents. arXiv preprint arXiv:2303.17071, 2023.

Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Thomas L. Griffiths, Yuan Cao, and Karthik Narasimhan. Tree of thoughts: Deliberate problem solving with large language models. Advances in Neural Information Processing Systems (NeurIPS), 2024.

Peng Xu, Wei Ping, Xianchao Wu, Lawrence McAfee, Chen Zhu, Zihan Liu, Sandeep Subramanian, Evelina Bakhturina, Mohammad Shoeybi, and Bryan Catanzaro. Retrieval meets long context large language models. arXiv preprint arXiv:2310.03025, 2024.

Lucas Bourtoule, Varun Chandrasekaran, Christopher A. Choquette-Choo, Henning Brendel, Milad Nasr, Matthew Hoover, Barbara Fung, Dimitris Papadopoulos, Chiyuan Zhang, Adelin Travers, et al. Machine unlearning. IEEE Symposium on Security and Privacy, 2021.

Zheyuan Liu, Guangyao Dou, Zhaoxuan Tan, Yijun Tian, and Meng Jiang. Towards safer large language models through machine unlearning. arXiv preprint arXiv:2402.10058, 2024b.

Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan, Yuxi Bi, Yi Dai, Jiawei Sun, and Haofen Wang. Retrieval-augmented generation for large language models: A survey. arXiv preprint arXiv:2312.10997, 2024.

John R. Anderson. A spreading activation theory of memory. Journal of Verbal Learning and Verbal Behavior, 22

(3):261–295, 1983.

Long Ouyang, Jeff Wu, Xu Jiang, Diogo Almeida, Carroll L. Wainwright, Pamela Mishkin, Chong Zhang, Sandhini Agarwal, Katarina Slama, Alex Ray, et al. Training language models to follow instructions with human feedback. Advances in Neural Information Processing Systems (NeurIPS), 2022.


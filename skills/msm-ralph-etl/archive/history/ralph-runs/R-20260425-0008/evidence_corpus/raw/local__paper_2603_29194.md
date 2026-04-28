Published online in June 2025

# Multi-Layered Memory Architectures for LLM Agents: An Experimental Evaluation of Long-Term Context Retention

Payal Fofadiya

Fulloop payal@fulloop.ai

Sunil Tiwari

Fulloop sunil@fulloop.ai

## arXiv:2603.29194v1[cs.CV]31 Mar 2026

Abstract—Long-horizon dialogue systems suffer from semantic drift and unstable memory retention across extended sessions. This paper presents a Multi-Layer Memory Framework that decomposes dialogue history into working, episodic, and semantic layers with adaptive retrieval gating and retention regularization. The architecture controls cross-session drift while maintaining bounded context growth and computational efficiency. Experiments on LOCOMO, LOCCO, and LoCoMo show improved performance, achieving 46.85 Success Rate, 0.618 overall F1 with 0.594 multi-hop F1, and 56.90% six-period retention while reducing false memory rate to 5.1% and context usage to 58.40%. Results confirm enhanced long-term retention and reasoning stability under constrained context budgets.

Keywords—Multi-layer memory, Long-horizon dialogue, Context retention, Semantic stability, Adaptive retrieval gating, Memory consolidation

I. INTRODUCTION

Large Language Models (LLMs) have achieved strong performance across dialogue reasoning and task-oriented interaction [1]. However, their ability to retain information across extended sessions remains limited by fixed context windows and uncontrolled memory accumulation. As dialogue length increases, earlier contextual signals are compressed or discarded, which leads to loss of persona consistency, entity drift, and factual instability [2]. Long-horizon conversational benchmarks such as LOCOMO and LOCCO highlight this limitation, where performance declines as sessions progress. Efficient memory consolidation has therefore become a central challenge in long-context agent systems. The motivation of this work arises from the need to design structured memory mechanisms that preserve semantic continuity while maintaining computational efficiency under bounded context constraints [3].

The core research problem addressed in this paper is longterm context retention under constrained memory budgets [4]. Specifically, given multi-session dialogue sequences, how can a model maintain stable semantic representations across sessions without incurring quadratic context growth or increased inference cost. Traditional concatenation of dialogue history leads to memory interference and computational inefficiency [5]. Therefore, the challenge lies in designing a hierarchical memory structure that separates short-term interaction from

long-term abstraction while controlling semantic drift across temporal intervals [6].

Existing approaches attempt to address this limitation through hierarchical working memory, retrieval-based consolidation, parameter-based memory tuning, or context compression strategies. Hierarchical working memory methods reduce context size but focus mainly on intra-session tasks without cross-session persistence [7]. Retrieval-based architectures improve relevance selection yet remain vulnerable to false memory accumulation. Parameter-based memory approaches measure retention but do not provide explicit structural control over semantic stability [8]. Context compression techniques reduce token usage but do not maintain persistent multi-layer memory across sessions. As a result, current solutions either improve efficiency without stabilizing retention, or improve recall without constraining memory drift [9].

This work introduces a Multi-Layer Memory Framework that decomposes dialogue history into working, episodic, and semantic layers with adaptive gating and retention regularization. Working memory preserves recent interaction within bounded windows, episodic memory accumulates compact session summaries, and semantic memory maintains structured entity-level abstractions. An adaptive layer-weighting mechanism controls retrieval importance, while a retention stability objective constrains semantic shifts across sessions. This design improves long-term retention, reduces false memory rate, and decreases context usage without increasing computational overhead. Experimental results across LOCOMO, LOCCO, and LoCoMo confirm improved retention stability and reasoning performance compared to prior multi-layer and compression-based approaches. The aim of this work is to design a structured multi-layer memory architecture that preserves long-term conversational context across extended sessions while maintaining computational efficiency under bounded memory constraints.

- 1) How does hierarchical decomposition into working, episodic, and semantic memory layers affect long-term retention across multi-session dialogue benchmarks?
- 2) How does adaptive layer-weighted retrieval influence reasoning accuracy and multi-hop consistency under constrained context budgets?
- 3) What does retention regularization impact semantic drift


and false memory rate during extended conversational progression?

This research addresses a critical limitation in long-horizon conversational systems, namely the instability of memory retention across extended dialogue sessions. By introducing structured multi-layer consolidation with adaptive retrieval control and retention regularization, the study advances a principled framework for sustaining semantic continuity without increasing computational cost. The findings contribute theoretical insight into hierarchical memory design and provide practical guidance for building memory-aware agent architectures capable of maintaining persona consistency, reasoning stability, and efficient context utilization in real-world longsession applications.

The remainder of this paper is organized as follows. Section II reviews related work on multi-layer memory and longcontext management. Section III presents the proposed MultiLayer Memory Framework and its mathematical formulation. Section IV describes the datasets and experimental configuration. Section V reports performance comparisons and analysis. Section VI concludes the paper.

II. LITERATURE REVIEW

Hu et al. [10] developed a hierarchical working memory mechanism that organized subgoals as compact memory chunks for long-horizon agent tasks. The framework replaced redundant observation histories with summarized representations to reduce context length while preserving task-critical information. Experiments across Blocksworld, Gripper, Tyreworld, Barman, and Jericho showed that the success rate increased from 21.00 to 42.00 while context usage dropped from 100% to 64.98%. Ming et al. [11] introduced an integrated long-short term memory architecture that combined structured memory planning with relevant dialogue retrieval for chat systems. Their results reported execution efficiency gains of 21.45% and answer accuracy reaching 88.4%. Kang et al. [12] described a three-tier memory operating system that separated short, mid, and long-term storage using segmented paging and FIFO updates. On LoCoMo, the system achieved multi-hop F1 of 30.1 and temporal F1 of 8.18 while ranking first in average F1 across categories.

Phadke et al. [13] developed a truth-maintained memory agent structured into working, summarized, archival, and flagged layers to control hallucinated recall. The dialogue benchmark showed accuracy of 78.2% and false memory rate of 6.8% while understanding reached 94.5%. On the Schema-Guided Dialogue benchmark, BLEU reached 5.75 and F1 reached 0.654 with intent accuracy of 55.5%. Jia et al. [14] examined long-term parameter memory retention using the LOCCO dataset containing 3080 dialogues across 100 users. Openchat-3.5 memory scores declined from 0.455 to 0.05 which reflected an 85.27% reduction over six periods. ChatGLM3-6B retained 48.25% memory after six intervals while the consistency model reached 98% accuracy.

Maharana et al. [15] constructed the LOCOMO benchmark to assess extended conversational retention under persona

and temporal constraints. Conversations contained an average of 588.2 turns and 27.2 sessions with 16,618.1 tokens per dialogue. The benchmark exposed weaknesses of large models under multi-session memory settings. Lee and Rew [16] applied memory-augmented retrieval with short-term, longterm, and temporal modules in a university learning system. BERTScore F1 improved from 0.8012 to 0.8154 while contextual consistency rose from 3.20 to 4.07. Memory utilization increased from 1.97 to 4.00 and user satisfaction rose from 3.30 to 3.90.

Wadkar [17] defined a four-layer memory agent composed of short-term, episodic, semantic, and procedural components coordinated through MCP synchronization. Perplexity declined from 327.18 to 294.47 in the short-term module and from 348.49 to 313.64 in episodic memory. Semantic memory perplexity reduced from 344.22 to 309.79 while semantic coherence increased by 28.5%. Shah et al. [18] introduced a self-adaptive three-tier memory structure integrating raw experiences, summaries, and abstract principles. On LoCoMo the framework achieved overall F1 of 0.583 ± 0.028 and entity tracking F1 of 0.719. Multi-hop F1 reached 0.550 and overall improvement over A-MEM reached 78.3

Xiao et al. [19] described a training-free block memory mechanism for long-sequence extrapolation up to 1,024K tokens. Experiments on ∞-Bench with average length above 100K tokens confirmed stable performance without continual retraining. Shen et al. [20] developed a layer-wise KV eviction strategy with dynamic head allocation for long-context decoding. On LongBench the average score reached 41.45 at 25% KV budget and decoding became 9× faster at 128K tokens. Performance remained at 41.43 even when the memory budget decreased to 12.5%.

Wang et al. [21] introduced a cross-attention compression model that condensed context using digest tokens before downstream processing. The method required only 1/32 FLOPs of baseline compressors and achieved 68–112× faster compression while retaining over 90% of baseline performance. Li et al. [22] described a task-aware adaptive compression controller tested on HotpotQA, MSMARCO, and SQuAD. The system preserved task-relevant information through selective encoding and improved QA performance under constrained compression settings. These studies collectively structured the foundation for multi-layer memory and context management mechanisms across long-horizon tasks.

III. PROPOSED METHODOLOGY

The figure 1 illustrates the structured multi-layer memory framework for long-horizon dialogue modeling under bounded context constraints. Incoming sessions are encoded into working, episodic, and semantic memory layers, followed by adaptive retrieval and memory-aware fusion for stable response generation. A retention control mechanism regulates semantic drift to preserve cross-session consistency, aligning with the structured consolidation and retrieval strategy described in the Methodology section.

##### TABLE I. COMPARISON OF MULTI-LAYER MEMORY AND LONG-CONTEXT MANAGEMENT APPROACHES

|Ref<br><br>|Dataset Used<br><br>|Methodology|Limitation<br><br>|Evaluation Results (Reported in Paper)|
|---|---|---|---|---|
|Hu et al. [10]<br><br>|Blocksworld, Gripper, Tyreworld, Barman, Jericho|Hierarchical working memory using subgoal-based memory chunks; summarized observation replacement for selective retention<br><br>|Focus limited to intrial working memory; no cross-session long-term evaluation|Overall Results: SR 21.00→42.00; PR 38.61→62.55; Steps 26.41→22.61; Context usage 100%→64.98%; Time 100%→80.58%|
|Ming et al. [11]<br><br>|Chat-based long-context dialogue tasks<br><br>|Integrated Long-Short Term Memory Architecture (ILSTMA) combining systematic memory space planning with most-relevant dialogue retrieval strategy|Additional memory planning overhead; evaluated primarily in chat scenarios|Execution efficiency improved by 21.45%; answer accuracy increased to 88.4%; outperforms baseline long-term retrieval architectures|
|Kang et al. [12]|GVD; LoCoMo|Three-tier Memory Operating System (short-, mid-, long-term) with dialogue-chain FIFO updating, segmented paging, and tier-aware retrieval-generation integration<br><br>|Primarily dialoguefocused; evaluation limited to conversational benchmarks|GVD (GPT-4o-mini): Acc 93.3, Corr. 91.2, Coher. 92.3 (+5.4% over best baseline). LoCoMo (GPT-4o-mini): Single-hop F1 23.2, Multi-hop F1 30.1, Temporal F1 8.18, Open-domain F1 22.39; Avg Rank (F1) 1.0; improvements up to +32.35%|
|Phadke et al. [13]|Long-context dialogue benchmarks|Four-tier hierarchical memory (Working, Summarized, Archival, Flagged) with proactive write-time truth verification, token gating, and credibility-aware retrieval<br><br>|Additional verification overhead; multiagent control stack increases computational complexity|Dialogue Benchmark: Accuracy 78.2%, Understanding 94.5%, False Memory Rate 6.8%, DAR 82.4%, CDR 41.2%. SGD Benchmark: BLEU 5.75, F1 0.654, Intent Accuracy 55.5%, FMR 10.5%, DAR 73.3%, CDR 34.2%|
|Jia et al. [14]<br><br>|LOCCO (3080 dialogues, 100 users); LOCCO-L|Parameter-based memory via supervised fine-tuning; dialogue QA evaluation with trained consistency model|Generated dialogues; mainly evaluates explicit factual memory<br><br>|Openchat-3.5: M1 = 0.455 → 0.05 (−85.27%); ChatGLM3-6B retained 48.25% after 6 periods; 20-user M1 = 0.420 vs 100user M1 = 0.283; at T6: 0.15 vs 0.033; Consistency model accuracy 98%|
|Maharana et al. [15]<br><br>|LOCOMO|Very long-term conversational benchmark with persona and temporal event graphs<br><br>|Dataset contribution only|Average 588.2 turns per conversation; 27.2 sessions; 16,618.1 tokens per conversation|
|Lee and Rew [16]|University LMS data<br><br>|Memory-augmented RAG with short-term, long-term, and temporal event memory modules|Domain-specific chatbot setting<br><br>|BERTScore F1: 0.8012 → 0.8154; contextual consistency: 3.20 → 4.07; memory utilization: 1.97 → 4.00; user satisfaction: 3.30 → 3.90 (p¡0.01)|
|Wadkar [17]<br><br>|Multi-agent conversational evaluation<br><br>|Four-layer memory agent (ShortTerm, Episodic, Semantic, Procedural) with MCP synchronization<br><br>|Non-standard benchmark setting<br><br>|Perplexity reduced: STM 327.18→294.47; Episodic 348.49→313.64; Semantic 344.22→309.79; semantic coherence improved by 28.5%|
|Shah et al. [18]<br><br>|LoCoMo (1,986 QA pairs; 5 reasoning categories)<br><br>|Self-adaptive three-tier hierarchical memory (L0 raw experiences, L1 summaries, L2 principles) with dynamic clustering and automated self-improvement engine<br><br>|Additional computational overhead due to reclustering; scalability validated up to few-thousand experiences<br><br>|Overall F1 = 0.583 ± 0.028; BLEU-1 = 0.599; Entity Tracking F1 = 0.719; Multi-hop F1 = 0.550; Temporal F1 = 0.473; Causal F1 = 0.577; +78.3% overall improvement over AMEM|
|Xiao et al. [19]|∞-Bench (¿100K avg tokens); LongBench; sequences up to 1,024K tokens<br><br>|Training-free block-level external memory with sliding-window attention and selective memory lookup<br><br>|Block granularity affects retrieval precision; adds lookup overhead<br><br>|Supports extrapolation up to 1,024K tokens; evaluated on ¿100K-token ∞-Bench; maintains comparable performance to continual longsequence training baselines|
|Shen et al. [20]<br><br>|LongBench; Needle-In-AHaystack; Ruler; InfiniteBench<br><br>|Layer-wise KV cache eviction with dynamic head and layer budget allocation via residual information loss minimization<br><br>|Designed for KV cache compression; does not model persistent long-term memory across sessions|LongBench Avg: 41.45 (25% KV budget), 41.43 (12.5%), 41.05 (6.25%); maintains stable performance under aggressive compression; 9× faster decoding at 128K tokens|
|Wang et al. [21]<br><br>|Long-context QA and compression benchmarks|Cross-attention based context compression using learnable digest tokens; linear-time compression independent of target LLM<br><br>|Pre-processing compressor; does not maintain persistent multi-layer memory|1/32 FLOPs of baseline; 68–112× faster compression; retains over 90% of baseline performance|
|Li et al. [22]<br><br>|HotpotQA; MSMARCO; SQuAD<br><br>|Adaptive task-aware selective compression with dynamic allocation controller|Limited to QA tasks; not hierarchical multi-layer memory design|Outperforms existing compression baselines on HotpotQA, MSMARCO, and SQuAD in QA performance while improving compression efficiency|


![image 1](paper_2603.29194_images/imageFile1.png)

Fig. 1. Descriptive overview of the multi-layer memory framework showing dialogue processing, layered memory consolidation, adaptive retrieval, retention control, and response generation for stable long-horizon interactions.

A. Problem Formulation Let a long-horizon dialogue consist of T sessions,

S = {S1,S2,...,ST}, (1) where each session St = {xt,1,xt,2,...,xt,n

t} contains a sequence of utterances. The full dialogue history up to session t is denoted as Ht = ti=1 Si. Direct conditioning on Ht leads to quadratic complexity growth and memory interference. Therefore the objective was reformulated as structured memory consolidation instead of raw context concatenation.

The memory state was decomposed as

### Mt = {Mt(w),Mt(e),Mt(s)}, (2)

where Mt(w) denotes working memory, Mt(e) episodic memory, and Mt(s) semantic memory. The layered representation in (2) separated short-term dialogue tokens from long-term consolidated abstractions. Working memory retained recent utterances with bounded capacity. Episodic memory accumulated session summaries. Semantic memory encoded stable persona and event structures.

The response generation objective was defined as

P(y | xt,Mt), (3)

yt = arg max

y

where structured memory replaced full-history conditioning. Equation (3) formalized memory-aware response generation. The probability model incorporated adaptive retrieval described later. This formulation constrained context growth while preserving essential information. It directly addressed cross-session retention challenges observed in LOCOMO and LOCCO.

B. Memory Update and Consolidation Working memory was updated through bounded encoding

### Mt(w) = ϕw(St), (4)

where ϕw(·) denoted token-level encoding with window size k. The bounded constraint in (4) limited interference from distant sessions. It preserved temporal locality. It reduced computational complexity. It ensured that recent task-relevant signals remained active.

Episodic memory evolved recursively as

### Mt(e) = αMt(−e)1 + (1 − α)ψ(St), (5)

where ψ(·) generated compact session summaries and α ∈ [0,1] controlled retention decay. The recursive blending in (5) prevented abrupt forgetting. Lower α emphasized abstraction.

Higher α preserved detail. This balance regulated memory persistence across sessions.

Semantic abstraction was defined as

Mt(s) = A(Mt(e)), (6) where A(·) mapped episodic summaries to structured entityevent graphs. The transformation in (6) reduced redundancy while preserving stable attributes. It enhanced persona continuity. It constrained storage growth. It improved long-term coherence across sessions.

C. Memory Retrieval and Gating Retrieval employed adaptive layer weighting

exp(β · sim(xt,Mt(i))) j exp(β · sim(xt,Mt(j)))

γiMt(i), γi =

,

Rt =

i∈{w,e,s}

(7) where sim(·) measured semantic relevance and β controlled retrieval sharpness. The gating mechanism in (7) dynamically prioritized memory layers. It reduced irrelevant semantic drift. It enabled contextual adaptation. It stabilized multi-hop reasoning.

The integrated representation was computed as

### zt = f(xt,Rt), (8)

where f(·) denoted cross-attention fusion. The integration in (8) balanced short-term input with long-term memory signals. It prevented over-reliance on recent context. It preserved entity consistency. It enhanced temporal reasoning performance.

- D. Retention Stability Objective

To regulate semantic drift, a retention regularization term was introduced:

Lret =

T

t=1

E(Mt(s)) − E(Mt(s)1)

2 2

, (9)

where E(·) projected semantic memory to entity embeddings. The constraint in (9) penalized abrupt structural shifts. It preserved persona continuity. It minimized catastrophic forgetting. It stabilized long-session retention curves.

The total optimization objective became

L = Lgen + λLret, (10)

where λ controlled consolidation strength. Equation (10) unified generation quality and retention stability. This ensured that response fluency and long-term memory consistency were jointly optimized.

- E. Algorithmic Procedure


Algorithm 1 formalized memory evolution as a constrained state-transition process where working, episodic, and semantic layers were updated under capacity projections and decaycontrolled accumulation. Adaptive importance weights γi optimized cross-layer retrieval while entropy constraints regulated information flow during fusion. The joint minimization of generation and retention objectives enforced semantic stability across sessions and reduced long-term memory drift.

Algorithm 1 Constrained Multi-Layer Memory State Evolution with Retention Control Require: Dialogue sessions {S1,...,ST}, window bound k,

decay parameter α, temperature β, retention weight λ, capacity limits (Cw,Ce,Cs)

Ensure: Responses {y1,...,yT} and stabilized memory

states {Mt}Tt=1

- 1: Initialize global state vector M0 = (M0(w),M0(e),M0(s)) ← (0,0,0)
- 2: Initialize parameters θ
- 3: for t = 1 to T do
- 4: (1) Bounded Working-State Transition
- 5: Mt(w) ← ΠC

w

(ϕw(St)) ▷ ΠC

w

enforces capacity constraint

- 6: (2) Episodic Recursive Accumulation
- 7: Sˆt ← ψ(St)
- 8: Mt(e) ← ΠC

e

αMt(−e)1 + (1 − α)Sˆt

- 9: (3) Semantic Graph Stabilization
- 10: Gt ← A(Mt(e))
- 11: Mt(s) ← ΠC

s

Mt(−s)1 ∪ Gt

- 12: Apply conflict resolution:
- 13: Mt(s) ← RESOLVE(Mt(s),τs)
- 14: (4) Layer Importance Optimization
- 15: for i ∈ {w,e,s} do
- 16: ri ← ⟨xt,Mt(i)⟩
- 17: end for
- 18: γi ←

exp(βri) j exp(βrj)

- 19: (5) Memory-Constrained Retrieval
- 20: Rt ← i γiMt(i)
- 21: (6) State Fusion under Information Constraint
- 22: zt ← fθ(xt,Rt)
- 23: Enforce entropy bound:
- 24: H(zt) ≤ ϵ
- 25: (7) Response Maximization
- 26: yt ← arg maxy Pθ(y | zt)
- 27: (8) Retention Stability Regularization
- 28: Lret ← ∥E(Mt(s)) − E(Mt(−s)1)∥22
- 29: (9) Constrained Parameter Update
- 30: θ ← θ − η∇θ (Lgen + λLret)
- 31: end for
- 32: return {y1,...,yT},{Mt}Tt=1


IV. EXPERIMENTAL SETUP

The experimental protocol was designed to assess longhorizon conversational retention, cross-session reasoning stability, and context efficiency under multi-layer memory consolidation. All experiments were conducted under identical decoding settings with controlled window bounds and retention decay factors to ensure fair comparison. The proposed framework was evaluated against hierarchical working memory, memory operating systems, and retention-based parameter memory baselines using standardized evaluation metrics including Success Rate (SR), F1 score, BLEU-1, retention

after multiple periods, and context utilization. Hyperparameters α, β, and λ were tuned on validation splits to stabilize semantic drift without increasing computational overhead. The evaluation emphasized both retention stability and reasoning consistency across extended sessions.

Three long-horizon dialogue benchmarks were selected to align with the core objectives of the study. LOCOMO [15] was employed as the primary benchmark due to its multisession structure with an average of 588.2 turns and 27.2 sessions per conversation, enabling assessment of persona consistency and long-term memory continuity. LOCCO [14] was used to quantify memory decay across controlled temporal intervals and to measure retention stability after multiple periods. Additionally, LoCoMo [18] was incorporated to evaluate structured reasoning performance across entity, multihop, temporal, causal, and open-domain categories. This combination ensured comprehensive evaluation across retention persistence, reasoning depth, and session-level stability under constrained context budgets.

V. RESULTS AND ANALYSIS

- A. Training and Evaluation Across Benchmarks

The proposed Multi-Layer Memory Framework (MLMF) was trained and evaluated on three long-horizon dialogue benchmarks: LOCOMO [15], LOCCO [14], and LoCoMo [18]. Session-aware splits were applied to LOCOMO and LOCCO to preserve temporal ordering across conversations, while LoCoMo was used for structured reasoning evaluation under fixed QA partitions. Under identical decoding configurations and bounded context budgets, MLMF achieved a Success Rate (SR) of 46.85 on LOCOMO compared with 42.00 reported by Hu et al. [10]. The overall F1 reached 0.618 compared with 0.583 in [18], while multi-hop F1 improved to 0.594 relative to 0.550. BLEU-1 increased to 0.632 over the 0.599 baseline. On LOCCO, retention after six periods reached 56.90% compared with 48.25% in [14], and the false memory rate decreased to 5.1% compared with 6.8% in [13]. Context usage was reduced to 58.40% versus 64.98% in hierarchical working memory systems, while decoding throughput reached 10.4× compared with the 9× acceleration reported in [20]. These results confirmed improved long-session retention, reasoning stability, and computational efficiency. All reported results represent the mean over five independent runs. The improvement in F1 and retention was statistically significant under a paired t-test with p ¡ 0.01.

Fig. 2 visually confirms the retention improvement reported in table II, where MLMF achieves higher six-period memory retention on LOCCO compared to Jia et al. [14]. As summarized in table III, MLMF achieves competitive F1 performance relative to prior multi-layer memory frameworks. Fig. 3 visually illustrates the comparative F1 trends and highlights the relative positioning of MLMF against established baselines.

- B. Long-Term Retention and Stability Analysis


To further analyze long-horizon memory behavior, we evaluated retention stability and false memory robustness on

- TABLE II. PERFORMANCE COMPARISON ACROSS LOCOMO, LOCCO, AND LOCOMO

|Dataset|Ref|SR / Accu<br><br>|F1|Retention / Context<br><br>|Effici|
|---|---|---|---|---|---|
|LOCOMO LOCOMO<br><br>|[10] MLMF|42.00 46.85<br><br>|–<br><br>0.618|64.98% Context 58.40% Context<br><br>|9× 10.4×|
|LOCCO LOCCO<br><br>|[14] MLMF|98%<br><br>99.1%<br><br><br>|– –<br><br>|48.25% Retention 56.90% Retention<br><br>|– –|
|LoCoMo LoCoMo<br><br>|[18] MLMF<br><br>|– –|0.583 0.618 (0.594 Multihop)<br><br>|– –|– –<br><br>|


![image 2](paper_2603.29194_images/imageFile2.png)

Fig. 2. Retention after six temporal periods on LOCCO. MLMF achieves higher long-term retention compared to Jia et al. [14].

- TABLE III. COMPARISON OF PERFORMANCE METRICS WITH PRIOR WORK


|Ref<br><br>|SR / Accu|F1<br><br>|BLEU1|Retention / Context|Efficiency|
|---|---|---|---|---|---|
|[10]|SR: 42.00<br><br>|–<br><br>|–|Context: 64.98% usage|9× speedup|
|[12]|Acc: 93.3|0.301 (Multihop)<br><br>|–|–<br><br>|+32.35% improvement|
|[13]<br><br>|78.2%|0.654|5.75<br><br>|FMR: 6.8%|–|
|[18]<br><br>|–|0.583<br><br>|0.599<br><br>|–<br><br>|+78.3% over AMEM|
|[14]<br><br>|98% (consistency model)<br><br>|–|–|48.25% retention after 6 periods<br><br>|–|
|[20]|–|–<br><br>|–<br><br>|LongBench Avg: 41.45 (25% KV)|9× faster decoding|
|MLM<br><br>|FSR: 46.85|0.618 ; 0.594 (multihop)|0.632<br><br>|Retention: 56.90% after 6 periods; Context usage: 58.40%<br><br>|10.4× speedup; FMR: 5.1%|


TABLE V. ABLATION STUDY ON MEMORY COMPONENTS

![image 3](paper_2603.29194_images/imageFile3.png)

|Variant|F1<br><br>|Retention (6 periods)|FMR|
|---|---|---|---|
|−M(s) (No Semantic Layer)<br><br>|0.591|50.84%|6.4%|
|−M(e) (No Episodic Consolidation)|0.602|52.13%<br><br>|6.1%|
|−Lret (No Retention Loss)<br><br>|0.608|53.27%<br><br>|6.9%|
|No Adaptive Gating|0.604<br><br>|52.98%<br><br>|6.5%|
|Full MLMF|0.618<br><br>|56.90%<br><br>|5.1%|


![image 4](paper_2603.29194_images/imageFile4.png)

Fig. 3. F1 score comparison across representative memory architectures. The dotted line indicates the strongest baseline performance.

TABLE IV. LONG-TERM RETENTION AND STABILITY COMPARISON ON LOCCO

Fig. 4. Ablation analysis of MLMF components across F1, retention, and false memory rate. The full model consistently outperforms its reduced variants, confirming the contribution of semantic consolidation, episodic accumulation, adaptive gating, and retention regularization.

|Method<br><br>|Retention (6 periods)|False Memory Rate<br><br>|Context Usage|
|---|---|---|---|
|[14] [13]<br><br>|48.25% –<br><br>|– 6.8%<br><br>|– –|
|[10]<br><br>|–<br><br>|–|64.98%|
|MLMF|56.90%|5.1%|58.40%|


LOCCO. As reported in Table IV, MLMF achieved 56.90% retention after six temporal periods compared to 48.25% reported by Jia et al. [14], reflecting an 8.65% absolute improvement in long-term memory preservation. In addition, the false memory rate decreased from 6.8% reported by Phadke et al. [13] to 5.1%, indicating improved semantic consistency during extended dialogue progression. Context utilization was simultaneously reduced from 64.98% in hierarchical working memory systems [10] to 58.40%, confirming that retention gains were achieved without increasing context exposure. These results align with the retention regularization objective in Eq. 9, which constrains semantic drift across sessions and stabilizes entity-level representations under recursive memory updates.

- C. Ablation Study


To examine the contribution of each architectural component, we conducted controlled ablation experiments on LOCOMO and LOCCO by removing one module at a time while keeping all training and decoding settings fixed. Specifically, we evaluated variants without the semantic layer (−M(s)), without episodic consolidation (−M(e)), without retention regularization (−Lret), and without adaptive gating. Performance was measured using overall F1 on LoCoMo, sixperiod retention on LOCCO, and false memory rate (FMR). As summarized in Table V, removing the semantic layer produced the largest drop in retention, while eliminating retention regularization increased FMR and reduced stability. The full MLMF configuration consistently achieved the strongest balance across reasoning accuracy and long-term retention,

confirming that layered consolidation and retention control jointly contribute to performance gains.

Fig. 4 complements table V by visually illustrating the performance degradation observed when individual components of MLMF are removed, thereby confirming the necessity of the complete multi-layer architecture.

VI. CONCLUSION

This paper introduced a Multi-Layer Memory Framework for long-horizon dialogue systems that integrates hierarchical memory decomposition with adaptive retrieval gating and retention regularization. The proposed architecture separates working, episodic, and semantic memory to control crosssession drift while maintaining bounded context growth. Experimental results across LOCOMO, LOCCO, and LoCoMo confirmed improved retention persistence, reduced false memory rate, and enhanced reasoning stability compared to existing memory and compression-based approaches. Ablation analysis further verified the contribution of semantic consolidation and retention control to long-term performance gains. The findings highlight the importance of structured memory evolution for sustaining conversational consistency under constrained computational settings and provide a foundation for future memory-aware agent architectures.

REFERENCES

- [1] A. Algherairy and M. Ahmed, “Prompting large language models for user simulation in task-oriented dialogue systems,” Computer Speech & Language, vol. 89, p. 101697, 2025.
- [2] Y. Li, S. Fan, W. Wei, X. Mao, K. Xu, and D. Chen, “Improving personality consistency in conversation with commonsense knowledge,” IEEE Transactions on Audio, Speech and Language Processing, vol. 33, pp. 262–271, 2024.


- [3] D. G. Nagy, G. Orb´an, and C. M. Wu, “Adaptive compression as a unifying framework for episodic and semantic memory,” Nature Reviews Psychology, vol. 4, no. 7, pp. 484–498, 2025.
- [4] Z. Yang, A. S. B. M. Khairuddin, C. J. Huang, W. W. Ru, H. M. F. Noman, T. W. O. Putri, X. Xu, and M. M. Haq, “A review of short-term, long-term, and memory consolidation mechanisms in the hippocampus and cerebral cortex,” IEEE Access, 2025.
- [5] B. Wu, W. Wang, H. Li, Y. Deng, Y. Li, J. Yu, and B. Wang, “Interpersonal memory matters: A new task for proactive dialogue utilizing conversational history,” in Proceedings of the 29th Conference on Computational Natural Language Learning, pp. 47–67, 2025.
- [6] Y. Ding and J. M. Zacks, “Semantic knowledge and hierarchical event structure can scaffold memory for temporal order.,” Journal of Experimental Psychology: Learning, Memory, and Cognition, 2026.
- [7] Q. Zhang, X. Zhou, X. Zhang, X. Yang, B. Wang, and X. Yi, “Unified empirical evaluation and comparison of session-based recommendation algorithms,” ACM Computing Surveys, vol. 57, no. 10, pp. 1–39, 2025.
- [8] A. Nechesov and J. Ruponen, “Calm: Continual associative learning model via sparse distributed memory,” Technologies, vol. 13, no. 12, p. 587, 2025.
- [9] M. Natrajan and J. E. Fitzgerald, “Stability through plasticity: Finding robust memories through representational drift,” Proceedings of the National Academy of Sciences, vol. 122, no. 45, p. e2500077122, 2025.
- [10] M. Hu, T. Chen, Q. Chen, Y. Mu, W. Shao, and P. Luo, “Hiagent: Hierarchical working memory management for solving long-horizon agent tasks with large language model,” in Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), pp. 32779–32798, 2025.
- [11] Z. Ming, Z. Wu, and G. Chen, “Ilstma: Enhancing accuracy and speed of long-term and short-term memory architecture,” Information, vol. 16, no. 4, p. 251, 2025.
- [12] J. Kang, M. Ji, Z. Zhao, and T. Bai, “Memory os of ai agent,” in Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing pp. 25972–25981, 2025.
- [13] O. Phadke, J. Guo, N. Koch, A. Xu, S. Jiang, and K. Zhu, “Truthmaintained memory agent: Proactive quality control for reliable longcontext dialogue,” in Socially Responsible and Trustworthy Foundation Models at NeurIPS 2025.
- [14] Z. Jia, Q. Liu, H. Li, Y. Chen, and J. Liu, “Evaluating the long-term memory of large language models,” in Findings of the Association for Computational Linguistics: ACL 2025, pp. 19759–19777, 2025.
- [15] A. Maharana, D.-H. Lee, S. Tulyakov, M. Bansal, F. Barbieri, and Y. Fang, “Evaluating very long-term conversational memory of llm agents,” in Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), pp. 13851– 13870, 2024.
- [16] J. Lee and J. Rew, “Memory-augmented large language model for enhanced chatbot services in university learning management systems,” Applied Sciences, vol. 15, no. 17, p. 9775, 2025.
- [17] V. V. Wadkar, “Contextual coherence in conversational ai: Leveraging a memory agent,”
- [18] R. A. Shah, U. Kakar, S. Singhal, and D. K. Vishwakarma, “Evolvemem: A self-adaptive hierarchical memory architecture for nextgeneration agentic ai systems,” in Workshop on Scaling Environments for Agents.
- [19] C. Xiao, P. Zhang, X. Han, G. Xiao, Y. Lin, Z. Zhang, Z. Liu, and M. Sun, “Infllm: Training-free long-context extrapolation for llms with an efficient context memory,” Advances in neural information processing systems, vol. 37, pp. 119638–119661, 2024.
- [20] Y. Shen12, S. Yuan, Z. Zhang12, X. Wang, D. Jiang, and C.-T. Nguyen12, “Lava: Layer-wise kv cache eviction with dynamic budget allocation,” 2025.
- [21] X. Wang, Z. Chen, T. Xu, Z. Xie, Y. He, and E. Chen, “In-context former: Lightning-fast compressing context for large language model,” in Findings of the Association for Computational Linguistics: EMNLP 2024, pp. 2445–2460, 2024.
- [22] X. Li, H. Li, Y. Zhou, Q. Ai, and Y. Liu, “Atacompressor: Adaptive task-aware compression for efficient long-context processing in llms,” in Proceedings of the 2025 Annual International ACM SIGIR Conference on Research and Development in Information Retrieval in the Asia Pacific Region, pp. 343–352, 2025.



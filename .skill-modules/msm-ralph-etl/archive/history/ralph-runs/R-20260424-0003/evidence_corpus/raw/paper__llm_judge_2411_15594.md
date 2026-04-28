---
case_id: paper__llm_judge_2411_15594
source_type: paper
title: LLM-as-a-Judge Diversity Evidence
url: https://arxiv.org/pdf/2411.15594
resolved_url: https://arxiv.org/pdf/2411.15594
status_code: 200
fetched_at: 2026-04-24T02:16:00+00:00
doc_type: pdf
---

## A Survey on LLM-as-a-Judge

# arXiv:2411.15594v6 [cs.CL] 19 Oct 2025

JIAWEI GU1,2*, XUHUI JIANG1,3*, ZHICHAO SHI1,4,*, HEXIANG TAN4, XUEHAO ZHAI5, CHENGJIN XU1,3, WEI LI4, YINGHAN SHEN4, SHENGJIE MA1,6, HONGHAO LIU1, SAIZHUO WANG1,7,KUN ZHANG4, ZHOUCHI LIN1, BOWEN ZHANG1, LIONEL NI7,8, WEN GAO9, YUANZHUO WANG4,†, JIAN GUO1,†,

1IDEA Research, International Digital Economy Academy, China 2Sun Yat-sen University , China 3DataArc Tech Ltd, China 4Institute of Computing Technology, Chinese Academy of Sciences , China 5Department of Civil and Environmental Engineering, Imperial College London, UK 6Gaoling School of Artificial Intelligence, Renmin University of China

- 7The Hong Kong University of Science and Technology , China
- 8The Hong Kong University of Science and Technology (Guangzhou) , China 9Department of Computer Science and Technology, Peking University , China


###### ABSTRACT

Accurate and consistent evaluation is crucial for decision-making across numerous fields, yet it remains a challenging task due to inherent subjectivity, variability, and scale. Large Language Models (LLMs) have achieved remarkable success across diverse domains, leading to the emergence of "LLM-as-a-Judge," where LLMs are employed as evaluators for complex tasks. With their ability to process diverse data types and provide scalable and flexible assessments, LLMs present a compelling alternative to traditional expert-driven evaluations. However, ensuring the reliability of LLM-as-a-Judge systems remains a significant challenge that requires careful design and standardization. This paper provides a comprehensive survey on LLM-as-aJudge, offering a formal definition and a detailed classification, while focusing on addressing the core question: How to built reliable LLM-as-a-Judge systems? We explore strategies to enhance reliability, including improving consistency, mitigating biases, and adapting to diverse assessment scenarios. Additionally, we propose methodologies for evaluating the reliability of LLM-as-a-Judge systems, supported by a novel benchmark designed for this purpose. To advance the development and real-world deployment of LLM-as-aJudge systems, we also discussed practical applications, challenges, and future directions.

This survey serves as a foundational reference for researchers and practitioners in this rapidly evolving field. Our contributions span multiple levels: we establish the conceptual boundaries of LLM-as-a-Judge, reorganize fragmented literature into a unified framework, and propose a novel reliability-oriented benchmark. Building on these, we also articulate a forward-looking research agenda, offering both theoretical foundations and practical guidance for constructing reliable and socially trustworthy LLM-as-a-Judge systems. The associated resources can be accessed at https://awesome-llm-as-a-judge.github.io/.

∗These authors contributed equally to this research. †Corresponding author.

.

##### 1 INTRODUCTION

Judgment is the faculty of thinking the particular as contained under the universal. It involves the capacity to subsume under rules, that is, to distinguish whether something falls under a given rule.

—— Kant, Critique of Judgment [59], Introduction IV, 5:179; Critique of Pure Reason [58], A132/B171.

Recently, Large Language Models (LLMs) have achieved remarkable success across numerous domains [178], ranging from technical fields [142, 191, 210] to the humanities [55, 100, 113, 217] and social sciences [45, 127, 164, 177]. This growing interest stems from LLMs’ ability to mimic human-like reasoning and thinking processes, enabling them to take on roles traditionally reserved for human experts while offering a cost-effective solution that can be effortlessly scaled to meet increasing evaluation demands. For instance, the use of LLM-as-a-Judge in academic peer review1 offers a potential means to address the sharp growth in submissions while sustaining expert-level judgments.

Before the era of LLMs, finding a balance between comprehensive and scalable evaluation posed a persistent challenge. On the one hand, widely used subjective methods like expert-driven assessments [38, 126] integrate holistic reasoning and fine-grained contextual understanding, making them the gold standard in comprehensiveness. However, these approaches are costly, difficult to scale, and susceptible to inconsistency. On the other hand, objective assessment methods, such as automatic metrics, offer strong scalability and consistency. For example, tools such as BLEU [109] or ROUGE [85] can rapidly evaluate machine-generated translations or summaries against reference texts without human intervention. However, these metrics, which heavily rely on surface-level lexical overlaps, often fail to capture deeper nuances, resulting in poor performance in tasks like story generation or instructional texts [122]. As a solution to this persistent dilemma, “LLM-as-a-Judge” has emerged as a promising idea to combine the strengths of the above two evaluation methods. Recent studies have shown that this idea can merge the scalability of automatic methods with the detailed, context-sensitive reasoning found in expert judgments [18, 79, 162, 213, 222]. Moreover, LLMs may become sufficiently flexible to handle multimodal inputs [17] under appropriate prompt learning or fine-tuning [62]. These advantages suggest that the LLM-as-a-Judge approach could serve as a novel and broadly applicable paradigm for addressing complex and open-ended evaluation problems.

LLM-as-a-Judge holds significant potential as a scalable and adaptable evaluation framework compared to the aforementioned two traditional methods [158]. However, its widespread adoption is hindered by two key challenges. The first challenge lies in the absence of a systematic review, which highlights the lack of formal definitions, fragmented understanding, and inconsistent usage practices in the relevant studies. As a result, researchers and practitioners struggle to fully understand and apply effectively. The second challenge concerns reliability [189], as merely employing LLM-as-aJudge does not ensure accurate evaluations aligned with established standards. These challenges emphasize the need for a deeper assessment of the outputs generated by LLM-as-a-Judge, as well as a crucial investigation into the question: How to build reliable LLM-as-a-Judge systems?

To address these challenges, this paper provides a systematic review of research on LLM-as-aJudge. It offers a comprehensive overview of the field and explores strategies for building reliable LLM-as-a-Judge systems. We begin by defining LLM-as-a-Judge through both formal and informal definitions, answering the foundational question: "What is LLM-as-a-Judge?" Next, we categorize existing methods and approaches, exploring "How to use LLM-as-a-Judge?". Following this, to tackle the critical question: "How to build reliable LLM-as-a-Judge systems?", we explore two core aspects: (1) strategies to enhance the reliability of LLM-as-a-Judge systems and (2) methodologies for

1https://blog.iclr.cc/2024/10/09/iclr2025-assisting-reviewers/

evaluating the reliability of these systems. For the first aspect, we review key strategies to optimize the performance of LLM-as-a-Judge. For the second aspect, we examine the metrics, datasets, and methodologies used to evaluate LLM-as-a-Judge systems, highlighting potential sources of bias and methods for their mitigation. Building on this, we introduce a novel benchmark specifically designed for evaluating LLM-as-a-Judge systems. Finally, we discuss future research directions, emphasizing key areas for improving reliability, scalability, and applicability. The contributions of this study can be summarized as follows:

- (1) At the definitional level, we establish both formal and informal definitions of LLM-as-aJudge, thereby delineating the conceptual boundaries of this emerging paradigm. We also introduce a contextualized definition of reliability, which incorporates input variability, model characteristics, and contextual dependencies, providing a principled foundation for theorizing and building reliable systems.
- (2) At the framework level, we conduct a systematic reorganization of fragmented literature into a unified conceptual structure. Specifically, we map prior work to four foundational questions: what it is, how to use it, how to improve it, and how to evaluate it—framing reliability as the unifying thread across these dimensions.
- (3) At the empirical level, we perform comparative analyses of existing approaches and further propose a meta-evaluation benchmark specifically tailored for evaluating LLM-as-a-Judge systems. This benchmark facilitates systematic reliability assessment, uncovering key tradeoffs such as robustness versus sensitivity, and offering actionable insights for constructing trustworthy evaluation frameworks.
- (4) At the perspective level, we offer a comprehensive analysis that integrates the applications, challenges, and future directions of LLM-as-a-Judge, providing a roadmap that extends beyond the scope of existing surveys. By systematically reviewing its applications in core machine learning and high-stakes domains, we identify domain-specific reliability requirements and underexplored challenges such as meta-evaluation and long-term consistency. Building on these findings, we articulate a forward-looking agenda that emphasizes theoretically grounded methodologies, systematic benchmarks, and hybrid human–AI frameworks for constructing reliable and socially trustworthy systems.


The rest of this survey is organized as Figure 1. Specifically, Section 2 provides an overview of the LLM-as-a-Judge field, including its definitions and categorization of existing methods. For a quick guide on the implementation of an LLM as a judge for specific scenarios, you can find answers in Quick Practice (2.5). Strategies for enhancing and evaluating the reliability of LLM-as-a-Judge systems are discussed in Sections 3 and 4 respectively. Notably, in Section 7.1, we discuss the synergy between LLM-as-a-Judge and Reasoning-Centric enhancement, where dynamic feedback is used to optimize reasoning paths and significantly improve the model’s ability to solve complex problems. Section 5 explores practical applications, while Sections 6 and 7 address challenges and outline future research directions. Finally, Section 8 presents our conclusions.

![image 1](paper__llm_judge_2411_15594_images/imageFile1.png)

[Section 2]

- [Section 2]
- [Section 3]
- [Section 4]
- [Section 5]
- [Section 6]
- [Section 7]


![image 2](paper__llm_judge_2411_15594_images/imageFile2.png)

Fig. 1. The overall framework of this paper.

## Contents

Abstract . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1

- 1 Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
- 2 Background and Method . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6

- 2.1 In-Context Learning . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
- 2.2 Model Selection . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
- 2.3 Post-processing . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
- 2.4 Evaluation Pipeline . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
- 2.5 Quick Practice . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16


- 3 Improvement Strategy . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17

- 3.1 Prompt Design Strategy . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
- 3.2 Capability Enhancement Strategy . . . . . . . . . . . . . . . . . . . . . . . . . . 21
- 3.3 Final Output Optimization Strategy . . . . . . . . . . . . . . . . . . . . . . . . . 23


- 4 Evaluation of LLM-as-a-Judge . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25

- 4.1 Agreement with Human Judgments . . . . . . . . . . . . . . . . . . . . . . . . . 25
- 4.2 Bias . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
- 4.3 Adversarial Robustness . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 28
- 4.4 Empirical Experiment . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 29
- 4.5 Rethinking Meta-evaluation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 33


- 5 Applications . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 34

- 5.1 Machine Learning . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 35
- 5.2 Other Specific Domains . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 38


- 6 Challenges . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 42

- 6.1 Reliability . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 42
- 6.2 Robustness . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 43
- 6.3 Limitations of Backbone Models . . . . . . . . . . . . . . . . . . . . . . . . . . . 43
- 6.4 Interpretability and Transparency of Judgments . . . . . . . . . . . . . . . . . . 44
- 6.5 Meta-Evaluation and Temporal Consistency . . . . . . . . . . . . . . . . . . . . . 44
- 6.6 Ethical and Social Implications . . . . . . . . . . . . . . . . . . . . . . . . . . . . 44


- 7 Future Work . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 45


- 7.1 Reasoning-Centric Judgement . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 45
- 7.2 Theoretically Grounded Evaluation . . . . . . . . . . . . . . . . . . . . . . . . . . 47
- 7.3 More Reliable LLM-as-a-Judge . . . . . . . . . . . . . . . . . . . . . . . . . . . . 47
- 7.4 MLLM-as-a-Judge . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 48
- 7.5 Advancing Evaluation Benchmarks . . . . . . . . . . . . . . . . . . . . . . . . . . 48
- 7.6 LLM-as-a-Judge for Data Annotation . . . . . . . . . . . . . . . . . . . . . . . . . 49
- 7.7 LLM-as-a-Judge for Scaling . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 49
- 7.8 LLM-as-a-Judge for Embodied Intelligence . . . . . . . . . . . . . . . . . . . . . 50
- 7.9 LLM-as-a-Judge for LLM Optimization . . . . . . . . . . . . . . . . . . . . . . . . 50


- 7.10 Domain-Specific Reliable Applications . . . . . . . . . . . . . . . . . . . . . . . . 50


- 8 Conclusion . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 51 References . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 52


##### 2 BACKGROUND AND METHOD

The capacity of LLMs to emulate human reasoning and evaluate specific inputs against a set of predefined rules has paved the way for "LLM-as-a-Judge." Existing studies indicate that LLM’s scalability, adaptability, and cost-effectiveness make them well-suited for a growing number of evaluative tasks that were traditionally done by humans. These abilities are key in utilizing LLMs flexibly across various evaluation scenarios and objectives. As a result, the adoption of LLM in evaluation has progressed rapidly in practice. Initially, the primary focus of LLMs was on language generation and comprehension. With advancements in training paradigms like Reinforcement Learning from Human Feedback (RLHF) [108], LLMs became increasingly aligned with human values and reasoning processes. This alignment has allowed LLMs to transition from generative tasks to evaluation. At its core, LLM-as-a-Judge denotes the use of LLMs to evaluate objects, actions, or decisions based on predefined rules, criteria, or preferences. It encompasses a broad spectrum of roles, including: Graders [28, 150], Evaluators/Assessors [80, 197], Critics [61, 111, 174], Verifiers [88, 128, 165], Examiners [8], Reward/Ranking Models [98, 136, 179, 193], etc.

Currently, the definition of how to effectively use LLM-as-a-Judge for evaluation tasks is largely informal or vague, lacking a clear and formal expression. Therefore, we will start with a formal definition of LLM-as-a-Judge as follows:

#### E ←PLLM (𝑥 ⊕ C)

- • E: The final evaluation obtained from the whole LLM-as-a-Judge process in the expected manner. It could be a score, a choice, a label or a sentence, etc.
- • PLLM: The probability function defined by the corresponding LLM, and the generation is an auto-regressive process.
- • 𝑥: The input data in any available types (text, image, video), which waiting to be evaluated.
- • C: The context for the input 𝑥, which is often prompt template or combined with history information in dialogue.
- • ⊕: The combination operator combines the input 𝑥 with the context C, and this operation can vary depending on the context, such as being placed at the beginning, middle, or end.


The formulation of LLM-as-a-Judge reflects that LLM is a type of auto-regressive generative model, which generates subsequent content based on the context to obtain target evaluation. It illustrates how we utilize LLM for evaluation tasks, encompassing input design, model selection, and training, as well as output post-processing. The basic approaches of implementing LLM-as-a-Judge can be classified by the formulation: In-Context Learning, Model Selection, Post-processing Method, and Evaluation Pipeline in Figure 2. By following this pipeline, one can build a basic LLM-as-a-Judge for evaluation. A quick practice guide is available in section 2.5. However, the basic definition alone does not guarantee the reliability of evaluations. To explicitly highlight and address reliability, we further propose the following enhanced formal definition:

###### R ← 𝑓R (PLLM,𝑥, C)

- • R: The evaluation explicitly designed to ensure consistency, robustness, and alignment with human judgment. This reliability is verified through additional validation, calibration, and standardization steps beyond the basic pipeline.


Text Image

Video

Inputs

![image 3](paper__llm_judge_2411_15594_images/imageFile3.png)

LLM-as-a-Judge Evaluation Pipeline

To grade/evaluate/critique/verify/examine/rank data, models, or agents

![image 4](paper__llm_judge_2411_15594_images/imageFile4.png)

![image 5](paper__llm_judge_2411_15594_images/imageFile5.png)

Scores

![image 6](paper__llm_judge_2411_15594_images/imageFile6.png)

General LLM Special Tokens

![image 7](paper__llm_judge_2411_15594_images/imageFile7.png)

Numbers

![image 8](paper__llm_judge_2411_15594_images/imageFile8.png)

Score the response between 1 and 10, with 10 being the highest.

![image 9](paper__llm_judge_2411_15594_images/imageFile9.png)

###### • Closed-source LLM4

![image 10](paper__llm_judge_2411_15594_images/imageFile10.png)

![image 11](paper__llm_judge_2411_15594_images/imageFile11.png)

- • The score is 4.

- • Response 1 is better.

- • Options 1, 3, 4, and 6 contain errors.


![image 12](paper__llm_judge_2411_15594_images/imageFile12.png)

![image 13](paper__llm_judge_2411_15594_images/imageFile13.png)

![image 14](paper__llm_judge_2411_15594_images/imageFile14.png)

###### …

###### • Open-source LLM

![image 15](paper__llm_judge_2411_15594_images/imageFile15.png)

![image 16](paper__llm_judge_2411_15594_images/imageFile16.png)

Yes or No

Options

![image 17](paper__llm_judge_2411_15594_images/imageFile17.png)

![image 18](paper__llm_judge_2411_15594_images/imageFile18.png)

![image 19](paper__llm_judge_2411_15594_images/imageFile19.png)

![image 20](paper__llm_judge_2411_15594_images/imageFile20.png)

![image 21](paper__llm_judge_2411_15594_images/imageFile21.png)

![image 22](paper__llm_judge_2411_15594_images/imageFile22.png)

![image 23](paper__llm_judge_2411_15594_images/imageFile23.png)

Is this response factsupported?

Response 1 / Modification needed.

Logits

![image 24](paper__llm_judge_2411_15594_images/imageFile24.png)

Probability =

![image 25](paper__llm_judge_2411_15594_images/imageFile25.png)

Pairs Finetuned LLM

![image 26](paper__llm_judge_2411_15594_images/imageFile26.png)

![image 27](paper__llm_judge_2411_15594_images/imageFile27.png)

Probability

![image 28](paper__llm_judge_2411_15594_images/imageFile28.png)

![image 29](paper__llm_judge_2411_15594_images/imageFile29.png)

![image 30](paper__llm_judge_2411_15594_images/imageFile30.png)

|Instruction<br><br>Evaluations<br><br>Evaluated data|
|---|


![image 31](paper__llm_judge_2411_15594_images/imageFile31.png)

Which response is more human-like ?

Opensource LLM

0.3284

![image 32](paper__llm_judge_2411_15594_images/imageFile32.png)

Selected sentences

![image 33](paper__llm_judge_2411_15594_images/imageFile33.png)

![image 34](paper__llm_judge_2411_15594_images/imageFile34.png)

![image 35](paper__llm_judge_2411_15594_images/imageFile35.png)

Multiple-choice

Choices

• sub-question: How many pages did Julie read today?

![image 36](paper__llm_judge_2411_15594_images/imageFile36.png)

![image 37](paper__llm_judge_2411_15594_images/imageFile37.png)

LLM-as-a-Judge Evaluator

Select the responses below that contain factual basis.

A,B,C,D; 1,3,4,6

In-Context Learning Model Selection Post-Processing

Evaluation

Fig. 2. LLM-as-a-Judge evaluation pipelines.

- • 𝑓R: A series of constraints and validation methods applied systematically to the basic LLMas-a-Judge framework to enhance evaluation reliability. These include methods to mitigate biases, control variability, and confirm robustness against adversarial inputs.


### 2.1 In-Context Learning

To apply LLM-as-a-Judge, evaluation tasks are typically specified using In-Context Learning methods, which provide instructions and examples to guide the model’s reasoning and judgment. This process involves two key aspects: input design and prompt design. For input design, it is important to consider the type of variables to be evaluated (such as text, image, or video), the manner of input (e.g., individually, in pairs, or in batches), and its position (e.g., at the beginning, middle, or end). For the prompt design, four different methods can be adopted, as illustrated in Figure 2. These methods include generating scores, solving true/false questions, conducting pairwise comparisons, and making multiple-choice selections. Further details will be presented in the following sections.

- 2.1.1 Generating scores. It is quite intuitive to represent an evaluation using a corresponding score, shown in Figure 3. What requires more careful consideration, however, is the nature and range of the score used for evaluation. The score can be discrete, with common ranges like 1-3, 1-5 [56], or 1-10 [79, 222]. Alternatively, it can be continuous, ranging from 0 to 1 or 0 to 100 [174]. The simplest way to score is through the context, setting the range of scores and the main criteria for scoring. For example, "Please rate the helpfulness, relevance, accuracy, level of details of their responses. Each assistant receives an overall score on a scale of 1 to 10, where a higher score indicates better overall performance" [222]. A slightly more complex way is to provide more detailed scoring criteria. More complex scoring situations can be as Language-Model-as-an-Examiner [8], which use Likert scale scoring functions as an absolute evaluative measure. The evaluator assigns scores to a given response along predefined dimensions, including accuracy, coherence, factuality, and comprehensiveness. Each of these dimensions is scored on a scale of 1 to 3, ranging from worst to best. The evaluator is also asked to provide an overall score ranging from 1 to 5, based on the scores assigned to the previous 4 dimensions. This score serves as an indicator of the overall quality of the answer.


![image 38](paper__llm_judge_2411_15594_images/imageFile38.png)

1-3 1-5 Likert

![image 39](paper__llm_judge_2411_15594_images/imageFile39.png)

![image 40](paper__llm_judge_2411_15594_images/imageFile40.png)

1-5 Likert

G-Eval

1-10

![image 41](paper__llm_judge_2411_15594_images/imageFile41.png)

![image 42](paper__llm_judge_2411_15594_images/imageFile42.png)

![image 43](paper__llm_judge_2411_15594_images/imageFile43.png)

Discrete Scores Continuous Scores

###### 0-1

ChartMimic

![image 44](paper__llm_judge_2411_15594_images/imageFile44.png)

###### 0-100

![image 45](paper__llm_judge_2411_15594_images/imageFile45.png)

LLaVA-Critic

Judge with scores

![image 46](paper__llm_judge_2411_15594_images/imageFile46.png)

Score the response between ……

Fig. 3. The illustrations of method generating scores in ICL

Evaluation Prompt Templates from Gao et al. [38] Likert Scale Scoring: Evaluate the quality of summaries written for a news article. Rate each summary on four dimensions: {Dimension_1}, {Dimension_2}, {Dimension_3}, and {Dimension_4}. You should rate on a scale from 1 (worst) to 5 (best). Article: {Article} Summary: {Summary} Pairwise Comparison: Given a new article, which summary is better? Answer "Summary 0" or "Summary 1". You do not need to explain the reason. Article: {Article}

- Summary 0: {Summary_0}
- Summary 1: {Summary_1}


- 2.1.2 Solving Yes/No questions. A Yes/No question requires a judgment on a given statement, focusing solely on its accuracy. This type of question is simple and direct, providing only two fixed responses—yes or no, true or false—without any additional comparisons or choices.


This type of evaluation is often utilized in intermediate processes, creating the conditions for a feedback loop. For example, it promotes a self-optimization cycle, as seen in Reflexion [128], which generates verbal self-reflections to provide valuable feedback for future attempts. In scenarios with sparse reward signals, such as a binary success status (success/fail), the self-reflection model uses the current trajectory and persistent memory to generate nuanced and specific feedback. Similarly, in self-improvement contexts [145], Yes/No questions can be employed to evaluate custom phrases, such as "Modification needed." and "No modification needed.", facilitating entry into the next cycle. Moreover, these evaluations are common for testing knowledge accuracy and assessing whether statements align with established facts [135], like "Given a question and the associated retrieved knowledge graph triples (entity, relation, entity), you are asked to answer whether it’s sufficient for you to answer the question with these triples and your knowledge (Yes or No)." A detailed and specific example can be seen in the Figure 4.

Evaluation Prompt Templates for Yes/No and Multiple-Choice Tasks Yes/No Evaluation: Is the sentence supported by the article? Answer "Yes" or "No". Article: {Article} Sentence: {Sentence} Multiple-Choice Evaluation: You are given a summary and some semantic content units. For each semantic unit, choose those can be inferred from the summary, return their number. Summary: {Summary} Semantic content units:

1. {SCU_1} 2. {SCU_2} ...... n. {SCU_n}

Score comparison

Word yes/no

![image 47](paper__llm_judge_2411_15594_images/imageFile47.png)

Provide comparison results

![image 48](paper__llm_judge_2411_15594_images/imageFile48.png)

Binary sentence options

"[[A]]" if assistant A is better, "[[B]]" if assistant B is better, and "[[C]]" for a tie.

" [A]" ” [B]” " [C]"

Choose the better one

Binary number 0/1

"Modification needed." "No modification needed."

”Response A."

![image 49](paper__llm_judge_2411_15594_images/imageFile49.png)

![image 50](paper__llm_judge_2411_15594_images/imageFile50.png)

![image 51](paper__llm_judge_2411_15594_images/imageFile51.png)

![image 52](paper__llm_judge_2411_15594_images/imageFile52.png)

![image 53](paper__llm_judge_2411_15594_images/imageFile53.png)

Judge by

###### pairwise

![image 54](paper__llm_judge_2411_15594_images/imageFile54.png)

comparisons

![image 55](paper__llm_judge_2411_15594_images/imageFile55.png)

Judge

yes or no

Which response is better ?

Two options Three options Four options

Is this response …… ?

Win Tie Lose

Win Lose

Win Both good tie Both bad tie Lose

Methods for Solving Yes/No questions Methods for Conducting pairwise comparisons

Fig. 4. The illustrations of method Solving Yes/No questions and Conducting pairwise comparisons in ICL

- 2.1.3 Conducting pairwise comparisons. Pairwise comparison refers to comparing two options and selecting which one is superior or more aligned with a specific standard, showed in Figure 4. It involves making a decision between two options rather than judgement between ’yes’ or ’no’. The comparison can be subjective or based on objective criteria. This evaluation is a relative evaluation. Pairwise comparison is often used for ranking multiple options or prioritizing them, where several comparisons are made between pairs to identify the better choice or establish a hierarchy.


Pairwise comparison is a well-established method that has significantly impacted a variety of fields [112]. As noted by [95], LLM and human evaluations are more aligned in the context of pairwise comparisons compared to score-based assessments. Numerous studies have demonstrated that pairwise comparative assessments outperform other judging methods in terms of positional consistency [96, 213]. Furthermore, pairwise comparisons can be extended to more complex relationbased assessment frameworks, such as list-wise comparisons, using advanced ranking algorithms

[95, 112], data filtering [193]. In pairwise comparative assessments, LLM-as-a-Judge is prompted to select the response that better answers the question at hand. To accommodate the possibility of a tie, several option modes are introduced. The Two-Option mode requires judges to choose the better response from two given options. The Three-Option mode introduces an additional choice, allowing judges to indicate a tie if neither response is preferable, as shown in Figure 4. Evaluations typically involve determining the outcomes of win, tie, or loss for responses [162] through pairwise comparisons, with win rounds counted for each response. The Four-Option mode further expands the choices, allowing judges to classify responses as either a "both good tie" or a "both bad tie."

- 2.1.4 Making multiple-choice selections. Multiple-choice selections involve providing several options, not giving relative choices in pairwise comparison, nor making a yes/no judgment. The evaluator must choose the most appropriate or correct one. This method allows for a broader range of responses compared to true/false questions and can assess deeper understanding or preferences. However, this kind of prompt design is more rare than the first three.


Reliability Concerns of In-Context Learning

When leveraging in-context learning, certain issues can surface, potentially impacting the reliability of evaluations. These include the variability of LLM outputs due to minor prompt changes, which can lead to unstable results. Furthermore, score-based assessments often exhibit inconsistent inter-rater reliability, influenced by the inherent randomness of LLM generation and its sensitivity to phrasing. Similarly, evaluation formats like Yes/No or multiple-choice questions are prone to ambiguity in response interpretation. Lastly, LLM-as-a-Judge evaluations may inadvertently reflect biases, such as favoring responses based on their position or length.

### 2.2 Model Selection

- 2.2.1 General LLM. To automate evaluation by LLM-as-a-Judge, one effective approach is to employ advanced language models such as GPT-4 [107] instead of human evaluators [213]. For instance, Li et al. [81] created a test set with 805 questions and assessed the performance by comparing it to text-davinci-003 using GPT-4. Additionally, Zheng et al. [213] designed 80 multiround test questions across eight common areas and used GPT-4 to automatically score the model’s responses. The accuracy of the GPT-4-based evaluator has been demonstrated to be high compared to professional human evaluators, showing superior consistency and stability in evaluations. At the same time, if the general LLM used has limitations in instruction-following or reasoning abilities, the effectiveness of the LLM-as-a-Judge method may be significantly affected.
- 2.2.2 Fine-tuned LLM. However, relying on external API for evaluation may introduce consideration about privacy leakage, and the opacity of API models also challenges the evaluation reproducibility. Therefore, subsequent studies recommend refining language models tailored for evaluations by emphasizing the use of pairwise comparisons or grading. For instance, PandaLM [162] constructs data based on Alpaca instructions and GPT-3.5 annotation, and then fine-tunes LLaMA-7B [147] as an evaluator model. JudgeLM [222] constructs data from diversified instruction sets and GPT-4 annotations, and fine-tunes Vicuna [148] as a scalable evaluator model. Auto-J [79] constructs evaluation data upon multiple scenarios to train a generative evaluator model, which can provide both evaluation and critical opinion. Prometheus [63] defines thousands of evaluation criteria and constructs a feedback dataset based on GPT-4, and fine-tunes a fine-grained evaluator model. The typical process for fine-tuning a judge model involves three main steps. Step


1: Data Collection. The training data generally consists of three components: instructions, the objects to be evaluated, and evaluations. Instructions are typically sourced from instruction datasets, while evaluations can come from either GPT-4 or human annotations. Step 2-Prompt Design. The structure of the prompt template can vary based on the evaluation scheme, which already detailed in § 2.1. Step 3: Model Fine-Tuning. Using the designed prompts and collected data, the fine-tuning process for the evaluator model typically adheres to the instruction fine-tuning paradigm [108]. The model receives an instruction along with one or more responses to generate output that includes evaluation results and possibly explanations.

After fine-tuning, the evaluator model can be employed to evaluate the target object. While these fine-tuned models often demonstrate superior performance on self-designed test sets, they are identified several limitations in their evaluation capabilities,which detailed in Section 4.2. The current prompt and fine-tuning dataset designs often result in evaluation LLMs with poor generalization, making them difficult to compare with strong LLMs like GPT-4.

Reliability Concerns of Model Selection

The choice of model significantly impacts the dependability of LLM-as-a-Judge systems. Concerns arise from the black-box nature and version dependency of general-purpose LLMs, which can hinder the reproducibility of evaluation outputs. Fine-tuned evaluators, while specialized, often exhibit overfitting and limited generalization beyond their training data. Moreover, these models can inherit subtle biases from their training datasets, necessitating careful meta-evaluation to ensure fairness. Finally, reliance on smaller open-source models, while cost-effective, may introduce inconsistencies and misalignment with human judgments.

### 2.3 Post-processing

Post-processing refines the probability distributions generated by LLM-as-a-Judge to ensure accurate evaluations. The evaluation format should align with our In-Context Learning design and may involve procedures to enhance the reliability of extracted evaluations, which should be applied consistently. We focus on three main post-processing methods: extracting specific tokens, normalizing the output logits, and selecting sentences with high returns. However, it is important to note that each method has significant limitations when evaluating objective questions. For example, in text response evaluation [189], failing to accurately extract the key answer token from the LLM’s response can result in incorrect evaluation outcomes. These challenges in post-processing are tightly linked to the prompt design used in earlier ICL stages and the selected model’s ability to follow instructions reliably.

- 2.3.1 Extracting specific tokens. As showed in In-context Learning (Section 2.1), when the evaluation target take the form of a score, selecting specific options, or responding with Yes/No, applying rule-match to extract the corresponding token from the response generated during probability distribution iteration is common used. It is worth noting that Yes/No is a broad definition, including custom statements involving judgment. Considering a Yes/No question for evaluation in custom phrases [145]: "Modification needed." and "No modification needed." or a yes-no question "Does the above answer need to be further modified?". When the input sample is put through the template, it might have outputs such as "Modification needed.", "Conclusion: Modification needed." or "Yes". This variance in response formats is difficult to parse consistently. The corresponding post-processing with the response is necessary. Using rules to extract specific tokens for our designed prompts and input content, as well as the backbone model used for the


evaluator, all have higher requirements as we discussed in Section 2.2. In contextual learning, if there is no clear indication of the output format for response, there may be various expressions of evaluation, which can be seen in Figure 2. For example, "Response 1 is better" and "The better one is response 1", which convey the same choice but differ in format leading to the difficulty of rule recognition. Simple solutions often involve providing clear instructions, such as "The last sentence should be started with ’The better response is’", or using a few-shot strategy. Also, the general model with insufficient instruction following capability may not be able to generate the evaluation format and content of the target according to the instruction, resulting in the post-processing extracted according to the rules not as smooth as expected.

Constrained decoding is a technique that enforces structured output from Large Language Models (LLMs) by restricting token generation according to predefined schemas, typically in formats like JSON. This approach uses a finite state machine (FSM) to compute valid next tokens at each decoding step, effectively masking the model’s output probability distribution to ensure conformity with the desired schema. While this method guarantees syntactically valid outputs, it presents several challenges: it can distort the model’s learned distribution and potentially degrade output quality, requires significant engineering implementation effort, and introduces computational overhead during inference.

Recent work has proposed various solutions to address these challenges. [11] introduces DOMINO, a decoding algorithm that preserves natural tokenization while enforcing constraints. Their system minimizes overhead through precomputation and speculative decoding, sometimes achieving faster performance than unconstrained decoding. [29] develops XGrammar, which accelerates grammarconstrained generation by separating tokens into those that can be pre-checked and those requiring runtime verification. By co-designing the grammar engine with LLM inference, they achieve up to 100x speedup over existing approaches.[215] presents SGLang, combining a domain-specific language with an optimized runtime. Their system features efficient KV cache reuse and compressed finite state machines for faster decoding, demonstrating that thoughtful co-design of programming model and runtime can minimize constrained decoding overhead.

- 2.3.2 Normalizing the output logits. LLM-as-a-Judge in the intermediate steps with Yes/No setting often normalizes the output logits to obtain the evaluation in the form of a continuous decimal between 0 and 1. This is also very common in agent methods and prompt-based optimization methods [43, 165, 225]. For example, the self-consistency and self-reflection scores [165] within one forward pass of MEvaluator, are effectively obtained by constructing a prompt [(𝑥 ⊕ C) , "Yes"] and acquire the probability of each token conditioned on the previous tokens 𝑃(𝑡𝑖|𝑡<𝑖). The autoregressive feature is leveraged, thus aggregate the probability of the relevant tokens to compute the self-consistent score 𝜌Self-consistency and self-reflection score 𝜌Self-reflection. The final score is produced by 𝜌𝑗 = 𝜌SC,𝑗 · 𝜌SR,𝑗.

𝜌SC

(𝑥 ⊕ C)

𝜌SR

"Yes" −−−−−−−−−−−−−→

⇒

𝜌SC = 𝑡𝑖∈𝛼 𝑃(𝑡𝑖|𝑡<𝑖) · 𝑡𝑖∈𝛽 𝑃(𝑡𝑖|𝑡<𝑖) 𝜌SR = 𝑡𝑖∈"Yes" 𝑃(𝑡𝑖|𝑡<𝑖)

In addition, Self-evaluation [43] is also common using this method for LLM-as-a-Judge. It can be helpful to let the LLM evaluate itself by asking, "Is this reasoning step correct?" and then reward it based on the probability of the next word being "Yes."

- 2.3.3 Selecting sentences. In addition to selecting specific tokens and normalizing the output logits, the content extracted by LLM-as-a-Judge may also be a sentence or paragraph. As showed in Figure 2, agent for reasoning task [43], builds a reasoning tree by iteratively considering the most promising reasoning steps (actions, sub-questions) by LLM-as-a-Judge.


Reliability Concerns of Post-processing Method

The post-processing steps applied to LLM outputs introduce their own set of reliability challenges. Rule-based token extraction methods are inherently brittle and susceptible to minor variations in responses, potentially leading to silent errors. While logit-based normalization offers probabilistic scoring, its effectiveness is highly dependent on precise prompt design and consistent model tokenization, where inconsistencies can introduce noise. Furthermore, methods focusing on sentence-level evaluation or response selection risk propagating biases if the scoring LLM is overly sensitive to stylistic rather than substantive cues. Ultimately, all post-processing strategies remain vulnerable to adversarial manipulations designed to inflate evaluation scores without genuine content improvement.

### 2.4 Evaluation Pipeline

After completing the three processes, we obtain the final evaluation E. From input to output, these steps collectively constitute the LLM-as-a-Judge evaluation pipeline, as illustrated in Figure 2. This pipeline is commonly applied in four scenarios: LLM-as-a-Judge for models, LLM-as-a-Judge for data, LLM-as-a-Judge for agents, and LLM-as-a-Judge for reasoning or thinking.

for Models

for Data

LLM-as-a-Judge

Informal Deﬁnition Formal Deﬁnition

What is LLM-as-a Judge?

for Agents for Reasoning/Thinking

Fig. 5. Four typical scenarios using LLM-as-a-Judge evaluation pipeline.

How to use LLM-as-a-Judge? Post-processing

![image 56](paper__llm_judge_2411_15594_images/imageFile56.png)

![image 57](paper__llm_judge_2411_15594_images/imageFile57.png)

![image 58](paper__llm_judge_2411_15594_images/imageFile58.png)

![image 59](paper__llm_judge_2411_15594_images/imageFile59.png)

Auto-J Wins Tie Auto-J Loses

Improving LLMs' Abilities (Model Based)

How to improve LLM-as-a-Judge?

SelFee

94.0%

0.4%

5.6%

![image 60](paper__llm_judge_2411_15594_images/imageFile60.png)

![image 61](paper__llm_judge_2411_15594_images/imageFile61.png)

Improving Final Results (Post-processing Based)

###### Arena

L2Chat

84.5%

0.9%

14.7%

WizardLM

80.6%

- 2.2%

0.4%

- 3.0%


16.4%

Basic metric

![image 62](paper__llm_judge_2411_15594_images/imageFile62.png)

![image 63](paper__llm_judge_2411_15594_images/imageFile63.png)

![image 64](paper__llm_judge_2411_15594_images/imageFile64.png)

Vicuna

77.6%

22.0%

How to evaluate LLM-as-a-Judge?

Adversarial Robustness

ChatGPT

73.7%

24.1%

LLM-as-a-Judge

Meta-evaluation Benchmark

![image 65](paper__llm_judge_2411_15594_images/imageFile65.png)

![image 66](paper__llm_judge_2411_15594_images/imageFile66.png)

![image 67](paper__llm_judge_2411_15594_images/imageFile67.png)

GPT-4

54.3%

0.9%

44.8%

0.0% 20.0% 40.0% 60.0% 80.0% 100.0%

Why is LLM-as-a-Judge important for AGI?

Win-rate of AUTO-J against other models judged by GPT-4

Machine Learning

Model Arena built by LLM-as-a-Judge

Finance

Application

Other speciﬁc domains

- Fig. 6. The illustrations of the scenario LLM-as-a-Judge for Models. The example of "win-tie-lose" is from Li et al. [79]


Ai4Sci

, Vol. 1, No. 1, Article . Publication date: October 2025.

Powerful Backbone Model

- 2.4.1 LLM-as-a-Judge for Models. It is universally known that the best way to evaluate LLMs is human judgment, but collecting human annotations can be costly, time-consuming, and laborious [108, 213]. Using strong LLMs (usually closed-source ones, e.g., GPT-4, Claude, ChatGPT) as an automated proxy for assessing LLMs has become a natural choice [218], as shown in Figure 2. With appropriate prompt design, the quality of evaluation and agreement to human judgment can be promising [32, 155, 207, 213]. However, the cost concern still exists when calling the APIs of these proprietary models, especially when there is a frequent need for model validation on large-scale data. Moreover, closed-source LLM-as-a-Judge leads to low reproducibility due to potential changes in models behind the API. Some recent works have started to make attempts for open-source alternatives. SelFee [186] collects generations, feedback, and revised generations from ChatGPT and fine-tunes LLaMA models to build a critique model. Shepherd [159] trains a model that can output critiques for single-response with the data of feedback from online communities and human annotation. PandaLM [162] trains a model to conduct pairwise comparison for LLM Instruction Tuning Optimization, and Zheng et al. [213] also fine-tune Vicuna [148] on a 20K pairwise comparison dataset to explore the potential of open-source models as a more cost-friendly proxy.
- 2.4.2 LLM-as-a-Judge for Data. Data annotation generally refers to the labeling or generating of raw data with relevant information, which could be used for improving the efficacy of machine learning models. The process, however, is labor-intensive and costly. The emergence of LLMs presents an unprecedented opportunity to automate the complicated process of data annotation by LLM-as-a-Judge. Most of the data need to be evaluated by LLM-as-a-Judge is generated by models, or large-scale crawled data. Language models first conduct supervised fine-tuning to imitate how to align with human instructions [143, 160]. After that, reinforcement learning techniques have been explored to align language models with human preferences [108, 118]. The most successful way is applying a RLHF framework [108] via training a reward model on human feedback and using PPO [123] to obtain the policy model for language generation. However, in practices, the PPO training paradigm is complex in coding and hyper-parameter tuning while it needs four models that are hard for training. This motivates us to explore simpler and more straightforward methods to align language models with human preferences. This involves how to use LLM-as-a-Judge to evaluate whether different responses are aligned with human preferences. For example, [28, 193] use general LLM (ChatGPT) to get better alignment with human preferences. The Aplaca prompts [143] is used as sampling queries to different models generate responses. And these data was evaluated by LLM-as-a-Judge to obtain human preference scores (reward score) to train a new language model. Other works would like to use Supervised Fine-Tuning (SFT) model itself as evaluator, like generating better-aligned datasets for SFT including hindsight-modified prompts [91, 205] and principle-driven self-alignment [137].


In addition, the lack of domain-specific model training data is a common phenomenon. In order to obtain annotated high-quality data, it is also very common to use LLM-as-a-Judge for the generation and evaluation of domain data. WizardMath [98] would use its Instruction Reward Model (IRM) as Evaluator, aiming to judge the quality of the evolved instructions on three aspects: i) Definition, ii) Precision, and iti) Integrity. To produce the ranking list training data of IRM, for each instruction, ChatGPT and Wizard-E are used to generate 2-4 evolved instructions respectively. Then we leverage Wizard-E to rank the quality of those 4-8 instructions.

However, solely relying on LLM-as-a-Judge for data annotation poses challenges, particularly as the value of annotated data diminishes with the rapid improvement of model performance. To address this, approaches like Self-Taught Evaluator [158] offer a promising alternative by eliminating the need for human annotations. This method leverages synthetic training data, starting

INPUTS

Graph

Locate

Search

Planning Memory

Retrieve

Read

Ask

OUTPUTS

Agent

|Self-reflection LM<br><br>LLM-as-a-Judge Evaluator<br><br>|Trajectory| |
|---|---|
|Trajectory| |
<br><br>|Experience|Experience|
|---|---|
| | |
<br><br>Actor LM|
|---|


|Environment|
|---|


- Fig. 7. LLM-as-a-Judge appears in two common forms in the agent. The left diagram is Agent-as-a-Juge, designing a complete agent to serve as an evaluator. The right diagram shows using LLM-as-a-Judge in the process of an Agent.


with unlabeled instructions and generating contrasting outputs from models. These outputs are then used to train an LLM-as-a-Judge to produce reasoning traces and final judgments. With each iteration, the evaluator improves by learning from its refined predictions, creating a cycle of continuous self-enhancement. This iterative approach not only keeps annotations relevant but also ensures that evaluators evolve alongside advancing models.

Recent research on evaluating multimodal data focuses on addressing vision-language misalignments in Multimodal Large Language Models (MLLMs), which often cause hallucinations—outputs inconsistent with visual or contextual evidence [24, 82, 154]. Techniques like RLHF and Factually Augmented RLHF have been employed to improve model alignment by incorporating structured ground-truth data and image captions, enhancing hallucination detection [136]. Benchmarks such as MLLM-as-a-Judge [17] assess these models using tasks like scoring, pair comparison, and batch ranking, revealing limitations in alignment with human preferences. Persistent issues include biases (e.g., position, verbosity) and hallucinations, with even advanced models like GPT-4V displaying challenges. While pair comparison tasks align better with human judgment, scoring and batch ranking require significant improvements for reliable deployment. These findings emphasize the need for innovative frameworks and datasets to refine MLLM evaluation and alignment.

- 2.4.3 LLM-as-a-Judge for Agents. There are two ways to apply LLM-as-a-Judge for an agent. One is to evaluate the entire process of the intelligent agent [226], and the other is to evaluate it at a specific stage in the agent framework process [43, 128]. Both approaches are briefly illustrated in Figure 7. Using LLM as the brain of agent, an agentic system [226] could evaluate like a human, it would reduce the need for human involvement and eliminate the trade-off between thoroughness and effort. In addition, the agent [128] can interact with the environment through language and receive feedback on actions through LLM to make decisions for the next action.
- 2.4.4 LLM-as-a-Judge for Reasoning/Thinking. Reasoning [50], defined as the cognitive process of applying logic, arguments, and evidence to draw conclusions, is central to intellectual tasks such as decision-making, problem-solving, and critical analysis. While reasoning is inherently more demanding and multifaceted than judging, it often depends on judgments to ensure logical


coherence, refine intermediate steps, and achieve clarity in its outcomes. LLM-as-a-Judge, in this sense, becomes an integral tool for enhancing the reasoning capability of LLM.

The role of LLM-as-a-Judge in enhancing reasoning or thinking can be understood through two frameworks: scaling training time [37, 150] and scaling test time [129]. In the training phase, LLM-as-a-Judge frequently operates within reinforcement learning paradigms, where it functions as a reward model or evaluator for data or processes. This enables the creation of high-quality reasoning datasets through mechanisms such as step-by-step verification [84], Direct Preference Optimization(DPO) [115], and self-refinement [192]. Recently, several LLMs trained with reinforcement learning to exhibit advanced reasoning and thinking abilities have gained attention, such as o11, DeepSeek-R12,gemini-thinking3, and QVQ4. In the test-time framework, LLM-as-a-Judge is crucial for evaluating and selecting the best reasoning paths. For example, in "Best-of-N" generation scenarios, where multiple reasoning outputs are produced, the judge determines the most accurate and coherent response. This dual role in both training and test phases demonstrates the indispensable nature of LLM-as-a-Judge in enhancing reasoning systems.

Reliability Concerns of Evaluation Pipeline

Within the broader evaluation pipeline, several factors can compromise the integrity of LLM-based assessments. When evaluating models, inherent biases such as position bias and self-enhancement can significantly impact fairness, requiring careful mitigation strategies. In data evaluation contexts, the extensive use of LLM-as-a-Judge for pseudo-labeling risks amplifying existing model biases, potentially leading to the generation of unverified and flawed training data. For agentic frameworks, the sequential application of LLM-as-a-Judge can lead to the accumulation of errors, where early misjudgments cascade into significant inaccuracies in final decisions. Moreover, evaluating complex reasoning tasks poses a particular risk; without robust verification of logical consistency, LLMs may produce seemingly confident but fundamentally flawed evaluations, undermining trust in sophisticated analytical processes.

![image 68](paper__llm_judge_2411_15594_images/imageFile68.png)

##### 2.5 Quick Practice

To effectively apply LLM-as-a-Judge design, it is recommended to find more effective configurations in the testing cycle for various scenarios. Crucially, reliable testing should form the bedrock of this quick practice, necessitating iterative refinement, continuous feedback loops, and the establishment of clear reliability metrics. The overarching aim is to continuously optimize evaluation stability and consistency through dedicated, reliability-focused testing cycles. The success of using LLMas-a-Judge also heavily depends on the implementation details, including the task complexity, the prompt design, the model selected, and the post-processing method.

As shown in Figure 8, The process of quick practice for LLM-as-a-Judge involves four main stages. First is the thinking phase, in which users define the evaluation objectives by determining what needs to be evaluated, understanding typical human evaluation approaches, and identifying some reliable evaluation examples. This initial conceptualization is vital for preempting potential ambiguities and biases that could compromise the fairness and accuracy of subsequent LLM judgments.

- 1https://openai.com/index/learning-to-reason-with-llms/
- 2https://api-docs.deepseek.com/news/news1120
- 3https://ai.google.dev/gemini-api/docs/thinking-mode
- 4https://huggingface.co/Qwen/QVQ-72B-Preview


Retest

Thinking Prompt Design

|What to evaluated ?|
|---|


|How do humans evaluate ?|
|---|


|Any reliable evaluation examples ?|
|---|


|Scoring Dimension|
|---|


|Relative comparison better|
|---|


|Example|
|---|


Model Selection

|Large Scale Model|
|---|


|Strong Reasoning Ability|
|---|


|Strong Instructionfollowing ability|
|---|


Test with cases

Fig. 8. Flowchart of Quick Practice

Specification

|\boxed{XX}|
|---|


|The score is: XX|
|---|


|Yes or No|
|---|


Next is prompt design, detailed in Section 2.1, where both wording and formats matter. The most efficient and generally effective approach involves specifying scoring dimensions, emphasizing relative comparisons for improved assessments, and creating effective examples to guide the LLM. Careful prompt engineering is essential to mitigate issues like output variability and inter-rater reliability, ensuring the LLM consistently interprets and responds to evaluation criteria as intended.

The third stage, model selection (Section 2.2), focuses on choosing a large-scale model with strong reasoning and instruction-following abilities to ensure reliable evaluations. The inherent biases and generalization limitations of different models, as well as their black-box nature, underscore the importance of selecting a robust and well-understood backbone to minimize evaluation inconsistencies and unverified judgments.

Finally, standardizing the evaluation process ensures that the outputs are structured (Section 2.3). This can be achieved by using specific formats like \boxed{XX}, numerical scores, or binary responses (e.g., "Yes" or "No"). Such standardization is crucial to counteract the fragility of token extraction methods and the potential for stylistic biases to propagate, thereby enhancing the interpretability and validity of the final evaluation results. The entire process includes iterative testing with cases and refinement through retesting, thereby enhancing reliability. During development, it is essential to compare models or prompts and verify ongoing improvements.

##### 3 IMPROVEMENT STRATEGY

When directly utilizing LLMs to conduct evaluation tasks—such as scoring, selection, pairwise comparison, or ranking—their inherent biases of LLMs like length bias, position bias, and concreteness bias[110] will undermine evaluation outcomes. Mitigating these inherent biases and improving the overall evaluation performance of LLMs remains a critical challenge for applying LLMs as evaluators. In this section, we introduce three improvement strategies to boost the evaluation performance of LLM-as-a-judge: design strategy of evaluation prompts (in-context learning based), improvement strategy of LLMs’ evaluation capabilities (model-based), and optimization strategy of final evaluation results (post-processing based). As shown in Figure 9, our categorization is based on the formal definition of LLM-as-a-judge in Section 2, focusing on enhancing the evaluation effectiveness by targeting three key phases of the process: the context C, the abilities of LLMs themselves PLLM and the post-processing ← to obtain the final results E

Improvement

- (Sec. 3)

Prompt Design Strategy

- (Sec. 3.1)

Improving LLMs’ Task Understanding

Few-shot prompting: FActScore [104] / SALAD-Bench [80] / GPTScore [33]

Evaluation steps decomposition: G-Eval [93] / DHP [163] / SocREval [44] / BSM [120]

Evaluation criteria decomposition: HD-Eval [94] / Hu and Gao et al. [47] Shuffling contents: Wang et al. [155] / Auto-J [79] / JudgeLM [222] / PandaLM [162] Conversion of evaluation tasks: Liu et al. [95]

Standardizing LLMs’ Output Format

Constraining outputs in structured formats: G-Eval [93] / DHP [163] / LLM-EVAL [86]

Providing evaluations with explanations: CLAIR [16] / FLEUR [74]

Capability Enhancement Strategy

- (Sec. 3.2)

Specialized Fine-tuning

Evaluation template: PandaLM [162] / SALAD-Bench [80] Deep transformation: OffsetBias [110] / JudgeLM [222] / CritiqueLLM [61] / Yu et al. [188]

Feedback-Driven Iterative Refinement

INSTRUCTSCORE [176] / JADE [202] / Think-J [48]

Final Output Optimization Strategy

- (Sec. 3.3)


Integrating Multi-Source Evaluation Results

Summarize by multiple rounds: Sottana et al. [133] / PsychoBench [51] / Auto-J [79]

Vote by multiple LLMs: CPAD [89] / Bai et al. [8] / EvalMORAAL [105] Hierarchical evaluation framework: Jung et al. [57] / Zhang et al. [203]

Direct Output Optimization

Score smoothing: FLEUR [74] / G-Eval [93] / DHP [163] / TrustJudge [161] Self validation: TrueTeacher [39]

Evaluation

- (Sec. 4)


Reliable LLM-as-a-Judge

Evaluation of Agreement with Human Judgments

- (Sec. 4.1)

Agreement [144] Cohen’s Kappa [144] Spearman’s correlation [8, 95]

Evaluation of Bias

- (Sec. 4.2)


Task-Agnostic Biases

- (Sec. 4.2.1)

Diversity Bias [185] Cultural Bias Self-Enhancement Bias [185, 213]

Judgment-Specific Biases

- (Sec. 4.2.2)


Position Bias[126, 144, 155, 185] Compassion-fade bias [66, 185] Style Bias [19, 75, 185] Length Bias [49, 110, 185, 213] Concreteness Bias [19, 110, 185]

Adversarial Phrases Attack [116] Null Model Attack [216] Majority Opinions Attack [66, 185] Meaningless Statement Robustness [66, 185]

Evaluation of Adversarial Robustness (Sec. 4.3)

Fig. 9. Structure of how to improve and evaluate LLM-as-a-Judge.

##### 3.1 Prompt Design Strategy

An evaluation prompt is an input to LLM evaluators, which is used to guide the LLMs to complete the required evaluation tasks. LLMs possess in-context learning ability, enabling them to learn how to perform specified tasks from relevant examples or instructions in prompts, without requiring weight updates or retraining[14]. This suggests that the design strategy of evaluation prompts will significantly impact the effectiveness of LLM-as-a-judge. Therefore, to achieve reliable evaluations, researchers have experimented with diverse prompt design strategies, including improving LLMs’ task understanding and standardizing LLMs’ output format in the prompt. This approach mitigates reliability concerns of In-context learning mentioned in Section 2.1, such as unstable results, inter-rater inconsistency, ambiguity in response, and positional or length biases.

- 3.1.1 Improving LLMs’ Task Understanding. In optimization methods of prompting LLMs to better understand evaluation tasks, one of the most commonly used and effective approaches is few-shot prompting[14]. By incorporating several high-quality evaluation examples into the evaluation prompts, LLM evaluators can effectively grasp the objectives, general processes, and


rough evaluation criteria of evaluation tasks. Many research works employ this prompt paradigm for evaluation, such as FActScore[104], SALAD-Bench[80], and GPTScore[33].

In addition to providing high-quality examples, refining the evaluation task instructions is also an effective approach to optimizing LLMs’ understanding of evaluation tasks. Current methods for refining evaluation tasks mainly include the decomposition of evaluation steps and criteria:

- • (a) Decomposition of Evaluation Steps entails breaking down the entire evaluation tasks into smaller steps, providing detailed definitions and constraints for each small step in prompts, thereby guiding LLMs comprehensively through the whole evaluation pipeline. For instance, G-Eval[93] and DHP[163] use Chain-of-Thought(CoT)[167] to guide LLMs. SocREval[44] employs the Socratic method to meticulously design each step to enhance evaluation performance. In existing research, this paradigm resembles providing detailed and sequential execution steps within a single prompt for a one-time evaluation, which guides the LLM-as-a-judge to complete evaluation tasks aligned with requirements, as illustrated in Fig 10(a). To better understand this paradigm, we present a demonstrative example prompt for evaluating summary quality: "You will be given a summary written for an article. ...... Evaluation Steps: 1. Read the Summary Thoroughly: Before diving into the evaluation, ensure that you ...; 2. Identify the Central Topic: A coherent summary will have a clear central topic or theme

...; 3. Look for Transitional Elements: Coherent summaries often have clear transitions between sentences or ideas ...; 4. Check for Logical Flow: Review the summary for logical sequencing ... X. Give a Score: ... Source Article: {{ Article }} Summary: {{ Summary }}". In this example, the evaluation task for summary quality is decomposed into many small steps to guide the LLM through the entire assessment process—from reading and analyzing to scoring—enabling methodical evaluation of a summary.

- • (b) Decomposition of Evaluation Criteria involves breaking down coarse evaluation criteria like Fluency into finer-grained sub-criteria like Grammar, Engagingness, and Readability, and then generating overall scores based on these different dimensions. Saha et al. propose Branch-Solve-Merge(BSM)[120], which divides evaluation tasks into multiple parallel subtasks based on different sub-criteria for separate evaluation and final merge. HD-Eval[94] proposes a hierarchical criteria decomposition method to iteratively align LLM evaluators with human preference, thereby addressing the potential bias in LLMs. Hu and Gao et al.[47] summarize and clearly define an explicit hierarchical classification system encompassing 11 criteria, addressing the issue of LLMs potentially confusing different evaluation standards. Different from the decomposition of steps, this paradigm presents greater complexity due to significant variations in evaluation requirements and procedures across different criteria dimensions. Current methodologies tend to decompose the original evaluation task into multiple sub-tasks based on distinct criteria. Each sub-task is assessed via a distinct prompt, with results subsequently merged or simply listed in a score table, as demonstrated in Fig 10(b).


In conclusion, these decompositions are specific to enable LLMs to understand the details of evaluation tasks more deeply, thereby aligning evaluation results more closely with human evaluation requirements and preferences. Providing detailed evaluation specifications and enhancing task comprehension can mitigate inter-rater inconsistency to some extent, while also reducing potential ambiguity.

Furthermore, the evaluation capabilities can be optimized based on specific shortcomings of LLMs in prompts. For instance, to address specific biases like position bias, which is common in pairwise evaluations, several research efforts have optimized prompt design by randomly swapping contents to be evaluated. Wang et al.[155] analyzed and validated the impact of position bias on LLM-as-a-judge and proposed a calibration framework to mitigate this bias by swapping the

![image 69](paper__llm_judge_2411_15594_images/imageFile69.png)

Fig. 10. Simplified Evaluation Pipeline of Two Decomposition Paradigms.

contents and averaging the scores. Auto-J[79] and JudgeLM[222] also enhance the evaluation consistency by shuffling the texts to be evaluated. In contrast to averaging scores, PandaLM[162] annotates the conflicting evaluation results after swapping as "Tie" to address the position bias. Since the content to be evaluated in each positional arrangement is taken into account during evaluation, the final evaluation results are thus reliable and free from positional bias.

To address the challenge of LLMs’ absolute scoring being less robust than relative comparing[116], some research works convert scoring tasks into pairwise comparison, thereby enhancing the reliability of evaluation results. Liu et al.[95] transform the scoring evaluation to ranking evaluation and introduce Pairwise-Preference Search (PARIS), which employs LLMs to conduct pairwise comparisons locally and efficiently ranks candidate texts globally, making evaluation results more aligned with human preferences. Unlike single numerical scores, which are more susceptible to prompt variations and inherent randomness, pairwise comparisons generate relative assessments. This approach only requires LLMs to evaluate the relative merits between candidates, consequently yielding more stable and reliable results.

In summary, the design of prompts for better understanding evaluation tasks is a core method for optimizing LLMs’ in-contextual learning abilities. By refining task instructions and criteria in prompts or few-shot prompting with high-quality examples, the details of evaluation prompts can be enriched, and the understanding of LLMs on evaluation tasks can be directly or indirectly enhanced. Additionally, targeted adjustments to prompts can address potential biases of LLMs, such as position bias. Thus, by improving LLMs’ task understanding, the inconsistent inter-rater reliability, the ambiguity in response, and the biases mentioned in Section 2.1 can be solved.

- 3.1.2 Standardizing LLMs’ Output Format. Directly requiring LLM evaluators to output evaluation results poses robustness problems. The response may unexpectedly vary due to the inherent generative randomness of LLMs, such as outputting text like "low relevance" while asked to measure with discrete scores, which hinders the automated extraction of evaluation results from LLM’s output. An effective method to enhance the robustness of output forms is to constrain


the output in structured formats within prompts. G-Eval[93] and DHP framework[163] perform evaluation tasks with a form-filling paradigm, constraining outputs with formats like "X: Y", where X represents the dimension or metric to be evaluated and Y denotes an identifiable output form like scores or specific tokens. LLM-EVAL[86] further modifies this form-filling paradigm, efficiently outputs evaluation results in JSON format, and obtains multidimensional scores, leveraging LLMs’ high understanding and generation capabilities of code-like textural formats.

Apart from challenges in robustness, directly outputting evaluation results by LLMs also suffers from a lack of interpretability. The meaning of evaluation results from LLM evaluators is difficult to align consistently with the instructions and metrics provided in prompts. To address the challenges, CLAIR[16] requires LLMs to output evaluation scores between 0-100 simultaneously with relevant reasons as explanations in JSON format, which enhances the rationality and interpretability of the scores. FLEUR[74] utilizes LLaVA to first provide quality scores for image captions and subsequently asks with "Why? Tell me the reason." for explanations with the images, captions, and scores as inputs, offering a stepwise approach to provide interpretable scores.

In general, by constraining or guiding the output process and format of LLM evaluators within prompts, the robustness and rationality of evaluation results can be effectively improved through structured outputs. This also facilitates the automated post-processing of evaluation results in subsequent steps, thereby enhancing the overall stability of the evaluation pipeline.

##### 3.2 Capability Enhancement Strategy

The evaluation capabilities of LLMs are a reflection of their powerful general language understanding and generation abilities triggered by specific prompts. Methods for optimizing evaluation through prompt design——focused on LLMs’ in-contextual learning capabilities——require LLMs to comprehend the meaning of prompts fully and consistently follow the relevant evaluation instructions. However, even state-of-the-art LLMs like GPT-4 encounter problems such as conceptual confusion[47], and smaller open-source LLMs have even more limitations in their evaluation capabilities. Fine-tuning LLMs may be a common approach, but as mentioned at the end of Section 2.2, fine-tuned LLMs might exhibit limited generalization capability beyond their training data distribution, and could also remain susceptible to subtle biases within the fine-tuning data that compromise fairness, leading to inconsistencies with human judgment. Therefore, researchers propose two solutions: On one hand, constructing fairer training datasets to fine-tune LLMs and eliminate judgment biases; on the other hand, implementing feedback-driven iterative refinement methods, which continuously update LLMs during usage to enhance their generalization capability, ultimately achieving reliable evaluation models.

- 3.2.1 Specialized Fine-tuning. A straightforward approach to enhancing the evaluation capabilities of LLMs is to fine-tune them via meta-evaluation datasets specifically constructed for evaluation tasks, which helps improve the LLMs’ understanding of specific evaluation prompts, boosts the evaluation performance, or addresses potential biases. The most critical step in this optimization strategy is the collection and construction of training data, since LLMs will adhere to the instructional formats defined by the training data and inherit any potentially subtle biases, ultimately affecting the evaluation performance. As shown in Fig 11, there are primarily two approaches to constructing meta-evaluation data: Evaluation Templates and Deep Transformation. The former typically populates sampled raw data into preset templates to form training data, while the latter employs algorithms or models to transform raw data in terms of style, content, and structure, thereby constructing training data more flexibly.


Using evaluation templates is a common method, which involves sampling evaluation questions from publicly available datasets, modifying them with certain templates, and supplementing the

![image 70](paper__llm_judge_2411_15594_images/imageFile70.png)

Fig. 11. Two paradigms of the construction process of meta evaluation datasets for training.

dataset with evaluation responses generated either manually or by powerful LLMs like GPT-4. For instance, PandaLM[162] samples inputs and instructions from Alpaca 52K[143] and generates responses using GPT-3.5 to construct training data, while SALAD-Bench[80] builds its training data from a subset of LMSYS-Chat[214] and Toxicchat[87].

To better align with the requirements of evaluation tasks, many research works further transform inputs and instructions sampled from public datasets to construct more targeted training data. OffsetBias[110] aims to reduce biases of LLMs by using GPT4 to generate off-topic versions of the original inputs and then having GPT-3.5 respond to the new inputs to produce bad responses. By pairing good and bad responses as training data to fine-tune the LLMs as evaluators, the biases in LLMs are significantly reduced, including length bias, concreteness bias, knowledge bias, and so on. JudgeLM[222] enhances LLMs’ evaluation capabilities by creating different types of training data through paradigms like reference support and reference drop. CritiqueLLM[61] proposes a multi-path prompting approach, combining pointwise-to-pairwise and referenced-to-reference-free prompting strategies to restructure referenced pointwise grading data into four types, which helps create Eval-Instruct to fine-tune LLMs, addressing shortcomings in pointwise grading and pairwise comparison. Yu et al.[188] sample data from the preference dataset and rewrite judge templates to synthesize training data, and use GPT-4o to analyze and judge the pairs of answers in the synthetic data. The correct judgments, along with the synthetic data and analysis, will be processed as training data for the SFT phase of judge models.

In summary, constructing meta-evaluation training data targeted at specific evaluation tasks and fine-tuning LLMs can directly adjust the model’s internal parameterized knowledge and language abilities. This is the most straightforward method to improve the evaluation performance of LLM evaluators and address potential biases.

- 3.2.2 Feedback-Driven Iterative Refinement. Fine-tuning LLMs on meta-evaluation datasets gives them the ability to produce evaluations that are more aligned with human preferences. However, as discussed in Section 2.2, LLMs exhibit version dependency, and even fine-tuned models remain constrained by their training data and inherently suffer from out-of-distribution limitations to some extent. Consequently, LLM-as-a-Judge may still exhibit biases during evaluation processes in practice, ultimately compromising evaluation quality. A natural improvement strategy is to iteratively optimize the model based on the feedback of evaluation results, which mainly comes from stronger models or directly from human evaluators’ corrections of the evaluation results.


A typical example is INSTRUCTSCORE[176]. To improve model performance and further benefit the final quality score calculation, this scoring framework collects failure modes of metric outputs, queries GPT-4 on each failure mode to gather automatic feedback, and finally selects explanations most aligned with human preferences to iteratively fine-tune the LLaMA model. Unlike INSTRUCTSCORE, which directly optimizes the model, the LLM evaluator in JADE[202] relies on human judges to correct LLMs’ evaluation results and updates the most frequently corrected samples into the example sets for few-shot prompting. JADE utilizes this relatively low-cost method to achieve iterative updates of the evaluation capabilities.

Iterative optimization methods are not limited to offline training. The success of R1-style methods shows the effectiveness of online reinforcement learning (RL) approaches. Thus, feedback-based online learning constitutes another strategic form of iterative optimization. Think-J[48] integrates both offline and online learning approaches. The offline approach trains a critic model to evaluate judgments from the judge model, thereby constructing positive and negative samples for SFT and DPO optimization. The online approach continuously optimizes the judge model using the Group Relative Policy Optimization (GRPO) algorithm with rule-based rewards as optimization feedback.

Since the feedback is more closely aligned with human preferences, LLMs can dynamically optimize their evaluation capabilities based on the feedback, leading to better evaluation results. This feedback-driven iterative refinement strategy addresses the problem of models’ imperfect generalization and improves the evaluation capabilities through dynamic updates.

##### 3.3 Final Output Optimization Strategy

Through optimization based on in-context learning and the model’s own capabilities, LLMs have become fairly reliable evaluators that are capable of understanding evaluation task requirements and providing rational evaluation results. However, the inherent generative randomness of LLM black boxes, the fragility of output extraction methods, and potential adversarial manipulations, as noted at the end of Section 2.3, may collectively contribute to unreliable and unfair evaluation results. Therefore, it is necessary for LLM evaluators to design optimization strategies during the post-processing stage from the outputs to the final evaluation results. Some strategies opt to directly modify output acquisition methods to extract evaluation results more robustly, while more mainstream strategies focus on designing frameworks that integrate multi-source evaluation results, which mitigate adverse effects caused by randomness and fragility, and enhance resistance to adversarial manipulations.

- 3.3.1 Integrating Multi-Source Evaluation Results. Integrating multiple evaluation results for the same content to obtain the final result is a common strategy in various experiments and engineering pipelines, which can reduce the impacts of accidental factors and random errors. The most basic optimization strategy is to perform multiple runs of evaluation on the same content with different hyper-parameters and settings, and then summarize these results. For example, the work of Sottana et al.[133] reduces randomness in evaluations by averaging multiple scores of the same sample. Similarly, PsychoBench[51] takes the mean and standard deviation from ten independent runs. Auto-J[79] further amplifies the differences between evaluation rounds, which combine critiques with and without scenario criteria to obtain the final results.


In addition to integrating results from multiple rounds of evaluation, using multiple LLM evaluators to assess the contents simultaneously and integrating the results is another effective method, which can reduce biases introduced by LLMs. For instance, CPAD[89] utilizes ChatGLM-6B[31], Ziya-13B[200], and ChatYuan-Large-v2[201] as evaluators to evaluate the contents and obtain the final results by voting. Bai et al.[8] propose a novel evaluation method called decentralized peer review of LLMs, which utilizes LLMs that generate content to evaluate each other’s generated

content and eventually integrate the results. EvalMORAAL[105] also employs a similar LLM-as-ajudge peer review mechanism, detecting conflicts in evaluation results by checking whether score differences exceed a preset threshold, and uses majority voting to resolve conflicts.

The aforementioned multi-round or multi-model approaches represent a type of peer-parallel evaluation strategy, and their integration process is relatively straightforward. Researchers have also proposed many more complex evaluation frameworks featuring greater interactivity between different evaluations. For example, Jaehun Jung et al. proposed Cascaded Selective Evaluation[57]. This framework transitions from weaker, smaller models to stronger, larger models based on confidence, allowing the majority of evaluations to be handled by smaller models, which significantly reduces the costs of computing resources and improves efficiency. Recent work [203], on the other hand, proposed Crowd-based Comparative Evaluation. This method utilizes multiple LLMs to construct crowd responses based on candidate responses for comparison, thereby generating multiple crowd judgments that serve as reference content for the final evaluation. This enables LLM-as-a-Judge to capture richer details and enhance evaluation reliability.

In summary, forming the final evaluation results by combining multiple rounds of evaluations or multiple LLM evaluators can reduce the random effects caused by accidental factors in a single round and reduce the potential biases of a single LLM evaluator. This strategy significantly enhances the stability and reliability of the evaluation results.

- 3.3.2 Direct Output Optimization. Different from obtaining evaluation results based on the outputs of multiple rounds or LLMs, directly optimizing the output of a single LLM evaluator involves further processing the evaluation output to make it more reliable, especially when dealing with scoring outputs from LLM evaluators. Due to the inherent randomness in LLMs’ generation, the scores may not fully reflect the LLMs’ complete view of the evaluation criteria. Therefore, to obtain more reliable evaluation results, it is necessary to optimize the LLM’s score outputs. An effective optimization strategy is to combine the implicit logits, which capture the LLMs’ randomness, with the explicit output scores. For example, FLEUR[74] proposes a score smoothing strategy. For scores generated by LLaVA, the probability of the token corresponding to each digit 𝑙 (0≤ 𝑙 ≤9) would be used as the weight to smooth the explicit scores and calculate the final evaluation scores. TrustJudge[161] proposes a distribution-sensitive scoring method that computes continuous expectations from discrete scoring probabilities, and a likelihood-aware aggregation method that utilizes bidirectional preference probabilities, to process the evaluation results from LLMs, addressing the inconsistency in LLM-as-a-Judge.


However, methods like score smoothing, which combine implicit logits and explicit outputs, require the LLMs to be open-source or to provide interfaces that allow access to token probabilities, which brings some limitations. Inspired by the work of Weng et al.[168] and Madaan et al.[103], self-verification can be used to filter out the evaluation results without sufficient robustness. For example, TrueTeacher[39] applies self-verification in its evaluation of distilled data by asking the LLM evaluator for its certainty about the evaluation results after providing them and retaining only those results that pass self-verification. Self-verification is suitable for all LLMs and requires no complex computing and processing.

In summary, compared to integrating multiple evaluation results, directly optimizing the LLMs’ outputs to obtain the final results is faster and lower-cost, although the effectiveness still needs further validation. However, these two approaches are not mutually exclusive. Performing integration after direct optimization of LLMs’ output may lead to more stable evaluation results.

###### Agreement with Human

Dataset

JudgeBench

MTBench

Chatbot Arena

CALM

FairEval

KUDGE

Metric

Spearman’s correlation

Accuracy

Percent Agreement

F1-score

###### Bias

- R1: 3.11 > 3.8
- R2: 3.8 > 3.11


|Position Bias|
|---|


- R1 is better!

- R2 is better!


|Length Bias|
|---|


R2: 3.8 > 3.11 R1: 3.11 > 3.8 LLM

|Concreteness Bias|Concreteness Bias|
|---|---|
|Diversity Bias| |


LLM favor the ﬁrst response.

###### Adversarial Robustness

|Null Model Attack|
|---|


Question: Ali had $21.

Leila gave him half of her $100. How much does Ali have now?

|Majority Opinion Attack|
|---|


Correct!

|Adversarial Phrases|
|---|


Response: "Solution" LLM

|System Prompt Attack|
|---|


Fig. 12. Three Dimensions of Evaluation.

##### 4 EVALUATION OF LLM-AS-A-JUDGE

Following the discussions on the application and enhancement of LLM-as-a-Judge, we now address the critical question of its evaluation. While the basic evaluation pipeline provides a conceptual foundation, it does not inherently guarantee the reliability of the system. To formally capture this essential property, we recall the enhanced formal definition of reliability:

###### R ← 𝑓R (PLLM,𝑥, C)

This formulation highlights that reliability R is a function of three independent variables: the

LLM’s probability function (PLLM), the input being evaluated (𝑥), and the accompanying context (C). Assessing LLM-as-a-Judge, therefore, requires a systematic examination of how these three factors collectively influence its performance.

Reliability may degrade if the underlying model, defined by its probability function PLLM, exhibits inherent biases or instability. For instance, a less robust LLM may produce inconsistent scores for identical prompts and inputs due to sampling variance or internal preference drift. Similarly, the quality of evaluation is susceptible to the nature of the input 𝑥. Noisy or adversarially perturbed inputs can cause the LLM to misjudge quality, thus diminishing its robustness. Finally, subtle changes in the prompt wording or the ordering of the context C can lead to different judgments for the same input, a phenomenon that undermines reliability.

Therefore, a comprehensive evaluation of LLM-as-a-Judge requires examining multiple aspects. We organize existing evaluation studies into three major dimensions: agreement with human judgments (Section 4.1), bias (Section 4.2), and adversarial robustness (Section 4.3), as depicted in Figure 12.

##### 4.1 Agreement with Human Judgments

Given that the initial motivation of LLM-as-a-judge lies in replacing human annotation, the foremost aspect of its evaluation should naturally be the extent to which it aligns with human judgments. Numerous studies approach this by considering the LLM evaluator as a virtual annotator and evaluating the extent of its agreement with human annotators. The percentage agreement metric

represents the proportion of samples on which LLM and human annotators agree [144]. Agreement = 𝑖∈D

I(Sllm = Shuman)

###### ∥D∥

where D is the dataset, 𝑆llm and 𝑆human are the evaluation results of the LLM evaluator and human judge, respectively, which can be in the form of both score or rank. Additionally, widely used correlation metrics such as Cohen’s Kappa [144] and Spearman’s correlation [8, 95] are also employed to assess agreement. Other works treat the LLM-as-a-judge task as a classification problem, where human annotations serve as the labels, and compute precision and recall to evaluate the performance [162, 222].

Evaluation Dimension Agreement Position Bias Length Bias Bias Types

Benchmark Release Year Size Annotation Format

MTBench [213] 2023 80 Pairwise ✓ ✓ ✓ 3 Chatbot Arena [213] 2023 30k Pairwise ✓ ✓ ✓ 3 FairEval [155] 2023 80 Pairwise ✓ ✓ ✗ 1 PandaLM [162] 2023 Pairwise ✓ ✓ ✗ 0 LLMEval2 [207] 2023 2553 Pairwise ✓ ✗ ✗ 0 Shepherd [159] 2023 1317 Score ✓ ✗ ✗ 0 EvalBiasBench [110] 2023 80 Pairwise ✓ ✓ ✓ 6 CALM [185] 2024 4356 Pairwise & Score ✗ ✓ ✓ 12 JudgeBench [139] 2024 - Pairwise ✓ ✗ ✗ 0 MLLM-as-a-Judge [17] 2024 30k Pairwise & Score ✓ ✗ ✗ 0 CodeJudge [212] 2024 1860 Score ✓ ✗ ✗ 0 KUDGE [130] 2024 3324 Pairwise & Score ✓ ✗ ✗ 0

Table 1. Benchmark for meta-evaluation of LLM-judge.

Datasets. Both of the above metrics rely on the datasets with LLM-generated responses and responding human judgments. Therefore, there is also a practical need to construct a comprehensive benchmark for the meta-evaluation. Table 1 shows existing banchmarks. MTBench [213] has only 80 human-crafted queries with their corresponding human annotation and LLMs’ responses. FairEval [155] is constructed from the 80 queries from VicunaBench [148] with human-annotated preference between ChatGPT and Vicuna responses. Chatbot Arena Conversations [213] is a larger collection of crowdsourced data (about 30k) with human annotated preferences. Research [195] constructs a benchmark to assess the capability of the LLM evaluator in evaluating whether a response follows the instruction. This dataset contains human-curated 419 pairs of outputs, one adhering to instructions while the other diverging, yet may possess deceptive qualities that mislead an LLM evaluator. Research [17] evaluates the capabilities of multi-modal LLMs in assisting evaluation tasks across various modalities and introduces MLLM-as-a-Judge, a comprehensive multi-modal benchmark. Recent advances also expand the scope of meta-evaluation benchmarks to specialized domains, including code assessment [212] and non-English language tasks [130]. Furthermore, CALM [185] presents a systematic framework for bias quantification, featuring an automated perturbation mechanism to generate meta-evaluation data for examining 12 distinct types of potential biases in LLM evaluators.

Current meta-evaluation primarily focuses on LLM-as-a-judge for models, while there is a lack of sufficient meta-evaluation when these LLM evaluators are used for automatically annotating largescale datasets (Section 2.4.2). We advocate for more rigorous assessment of the alignment between LLM-as-a-judge and human judgment when they are employed for large-scale data annotation. Additionally, it is also crucial to assess the potential bias and robustness, which will be discussed in the following sections.

##### 4.2 Bias

As LLM-as-a-Judge becomes more widely deployed, it has been observed to manifest a range of salient biases, even in cases where its evaluations align with human judgments. Prior studies have emphasized that large language models inherently exhibit diverse forms of bias across different tasks [25, 34, 138]. Such internal biases may propagate into the LLM-as-a-Judge setting, potentially resulting in unfair evaluation outcomes and, in turn, influencing the development of downstream LLMs. Consequently, it is imperative to both characterize the types of biases that LLM evaluators may carry and to establish systematic approaches for their assessment. In this section, we review the major categories of biases in the context of LLM-as-a-Judge, outlining their definitions, associated metrics, and datasets commonly employed for evaluation.

The meta-evaluation of LLM-as-a-judge introduces systematic biases that can be broadly categorized into two classes: task-agnostic biases inherent to LLMs across general applications, and judgment-specific biases unique to LLM-as-a-judge scenarios. This taxonomy aims to clarify their distinct characteristics and implications. The former may be partially attributed to the characteristics of the judgment task itself, such as its specific input-output format, which could potentially be mitigated through task-specific design. In contrast, task-agnostic biases are more fundamental issues inherent to the LLMs themselves and are therefore more difficult to address. Mitigating such biases likely depends on advancements in the foundation models.

- 4.2.1 Task-Agnostic Biases. These biases manifest across diverse LLM applications, including open-domain QA, classification, and summarization. However, when arising in the LLM-as-a-judge, the biases are particularly critical due to their cascading effects on downstream tasks. When LLMgenerated judgments serve as feedback for model training or data annotation, these biases risk being amplified and propagated. We present a few typical examples and recommend consulting comprehensive reviews on language model bias [35, 42] for a more thorough understanding.

Diversity Bias refers to bias against certain demographic groups [185], including certain genders [19], race, and sexual orientation [70]. In the context of LLM-as-a-judge scenarios, this bias may appear when evaluators give higher scores to responses that align with stereotypes of certain groups.

Cultural Bias. In general domains, cultural bias refers to situations where models might misinterpret expressions from different cultures or fail to recognize regional language variants [35]. In the context of LLM-as-a-judge, it indicates that evaluators might score expressions from unfamiliar cultures poorly.

Self-Enhancement Bias describes the phenomenon that LLM evaluators may prefer responses generated by themselves [185, 213]. This bias has also been known as source bias in retrieval task [26] and open-domain question answering systems [138]. Considering the significant selfenhancement bias, as suggested in [185], we should avoid using the same model as the evaluator. This is only a stopgap, as we may not use the optimal evaluator when evaluating the most advanced LLMs.

- 4.2.2 Judgment-Specific Biases. Judgment-specific biases are either unique to the LLM-as-ajudge setting or have a significant impact on judgment tasks. A classic example is the "position bias", which has a more pronounced effect in the context of LLM-as-a-judge, where the evaluator often needs to compare pairwise responses. Different from task-agnostic biases, judgment-specific biases are more difficult to resolve naturally with the development of foundational large model capabilities and require targeted optimization for judgment tasks.


Position Bias is the tendency of LLM evaluators to favor responses in certain positions within the prompt [126, 144, 155, 185]. This bias may have detrimental effects, as Vicuna-13B could

outperform ChatGPT when evaluated by ChatGPT, simply by positioning the response of Vicuna13B in the second place [155]. To measure this bias, recent work [126] proposed two metrics: Position Consistency, which quantifies how frequently a judge model selects the same response after changing their positions, and Preference Fairness, which measures the extent to which judge models favor a response in certain positions. The study [155] also introduced a metric Conflict Rate to measure the percent of disagreement after changing the position of two candidate responses. Their analytical experiments reveal that the degree of positional bias fluctuates depending on the disparity in response quality, and the preferred position varies with different LLMs. For instance, GPT-4 tends to favor the first position, while ChatGPT shows a preference for the second position.

Compassion-fade bias describes the effect of the model names [66, 185]. This tendency occurs when we explicitly provide model names. for instance, evaluators may be inclined to give higher scores to results labeled as “gpt-4”. This tendency underscores the necessity of anonymous evaluation.

Style Bias refers to the tendency towards a certain text style. As revealed in [19], an evaluator may also prefer visually appealing content, regardless of its actual validity, such as the text with emojis. Furthermore, LLM evaluators may favor responses with certain emotional tones, such as cheerful, sad, angry, and fearful, which is defined as sentiment bias [75, 185].

Length Bias refers to the tendency to favor responses of a particular length, such as a preference for more verbose responses, which is also known as verbosity bias [49, 110, 185, 213]. Length bias can be revealed by rephrasing one of the original responses into a more verbose one [185, 213]. Even though these expansions do not introduce new information, there is still concern regarding changes to the original response in terms of perplexity, fluency, or style. Alternatively, a previous study [121] investigated this bias by comparing multiple sampled responses and revealed a statistical tendency towards longer answers. However, ensuring the comparable quality of multiple samples remains a challenging problem.

Concreteness Bias reflects that LLM evaluators favor responses with specific details, including citation of authoritative sources, numerical values, and complex terminologies, which is called authority bias [110] or citation bias [19, 185]. The negative effects of concreteness bias arise from the neglect of the factual correctness of these details, thereby encouraging hallucination [1].

##### 4.3 Adversarial Robustness

As LLM-as-a-Judge becomes further integrated into evaluation pipelines and increasingly serves as the standard protocol, a variety of adversarial attacks have emerged. Adversarial robustness refers to the ability of a model to withstand deliberate attempts to manipulate the scores through carefully crafted inputs. Unlike bias evaluations (Section 4.2), which mainly focus on naturally occurring samples, adversarial robustness involves samples intentionally crafted to manipulate scoring, such as inserting phrases that artificially enhance scores. Robustness is crucial because insufficient robustness allows trivial manipulations to deceive the evaluators and to undermine the evaluation of text quality. Ensuring robust evaluators is essential for maintaining accurate and reliable assessments, particularly in high-stakes applications.

Research [116] constructed a surrogate model from the black-box LLM-evaluator and then learn a adversarial attack phrases based on it. The evaluation score can be drastically inflated by universally inserting the learned attack phrases without improving the text quality. Similarly, work by Lee et al. [73] introduced EMBER, a benchmark that revealed biases in when assessing outputs with epistemic markers, such as expressions of certainty or uncertainty. Furthermore, other work [216] demonstrated that even a "null model" that outputs a constant response irrelevant to input instructions can achieve high win rates for various LLM-as-a-judge methods. Similarly, recent work [211] also revealed that on-word symbols (e.g., “:”) or reasoning openers like “Thought process:” can

often fool LLM evaluators to produce positive evaluations. Several recent works [66, 185] proposed to increase the evaluation score by adding the majority opinions, such as “90% believe this is better”. Other research [66, 185] evaluated robustness against meaningless statement in the System Prompt, e.g., ”Assistant A loves eating pasta”. These works revealed that LLM-as-a-judge are still insufficiently robust against interference irrelevant to text quality. Defensive measures like the perplexity score [52, 116] can only detect limited types of adversarial examples. Therefore, constructing more robust LLM-as-a-judge is a crucial research direction for the future.

##### 4.4 Empirical Experiment

|LLM-as-a-judge<br><br>|Iterative Optimization for Evaluator|
|---|
<br><br>|Post-process<br><br>|Multi-Turns|
|---|
<br><br>|Multi-LLMs|
|---|
<br><br>|Score Smooth|
|---|
<br><br>|Self-Validation|
|---|
<br><br>|LLM-Evaluator<br><br>|Loading of LLMs|
|---|
<br><br>|Extraction of Results|
|---|
<br><br>|Scheduling of Decomposed Tasks|
|---|
<br><br>|Prompt-Design<br><br>|Structured Output|
|---|
<br><br>|Few-shot|
|---|
<br><br>|Explanation|
|---|
<br><br>|Task/Criteria Decomposition|
|---|
<br><br>|Shuffling Contents|
|---|
|
|---|
<br><br>|Query LLMs|
|---|
|
|---|
|
|---|
|
|---|


Fig. 13. LLM-as-a-Judge Meta-evaluation Pipeline and Tools

In Section 3, we have introduced the improvement strategies in existing LLM-as-a-judge works to improve the evaluation capabilities of LLMs. Although numerous works have proposed metaevaluation benchmarks to assess the performance of LLMs in evaluation tasks, there is a lack of meta-evaluation on whether these improvement strategies effectively make LLM-as-a-Judge more reliable. So in the preceding subsection of this Section 4, we systematically introduced the dimensions and criteria for evaluating the evaluation performance and reliability of LLM-as-a-Judge, thereby providing quantifiable metrics that inform the evaluation of the aforementioned strategies.

Based on partial dimensions mentioned in sec 4.1 and sec 4.2, we designed a robust and scalable meta-evaluation tool as shown in Figure 13 and conducted a simple meta-evaluation experiment on the improvement strategies summarized in Section 3, examining their effectiveness from the perspectives of biases and agreement with human evaluation.

##### 4.4.1 Experiment Settings.

Evaluation Dimensions and Benchmarks. The most direct metric to reflect the quality of automatic evaluation is the alignment with human evaluation. We use LLMEval2 [207] to assess the alignment of LLM-as-a-judge with human evaluations. LLMEval2 is the largest and most diverse evaluation benchmark for LLM-as-a-judge to date, with 2,553 samples compiled from multiple data sources with human-annotated preferences. Each sample consists of a question, a pair of candidate responses, and a human label indicating the preferred response.

Bias is also a crucial dimension for assessing the quality of LLM-as-a-judge evaluation results. We use EVALBIASBENCH[110] to measure six types of biases in LLM-as-a-judge, including length bias, concreteness bias, empty reference bias, content continuation bias, nested instruction bias, and familiar knowledge bias. EVALBIASBENCH consists of 80 samples, each containing a question, a pair of candidate responses, and a label indicating the correct response without bias influence. In addition to the six types of biases, we also evaluated position bias. The meta-evaluation samples for

position bias are the paired samples constructed by swapping the position of candidate responses within prompts in samples of LLMEval2 and EVALBIASBENCH.

Evaluation Metrics. For the alignment with human evaluation, we use Percentage Agreement Metric[144] for evaluation, as shown in Section 4.1. For biases except for position bias, we use Accuracy for evaluation, which represents the proportion of samples where LLM-as-a-judge selects the correct candidate response annotated in EVALBIASBENCH.

For position bias, we use Position Consistency as the metric, which quantifies how frequently the LLM-as-a-judge selects the same response after swapping the position of candidate responses. Formally, given 𝑁 samples {(𝑞𝑖,𝑟1𝑖,𝑟2𝑖)}𝑖𝑁=1, for each sample (𝑞𝑖,𝑟1𝑖,𝑟2𝑖), we queried the LLM-asa-judge with two prompts 𝑃(𝑞𝑖,𝑟1𝑖,𝑟2𝑖) and 𝑃(𝑞𝑖,𝑟2𝑖,𝑟1𝑖), and obtained two evaluation results 𝑆𝑖𝑟12 and 𝑆𝑖𝑟21. Each 𝑆𝑖 is 𝑟1𝑖, 𝑟2𝑖 or "TIE". Then we calculate the Position Consistency as follows:

𝑁 𝑖=1 I(𝑆𝑖𝑟12 = 𝑆𝑖𝑟21)

Position Consistency =

𝑁 where I(·) is the indicator function.

Target LLMs and Strategies. For LLMs, we selected six LLMs commonly used in the automatic evaluation, including closed-source LLMs GPT-4, GPT-3.5, and open-source LLMs Qwen2.5-7B, LLaMA3-8B, Mistral-7B, and Mixtral-8×7B.

For improvement strategies, we selected Providing Evaluations with Explanations, Self Validation, Summarize by Multiple Rounds, and Vote by Multiple LLMs, since these strategies are all straightforward and relatively common in many works. We adopt GPT-3.5 as the base evaluator for the meta-evaluation of these improvement strategies.

Model Configuration. For closed-source LLMs, we interact using OpenAI’s official APIs. The model versions we selected are GPT-4-turbo and GPT-3.5-turbo, specifically referencing gpt-4turbo-2024-04-09 and gpt-3.5-turbo-0125 respectively1.

For open-source LLMs, we adopt Qwen2.5-7B-Instruct2, Meta-Llama-3-8B-Instruct3, Mistral-7BInstruct-v0.34, Mixtral-8×7B-Instruct-v0.15, deployed on an Ubuntu machine equipped with a 40GB NVIDIA A100 GPU.

To stabilize the evaluation results of LLMs, we set the hyper-parameter temperature to 0 to reduce the impact of randomness in LLMs’ output. For Summarize by Multiple Rounds, we conduct

- 5 rounds for each sample and verify the effects of three different processing methods for results of multiple rounds: majority voting(- majority@5), taking the mean score(- mean@5), and taking the best score(- best@5). For Vote by Multiple LLMs, we conduct experiments on two settings, each involving three LLMs. Setting 1 consists of GPT-4-turbo, GPT-3.5-turbo, and LLaMA3-8B-Instruct, while setting 2 consists of GPT-4-turbo, GPT-3.5-turbo, and Qwen2.5-7B-Instruct.


- 4.4.2 Results and Analysis. Comparison with Different LLMs. The experiment results on different LLMs are shown in


- Table 2. Comparing the evaluation performance of different LLMs, we found GPT-4 outperformed other LLMs with a large margin across all meta-evaluation dimensions and showed fewer biases.


Therefore, when conditions allow, using GPT-4 as an evaluator may obtain more objective and less biased evaluations. For open-source LLMs, we found that Qwen2.5-7B-Instruct showed

- 1https://platform.openai.com/docs/models
- 2https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
- 3https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct
- 4https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3
- 5https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1


Alignment Biases with

Concre- Empty Content Nested Familiar

LLMs

Position Length

Human teness Reference Continuation Instruction Knowledge (n=5106) (n=2633) (n=34) (n=28) (n=26) (n=24) (n=24) (n=24)

GPT-4-turbo 61.54 80.31 91.18 89.29 65.38 95.83 70.83 100.0 GPT-3.5-turbo 54.72 68.78 20.59 64.29 23.08 91.67 58.33 54.17

Qwen2.5-7B-Instruct 56.54 63.50 64.71 71.43 69.23 91.67 45.83 83.33 LLaMA3-8B-Instruct 50.72 38.85 20.59 57.14 65.38 75.00 45.83 54.17 Mistral-7B-Instruct-v0.3 55.42 59.78 26.47 67.86 53.85 66.67 37.50 41.67 Mixtral-8×7B-Instruct-v0.1 56.29 59.06 50.00 78.57 42.31 83.33 29.17 83.33

gemini-2.0-thinking 60.75 76.84 94.12 89.29 50.00 100.00 83.33 100.00

- o1-mini 60.16 76.73 91.18 89.29 53.85 95.83 75.00 95.83
- o3-mini 61.66 74.63 82.35 92.86 73.08 95.83 87.50 91.67 deepseek r1 56.48 69.17 94.12 100.00 50.00 100.00 75.00 87.50


Table 2. The meta-evaluation results for different LLMs. All the values are percentages.

human=model1 human=model2 human=TIE aligned / total accuracy (%) aligned / total accuracy (%) aligned / total accuracy (%)

LLMs

GPT-4-turbo 1418 / 2071 68.47 1438 / 2070 69.47 286 / 962 29.73 gemini-2.0-thinking 1354 / 2070 65.41 1621 / 2070 78.31 127 / 962 13.20

- o1-mini 1444 / 2070 69.76 1401 / 2071 67.65 227 / 963 23.57
- o3-mini 1448 / 2004 72.26 1206 / 2004 60.18 399 / 943 42.31 deepseek r1 1369 / 2071 66.10 1342 / 2071 64.80 173 / 964 17.95


- Table 3. The results of each human label in LLMEval2. Only valid responses are counted when calculating the accuracy, while samples that couldn’t receive responses due to triggering Azure OpenAI’s content management policy are excluded. So there are some differences in the total values of different models.


Alignment Biases with

Concre- Empty Content Nested Familiar

Improvement Strategies

Position Length

Human teness Reference Continuation Instruction Knowledge (n=5106) (n=2633) (n=34) (n=28) (n=26) (n=24) (n=24) (n=24)

GPT-3.5-turbo

- - base 54.72 68.78 20.59 64.29 23.08 91.67 58.33 54.17
- - w/ explanation 52.47 48.97 35.29 60.71 38.46 91.67 41.67 50.00
- - w/ self-validation 54.86 69.31 23.53 60.71 23.08 91.67 41.67 50.00 w/ multi rounds
- - majority@5 54.68 70 11 26.47 67.86 23.08 95.83 54.17 50.00
- - mean@5 54.72 69.58 11.76 57.14 26.92 87.50 50.00 50.00
- - best-of-5 51.95 58.72 5.88 42.86 19.23 87.50 37.50 45.83


- multi LLMs (set 1) 57.66 32.28 26.47 64.28 46.15 87.50 66.67 62.50
- multi LLMs (set 2) 58.19 70.98 64.71 71.43 69.23 91.67 45.83 83.33 Table 4. The results for different strategies based on GPT-3.5-turbo. All the values are percentages.


exceptional evaluation capabilities, outperforming other open-source LLMs in the experiments. Moreover, it surpassed GPT-3.5-turbo in most dimensions except for Position Bias and Nested Instruction Bias, indicating that it can be a promising choice as an open-source LLM-as-a-Judge, with the potential to serve as a robust base model for specialized evaluators in specific scenarios.

Additionally, we observed that, apart from Concreteness Bias and Content Continuation Bias, the performance of LLMs, except GPT-4-turbo, was generally poor, particularly in the Length Bias. Even GPT-4-turbo experienced substantial degradation in Empty Reference Bias and Nested Instruction Bias. While Position Bias can be mitigated by swapping the positions of the inputs, addressing other biases may require researchers to explore more effective evaluation strategies. Meanwhile, we also observed that different LLMs in the experiments show no significant differences in the alignment with humans, and there is clear space for improvement.

Therefore, to achieve reliable evaluations, suggestions for model selection include: First, prioritizing powerful or fine-tuned LLMs as foundational evaluators. This approach increases the likelihood of obtaining human-aligned judgments while leveraging stronger instruction-following and comprehension capabilities to handle evaluation prompts with complex strategies. Additionally, it is advisable to conduct small-scale meta-evaluations before model selection to detect potential biases. As experimental results demonstrate, different models exhibit varying susceptibility to distinct biases—even powerful LLMs like GPT-4-Turbo can be severely impacted by specific biases such as Empty Reference. Thus, understanding a model’s bias profile before selection aids in formulating effective evaluation strategies and obtaining reliable results.

Comparison with Different Strategies. Table 4 shows the effectiveness of different improvement strategies for enhancing the evaluation performance of GPT-3.5-turbo. The results reveal that not all strategies effectively improve LLM-as-a-judge’s performance. Providing with Explanation (w/ explanation) provides interpretability by offering reasons alongside evaluation scores or selections, which aids in logical backtracking during human review. However, in terms of evaluation performance and bias mitigation, it generally has a negative impact. This performance decline is speculated to be caused by deeper biases introduced by self-explanation. Self Validation (w/ selfvalidation) shows minimal effectiveness, likely due to the LLMs’ overconfidence, which may limit its re-evaluation efforts during self-validation. We will further discuss this limitation in Section 6.1.

Summarize by Multiple Rounds with majority voting (w/ majority@5) is a strategy with clear benefits, showing improvements across multiple dimensions. It suggests that taking the majority voting results from repeated evaluations helps reduce the impact of randomness in LLMs, thereby addressing bias issues. However, Summarize by Multiple Rounds with taking mean score (w/ mean@5) or with taking best score (w/ best-of-5) did not improve the evaluation performance and even had some adverse effects. Compared to w/ majority@5, which selects the major result from multiple rounds, w/ mean@5 might include results with biases in the mean score calculation, and similarly w/ best-of-5 could potentially select overly high scores influenced by biases. Therefore, the latter two strategies do not effectively mitigate the impact of biases on automated evaluation.

The evaluation results of Vote by Multiple LLMs (multi LLMs set 1 and set 2) are closely related to the LLM selection. Comparing set 1 and set 2, where LLaMA3-8B-Instruct was replaced by Qwen2.5-7B-Instruct in set 2, it revealed significant differences in performance across various dimensions. In set 1, the poor performance of GPT-3.5-turbo and LLaMA3-8B-Instruct in the Length Bias negatively impacted the overall performance, whereas in set 2, the performance in this dimension was better, which was aligned with Qwen2.5-7B-Instruct. Similar trends were observed in dimensions like Position Bias, Familiar Knowledge Bias, and so on. This suggests that when multiple LLMs are adopted for joint evaluation, the differences between their evaluation performances must be carefully considered.

Based on current experiments, several evaluation strategy design suggestions may be beneficial for achieving reliable evaluations. First, integrating multiple-source results serves as a straightforward and effective approach. After selecting reliable models as evaluators, integrating multi-source results effectively mitigates the negative impacts of inherent noise (e.g., stochasticity in LLMs), enhancing the stability and trustworthiness of evaluation results. Second, experiments comparing majority@5 and mean@5 strategies reveal that pairwise evaluations by LLMs yield more reliable results than pointwise—likely because the comparison process better captures nuanced distinctions. Finally, simultaneously generating evaluations and explanations may not be advisable. While explanations help humans understand LLM decision processes, their simultaneous execution may compromise the quality of evaluations.

Evaluation of Reasoning LLM-as-a-Judge. As discussed in Sections 2.4 and 2.5, judgment serves as the foundation for effective reasoning capabilities. In other words, models with stronger reasoning capabilities are generally better equipped to perform as reliable judges. To validate this assumption, we conducted evaluations on several reasoning LLMs, including o1-mini, o3mini, Gemini-thinking, and Deepseek-R1. The results in Tables 2 and 3 provide key insights into the performance of reasoning-focused LLMs. While these models—gemini-2.0-thinking, o1-mini, o3-mini, and deepseek r1—demonstrate competitive alignment and accuracy relative to the top-performing GPT-4-turbo, their improvements in tasks requiring human alignment are not as pronounced as expected.

GPT-4-turbo remains the benchmark for alignment, achieving the highest accuracy rates of 68.47% and 69.44% in the human=model1 and human=model2 scenarios, respectively. It also excels in resolving ambiguous cases, with an accuracy of 29.67% in the human=TIE scenario, outperforming all other models. Among reasoning-enhanced models, gemini-2.0-thinking shows strong performance in the human=model2 scenario, achieving an accuracy of 78.27%—surpassing GPT-4turbo—highlighting its capability to identify models that align more closely with human judgment. However, this strength does not consistently extend to other tasks or scenarios. Similarly, o1-mini and deepseek-R1, while trailing slightly behind GPT-4-turbo and gemini-2.0-thinking, outperform non-GPT models like Mixtral-8×7B-Instruct-v0.1, demonstrating the added value of reasoning-based enhancements in alignment tasks. These results indicate that reasoning-enhanced LLMs provide meaningful advancements over baseline models but fall short of delivering consistent advantages in alignment-related tasks, suggesting room for further optimization in this area.

Experiment Summary. Due to the inherent capabilities and potential risks of LLMs, common improvement strategies for LLM-as-a-judge are not fully effective in improving the performance or mitigating biases. The limitations and challenges will be further discussed in Section 6.

Based on the current experimental analysis, an empirical strategy for pairwise comparison evaluation tasks is to select more powerful LLMs and to adopt two evaluation strategies: one is swapping the positions of the evaluation contents, the other is taking the majority voting results from multiple rounds of evaluation, which can effectively mitigate biases. As for improving the alignment with humans, further exploration is still needed.

##### 4.5 Rethinking Meta-evaluation

While prior work has introduced various evaluation dimensions, datasets, and metrics, such efforts remain insufficient for evaluating LLM-as-a-Judge. Based on a comprehensive review of existing works and the empirical analyses for experiments in sec 4.4, it can be observed that current metaevaluation frameworks continue to face substantial limitations, underscoring the need for more systematic and robust approaches.

- (1) Need for Unified and Comprehensive Benchmark. Given the diverse evaluation dimensions,


such as agreement, multiple types of bias, and adversarial robustness, there is a pressing need for a unified benchmark that systematically and comprehensively quantifies these biases within a single framework. As shown in Table 1, EVALBIASBENCH [110] was proposed as a test set to measure six types of bias. Other work [185] is dedicated to proposing a unified bias testing process, including automated perturbation and a unified metric. They constructed a bias quantification framework CALM, which covers 12 types of bias. Despite these efforts, existing work only covers a subset of evaluation dimensions and lacks a comprehensive framework that includes all relevant aspects. As a result, many current studies that adopt LLM-as-a-judge still need to design their own meta-evaluation protocols and conduct manual verification to justify the reliability. Establishing a

unified, systematic, and authoritative meta-evaluation benchmark would significantly advance the development and adoption of LLM-as-a-judge.

- (2) Challenges of Controlled Study. When evaluating a specific dimension, especially a particular


type of bias, it is often challenging to isolate the bias of interest from other confounding factors such as additional biases or general quality-related characteristics. For instance, in the case of position bias, lengthening the response could potentially alter the style, fluency, and coherence, or even introduce new biases such as self-enhancement bias. Additionally, the tendency for GPT-4 to favor its own responses over those of GPT-3.5 can be interpreted as either self-enhancement bias or a proper tendency towards higher quality text. Therefore, it is essential for analytical work to carefully control for these variances.

Informal Deﬁnition Formal Deﬁnition

What is LLM-as-a Judge?

##### 5 APPLICATIONS

The application of LLM-as-a-Judge spans a wide spectrum, reflecting both technical advancements and domain-specific demands. In machine learning, they are used to evaluate NLP tasks, assess social intelligence, and support multi-modal evaluation. Beyond the technical sphere, LLMs are increasingly applied in critical domains, as shown in Figure 14, such as finance, law, and scientific discovery (Ai4Sci) [210], where domain expertise and rigorous evaluation are indispensable.

Evaluation Pipeline

Quick Practice

How to improve LLM-as-a-Judge?

![image 71](paper__llm_judge_2411_15594_images/imageFile71.png)

![image 72](paper__llm_judge_2411_15594_images/imageFile72.png)

to evaluate the quality of academic works.

to evaluate the viability of creative ideas.

![image 73](paper__llm_judge_2411_15594_images/imageFile73.png)

![image 74](paper__llm_judge_2411_15594_images/imageFile74.png)

How to evaluate LLM-as-a-Judge?

LLM-as-a-Judge

![image 75](paper__llm_judge_2411_15594_images/imageFile75.png)

Writer

Reviewer

Why is LLM-as-a-Judge important for AGI?

![image 76](paper__llm_judge_2411_15594_images/imageFile76.png)

![image 77](paper__llm_judge_2411_15594_images/imageFile77.png)

Machine Learning

Application

Other speciﬁc domains

Quant

Doctor

![image 78](paper__llm_judge_2411_15594_images/imageFile78.png)

![image 79](paper__llm_judge_2411_15594_images/imageFile79.png)

to evaluate market trends and financial risks.

to evaluate pa ent data to diagnose condi ons.

play as

Reliability Robustness

Fig. 14. The development process and future prospects of LLM-as-a-Judge.

In the AI era [178], LLM-as-a-Judge systems are also demonstrating their potential to assist or even replace human judgment across a broad range of professional domains. Many roles inherently require the ability to evaluate, assess, or adjudicate complex scenarios, and LLMs, with their advanced data processing and pattern recognition capabilities, are particularly well-suited to support or enhance these tasks [166]. For instance, writers can leverage LLMs to assess the viability and originality of creative ideas by analyzing narrative structures and market trends; doctors can employ LLMs to diagnose conditions and predict outcomes from medical records and imaging data [142, 206, 217]; quantitative analysts can utilize LLMs to forecast market movements and assess risks by identifying patterns in financial data; and judges can rely on LLMs to interpret laws and precedents, aiding in the adjudication of legal cases. These emerging applications further

LLM-as-a-Judge for Data Annotation MLLM-as-a-Judge More LLM-as-a-Judge Benchmarks LLM-as-a-Judge for LLM Optimization

Future work

demonstrate the adaptability of LLM evaluators, opening pathways toward broader integration in practice. This section systematically reviews these domains, outlining how LLM-as-a-Judge contributes to reliable and scalable evaluation in each.

##### 5.1 Machine Learning

Large Language Models (LLMs) have emerged as powerful evaluative tools across a wide range of machine learning (ML) tasks, giving rise to the paradigm of “LLM-as-a-Judge”. This approach leverages the language understanding and reasoning capabilities of LLMs not only to generate responses or predictions, but also to assess, critique, and compare model outputs in various scenarios. Applications span classic NLP tasks, text generation, reasoning and procedural tasks, information retrieval, as well as more recent advances in social intelligence and multi-modal understanding. In the following, we categorize the main areas where LLM-as-a-Judge has been actively applied within machine learning, and analyze the unique requirements and challenges encountered in each domain.

- 5.1.1 NLP. LLMs have been successfully employed as evaluators in several NLP tasks, including sentiment analysis, machine translation, and text summarization. In sentiment analysis, numerous biases influencing LLM-based judgments have been identified, prompting the creation of automated frameworks to systematically quantify these biases.


Text Generation. Text generation tasks, such as dialog response generation, summarization, story creation, and creative writing, require content that is safe, accurate, and contextually relevant, though there isn’t a single "correct" answer [6, 9]. Unlike traditional metrics-based evaluations, LLM-as-a-judge offers a nuanced, adaptable, and customized assessment. According to Zheng et al. [213], LLMs like GPT-4 can evaluate text generation comparably to humans. This method has been used to evaluate outputs from single models and to compare multiple models in competitive settings. For instance, Gao et al. [38] employ ChatGPT for human-like summarization evaluation, while Wu et al. [169] propose a comparison-based framework where LLMs act as judges to evaluate summarization quality.

Modern LLMs excel at generating detailed, long-form responses, but longer outputs increase the risk of hallucinations. To address this, Cheng et al. [21] and Zhang et al. [198] use GPT-4 to identify logically structured yet nonsensical statements. Additionally, Wang et al. [152] propose a critique-based system to evaluate hallucinations by selecting relevant evidence and providing detailed critiques. Beyond hallucinations, generating harmful or unsafe responses is a significant concern. To tackle this, Li et al. [80] introduce MD-Judge and MCQ-Judge for evaluating safetyrelated QA pairs, focusing on queries designed to provoke unsafe responses. However, an overly cautious approach can lead to excessive refusal responses, affecting user experience. To explore this, Xie et al. [172] conduct a meta-evaluation of various LLM-as-a-judge frameworks, assessing refusal tendencies in response to potentially unsafe queries. Additionally, Yu et al. [189] introduce an LLM-based answer extractor to accurately identify critical parts of answers in text generation, and An et al. [2] propose L-Eval, a framework for standardized evaluation of long-context language models, followed by Bai et al. [7] who use LLM-as-a-judge to filter evaluation data for long-context LLMs.

Recent studies have also used LLM-as-a-judge to evaluate the general capabilities of generative models through debate-based frameworks. For example, Chan et al. [15] introduce a multi-agent debate framework to facilitate autonomous discussions and assess the quality of generated responses in tasks. Similarly, Moniri et al. [106] propose an automated debate framework to evaluate LLMs on domain knowledge, problem definition, and inconsistency recognition.

Reasoning. Enhancing the reasoning capabilities of LLMs can overcome the limitations of scaling laws, unlocking their full potential. Effective reasoning is essential for tackling complex problems, making informed decisions, and delivering accurate, context-aware responses. Wei et al. [167] introduce Chain-of-Thought (CoT) prompting to facilitate step-by-step reasoning. More sophisticated cognitive structures [43, 182] have been proposed to further enhance reasoning, yet selecting a reliable reasoning path remains a significant challenge. LLM-as-a-judge has been employed to address this issue.

Some studies focus on sample-level reasoning path selection. Gao et al. [36] present a strategy evaluator for assessing candidate strategies. Kawabata and Sugawara [60] propose REPS (Rationale Enhancement through Pairwise Selection), which uses pairwise self-evaluation to select valid rationales. Lahoti et al. [71] demonstrate that LLMs can identify and enhance response diversity by aggregating multiple critiques. In multi-agent frameworks, Liang et al. [83] introduce multi-agent debating (MAD), where a judge LLM selects the most reasonable response. Similarly, Li et al. [76] utilize a judge LLM in layer-based multi-agent collaboration to improve response quality and efficiency.

For step-level reasoning path selection, LLMs act as process reward models (PRMs) to evaluate state scores. Creswell et al. [23] break down reasoning into Selection and Inference, using LLMs to judge potential reasoning traces. Xie et al. [173] propose the Kwai-STaR framework, transforming LLMs into state-transition reasoners for mathematical reasoning. Lightman et al. [84] train LLMs as PRMs for inference-time supervision and best-of-N sampling. Setlur et al. [124] introduce process advantage verifiers (PAVs) to generate rewards based on the likelihood of future correct responses. Advanced cognitive structures are also simulated; Hao et al. [43] use LLMs as a world model with Monte Carlo Tree Search (MCTS) for deliberate path selection. Besta et al. [10] model LLM outputs as graphs to evaluate coherence and logical reasoning. Additionally, critique-based LLM judges [4, 72, 184, 194] provide detailed feedback to enhance the reasoning process.

Yao et al. [183] pioneered the use of LLMs in an interleaved manner to generate reasoning traces and task-specific actions. Reasoning traces guide the model in updating action plans, while actions facilitate interaction with external sources. Building on this, Yang et al. [180] introduced Auto-GPT, which leverages LLM-as-a-judge to enhance tool usage accuracy. By integrating a variety of external tools, LLMs become more versatile, improving planning performance through judicious tool selection. Sha et al. [125] explored the potential of LLMs in decision-making for complex autonomous driving scenarios, requiring human-like commonsense reasoning. Zhou et al. [220] employed a self-discovery process where LLMs judge queries and select the most suitable reasoning structure for subsequent inference.

Retrieval. The role of LLM-as-a-judge in retrieval encompasses both traditional document ranking and dynamic Retrieval-Augmented Generation (RAG) approaches. In traditional retrieval, LLMs enhance ranking accuracy through advanced prompting techniques, enabling effective document ordering with minimal labeled data. RAG frameworks leverage LLMs’ ability to generate content guided by retrieved information, supporting applications requiring complex or evolving knowledge integration.

Recent studies have explored LLMs as judges for document ranking, aiming to boost precision and reduce reliance on extensive training data. Zhuang et al. [223] embed fine-grained relevance labels within LLM prompts, enabling models to distinguish subtle relevance variations for refined document ordering. Innovations in listwise ranking include Ma et al. [102]’s Listwise Reranker with a Large Language Model (LRL), which reorders document identifiers without task-specific training data. Zhuang et al. [224] introduce a Setwise prompting strategy for zero-shot ranking, enhancing efficiency without sacrificing performance. To address positional biases, Tang et al. [141]

propose permutation self-consistency, averaging multiple list orders to yield order-independent rankings. Qin et al. [112] critique pointwise and listwise ranking prompts, proposing Pairwise Ranking Prompting (PRP) with medium-sized, open-source LLMs as a cost-efficient alternative to larger models.

Recent advancements in RAG have explored LLMs’ capacity for self-evaluation and improvement without annotated datasets or parameter adjustments. Tang et al. [140] propose Self-Retrieval, consolidating information retrieval within a single LLM using natural language indexing, transforming retrieval into a document generation and self-assessment process. In question answering, LLMs are increasingly used as evaluative agents. Rackauckas et al. [114] introduce an LLM-based evaluation framework generating synthetic queries from user interactions and domain-specific documents, with LLMs evaluating retrieved documents and ranking RAG agent variants via RAGElo. Zhang et al. [199] study LLMs’ ability to assess relevance versus utility in open-domain QA, demonstrating effective distinction and adaptability with counterfactual passages.

Domain-specific RAG systems reveal LLMs’ potential to navigate complex queries by integrating specialized knowledge structures. Wang et al. [153] present BIORAG, enhancing vector retrieval with hierarchical knowledge structures and a self-aware evaluated retriever. Li et al. [77] introduce DALK, combining an LLM with a continuously evolving Alzheimer’s Disease knowledge graph, using self-aware knowledge retrieval for noise filtering. Jeong et al. [53] propose Self-BioRAG, adapting RAG principles to biomedical applications Liu et al. [92], with LLMs selecting the best evidence for answer generation.

Within NLP, especially for tasks such as text generation, reasoning and retrieval, LLM-as-aJudge enables flexible, scalable, and human-aligned evaluation. However, the open-endedness and diversity of NLP tasks (such as dialog or story generation) mean that the requirements for judgment reliability often focus on robustness to context, avoidance of hallucinations, and sensitivity to subtle errors or biases. In domains such as safety or factuality evaluation, higher reliability is needed due to the risk of generating unsafe or misleading content. This specificity raises demands for both the reasoning ability and the transparency of the LLM judge, as highlighted by the increasing focus on critique-based and meta-evaluations.

- 5.1.2 Social Intelligence. As the capabilities of large language models (LLMs) continue to grow, they are increasingly being applied to tasks that require nuanced social understanding—abilities traditionally considered uniquely human. Social intelligence encompasses a range of competencies, including the interpretation of social contexts, adherence to ethical and cultural norms, understanding of emotional cues, and participation in multi-turn interactions that involve negotiation, persuasion, or empathy. Evaluating these capabilities requires moving beyond conventional academic benchmarks toward more interactive and context-sensitive frameworks.


Recent studies have begun to systematically explore the social intelligence of LLMs. For example, Xu et al. [175] conduct a comprehensive assessment comparing LLMs’ social reasoning skills with their performance on academic tasks. Their findings indicate that although LLMs have made substantial progress in structured problem-solving, they still lag significantly in social intelligence relative to human standards. To facilitate more nuanced evaluation, Zhou et al. [221] developed SOTOPIA, a simulated environment where multiple LLM-based agents interact in rich social scenarios with assigned goals and social constraints. The accompanying evaluation framework, SOTOPIA-EVAL, employs GPT-4 as an automated judge to assess the agents’ performance on dimensions such as goal achievement, financial decision-making, and maintenance of social relationships. This line of research highlights both the potential and the limitations of current LLMs in replicating human-like social reasoning and interaction. Zhang et al. [196] introduces “Agent-as-a-Judge,” a scalable framework in which large language models are instructed to act as

sentient evaluators of multi-agent social interactions. By embedding LLMs in role-playing scenarios that demand theory-of-mind, empathy, and conflict resolution, the study shows that GPT-4-based judges correlate strongly with human ratings (r = 0.83) on higher-order social cognition tasks, while also revealing systematic biases that increase with agent anonymity.

Further efforts are being made to refine evaluation protocols and expand the scope of social intelligence benchmarks. Some researchers are incorporating human-in-the-loop evaluations to calibrate automated judgments, while others are designing more diverse cultural and linguistic scenarios to test cross-cultural adaptability. These developments are critical for deploying LLMs in applications such as virtual assistants, educational tools, and interactive entertainment, where social alignment is essential for user trust and engagement.

- 5.1.3 Multi-Modal Evaluation. The emergence of multi-modal large language models (MLLMs) that integrate text with visual, auditory, and other sensory inputs has created a need for robust evaluation frameworks capable of assessing cross-modal understanding and generation. Multimodal evaluation introduces unique challenges such as modality alignment, semantic consistency across domains, and the integration of contextual information from heterogeneous sources.


Several recent benchmarks have been developed to address these challenges. Chen et al. [17] introduced a comprehensive benchmark for evaluating MLLMs on tasks including image captioning, visual question answering, and mathematical reasoning with visual inputs. Their study revealed that while LLM-based judges perform well in pairwise comparisons—often matching human preferences—they struggle with absolute scoring and batch ranking tasks, where consistency and calibration are more difficult to achieve. In the context of non-English modalities, Wu et al. [170] presented a benchmark focused on Chinese multi-modal alignment, identifying specific challenges related to coherence and reasoning. They proposed a calibrated evaluation model that significantly improves judgment consistency over existing systems.

To increase transparency in multi-modal evaluations, Xiong et al. [174] explored the use of LLMas-a-judge to not only score model outputs but also generate natural language rationales explaining each assessment. This dual approach improves the interpretability of model judgments and helps developers identify failure modes. In a specialized application, Chen et al. [20] constructed the first benchmark for evaluating large vision-language models (LVLMs) on self-driving corner cases. Their results demonstrate that LLM-based judges correlate more closely with human evaluations than judgments provided by LVLMs themselves, underscoring the generalizability of text-based judges even in vision-dominated tasks.

Surveying broader trends, Jiang et al. [54] reviewed advancements in multi-modal and multiagent systems, highlighting mechanisms designed to enhance inter-agent collaboration and reduce cognitive bias. Ongoing research is extending multi-modal evaluation to dynamic video content, audio-visual integration, and embodied AI environments, where temporal and interactive dimensions further complicate assessment. These efforts collectively contribute to more reliable, scalable, and human-aligned evaluation paradigms for multi-modal AI systems.

##### 5.2 Other Specific Domains

- 5.2.1 Finance. LLMs have demonstrated significant potential in the finance domain, particularly in tasks such as forecasting, anomaly detection, and personalized text generation [209]. As financial applications frequently require rigorous evaluations with high stakes, there is an increasing demand for reliable and transparent LLM-based evaluators tailored to financial contexts.


Current research on LLM-as-a-Judge applications in finance primarily falls into three main areas. Firstly, considerable efforts have focused on designing evaluators that effectively incorporate expert domain knowledge. For instance, Brief et al. [13] investigated multi-task fine-tuning techniques

![image 80](paper__llm_judge_2411_15594_images/imageFile80.png)

KB

Update

Writer

Shared Context

𝒕𝟎 𝒕𝟏 𝒕𝟐 𝒕𝑻

ts_zscore((ts_av_diff(cashflo w, 66)) / ts_sum(ts_av_diff(cashflow, 66), 252), 252)

if_else(cond rank(ts_sum(vec _avg(news_senti))), alpha_1, -1)

ts_zscore(covariance(fundame ntal_alpha_0， alpha_1, 252), 252)

Trading Idea: Cashflow alpha

……

Review: May combine with sentiment to make it more accurate Passed: FALSE

Review: May also incorporate fundamental data as confirmation Passed: FALSE

Review: Looks good to me! Passed:TRUE

LLM-as-a-Judge

|LLM-as-a-Judge Based on the eval result, I suggest several further improvements: 1. incorporate ema smoothing …|
|---|


|Quantitative Evaluation<br><br>{ic_score: 0.08, turnover: 0.24, Sharpe: 1.21, vol: 0.24, max_drawdown: 0.24}|
|---|


Real Environment

Knowledge retrieval

In-context inference

Inner loop iteration

Final Answer

Submit

Fig. 15. Illustration of using dual-LLM iterative feedback loop for alpha generation in finance. Figure adapted from Wang et al. [157].

specifically developed to improve LLM performance in finance-related assessments. Similarly, Yu et al. [190] introduced FinCon, a multi-agent system that utilises conceptual verbal reinforcement from an LLM-based evaluator to support financial decision-making processes.

Secondly, developing robust benchmarks and evaluation frameworks constitutes a major area of research. Representative efforts include UCFE, a financial evaluation benchmark based on user feedback [181]; IndoCareer, a dataset consisting of professional financial examination questions [67]; and AI-generated, domain-specific evaluation sets designed to systematically assess LLMs’ understanding of financial knowledge and reasoning abilities [117].

Thirdly, targeted research addresses specific application scenarios within finance, including quantitative investment strategies, credit scoring, and ESG (Environmental, Social, and Governance) scoring. Wang et al. [157] proposed the QuantAgent framework, which employs a dual-LLM iterative loop to refine trading signals. In this architecture, one LLM generates initial trading ideas, while a second LLM rigorously evaluates and iteratively improves these ideas using quantitative metrics such as the information coefficient and Sharpe ratio (see Figure 15). Additionally, recent studies have demonstrated promising LLM-based evaluators for credit scoring [5, 187] and ESG scoring [209], further highlighting the broad potential of LLMs in financial applications.

Despite these advancements, current applications remain in their early stages, constrained by several critical limitations. Ensuring factual accuracy and consistent judgments is challenging, particularly when navigating complex financial regulations or rapidly evolving market data. Additionally, LLMs primarily excel in qualitative assessments and textual analysis—such as reviewing financial news or reports—and currently cannot autonomously perform quantitative tasks such as portfolio optimization or high-frequency trading. As such, their role remains predominantly auxiliary.

In summary, LLM-as-a-Judge applications in finance are in an emergent phase, showing promise in qualitative analysis but limited by inconsistencies in handling dynamic market data and regulatory complexities. Users demand high reliability in the form of factual accuracy and consistent judgments to mitigate financial risks, echoing broader challenges in bias mitigation and robustness discussed earlier in this survey. As such, integrating domain-specific validation will be key to building trust and enabling scalable deployment.

- 5.2.2 Law. LLMs have shown growing capabilities in providing professional advice in specialized fields such as legal consultation, particularly excelling in tasks like text summarization and legal reasoning. Given the complexity, sensitivity, and societal importance of legal decisions, the legal


domain exhibits heightened concerns regarding potential biases, factual inaccuracies, and transparency challenges inherent in LLM-based evaluators. Thus, rigorous evaluation methodologies are imperative for responsible deployment in this context.

Current research on LLM-as-a-Judge applications in the legal domain can be categorized into two main areas. Firstly, considerable efforts are devoted to developing specialized evaluators that directly incorporate expert legal knowledge and practices. For example, Ma et al. [101] employ general LLMs with expert-designed few-shot prompts to simulate the annotation process, effectively identifying legally relevant facts and precedents. This demonstrates the potential of automated judicial evaluators. Cheong et al. [22] propose a comprehensive four-dimensional framework for developing responsible LLM-driven legal advice systems. This framework explicitly considers user characteristics, query specificity, AI capabilities, and broader social implications, emphasising the need for a nuanced and context-aware approach to LLM integration in legal practice. Similarly, Ryu et al. [119] introduce Eval-RAG, a retrieval-augmented evaluator designed to validate LLMgenerated legal texts. In experiments involving Korean legal question-answering tasks, Eval-RAG achieved closer alignment with human expert judgements than conventional evaluation methods, reinforcing the value of integrating domain-specific retrieval mechanisms.

Secondly, the development of comprehensive benchmarks and evaluation datasets represents a crucial research area, aiming to systematically measure and improve LLM legal reasoning capabilities. Representative examples include multi-domain datasets such as IndoCareer, which contains professional legal examination questions [67], and LegalBench, a collaborative benchmark specifically designed to assess legal reasoning skills across multiple jurisdictions and languages [41]. Additionally, language-specific benchmarks have been developed, including LexEval for evaluating Chinese legal texts [78] and Eval-RAG for Korean legal contexts [119]. In addition to evaluating technical reasoning abilities, targeted benchmarks have also been introduced to assess ethically sensitive aspects of legal advice, such as ethical reasoning [204] and the potential harmfulness or biases present in generated outputs [3], highlighting the complexity and sensitivity of LLM evaluation in the legal domain.

Despite these advancements, significant gaps and limitations persist, restricting the widespread adoption of LLMs in the legal domain. Legal reasoning inherently requires precision, transparency, and strict adherence to established statutes and case precedents. However, current LLMs are still prone to factual hallucinations and may overlook subtle but legally significant distinctions. Bias is also a major concern. LLMs trained on large-scale datasets may unintentionally incorporate societal biases, leading to unfair or skewed legal judgments, especially in sensitive cases involving ethics or human rights. Additionally, due to the complexity and variability of jurisdiction-specific legal frameworks, general-purpose LLMs often struggle to capture nuanced differences without detailed contextualization and additional guidance.

Future research should prioritize addressing these limitations through targeted innovations. Promising directions include enhancing factual reliability by integrating robust legal databases and retrieval mechanisms, thereby enabling real-time cross-verification of LLM-generated outputs against authoritative legal sources. Another important avenue is the development of bias mitigation strategies, such as selective filtering of training data or calibration processes guided by expert legal annotations. Crucially, greater interpretability and transparency will be essential. Future LLM judges should ideally provide explicit rationales, relevant statutory references, and coherent justifications for each decision. Ultimately, close collaboration between AI developers and legal professionals will be vital to navigating regulatory frameworks, ensuring ethical compliance, and facilitating the responsible deployment of LLM-as-a-Judge systems within legal contexts.

###### 5.2.3 AI for Science. LLMs have demonstrated notable potential in scientific fields, particularlyin domains such as medicine and mathematics, where they increasingly act as evaluators to enhanceaccuracy and consistency [142, 210, 219].

Current research on LLM-as-a-Judge in science can be grouped into three major directions. First, specialized evaluators are being crafted for high-stakes clinical reasoning. Brake and Schaaf [12] showed that a LLaMA-2 evaluator attains human-level agreement (Cohen’s 𝜅 =0.79) when checking the internal consistency of clinical notes, while Krolik et al. [68] reported similarly strong performance for judging medical Q&A responses. Hosseini et al. [46] released the first public benchmark targeting long-form medical QA; their study found that open-weight LLMs acting as judges correlate well with physician ratings on criteria such as correctness, helpfulness and harmfulness.

Second, mathematics research has embraced step-wise reward modeling to verify reasoning chains. WizardMath applies Reinforcement Learning from Evol-Instruct Feedback and surpasses GPT-3.5 on GSM8K and MATH [99]. Building on this idea, Math-Shepherd introduces an automatic process-reward model that verifies each reasoning step without human annotations and then reinforces the solver, boosting Mistral-7B accuracy to 84.1 % on GSM8K [156]. Tong et al. proposed DART-Math, a difficulty-aware rejection-tuning pipeline that focuses training on hard problems and achieves state-of-the-art results across six math benchmarks [146]. For multimodal scenarios, Lu et al. created MathVista to evaluate textual–visual reasoning, revealing persistent weaknesses when diagrams are involved [97].

Third, comprehensive benchmarking frameworks are emerging to assess scientific LLM judges at scale. Nature Medicine’s 2024 review highlighted gaps in automatic metrics and advocated clinicianin-the-loop pipelines for summarization tasks [151]. Stanford HAI’s MedHELM introduced a holistic evaluation suite covering eleven clinical tasks and showed that even top commercial models still lag on medication-safety questions [64]. In mathematics, Xia et al. [171] built a logic-coherence judge that scores entire proof trajectories rather than final answers, providing richer diagnostic signals.

Limitations and future directions. Despite rapid progress, current medical evaluators often rely on exam-style or short-form outputs and struggle with real-world clinical complexity; hallucination detection remains an open problem [64]. Math-centric judges are still brittle on open-ended or multimodal problems, and exhaustive step verification is computationally costly. Future work should fuse LLM judges with symbolic solvers or medical knowledge bases for fact-checking, incorporate uncertainty estimation (e.g. calibrated refusals), and design multimodal-aware judges capable of interpreting figures and tables. Finally, establishing public, diverse scientific benchmarks—paired with transparent reporting of failure cases—will be crucial for trustworthy deployment of LLM-asa-Judge systems in scientific research and practice.

In summary, the LLM-as-a-Judge paradigm in scientific domains is progressing rapidly, supported by specialised evaluators and benchmarks. However, its uptake remains limited by multimodal constraints and the high cost of verification in complex settings. Reliability requirements therefore centre on hallucination detection and evidence-based rigour to maintain scientific validity, echoing the survey’s discussion of output consistency and adversarial robustness. Integrating large language models with structured knowledge bases is likely to meet these high-stakes needs for precise, verifiable judgements.

###### 5.2.4 Others. LLMs have also been employed as evaluators to enhance efficiency and consistencyacross various fields. In software engineering, a method was proposed for using LLMs to evaluatebug report summarizations, demonstrating high accuracy in assessing correctness and complete-ness, even surpassing human evaluators who experienced fatigue [69]. This approach offers a

scalable solution for evaluation. In education, automated essay scoring and revising have been explored using open-source LLMs, achieving performance comparable to traditional deep-learning models. Techniques such as few-shot learning and prompt tuning improved scoring accuracy, while revisions effectively enhanced essay quality without compromising original meaning [132]. In content moderation, an LLM-based approach was developed to identify rule violations on platforms like Reddit, achieving high true-negative rates but encountering challenges with complex rule interpretation, emphasizing the necessity of human oversight for nuanced cases [65]. In behavioral sciences, the LLM-as-a-Judge framework was evaluated for assessing user preferences based on personas, revealing limitations in reliability and consistency due to oversimplified personas, but improved significantly through verbal uncertainty estimation, achieving high agreement with human evaluations for high-certainty cases [30]. These applications of LLMs as evaluators highlight their growing potential in diverse sectors, emphasizing the need for integrating domain-specific knowledge and refining methodologies.

Moreover, LLMs as evaluators demonstrate significant advantages in qualitative assessments that are difficult to quantify, such as evaluating service quality, analyzing user experience feedback, and assessing creative content like art or literature reviews. LLMs’ capability to understand and generate nuanced language makes them well-suited for subjective evaluation tasks traditionally requiring human judgment. Future research will focus more on these areas, exploring how LLMs as judges can enhance assessment accuracy and consistency where traditional quantitative methods fall short.

In summary, the LLM-as-a-Judge paradigm is gaining traction across domains such as software engineering, education and behavioural science, where it enables scalable qualitative assessment. Nevertheless, its deployment is constrained by context-specific inconsistencies and by the difficulty of replacing fatigued human reviewers. Reliability requirements differ by field. They often centre on the consistent interpretation of nuanced rules or subjective preferences so as to minimise bias, echoing the survey’s broader themes of prompt optimisation and self-consistency. Therefore, domain-specific adaptation will be essential to satisfy these varied demands and to support reliable, efficient applications.

##### 6 CHALLENGES

In this chapter, we explore the key challenges that arise when utilizing LLMs for evaluation tasks, particularly in the context of LLM-as-a-Judge. Despite their growing capabilities, LLMs still face significant issues related to reliability, robustness, and their backbone models’ limitations. Understanding these challenges is crucial for advancing the use of LLMs in a fair, consistent, and reliable manner. We address these concerns under four main themes: reliability, robustness, powerful backbone models, and the ethical and social implications of their use.

##### 6.1 Reliability

The reliability of LLM-as-a-Judge is a primary concern, as it directly impacts the consistency and fairness of evaluations. While human judges also exhibit inherent biases, LLMs introduce their own unique set of reliability issues. These issues stem from the probabilistic nature of the models and their sensitivity to input nuances. We can further break down reliability challenges into several key areas.

In-Context Learning Sensitivity. LLMs’ in-context learning ability, where a model learns from examples in a prompt, can introduce significant reliability issues. Minor changes in prompt wording or the order of examples can lead to unstable and inconsistent results. For instance, position bias is a well-documented issue where LLMs tend to favor the first or last response in a list, leading

to unfair evaluations if the examples are poorly arranged. Similarly, the inherent randomness of an LLM’s generation can cause inconsistent inter-rater reliability, where the model gives different scores for the same input.

Overconfidence and Self-Enhancement. A major issue is overconfidence, where models, particularly those trained with Reinforcement Learning with Human Feedback (RLHF), may offer overly favorable scores for their own responses, leading to misleading evaluations. This is often tied to self-enhancement bias, where an LLM is more likely to give a higher score to an answer it generated itself compared to an equivalent answer generated by a different model.

Model Selection and Generalization. The choice of LLM itself significantly impacts evaluation dependability. The black-box nature and version dependency of commercial models like GPT-4 hinder reproducibility. While fine-tuned evaluators may seem like a solution, they often exhibit overfitting, meaning their evaluation capabilities may not generalize well beyond their training data. These models can also inherit subtle biases from their training datasets, necessitating careful meta-evaluation to ensure fairness.

##### 6.2 Robustness

The robustness of LLM-as-a-Judge refers to its ability to resist adversarial attacks and inconsistent inputs. While attacks on traditional Natural Language Generation (NLG) models are well-studied, attacks on LLM-as-a-Judge are relatively under-explored. These attacks aim to exploit a judge model’s biases, inconsistencies, or loopholes to manipulate its decision-making process.

Adversarial Attacks. Unlike traditional attacks that aim to make a model generate harmful content, attacks on LLM-as-a-Judge aim to subtly manipulate the input to change the evaluation outcome. For example, an attacker could introduce imperceptible perturbations to the text—such as paraphrasing a key sentence or adding a misleading but grammatically correct phrase—to trick the judge model into a different conclusion. These attacks are particularly insidious because the manipulated input appears harmless to a human but can cause a significant deviation in the LLM’s judgment.

Input Sensitivity and Jailbreaking. LLM judges are also susceptible to jailbreaking techniques. An attacker could craft a prompt that bypasses the model’s safety and fairness filters, causing it to produce a biased or inconsistent evaluation. The model might be prompted to take on a "persona" with specific prejudices, leading to skewed judgments. This is a significant concern for open-source LLM judges, which may not have the same level of fine-tuning for safety as proprietary models.

Brittleness of Scoring Mechanisms. The reliance on specific scoring formats can be a point of weakness. If a prompt requires an exact numerical score (e.g., "rate on a scale of 1-5"), a clever attacker could create input that confuses the model, causing it to output text instead of a number, thus breaking the automated scoring pipeline. This brittleness undermines the reliability and automation of the entire evaluation system.

##### 6.3 Limitations of Backbone Models

The effectiveness of any LLM-as-a-Judge system is directly tied to its underlying backbone model’s capabilities. A primary bottleneck lies in the lack of robust models that can serve as reliable judges for complex, multimodal content. While powerful in text, current multimodal LLMs like GPT-4 Vision still struggle with sophisticated reasoning that integrates different modalities. For example, in a medical context, a judge model might need to evaluate a diagnosis based on both a

textual description of symptoms and an image of an X-ray. A flawed model could miss a subtle but critical inconsistency between the two, leading to an inaccurate judgment. This limitation poses a significant challenge to achieving reliable evaluations in a wide range of real-world scenarios.

Even for purely text-based tasks, current LLMs have limitations in abstract and causal reasoning. When evaluating a response that requires a deep understanding of logical consistency, a model might produce a seemingly confident but fundamentally flawed evaluation. For instance, in judging a complex scientific paper or legal argument, the model may give a high score for stylistic fluency while failing to identify a subtle but fundamental flaw in the logical chain or causal argument. This gap between the model’s superficial fluency and its true reasoning depth undermines trust in its ability to handle sophisticated analytical processes and highlights the need for more robust reasoning backbones.

##### 6.4 Interpretability and Transparency of Judgments

While current LLM-as-a-Judge systems can provide seemingly reasonable scores or conclusions for many tasks, their evaluation process is often an opaque black box. This lack of transparency significantly limits user trust and constrains the application in high-stakes domains such as medicine, law, and education. For instance, in a legal context, an LLM judge might accurately summarize a case and suggest a verdict, but it cannot explicitly show which case precedents it referenced or which legal statutes it prioritized in its reasoning process. This is fundamentally different from human lawyers, who can always provide a traceable rationale for their judgment. A core challenge, therefore, lies in developing methods that can make the reasoning behind LLM-based judgments explicit and verifiable, allowing human experts to trace and validate the model’s logic path.

##### 6.5 Meta-Evaluation and Temporal Consistency

Existing research predominantly focuses on assessing the LLM-as-a-Judge’s evaluation results on a specific task, while rarely subjecting the "evaluator itself" to systematic scrutiny. This creates a critical gap, as we lack rigorous benchmarks to measure a judge’s accuracy, stability, and bias. This raises a new research imperative: how do we evaluate the evaluator, thereby ensuring the reliability of LLM-as-a-Judge systems? Furthermore, extensive empirical evidence suggests that the performance of LLM-as-a-Judge is not static, with its judgments potentially drifting over time due to model updates or contextual changes. For example, a response to a controversial topic might be rated as acceptable by a model version from March, but subsequently penalized by a June version due to new safety fine-tuning. This "evaluation drift," a type of temporal unreliability, is a particularly pronounced issue in practical scenarios where users demand consistent and stable standards over the long term, ultimately undermining trust and raising concerns about fairness.

##### 6.6 Ethical and Social Implications

Beyond technical challenges, the use of LLM-as-a-Judge raises critical ethical and social questions that must be addressed.

Bias Amplification. LLMs are trained on vast amounts of internet data, which often contains societal biases related to gender, race, and other demographics. When used as judges, these models can amplify and perpetuate these biases, leading to unfair evaluations. For instance, a model might unfairly penalize a response written in a non-standard English dialect or a writing style associated with a marginalized group. This has profound social implications, especially in high-stakes areas like hiring or content moderation.

Lack of Accountability and Transparency. The "black box" nature of proprietary LLMs makes it difficult to understand how they arrive at a specific evaluation. When an evaluation is deemed

unfair or incorrect, there is no clear way to trace the error or hold the model accountable. This lack of transparency undermines trust in the evaluation process and can be particularly problematic in fields where human oversight and accountability are paramount.

Impact on Creative and Diverse Outputs. By acting as a judge, an LLM can inadvertently shape the types of content being produced. If a model consistently favors a certain style, format, or tone, it could stifle creative and diverse outputs, leading to a homogenization of content. This phenomenon, known as evaluation-driven convergence, could harm innovation and reduce the richness of the information ecosystem.

##### 7 FUTURE WORK

The field of LLM-as-a-Judge is rapidly evolving, moving from an emerging concept to a core component of modern AI development. While we’ve seen significant progress in using LLMs for evaluation, there are still critical challenges and vast opportunities to explore. This section outlines key future research directions that are essential for building more reliable, versatile, and impactful LLM-as-a-Judge systems. We’ll delve into topics ranging from advancing the foundational reasoning and judgment capabilities of these models to expanding their application into new domains like data annotation and embodied intelligence. Our discussion also focuses on the necessity of developing more robust theoretical frameworks and benchmarks to ensure these systems are not only effective but also trustworthy and aligned with human values. This forward-looking agenda aims to guide the next generation of research, paving the way for LLM-as-a-Judge to become an indispensable tool in the pursuit of more intelligent and socially beneficial AI.

##### 7.1 Reasoning-Centric Judgement

Moving forward, Moving forward, the field is transitioning from traditional evaluation methods to a reasoning-centric approach made possible by LLM-as-a-Judge. We will first examine the symbiotic relationship between reasoning and judgment, highlighting how their synergy is essential for creating sophisticated and capable AI systems. Next, we will discuss how the integration of LLMas-a-Judge into dynamic feedback loops enables continuous self-improvement, which is key to advancing model capabilities. We conclude with the long-term vision of Self-Evolving Judges, which can adapt and refine their own evaluative abilities over time.

![image 81](paper__llm_judge_2411_15594_images/imageFile81.png)

Improve & Approach

![image 82](paper__llm_judge_2411_15594_images/imageFile82.png)

![image 83](paper__llm_judge_2411_15594_images/imageFile83.png)

LLM-as-a-Judge

![image 84](paper__llm_judge_2411_15594_images/imageFile84.png)

Reasoning/Thinking

![image 85](paper__llm_judge_2411_15594_images/imageFile85.png)

Support

Fig. 16. The relationship of LLM-as-a-Judge and Reasoning/Thinking.

- 7.1.1 The Synergy Between Judgment and Reasoning. As shown in Figure 16, reasoning and judgment are two deeply connected yet distinct cognitive abilities. Reasoning is the logical process of drawing conclusions from evidence or premises. It’s the engine that powers problem-solving, decision-making, and critical analysis. In contrast, judgment is the act of evaluating something—an


The Development of Evaluation Method

![image 86](paper__llm_judge_2411_15594_images/imageFile86.png)

Fig. 17. The development process and future prospects of LLM-as-a-Judge.

idea, an output, or a situation—against a set of standards or principles to determine its quality or validity. This distinction is crucial, but their relationship is symbiotic.

The philosopher Immanuel Kant famously described judgment as “the faculty of thinking the particular as contained under the universal.” In the context of LLMs, this means applying a general rule or set of principles (the "universal") to a specific output (the "particular") to determine its quality. For example, an LLM-as-a-Judge might evaluate a generated summary against the universal principles of conciseness, accuracy, and coherence. The relationship between these two functions is not one-way; they are mutually reinforcing. Reasoning depends on judgment to validate its intermediate steps. As a model works through a complex problem, it needs to evaluate whether each step in its chain of thought is logical and contributes to a sound final conclusion. This internal evaluation is a form of judgment. Conversely, effective judgment requires strong reasoning to evaluate options against a logical framework. You can’t make a good judgment without understanding the underlying logic.

This synergy is at the core of advanced LLM capabilities. When judgment is performed continuously and at a high frequency—for instance, an LLM evaluating every step of its own thought process—it starts to approximate the process of reasoning itself. The more a model systematically evaluates and refines its own thought processes, the more it becomes an effective reasoner. This is why LLM-as-a-Judge is more than just an evaluation tool; it’s a mechanism for enhancing a model’s reasoning capabilities.

- 7.1.2 Feedback Loops and Self-Improvement. The true power of the LLM-as-a-Judge paradigm is unleashed when it is integrated into a feedback loop that enables continuous self-improvement. A prime example is OpenAI’s o1 model, which demonstrates enhanced problem-solving ability through structured, iterative reasoning. A central component of o1’s advancement is the use of LLMas-a-Judge modules that evaluate reasoning paths at each stage, offering feedback that improves future steps. This allows the model to correct inconsistencies, identify simpler decompositions of complex problems, and progressively refine its outputs.


This dynamic feedback mechanism operates in two key modes:

- (1) Training-Time Evaluation: During the training phase, an LLM-as-a-Judge provides feedback on a model’s reasoning process. This feedback is integrated into learning objectives, for example, via RLHF or a similar mechanism. By learning from its mistakes and successes, the model internalizes better reasoning strategies that generalize across tasks.
- (2) Inference-Time Evaluation: During the testing or deployment phase, the LLM-as-a-Judge dynamically evaluates the model’s reasoning as it’s happening. This real-time feedback allows the model to make on-the-fly corrections, refining its output and leading to better results without the need for additional training.


This continuous loop of reasoning → judgment → refinement closely mirrors the principles of Constitutional AI, a framework where models are trained to self-critique and self-correct based on a set of predefined principles. For example, in models like DeepSeek-R1, the LLM acts as its own judge, refining its decisions through internal assessments. This self-generated feedback loop helps the model improve without needing external verification. By integrating LLM-as-a-Judge within such feedback-rich frameworks, models gain the ability to not only evaluate external content but also to introspect and evolve their own reasoning processes. This represents a significant step toward building AI systems that are capable of LLM optimization and self-improvement over time.

- 7.1.3 Self-Evolving Judges. A long-term vision is to enable LLM-as-a-Judge systems to possess self-calibration and self-correction abilities. This would involve evaluators that can continuously refine their biases based on external feedback, thus evolving into more reliable "evaluation agents" over time. This direction aligns with the emerging idea of "World Model-as-a-Judge," as shown in Figure 17 where an AI system can use its internal models of the world to make and justify judgments. For example, a judge could not only evaluate a proposed solution to a problem but also simulate the consequences of that solution in a hypothetical environment, identifying potential flaws before they occur. This vision implies that future evaluators will no longer be static tools but rather dynamic, evolving intelligent systems that can adapt and improve their own judgment capabilities, marking a significant step towards more autonomous and trustworthy AI.


##### 7.2 Theoretically Grounded Evaluation

Current research on the reliability of LLM-as-a-Judge primarily relies on empirical benchmarks, but it lacks a solid theoretical foundation. As a next step, it is imperative to move beyond these empirical approaches and establish a more formal theoretical framework for evaluation. Future work should borrow ideas from fields like statistics and measurement theory to introduce formal definitions of concepts like consistency and robustness. For instance, researchers could adapt established metrics such as Cohen’s Kappa or Krippendorff’s Alpha to quantify the inter-rater reliability of different LLM judges. Such a framework would allow us to systematically characterize and improve the reliability of these evaluators, moving the field from a trial-and-error approach to one that is scientifically grounded and allows for verifiable, reproducible results.

##### 7.3 More Reliable LLM-as-a-Judge

As highlighted in our Formulation (§ 2) and Strategy (§ 3), LLMs are probabilistic models that require extensive research and optimization to enhance their reliability as judges. Although current methods have improved the reliability of LLM-as-a-Judge, many challenges, including adaptability and robustness, remain unresolved. To enable probabilistic models to deliver evaluations closely aligned with real-world scenarios, future research should prioritize refining and implementing LLMas-a-Judge across the evaluation pipeline. There is considerable potential for improving reliability in various aspects, including in-context learning, model selection, post-processing techniques, and the overall evaluation framework for LLM-as-a-Judge. These efforts should prioritize not

only enhancing the reliability of assessments but also developing methodologies to systematically evaluate and validate the robustness of these assessments. Furthermore, the establishment of comprehensive evaluation benchmarks and interpretable analytical tools will be crucial for assessing and improving the reliability of LLM evaluators. Finally, the uncertain and evolving nature of robustness risks underscores the necessity of proactive mitigation strategies. These strategies should include the development of adversarial training techniques tailored to judgment tasks, the integration of robust uncertainty quantification methods, and the implementation of humanin-the-loop systems to oversee critical decisions. By addressing these challenges, we can build more resilient and dependable systems capable of maintaining high levels of reliability even under adversarial conditions.

##### 7.4 MLLM-as-a-Judge

AI systems are evolving into highly versatile and multifunctional entities [27]. Traditionally, specialized models were required for distinct language processing tasks, such as sentiment analysis, syntactic parsing, and dialogue modeling. However, large language models (LLMs) have demonstrated competence across these tasks using a single set of weights [134]. Similarly, advancements are being made toward unified systems capable of processing multiple data modalities. Instead of employing distinct architectures for processing text, audio, and images, recent models like GPT-4o [107], Gemini [40], and LLaVA [90] integrate these capabilities within a single framework. These developments highlight a growing trend toward unification in the structure and functionality of AI systems, which extends to the emerging paradigm of LLM-as-a-Judge.

Currently, MLLM-as-a-Judge frameworks [17] are emerging for evaluating models. However, research exploring how MLLM-as-a-Judge could be applied to the evaluation of data or agents remains limited. Beyond model evaluation, MLLM-as-a-Judge, much like LLM-as-a-Judge, is envisioned to have the capability to assess or annotate data, function as a Reward Model, or serve as a Verifier within intermediate reasoning processes. These expanded roles would allow MLLM-as-a-Judge to contribute more broadly to the AI pipeline.

The future of evaluation lies in developing robust multi-modal evaluators capable of reasoning and assessing complex content spanning text, audio, images, and video. While current multi-modal LLMs exhibit promising capabilities, they often lack the reasoning depth and reliability of their text-based counterparts. Future research must address these limitations, with a focus on enhancing reasoning capabilities, improving reliability, and enabling seamless integration across modalities. A practical multi-modal evaluator has the potential to not only advance AI research but also enable new applications in areas such as multi-modal content moderation and automated knowledge extraction.

##### 7.5 Advancing Evaluation Benchmarks

The development of more comprehensive and rigorous benchmarks is critical for advancing the reliability and applicability of LLM-as-a-Judge systems. This effort must proceed on two distinct but interconnected fronts: establishing a framework to evaluate the judge itself and expanding the scope of what the judge can evaluate.

Evaluation of the Evaluator (Meta-Evaluation). A critical future direction is the development of systematic meta-evaluation frameworks designed specifically to test the reliability, fairness, and consistency of LLM judges. Unlike existing benchmarks that evaluate a model’s performance on a task, these new frameworks would focus on the evaluator itself. For example, a meta-evaluation benchmark could include a carefully constructed set of prompts with known adversarial qualities, such as subtle word substitutions or paraphrasing, to test a judge’s robustness to input perturbations.

Furthermore, these frameworks must be capable of assessing the judge’s stability over time and across different model versions, thereby tracking and mitigating issues like "evaluation drift." This type of framework would be model-agnostic, capable of not only quantifying performance but also providing a basis for explaining a judge’s behavior, which in turn fosters greater transparency and trust in the system.

Expanding Benchmark Scope. While meta-evaluation ensures the integrity of the judge, we must also continue to develop more comprehensive and diverse benchmarks to push the boundaries of what LLM-as-a-Judge can accomplish. Future efforts could focus on creating high-quality, largescale datasets that encompass a wide range of scenarios, including domain-specific applications, multimodal content, and real-world complexities. For instance, a new benchmark could feature legal documents and require the judge to evaluate the logical soundness of a legal argument, or include a combination of images and text, requiring the judge to identify inconsistencies between them. These benchmarks should also integrate more detailed and fine-grained evaluation metrics that go beyond simple scores. By establishing rigorous standards and datasets akin to ImageNet in scale and impact, the LLM-as-a-Judge field can achieve deeper insights into model performance and accelerate the development of more capable and reliable evaluation methodologies.

##### 7.6 LLM-as-a-Judge for Data Annotation

In contrast, LLM-as-a-judge is a general technique where you use LLM to approximate human labeling. When you ask an LLM to assess qualities like "faithfulness to source," "correctness," or "helpfulness," you define what these terms mean in the evaluation prompt and rely on the semantic relationships the LLM learned from training data. Despite its wide applications, data annotation poses significant challenges for current machine-learning models due to the complexity, subjectivity, and diversity of data. This process requires domain expertise and is resource-intensive, particularly when manually labeling large datasets. Advanced LLMs such as GPT-4 [107], Gemini [40], and LLaMA-2 [149] offer a promising opportunity to revolutionize data annotation. LLMs serve as more than just tools but play a crucial role in improving the effectiveness and precision of data annotation. Their ability to automate annotation tasks [208], ensure consistency across large volumes of data, and adapt through fine-tuning or prompting for specific domains [101, 131], significantly mitigates the challenges encountered with traditional annotation methods, setting a new standard for what is achievable in the realm of NLP.

Whether in the field of scientific research or industry, we are all still suffering from insufficient target data and domain-specific data, or situations where the data quality is not high enough. Assuming that LLM-as-a-judge can achieve stable performance and be fair and reliable, we can use LLM to annotate data in scenarios where data is insufficient to expand the data. In scenarios with low data quality, we can assess the data quality through LLM, and label the quality tags to achieve the goal of selecting high-quality data. Currently, we have not been able to experimentally rely solely on LLM for a reliable evaluation of various scenarios of data; most of the time, we still rely on human annotation to ensure professionalism and reliability. LLM-as-a-judge often needs to learn from human annotations in order to perform certain labeling tasks.

##### 7.7 LLM-as-a-Judge for Scaling

The paradigm of LLM-as-a-Judge is poised to become a core mechanism for scaling AI development, particularly in an era where models are increasingly trained through interactive and iterative feedback loops. At its most fundamental level, this involves scaling data annotation. Traditional human labeling is a major bottleneck, as it is both costly and slow. LLM-as-a-Judge offers a path to rapidly generate massive, high-quality datasets that would be otherwise impossible to obtain.

For instance, it can be used to generate preference labels for RLHF at a scale that is prohibitive for human annotators, thus fueling the development of more sophisticated models. The judge can also be deployed in semi-automated workflows where it provides initial annotations that are then quickly verified by humans, significantly boosting throughput and efficiency. Beyond static data creation, the judge can scale the entire model optimization process by acting as an automated critic or reward model. In multi-agent systems, an LLM judge can evaluate the quality of inter-agent communication and collaboration in real time, and in optimization pipelines, it can provide nuanced, dynamic feedback to guide model fine-tuning and enhance reasoning chains, thus serving as a scalable alternative to traditional, fixed metrics.

##### 7.8 LLM-as-a-Judge for Embodied Intelligence

While LLM-as-a-Judge has primarily focused on evaluating digital outputs like text and images, its application can be extended to the domain of embodied intelligence. This presents a novel and complex challenge: judging the actions and behaviors of agents in physical or simulated environments. Unlike evaluating a text response, judging an embodied agent requires assessing a sequence of actions, their spatiotemporal relationships, and their alignment with a high-level goal, which necessitates a deep understanding of physics and cause and effect. For instance, an LLM judge could evaluate a robot’s performance in a complex task like preparing a meal. The judge would need to assess not only if the final product is correct, but also if the robot’s movements were efficient, safe, and followed a logical sequence, such as correctly aligning a cup with a dispenser to avoid spillage. Similarly, in virtual environments or gaming, an LLM judge could assess an agent’s strategic ability, navigation skills, or its capacity to solve puzzles in a human-like manner. This judge would act as a crucial feedback mechanism, providing high-dimensional, natural language feedback to guide the embodied agent’s learning process. This rich feedback, far more informative than a simple scalar reward signal, could accelerate learning and lead to more generalizable and human-aligned intelligent systems.

##### 7.9 LLM-as-a-Judge for LLM Optimization

LLM-as-a-Judge shows substantial promise for advancing LLM optimization. Recent studies [226] have begun incorporating LLM-as-a-Judge into multi-agent frameworks to guide inter-agent interactions, thereby improving overall decision-making efficiency and quality. In addition, LLM-as-a-Judge has been employed in Reinforced Fine-Tuning (ReFT) pipelines [150], functioning as a crucial scoring module for evaluating the reasoning processes of models. By flexibly adapting to diverse content formats and domains, LLM-as-a-Judge offers a robust and efficient evaluation mechanism for a wide range of optimization tasks.

Despite these encouraging developments, current research efforts are still in their infancy. Future work should focus on broadening the application domains and strategies for implementing LLMas-a-Judge, especially in complex, multi-modal scenarios. Furthermore, a systematic assessment of its reliability and generalization capabilities will be critical for fully realizing the potential of LLM-as-a-Judge in enhancing model performance and robustness.

##### 7.10 Domain-Specific Reliable Applications

The reliability requirements for evaluation differ significantly across domains. Future work should focus on developing customized LLM-as-a-Judge systems tailored for specific application scenarios, such as medical diagnosis, legal adjudication, educational assessment, and scientific peer review. This requires more than just adjusting prompts or fine-tuning strategies. For instance, a judge designed for legal cases must be trained to prioritize strict adherence to legal precedents and statutes, ensuring its judgments are defensible and auditable. Similarly, a judge for medical diagnosis must

be rigorously tested on its ability to understand clinical guidelines and interpret medical jargon correctly. This demands a specialized design concerning evaluation standards, bias control, and social responsibility to meet the unique needs of each field and earn the trust of domain experts.

##### 8 CONCLUSION

LLM-as-a-Judge has emerged as a promising paradigm for automated evaluation, offering scalability and adaptability that surpass traditional expert-driven or metric-based methods. By leveraging the reasoning capabilities of large language models, this framework excels in tasks such as text quality assessment, model evaluation, and automated data annotation. It is particularly valuable for large-scale, efficient, and adaptable evaluation. Its ability to process diverse content formats and integrate domain-specific knowledge makes it particularly well-suited for applications in education, peer review, and decision-making systems.

Despite these strengths, several challenges must be addressed to fully realize its potential. Ensuring reliability remains a key issue, because probabilistic outputs can introduce inconsistencies, overconfidence, and biases inherited from training data. Although techniques RLHF have improved alignment with human judgment, they do not eliminate all sources of subjectivity. Moreover, ensuring robustness is another critical concern. LLM-as-a-Judge can be susceptible to adversarial prompt manipulation and contextual framing biases, potentially causing unintended or unreliable evaluations. Finally, generalization across domains and modalities remains a significant hurdle, as current models struggle with evaluating multi-modal inputs, reasoning over structured data, and adapting to domain-specific evaluation standards.

To address these challenges, this paper has offered a comprehensive and principled roadmap. First, at the definitional level, we have provided both formal and informal definitions of LLM-as-aJudge, thereby establishing the conceptual boundaries of this paradigm. Critically, we introduced a contextualized definition of reliability that accounts for input variability, model characteristics, and contextual dependencies, providing a foundational framework for designing trustworthy systems. Second, at the framework level, we have brought structure to the fragmented literature by organizing existing work around four foundational questions: What is LLM-as-a-Judge? How to use it? How to improve it? and How to evaluate it? This synthesis not only unifies a scattered body of research but also identifies critical gaps and opportunities for future exploration. Third, at the empirical level, we have performed comparative analyses of existing approaches and, more importantly, proposed a novel meta-evaluation benchmark tailored to assess the judge itself. This empirical contribution facilitates systematic performance assessments, revealing crucial tradeoffs—such as robustness versus sensitivity—and providing actionable insights for constructing methodologically rigorous and practically deployable evaluation frameworks. Finally, at the perspective level, we have presented a comprehensive analysis that integrates the applications, challenges, and future directions of this paradigm. We have shown that LLM-as-a-Judge can serve as an integral component in high-stakes domains, from finance to law, by identifying unique, domainspecific reliability requirements. Our forward-looking agenda, which emphasizes theoretically grounded methodologies, systematic benchmarks for meta-evaluation, and hybrid human–AI frameworks, aims to guide the community toward LLM-as-a-Judge systems that are not only technically robust but also epistemically sound, socially trustworthy, and broadly applicable in critical sectors.

Ultimately, LLM-as-a-Judge is poised to become an integral component of next-generation evaluation systems, augmenting human expertise rather than replacing it. By addressing the challenges of reliability, robustness, and generalization, we can create more trustworthy, adaptive, and comprehensive evaluators, paving the way for their adoption across scientific research, education, industry, and beyond.

##### REFERENCES

- [1] Ayush Agrawal, Mirac Suzgun, Lester Mackey, and Adam Tauman Kalai. 2023. Do Language Models Know When They’re Hallucinating References? arXiv preprint arXiv:2305.18248 (2023).

- [2] Chenxin An, Shansan Gong, Ming Zhong, Xingjian Zhao, Mukai Li, Jun Zhang, Lingpeng Kong, and Xipeng Qiu.

2023. L-eval: Instituting standardized evaluation for long context language models. arXiv preprint arXiv:2307.11088

(2023).

- [3] Maksym Andriushchenko, Alexandra Souly, Mateusz Dziemian, Derek Duenas, Maxwell Lin, Justin Wang, Dan Hendrycks, Andy Zou, Zico Kolter, Matt Fredrikson, et al. 2024. AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents. ArXiv preprint abs/2410.09024 (2024). https://arxiv.org/abs/2410.09024

- [4] Zachary Ankner, Mansheej Paul, Brandon Cui, Jonathan D Chang, and Prithviraj Ammanabrolu. 2024. Critique-outloud reward models. arXiv preprint arXiv:2408.11791 (2024).

- [5] Golnoosh Babaei and Paolo Giudici. 2024. GPT classifications, with application to credit lending. Machine Learning with Applications 16 (2024), 100534.

- [6] Sher Badshah and Hassan Sajjad. 2024. Reference-Guided Verdict: LLMs-as-Judges in Automatic Evaluation of Free-Form Text. ArXiv preprint abs/2408.09235 (2024). https://arxiv.org/abs/2408.09235

- [7] Yushi Bai, Shangqing Tu, Jiajie Zhang, Hao Peng, Xiaozhi Wang, Xin Lv, Shulin Cao, Jiazheng Xu, Lei Hou, Yuxiao Dong, et al. 2024. LongBench v2: Towards Deeper Understanding and Reasoning on Realistic Long-context Multitasks. arXiv preprint arXiv:2412.15204 (2024).

- [8] Yushi Bai, Jiahao Ying, Yixin Cao, Xin Lv, Yuze He, Xiaozhi Wang, Jifan Yu, Kaisheng Zeng, Yijia Xiao, Haozhe Lyu, Jiayin Zhang, Juanzi Li, and Lei Hou. 2023. Benchmarking Foundation Models with Language-Model-as-an-Examiner. In Advances in Neural Information Processing Systems 36: Annual Conference on Neural Information Processing Systems 2023, NeurIPS 2023, New Orleans, LA, USA, December 10 - 16, 2023, Alice Oh, Tristan Naumann, Amir Globerson, Kate Saenko, Moritz Hardt, and Sergey Levine (Eds.). http://papers.nips.cc/paper_files/paper/2023/hash/ f64e55d03e2fe61aa4114e49cb654acb-Abstract-Datasets_and_Benchmarks.html

- [9] Sergio Bermejo. 2024. Enhancing Annotated Bibliography Generation with LLM Ensembles. arXiv preprint arXiv:2412.20864 (2024).

- [10] Maciej Besta, Nils Blach, Ales Kubicek, Robert Gerstenberger, Michal Podstawski, Lukas Gianinazzi, Joanna Gajda, Tomasz Lehmann, Hubert Niewiadomski, Piotr Nyczyk, and Torsten Hoefler. 2024. Graph of Thoughts: Solving Elaborate Problems with Large Language Models. In Thirty-Eighth AAAI Conference on Artificial Intelligence, AAAI 2024, Thirty-Sixth Conference on Innovative Applications of Artificial Intelligence, IAAI 2024, Fourteenth Symposium on Educational Advances in Artificial Intelligence, EAAI 2014, February 20-27, 2024, Vancouver, Canada, Michael J. Wooldridge, Jennifer G. Dy, and Sriraam Natarajan (Eds.). AAAI Press, 17682–17690. doi:10.1609/AAAI. V38I16.29720

- [11] Luca Beurer-Kellner, Marc Fischer, and Martin Vechev. 2024. Guiding LLMs the right way: fast, non-invasive constrained generation. In Proceedings of the 41st International Conference on Machine Learning (ICML’24, Vol. 235). JMLR.org, Vienna, Austria, 3658–3673.

- [12] Nathan Brake and Thomas Schaaf. 2024. Comparing Two Model Designs for Clinical Note Generation: Is an LLM a Useful Evaluator of Consistency? Findings of the ACL (2024).

- [13] Meni Brief, Oded Ovadia, Gil Shenderovitz, Noga Ben Yoash, Rachel Lemberg, and Eitam Sheetrit. 2024. Mixing It Up: The Cocktail Effect of Multi-Task Fine-Tuning on LLM Performance–A Case Study in Finance. ArXiv preprint abs/2410.01109 (2024). https://arxiv.org/abs/2410.01109

- [14] Tom B. Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah, Jared Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda Askell, Sandhini Agarwal, Ariel Herbert-Voss, Gretchen Krueger, Tom Henighan, Rewon Child, Aditya Ramesh, Daniel M. Ziegler, Jeffrey Wu, Clemens Winter, Christopher Hesse, Mark Chen, Eric Sigler, Mateusz Litwin, Scott Gray, Benjamin Chess, Jack Clark, Christopher Berner, Sam McCandlish, Alec Radford, Ilya Sutskever, and Dario Amodei. 2020. Language Models are Few-Shot Learners. In Advances in Neural Information ProcessingSystems33:AnnualConferenceonNeuralInformationProcessingSystems2020,NeurIPS2020,December 6-12, 2020, virtual, Hugo Larochelle, Marc’Aurelio Ranzato, Raia Hadsell, Maria-Florina Balcan, and Hsuan-Tien Lin (Eds.). https://proceedings.neurips.cc/paper/2020/hash/1457c0d6bfcb4967418bfb8ac142f64a-Abstract.html

- [15] Chi-Min Chan, Weize Chen, Yusheng Su, Jianxuan Yu, Wei Xue, Shanghang Zhang, Jie Fu, and Zhiyuan Liu. 2023. ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate. In The Twelfth International Conference on Learning Representations.

- [16] David Chan, Suzanne Petryk, Joseph Gonzalez, Trevor Darrell, and John Canny. 2023. CLAIR: Evaluating Image Captions with Large Language Models. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, Houda Bouamor, Juan Pino, and Kalika Bali (Eds.). Association for Computational Linguistics, Singapore, 13638–13646. doi:10.18653/v1/2023.emnlp-main.841


- [17] Dongping Chen, Ruoxi Chen, Shilin Zhang, Yaochen Wang, Yinuo Liu, Huichi Zhou, Qihui Zhang, Yao Wan, Pan Zhou, and Lichao Sun. 2024. MLLM-as-a-Judge: Assessing Multimodal LLM-as-a-Judge with Vision-Language Benchmark. In Forty-first International Conference on Machine Learning. https://openreview.net/forum?id=dbFEFHAD79

- [18] Daoyuan Chen, Yilun Huang, Zhijian Ma, Hesen Chen, Xuchen Pan, Ce Ge, Dawei Gao, Yuexiang Xie, Zhaoyang Liu, Jinyang Gao, et al. 2024. Data-juicer: A one-stop data processing system for large language models. In Companion of the 2024 International Conference on Management of Data. 120–134.

- [19] Guiming Hardy Chen, Shunian Chen, Ziche Liu, Feng Jiang, and Benyou Wang. 2024. Humans or llms as the judge? a study on judgement biases. ArXiv preprint abs/2402.10669 (2024). https://arxiv.org/abs/2402.10669

- [20] Kai Chen, Yanze Li, Wenhua Zhang, Yanxin Liu, Pengxiang Li, Ruiyuan Gao, Lanqing Hong, Meng Tian, Xinhai Zhao, Zhenguo Li, et al. 2024. Automated evaluation of large vision-language models on self-driving corner cases. ArXiv preprint abs/2404.10595 (2024). https://arxiv.org/abs/2404.10595

- [21] Qinyuan Cheng, Tianxiang Sun, Wenwei Zhang, Siyin Wang, Xiangyang Liu, Mozhi Zhang, Junliang He, Mianqiu Huang, Zhangyue Yin, Kai Chen, et al. 2023. Evaluating hallucinations in chinese large language models. ArXiv preprint abs/2310.03368 (2023). https://arxiv.org/abs/2310.03368

- [22] Inyoung Cheong, King Xia, KJ Kevin Feng, Quan Ze Chen, and Amy X Zhang. 2024. (A) I Am Not a Lawyer, But...: Engaging Legal Experts towards Responsible LLM Policies for Legal Advice. In The 2024 ACM Conference on Fairness, Accountability, and Transparency. 2454–2469.

- [23] Antonia Creswell, Murray Shanahan, and Irina Higgins. 2023. Selection-Inference: Exploiting Large Language Models for Interpretable Logical Reasoning. In The Eleventh International Conference on Learning Representations, ICLR 2023, Kigali, Rwanda, May 1-5, 2023. OpenReview.net. https://openreview.net/pdf?id=3Pf3Wg6o-A4

- [24] Chenhang Cui, Yiyang Zhou, Xinyu Yang, Shirley Wu, Linjun Zhang, James Zou, and Huaxiu Yao. 2023. Holistic analysis of hallucination in gpt-4v (ision): Bias and interference challenges. ArXiv preprint abs/2311.03287 (2023). https://arxiv.org/abs/2311.03287

- [25] Sunhao Dai, Chen Xu, Shicheng Xu, Liang Pang, Zhenhua Dong, and Jun Xu. 2024. Unifying Bias and Unfairness in Information Retrieval: A Survey of Challenges and Opportunities with Large Language Models. arXiv preprint arXiv:2404.11457 (2024).

- [26] Sunhao Dai, Yuqi Zhou, Liang Pang, Weihao Liu, Xiaolin Hu, Yong Liu, Xiao Zhang, Gang Wang, and Jun Xu. 2024. Neural Retrievers are Biased Towards LLM-Generated Content. In Proceedings of the 30th ACM SIGKDD Conference on Knowledge Discovery and Data Mining (Barcelona, Spain) (KDD ’24). Association for Computing Machinery, New York, NY, USA, 526–537. doi:10.1145/3637528.3671882

- [27] MRSB DATA. 2024. Multimodal artificial intelligence foundation models: Unleashing the power of remote sensing big data in earth observation. Innovation 2, 1 (2024), 100055.

- [28] Hanze Dong, Wei Xiong, Deepanshu Goyal, Yihan Zhang, Winnie Chow, Rui Pan, Shizhe Diao, Jipeng Zhang, Kashun Shum, and Tong Zhang. 2023. RAFT: Reward rAnked FineTuning for Generative Foundation Model Alignment. arXiv preprint arXiv:2304.06767 (2023). https://arxiv.org/abs/2304.06767

- [29] Yixin Dong, Charlie F. Ruan, Yaxing Cai, Ruihang Lai, Ziyi Xu, Yilong Zhao, and Tianqi Chen. 2024. XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models. doi:10.48550/arXiv.2411.15100 arXiv:2411.15100 [cs].
- [30] Yijiang River Dong, Tiancheng Hu, and Nigel Collier. 2024. Can LLM be a Personalized Judge? arXiv preprint arXiv:2406.11657 (2024).

- [31] Zhengxiao Du, Yujie Qian, Xiao Liu, Ming Ding, Jiezhong Qiu, Zhilin Yang, and Jie Tang. 2022. GLM: General Language Model Pretraining with Autoregressive Blank Infilling. In Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), Smaranda Muresan, Preslav Nakov, and Aline Villavicencio (Eds.). Association for Computational Linguistics, Dublin, Ireland, 320–335. doi:10.18653/v1/2022.acl-long.26

- [32] Yann Dubois, Chen Xuechen Li, Rohan Taori, Tianyi Zhang, Ishaan Gulrajani, Jimmy Ba, Carlos Guestrin, Percy Liang, and Tatsunori B. Hashimoto. 2023. AlpacaFarm: A Simulation Framework for Methods that Learn from Human Feedback. In Advances in Neural Information Processing Systems 36: Annual Conference on Neural Information Processing Systems 2023, NeurIPS 2023, New Orleans, LA, USA, December 10 - 16, 2023, Alice Oh, Tristan Naumann, Amir Globerson, Kate Saenko, Moritz Hardt, and Sergey Levine (Eds.). http://papers.nips.cc/paper_files/paper/2023/ hash/5fc47800ee5b30b8777fdd30abcaaf3b-Abstract-Conference.html

- [33] Jinlan Fu, See-Kiong Ng, Zhengbao Jiang, and Pengfei Liu. 2024. GPTScore: Evaluate as You Desire. In Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers), Kevin Duh, Helena Gomez, and Steven Bethard (Eds.). Association for Computational Linguistics, Mexico City, Mexico, 6556–6576. https://aclanthology.org/2024.naacl-long.365

- [34] Isabel O Gallegos, Ryan A Rossi, Joe Barrow, Md Mehrab Tanjim, Sungchul Kim, Franck Dernoncourt, Tong Yu, Ruiyi Zhang, and Nesreen K Ahmed. 2024. Bias and fairness in large language models: A survey. Computational Linguistics


(2024), 1–79.

- [35] Isabel O Gallegos, Ryan A Rossi, Joe Barrow, Md Mehrab Tanjim, Sungchul Kim, Franck Dernoncourt, Tong Yu, Ruiyi Zhang, and Nesreen K Ahmed. 2024. Bias and fairness in large language models: A survey. Computational Linguistics 50, 3 (2024), 1097–1179.

- [36] Chang Gao, Haiyun Jiang, Deng Cai, Shuming Shi, and Wai Lam. 2023. Strategyllm: Large language models as strategy generators, executors, optimizers, and evaluators for problem solving. arXiv preprint arXiv:2311.08803 (2023).

- [37] Leo Gao, John Schulman, and Jacob Hilton. 2023. Scaling laws for reward model overoptimization. In International Conference on Machine Learning. PMLR, 10835–10866.

- [38] Mingqi Gao, Jie Ruan, Renliang Sun, Xunjian Yin, Shiping Yang, and Xiaojun Wan. 2023. Human-like summarization evaluation with chatgpt. ArXiv preprint abs/2304.02554 (2023). https://arxiv.org/abs/2304.02554

- [39] Zorik Gekhman, Jonathan Herzig, Roee Aharoni, Chen Elkind, and Idan Szpektor. 2023. TrueTeacher: Learning Factual Consistency Evaluation with Large Language Models. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, Houda Bouamor, Juan Pino, and Kalika Bali (Eds.). Association for Computational Linguistics, Singapore, 2053–2070. doi:10.18653/v1/2023.emnlp-main.127

- [40] Google. 2023. Gemini: a family of highly capable multimodal models. ArXiv preprint abs/2312.11805 (2023). https: //arxiv.org/abs/2312.11805

- [41] Neel Guha, Julian Nyarko, Daniel E. Ho, Christopher Ré, Adam Chilton, Aditya K, Alex Chohlas-Wood, Austin Peters, Brandon Waldon, Daniel N. Rockmore, Diego Zambrano, Dmitry Talisman, Enam Hoque, Faiz Surani, Frank Fagan, Galit Sarfaty, Gregory M. Dickinson, Haggai Porat, Jason Hegland, Jessica Wu, Joe Nudell, Joel Niklaus, John J. Nay, Jonathan H. Choi, Kevin Tobia, Margaret Hagan, Megan Ma, Michael A. Livermore, Nikon Rasumov-Rahe, Nils Holzenberger, Noam Kolt, Peter Henderson, Sean Rehaag, Sharad Goel, Shang Gao, Spencer Williams, Sunny Gandhi, Tom Zur, Varun Iyer, and Zehua Li. 2023. LegalBench: A Collaboratively Built Benchmark for Measuring Legal Reasoning in Large Language Models. In Advances in Neural Information Processing Systems 36: Annual Conference on Neural Information Processing Systems 2023, NeurIPS 2023, New Orleans, LA, USA, December 10 - 16, 2023, Alice Oh, Tristan Naumann, Amir Globerson, Kate Saenko, Moritz Hardt, and Sergey Levine (Eds.). http://papers.nips.cc/ paper_files/paper/2023/hash/89e44582fd28ddfea1ea4dcb0ebbf4b0-Abstract-Datasets_and_Benchmarks.html

- [42] Yufei Guo, Muzhe Guo, Juntao Su, Zhou Yang, Mengqiu Zhu, Hongfei Li, Mengyang Qiu, and Shuo Shuo Liu. 2024. Bias in large language models: Origin, evaluation, and mitigation. arXiv preprint arXiv:2411.10915 (2024).

- [43] Shibo Hao, Yi Gu, Haodi Ma, Joshua Hong, Zhen Wang, Daisy Wang, and Zhiting Hu. 2023. Reasoning with Language Model is Planning with World Model. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, Houda Bouamor, Juan Pino, and Kalika Bali (Eds.). Association for Computational Linguistics, Singapore, 8154–8173. doi:10.18653/v1/2023.emnlp-main.507

- [44] Hangfeng He, Hongming Zhang, and Dan Roth. 2024. SocREval: Large Language Models with the Socratic Method for Reference-free Reasoning Evaluation. In Findings of the Association for Computational Linguistics: NAACL 2024, Kevin Duh, Helena Gomez, and Steven Bethard (Eds.). Association for Computational Linguistics, Mexico City, Mexico, 2736–2764. https://aclanthology.org/2024.findings-naacl.175

- [45] Shijun He, Fan Yang, Jian-ping Zuo, and Ze-min Lin. 2023. ChatGPT for scientific paper writing—promises and perils. The Innovation 4, 6 (2023).

- [46] Pedram Hosseini, Jessica M. Sin, Bing Ren, Bryceton G. Thomas, Elnaz Nouri, Ali Farahanchi, and Saeed Hassanpour.

2024. A Benchmark for Long-Form Medical Question Answering. In Proceedings of EMNLP.

- [47] Xinyu Hu, Mingqi Gao, Sen Hu, Yang Zhang, Yicheng Chen, Teng Xu, and Xiaojun Wan. 2024. Are LLM-based Evaluators Confusing NLG Quality Criteria?. In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). 9530–9570. https://aclanthology.org/2024.acl-long.516

- [48] Hui Huang, Yancheng He, Hongli Zhou, Rui Zhang, Wei Liu, Weixun Wang, Wenbo Su, Bo Zheng, and Jiaheng Liu.

2025. Think-j: Learning to think for generative llm-as-a-judge. arXiv preprint arXiv:2505.14268 (2025).

- [49] Hui Huang, Yingqi Qu, Jing Liu, Muyun Yang, and Tiejun Zhao. 2024. An empirical study of llm-as-a-judge for llm evaluation: Fine-tuned judge models are task-specific classifiers. ArXiv preprint abs/2403.02839 (2024). https: //arxiv.org/abs/2403.02839

- [50] Jie Huang and Kevin Chen-Chuan Chang. 2023. Towards Reasoning in Large Language Models: A Survey. In Findings of the Association for Computational Linguistics: ACL 2023, Anna Rogers, Jordan Boyd-Graber, and Naoaki Okazaki (Eds.). Association for Computational Linguistics, Toronto, Canada, 1049–1065. doi:10.18653/v1/2023.findings-acl.67

- [51] Jen-tse Huang, Wenxuan Wang, Eric John Li, Man Ho Lam, Shujie Ren, Youliang Yuan, Wenxiang Jiao, Zhaopeng Tu, and Michael Lyu. 2023. On the humanity of conversational ai: Evaluating the psychological portrayal of llms. In The Twelfth International Conference on Learning Representations. https://openreview.net/forum?id=H3UayAQWoE

- [52] Neel Jain, Avi Schwarzschild, Yuxin Wen, Gowthami Somepalli, John Kirchenbauer, Ping-yeh Chiang, Micah Goldblum, Aniruddha Saha, Jonas Geiping, and Tom Goldstein. 2023. Baseline defenses for adversarial attacks against aligned language models. ArXiv preprint abs/2309.00614 (2023). https://arxiv.org/abs/2309.00614


- [53] Minbyul Jeong, Jiwoong Sohn, Mujeen Sung, and Jaewoo Kang. 2024. Improving medical reasoning through retrieval and self-reflection with retrieval-augmented large language models. Bioinformatics 40, Supplement_1 (2024), i119– i129.

- [54] Bowen Jiang, Yangxinyu Xie, Xiaomeng Wang, Weijie J Su, Camillo Jose Taylor, and Tanwi Mallick. 2024. Multi-modal and multi-agent systems meet rationality: A survey. In ICML 2024 Workshop on LLMs and Cognition.

- [55] Theodore T. Jiang, Li Fang, and Kai Wang. 2023. Deciphering “the language of nature”: A transformer-based language model for deleterious mutations in proteins. The Innovation 4, 5 (2023), 100487. doi:10.1016/j.xinn.2023.100487

- [56] Jaylen Jones, Lingbo Mo, Eric Fosler-Lussier, and Huan Sun. 2024. A Multi-Aspect Framework for Counter Narrative Evaluation using Large Language Models. In Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 2: Short Papers), Kevin Duh, Helena Gomez, and Steven Bethard (Eds.). Association for Computational Linguistics, Mexico City, Mexico, 147–168. https://aclanthology.org/2024.naacl-short.14

- [57] Jaehun Jung, Faeze Brahman, and Yejin Choi. 2024. Trust or Escalate: LLM Judges with Provable Guarantees for Human Agreement. arXiv preprint arXiv:2407.18370 (2024).

- [58] Immanuel Kant. 1781. Critique of Pure Reason (a/b ed.). Macmillan, London. Akademie-Ausgabe, Vol. 3, A132/B171.

- [59] Immanuel Kant. 1790. Critique of Judgment. Hackett Publishing Company, Indianapolis. Akademie-Ausgabe, Vol. 5, 5:179.

- [60] Akira Kawabata and Saku Sugawara. 2024. Rationale-Aware Answer Verification by Pairwise Self-Evaluation. In Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing. 16178–16196.

- [61] Pei Ke, Bosi Wen, Andrew Feng, Xiao Liu, Xuanyu Lei, Jiale Cheng, Shengyuan Wang, Aohan Zeng, Yuxiao Dong, Hongning Wang, et al. 2024. CritiqueLLM: Towards an Informative Critique Generation Model for Evaluation of Large Language Model Generation. In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). 13034–13054. https://aclanthology.org/2024.acl-long.704

- [62] Muhammad Uzair Khattak, Hanoona Rasheed, Muhammad Maaz, Salman Khan, and Fahad Shahbaz Khan. 2023. Maple: Multi-modal prompt learning. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. 19113–19122.

- [63] Seungone Kim, Jamin Shin, Yejin Cho, Joel Jang, Shayne Longpre, Hwaran Lee, Sangdoo Yun, Seongjin Shin, Sungdong Kim, James Thorne, et al. 2023. Prometheus: Inducing Fine-grained Evaluation Capability in Language Models. ArXiv preprint abs/2310.08491 (2023). https://arxiv.org/abs/2310.08491

- [64] Pang Wei Koh, Jialin Zhang, Jane Lee, and Percy Liang. 2024. MedHELM: Holistic Evaluation of Language Models for Medical Applications. Technical Report. Stanford Human-Centered Artificial Intelligence.

- [65] Mahi Kolla, Siddharth Salunkhe, Eshwar Chandrasekharan, and Koustuv Saha. 2024. LLM-Mod: Can Large Language Models Assist Content Moderation?. In Extended Abstracts of the CHI Conference on Human Factors in Computing Systems. 1–8.

- [66] Ryan Koo, Minhwa Lee, Vipul Raheja, Jong Inn Park, Zae Myung Kim, and Dongyeop Kang. 2023. Benchmarking cognitive biases in large language models as evaluators. ArXiv preprint abs/2309.17012 (2023). https://arxiv.org/abs/ 2309.17012

- [67] Fajri Koto. 2024. Cracking the Code: Multi-domain LLM Evaluation on Real-World Professional Exams in Indonesia. ArXiv preprint abs/2409.08564 (2024). https://arxiv.org/abs/2409.08564

- [68] Jack Krolik, Herprit Mahal, Feroz Ahmad, Gaurav Trivedi, and Bahador Saket. 2024. Towards Leveraging Large Language Models for Automated Medical Question–Answer Evaluation. arXiv preprint arXiv:2403.01892 (2024).

- [69] Abhishek Kumar, Sonia Haiduc, Partha Pratim Das, and Partha Pratim Chakrabarti. 2024. LLMs as Evaluators: A Novel Approach to Evaluate Bug Report Summarization. ArXiv preprint abs/2409.00630 (2024). https://arxiv.org/ abs/2409.00630

- [70] Abhishek Kumar, Sarfaroz Yunusov, and Ali Emami. 2024. Subtle Biases Need Subtler Measures: Dual Metrics for Evaluating Representative and Affinity Bias in Large Language Models. ArXiv preprint abs/2405.14555 (2024). https://arxiv.org/abs/2405.14555

- [71] Preethi Lahoti, Nicholas Blumm, Xiao Ma, Raghavendra Kotikalapudi, Sahitya Potluri, Qijun Tan, Hansa Srinivasan, Ben Packer, Ahmad Beirami, Alex Beutel, and Jilin Chen. 2023. Improving Diversity of Demographic Representation in Large Language Models via Collective-Critiques and Self-Voting. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, Houda Bouamor, Juan Pino, and Kalika Bali (Eds.). Association for Computational Linguistics, Singapore, 10383–10405. doi:10.18653/v1/2023.emnlp-main.643

- [72] Tian Lan, Wenwei Zhang, Chen Xu, Heyan Huang, Dahua Lin, Kai Chen, and Xian-Ling Mao. [n.d.]. CriticEval: Evaluating Large-scale Language Model as Critic. In The Thirty-eighth Annual Conference on Neural Information Processing Systems.

- [73] Dongryeol Lee, Yerin Hwang, Yongil Kim, Joonsuk Park, and Kyomin Jung. 2024. Are LLM-judges robust to expressions of uncertainty? investigating the effect of epistemic markers on LLM-based evaluation. arXiv preprint


- arXiv:2410.20774 (2024).
- [74] Yebin Lee, Imseong Park, and Myungjoo Kang. 2024. FLEUR: An Explainable Reference-Free Evaluation Metric for Image Captioning Using a Large Multimodal Model. In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics. 3732–3746. https://aclanthology.org/2024.acl-long.205

- [75] Alice Li and Luanne Sinnamon. 2023. Examining query sentiment bias effects on search results in large language models. In The Symposium on Future Directions in Information Access (FDIA) co-located with the 2023 European Summer School on Information Retrieval (ESSIR).

- [76] Dawei Li, Zhen Tan, Peijia Qian, Yifan Li, Kumar Satvik Chaudhary, Lijie Hu, and Jiayi Shen. 2024. SMoA: Improving Multi-agent Large Language Models with Sparse Mixture-of-Agents. ArXiv preprint abs/2411.03284 (2024). https: //arxiv.org/abs/2411.03284

- [77] Dawei Li, Shu Yang, Zhen Tan, Jae Young Baik, Sunkwon Yun, Joseph Lee, Aaron Chacko, Bojian Hou, Duy DuongTran, Ying Ding, et al. 2024. DALK: Dynamic Co-Augmentation of LLMs and KG to answer Alzheimer’s Disease Questions with Scientific Literature. ArXiv preprint abs/2405.04819 (2024). https://arxiv.org/abs/2405.04819

- [78] Haitao Li, You Chen, Qingyao Ai, Yueyue Wu, Ruizhe Zhang, and Yiqun Liu. 2024. LexEval: A Comprehensive Chinese Legal Benchmark for Evaluating Large Language Models. ArXiv preprint abs/2409.20288 (2024). https: //arxiv.org/abs/2409.20288

- [79] Junlong Li, Shichao Sun, Weizhe Yuan, Run-Ze Fan, Hai Zhao, and Pengfei Liu. 2023. Generative judge for evaluating alignment. ArXiv preprint abs/2310.05470 (2023). https://arxiv.org/abs/2310.05470

- [80] Lijun Li, Bowen Dong, Ruohui Wang, Xuhao Hu, Wangmeng Zuo, Dahua Lin, Yu Qiao, and Jing Shao. 2024. SALAD-Bench: A Hierarchical and Comprehensive Safety Benchmark for Large Language Models. In Findings of the Association for Computational Linguistics ACL 2024. 3923–3954. https://aclanthology.org/2024.findings-acl.235

- [81] Xuechen Li, Tianyi Zhang, Yann Dubois, Rohan Taori, Ishaan Gulrajani, Carlos Guestrin, Percy Liang, and Tatsunori B. Hashimoto. 2023. AlpacaEval: An Automatic Evaluator of Instruction-following Models. https://github.com/tatsulab/alpaca_eval.
- [82] Yifan Li, Yifan Du, Kun Zhou, Jinpeng Wang, Xin Zhao, and Ji-Rong Wen. 2023. Evaluating Object Hallucination in Large Vision-Language Models. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, Houda Bouamor, Juan Pino, and Kalika Bali (Eds.). Association for Computational Linguistics, Singapore, 292–305. doi:10.18653/v1/2023.emnlp-main.20

- [83] Tian Liang, Zhiwei He, Wenxiang Jiao, Xing Wang, Yan Wang, Rui Wang, Yujiu Yang, Zhaopeng Tu, and Shuming Shi. 2023. Encouraging divergent thinking in large language models through multi-agent debate. ArXiv preprint abs/2305.19118 (2023). https://arxiv.org/abs/2305.19118

- [84] Hunter Lightman, Vineet Kosaraju, Yuri Burda, Harrison Edwards, Bowen Baker, Teddy Lee, Jan Leike, John Schulman, Ilya Sutskever, and Karl Cobbe. 2023. Let’s verify step by step. In The Twelfth International Conference on Learning Representations.

- [85] Chin-Yew Lin. 2004. Rouge: A package for automatic evaluation of summaries. In Text summarization branches out. 74–81.

- [86] Yen-Ting Lin and Yun-Nung Chen. 2023. LLM-Eval: Unified Multi-Dimensional Automatic Evaluation for OpenDomain Conversations with Large Language Models. In Proceedings of the 5th Workshop on NLP for Conversational AI (NLP4ConvAI 2023), Yun-Nung Chen and Abhinav Rastogi (Eds.). Association for Computational Linguistics, Toronto, Canada, 47–58. doi:10.18653/v1/2023.nlp4convai-1.5

- [87] Zi Lin, Zihan Wang, Yongqi Tong, Yangkun Wang, Yuxin Guo, Yujia Wang, and Jingbo Shang. 2023. ToxicChat: Unveiling Hidden Challenges of Toxicity Detection in Real-World User-AI Conversation. In Findings of the Association for Computational Linguistics: EMNLP 2023, Houda Bouamor, Juan Pino, and Kalika Bali (Eds.). Association for Computational Linguistics, Singapore, 4694–4702. doi:10.18653/v1/2023.findings-emnlp.311

- [88] Zhan Ling, Yunhao Fang, Xuanlin Li, Zhiao Huang, Mingu Lee, Roland Memisevic, and Hao Su. 2024. Deductive verification of chain-of-thought reasoning. In Proceedings of the 37th International Conference on Neural Information Processing Systems (New Orleans, LA, USA) (NIPS ’23). Curran Associates Inc., Red Hook, NY, USA, Article 1580, 27 pages.

- [89] Chengyuan Liu, Fubang Zhao, Lizhi Qing, Yangyang Kang, Changlong Sun, Kun Kuang, and Fei Wu. 2023. GoalOriented Prompt Attack and Safety Evaluation for LLMs. arXiv e-prints (2023), arXiv–2309. https://arxiv.org/abs/ 2309.11830

- [90] Haotian Liu, Chunyuan Li, Qingyang Wu, and Yong Jae Lee. 2023. Visual Instruction Tuning. In Advances in Neural Information Processing Systems 36: Annual Conference on Neural Information Processing Systems 2023, NeurIPS 2023, New Orleans, LA, USA, December 10 - 16, 2023, Alice Oh, Tristan Naumann, Amir Globerson, Kate Saenko, Moritz Hardt, and Sergey Levine (Eds.). http://papers.nips.cc/paper_files/paper/2023/hash/ 6dcf277ea32ce3288914faf369fe6de0-Abstract-Conference.html


- [91] Hao Liu, Carmelo Sferrazza, and Pieter Abbeel. 2023. Languages are rewards: Hindsight finetuning using human feedback. ArXiv preprint abs/2302.02676 (2023). https://arxiv.org/abs/2302.02676

- [92] Yuan Liu, Yamei Chen, and Leng Han. 2023. Bioinformatics: Advancing biomedical discovery and innovation in the era of big data and artificial intelligence. The Innovation Medicine 1, 1 (2023), 100012.

- [93] Yang Liu, Dan Iter, Yichong Xu, Shuohang Wang, Ruochen Xu, and Chenguang Zhu. 2023. G-Eval: NLG Evaluation using Gpt-4 with Better Human Alignment. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, Houda Bouamor, Juan Pino, and Kalika Bali (Eds.). Association for Computational Linguistics, Singapore, 2511–2522. doi:10.18653/v1/2023.emnlp-main.153

- [94] Yuxuan Liu, Tianchi Yang, Shaohan Huang, Zihan Zhang, Haizhen Huang, Furu Wei, Weiwei Deng, Feng Sun, and Qi Zhang. 2024. HD-Eval: Aligning Large Language Model Evaluators Through Hierarchical Criteria Decomposition. In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). 7641–7660. https://aclanthology.org/2024.acl-long.413

- [95] Yinhong Liu, Han Zhou, Zhijiang Guo, Ehsan Shareghi, Ivan Vulic, Anna Korhonen, and Nigel Collier. 2024. Aligning with human judgement: The role of pairwise preference in large language model evaluators. In The 1st Conference on Language Modeling.

- [96] Adian Liusie, Potsawee Manakul, and Mark Gales. 2024. LLM Comparative Assessment: Zero-shot NLG Evaluation through Pairwise Comparisons using Large Language Models. In Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics (Volume 1: Long Papers), Yvette Graham and Matthew Purver (Eds.). Association for Computational Linguistics, St. Julian’s, Malta, 139–151. https://aclanthology.org/2024. eacl-long.8

- [97] Yuxuan Lu, Xiaoyi Ding, Lingfeng Wang, Zheng Zhu, and Junxian He. 2023. MathVista: Evaluating Mathematical Reasoning in Visual Contexts. arXiv preprint arXiv:2308.14737 (2023).

- [98] Haipeng Luo, Qingfeng Sun, Can Xu, Pu Zhao, Jianguang Lou, Chongyang Tao, Xiubo Geng, Qingwei Lin, Shifeng Chen, and Dongmei Zhang. 2023. Wizardmath: Empowering mathematical reasoning for large language models via reinforced evol-instruct. ArXiv preprint abs/2308.09583 (2023). https://arxiv.org/abs/2308.09583

- [99] Haipeng Luo, Qingfeng Sun, Can Xu, Pu Zhao, Jianguang Lou, Chongyang Tao, Xiubo Geng, Qingwei Lin, Shifeng Chen, and Dongmei Zhang. 2023. WizardMath: Empowering Mathematical Reasoning for Large Language Models via Reinforced Evol-Instruct. arXiv preprint arXiv:2308.09583 (2023).

- [100] Ming Luo, Wenyu Yang, Long Bai, Lin Zhang, Jia-Wei Huang, Yinhong Cao, Yuhua Xie, Liping Tong, Haibo Zhang, Lei Yu, et al. 2024. Artificial intelligence for life sciences: A comprehensive guide and future trends. The Innovation Life 2, 4 (2024), 100105–1.

- [101] Shengjie Ma, Chong Chen, Qi Chu, and Jiaxin Mao. 2024. Leveraging Large Language Models for Relevance Judgments in Legal Case Retrieval. arXiv:2403.18405 [cs.AI] https://arxiv.org/abs/2403.18405
- [102] Xueguang Ma, Xinyu Zhang, Ronak Pradeep, and Jimmy Lin. 2023. Zero-shot listwise document reranking with a large language model. ArXiv preprint abs/2305.02156 (2023). https://arxiv.org/abs/2305.02156

- [103] Aman Madaan, Niket Tandon, Prakhar Gupta, Skyler Hallinan, Luyu Gao, Sarah Wiegreffe, Uri Alon, Nouha Dziri, Shrimai Prabhumoye, Yiming Yang, Shashank Gupta, Bodhisattwa Prasad Majumder, Katherine Hermann, Sean Welleck, Amir Yazdanbakhsh, and Peter Clark. 2023. Self-Refine: Iterative Refinement with Self-Feedback. In Advances in Neural Information Processing Systems 36: Annual Conference on Neural Information Processing Systems 2023, NeurIPS 2023, New Orleans, LA, USA, December 10 - 16, 2023, Alice Oh, Tristan Naumann, Amir Globerson, Kate Saenko, Moritz Hardt, and Sergey Levine (Eds.). http://papers.nips.cc/paper_files/paper/2023/hash/ 91edff07232fb1b55a505a9e9f6c0ff3-Abstract-Conference.html

- [104] Sewon Min, Kalpesh Krishna, Xinxi Lyu, Mike Lewis, Wen-tau Yih, Pang Koh, Mohit Iyyer, Luke Zettlemoyer, and Hannaneh Hajishirzi. 2023. FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, Houda Bouamor, Juan Pino, and Kalika Bali (Eds.). Association for Computational Linguistics, Singapore, 12076–12100. doi:10.18653/v1/2023.emnlp-main.741

- [105] Hadi Mohammadi, Anastasia Giachanou, and Ayoub Bagheri. 2025. EvalMORAAL: Interpretable Chain-of-Thought and LLM-as-Judge Evaluation for Moral Alignment in Large Language Models. arXiv preprint arXiv:2510.05942

(2025).

- [106] Behrad Moniri, Hamed Hassani, and Edgar Dobriban. 2024. Evaluating the Performance of Large Language Models via Debates. ArXiv preprint abs/2406.11044 (2024). https://arxiv.org/abs/2406.11044

- [107] OpenAI. 2023. GPT-4 Technical Report. arXiv:2303.08774 [cs.CL]
- [108] Long Ouyang, Jeffrey Wu, Xu Jiang, Diogo Almeida, Carroll L. Wainwright, Pamela Mishkin, Chong Zhang, Sandhini Agarwal, Katarina Slama, Alex Ray, John Schulman, Jacob Hilton, Fraser Kelton, Luke Miller, Maddie Simens, Amanda Askell, Peter Welinder, Paul F. Christiano, Jan Leike, and Ryan Lowe. 2022. Training language models to follow instructions with human feedback. In Advances in Neural Information Processing Systems 35: Annual


- Conference on Neural Information Processing Systems 2022, NeurIPS 2022, New Orleans, LA, USA, November 28 - December 9, 2022, Sanmi Koyejo, S. Mohamed, A. Agarwal, Danielle Belgrave, K. Cho, and A. Oh (Eds.). http: //papers.nips.cc/paper_files/paper/2022/hash/b1efde53be364a73914f58805a001731-Abstract-Conference.html
- [109] Kishore Papineni, Salim Roukos, Todd Ward, and Wei-Jing Zhu. 2002. Bleu: a method for automatic evaluation of machine translation. In Proceedings of the 40th annual meeting of the Association for Computational Linguistics. 311–318.

- [110] Junsoo Park, Seungyeon Jwa, Meiying Ren, Daeyoung Kim, and Sanghyuk Choi. 2024. Offsetbias: Leveraging debiased data for tuning evaluators. ArXiv preprint abs/2407.06551 (2024). https://arxiv.org/abs/2407.06551

- [111] Pranav Putta, Edmund Mills, Naman Garg, Sumeet Motwani, Chelsea Finn, Divyansh Garg, and Rafael Rafailov. 2024. Agent q: Advanced reasoning and learning for autonomous ai agents. arXiv preprint arXiv:2408.07199 (2024).

- [112] Zhen Qin, Rolf Jagerman, Kai Hui, Honglei Zhuang, Junru Wu, Le Yan, Jiaming Shen, Tianqi Liu, Jialu Liu, Donald Metzler, Xuanhui Wang, and Michael Bendersky. 2024. Large Language Models are Effective Text Rankers with Pairwise Ranking Prompting. In Findings of the Association for Computational Linguistics: NAACL 2024, Kevin Duh, Helena Gomez, and Steven Bethard (Eds.). Association for Computational Linguistics, Mexico City, Mexico, 1504–1518. https://aclanthology.org/2024.findings-naacl.97

- [113] Youzhi Qu, Penghui Du, Wenxin Che, Chen Wei, Chi Zhang, Wanli Ouyang, Yatao Bian, Feiyang Xu, Bin Hu, Kai Du, et al. 2024. Promoting interactions between cognitive science and large language models. The Innovation 5, 2 (2024).

- [114] Zackary Rackauckas, Arthur Câmara, and Jakub Zavrel. 2024. Evaluating rag-fusion with ragelo: an automated elo-based framework. ArXiv preprint abs/2406.14783 (2024). https://arxiv.org/abs/2406.14783

- [115] Rafael Rafailov, Archit Sharma, Eric Mitchell, Christopher D Manning, Stefano Ermon, and Chelsea Finn. 2024. Direct preference optimization: Your language model is secretly a reward model. Advances in Neural Information Processing Systems 36 (2024).

- [116] Vyas Raina, Adian Liusie, and Mark Gales. 2024. Is LLM-as-a-Judge Robust? Investigating Universal Adversarial Attacks on Zero-shot LLM Assessment. ArXiv preprint abs/2402.14016 (2024). https://arxiv.org/abs/2402.14016

- [117] Ravi Raju, Swayambhoo Jain, Bo Li, Jonathan Li, and Urmish Thakkar. 2024. Constructing domain-specific evaluation sets for llm-as-a-judge. ArXiv preprint abs/2408.08808 (2024). https://arxiv.org/abs/2408.08808

- [118] Rajkumar Ramamurthy, Prithviraj Ammanabrolu, Kianté Brantley, Jack Hessel, Rafet Sifa, Christian Bauckhage, Hannaneh Hajishirzi, and Yejin Choi. 2023. Is Reinforcement Learning (Not) for Natural Language Processing: Benchmarks, Baselines, and Building Blocks for Natural Language Policy Optimization. In The Eleventh International Conference on Learning Representations, ICLR 2023, Kigali, Rwanda, May 1-5, 2023. OpenReview.net. https:// openreview.net/pdf?id=8aHzds2uUyB

- [119] Cheol Ryu, Seolhwa Lee, Subeen Pang, Chanyeol Choi, Hojun Choi, Myeonggee Min, and Jy-Yong Sohn. 2023. Retrieval-based Evaluation for LLMs: A Case Study in Korean Legal QA. In Proceedings of the Natural Legal Language Processing Workshop 2023, Daniel Preot,iuc-Pietro, Catalina Goanta, Ilias Chalkidis, Leslie Barrett, Gerasimos Spanakis, and Nikolaos Aletras (Eds.). Association for Computational Linguistics, Singapore, 132–137. doi:10.18653/v1/2023.nllp-1.13

- [120] Swarnadeep Saha, Omer Levy, Asli Celikyilmaz, Mohit Bansal, Jason Weston, and Xian Li. 2024. Branch-SolveMerge Improves Large Language Model Evaluation and Generation. In Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers), Kevin Duh, Helena Gomez, and Steven Bethard (Eds.). Association for Computational Linguistics, Mexico City, Mexico, 8352–8370. https://aclanthology.org/2024.naacl-long.462

- [121] Keita Saito, Akifumi Wachi, Koki Wataoka, and Youhei Akimoto. 2023. Verbosity bias in preference labeling by large language models. ArXiv preprint abs/2310.10076 (2023). https://arxiv.org/abs/2310.10076

- [122] Natalie Schluter. 2017. The limits of automatic summarisation according to ROUGE. In Proceedings of the 15th Conference of the European Chapter of the Association for Computational Linguistics: Volume 2, Short Papers, Mirella Lapata, Phil Blunsom, and Alexander Koller (Eds.). Association for Computational Linguistics, Valencia, Spain, 41–45. https://aclanthology.org/E17-2007

- [123] John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, and Oleg Klimov. 2017. Proximal policy optimization algorithms. ArXiv preprint abs/1707.06347 (2017). https://arxiv.org/abs/1707.06347

- [124] Amrith Setlur, Chirag Nagpal, Adam Fisch, Xinyang Geng, Jacob Eisenstein, Rishabh Agarwal, Alekh Agarwal, Jonathan Berant, and Aviral Kumar. 2024. Rewarding Progress: Scaling Automated Process Verifiers for LLM Reasoning. arXiv preprint arXiv:2410.08146 (2024).

- [125] Hao Sha, Yao Mu, Yuxuan Jiang, Li Chen, Chenfeng Xu, Ping Luo, Shengbo Eben Li, Masayoshi Tomizuka, Wei Zhan, and Mingyu Ding. 2023. Languagempc: Large language models as decision makers for autonomous driving. ArXiv preprint abs/2310.03026 (2023). https://arxiv.org/abs/2310.03026

- [126] Lin Shi, Weicheng Ma, and Soroush Vosoughi. 2024. Judging the Judges: A Systematic Investigation of Position Bias in Pairwise Comparative Assessments by LLMs. ArXiv preprint abs/2406.07791 (2024). https://arxiv.org/abs/2406.07791


- [127] Yi Shi. 2024. Drug development in the AI era: AlphaFold 3 is coming! The Innovation 5, 5 (2024).

- [128] Noah Shinn, Federico Cassano, Ashwin Gopinath, Karthik Narasimhan, and Shunyu Yao. 2023. Reflexion: language agents with verbal reinforcement learning. In Advances in Neural Information Processing Systems 36: Annual Conference on Neural Information Processing Systems 2023, NeurIPS 2023, New Orleans, LA, USA, December 10

- 16, 2023, Alice Oh, Tristan Naumann, Amir Globerson, Kate Saenko, Moritz Hardt, and Sergey Levine (Eds.). http://papers.nips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html

- [129] Charlie Snell, Jaehoon Lee, Kelvin Xu, and Aviral Kumar. 2024. Scaling llm test-time compute optimally can be more effective than scaling model parameters. arXiv preprint arXiv:2408.03314 (2024).

- [130] Guijin Son, Hyunwoo Ko, Hoyoung Lee, Yewon Kim, and Seunghyeok Hong. 2024. Llm-as-a-judge & reward model: What they can and cannot do. ArXiv preprint abs/2409.11239 (2024). https://arxiv.org/abs/2409.11239

- [131] Feifan Song, Bowen Yu, Minghao Li, Haiyang Yu, Fei Huang, Yongbin Li, and Houfeng Wang. 2024. Preference Ranking Optimization for Human Alignment. In Thirty-Eighth AAAI Conference on Artificial Intelligence, AAAI 2024, Thirty-Sixth Conference on Innovative Applications of Artificial Intelligence, IAAI 2024, Fourteenth Symposium on Educational Advances in Artificial Intelligence, EAAI 2014, February 20-27, 2024, Vancouver, Canada, Michael J. Wooldridge, Jennifer G. Dy, and Sriraam Natarajan (Eds.). AAAI Press, 18990–18998. doi:10.1609/AAAI.V38I17.29865

- [132] Yishen Song, Qianta Zhu, Huaibo Wang, and Qinhua Zheng. 2024. Automated Essay Scoring and Revising Based on Open-Source Large Language Models. IEEE Transactions on Learning Technologies (2024).

- [133] Andrea Sottana, Bin Liang, Kai Zou, and Zheng Yuan. 2023. Evaluation Metrics in the Era of GPT-4: Reliably Evaluating Large Language Models on Sequence to Sequence Tasks. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, Houda Bouamor, Juan Pino, and Kalika Bali (Eds.). Association for Computational Linguistics, Singapore, 8776–8788. doi:10.18653/v1/2023.emnlp-main.543

- [134] Aarohi Srivastava, Abhinav Rastogi, Abhishek Rao, Abu Awal Md Shoeb, Abubakar Abid, Adam Fisch, Adam R Brown, Adam Santoro, Aditya Gupta, Adrià Garriga-Alonso, et al. 2022. Beyond the imitation game: Quantifying and extrapolating the capabilities of language models. ArXiv preprint abs/2206.04615 (2022). https://arxiv.org/abs/2206. 04615

- [135] Jiashuo Sun, Chengjin Xu, Lumingyuan Tang, Saizhuo Wang, Chen Lin, Yeyun Gong, Heung-Yeung Shum, and Jian Guo. 2023. Think-on-graph: Deep and responsible reasoning of large language model with knowledge graph. ArXiv preprint abs/2307.07697 (2023). https://arxiv.org/abs/2307.07697

- [136] Zhiqing Sun, Sheng Shen, Shengcao Cao, Haotian Liu, Chunyuan Li, Yikang Shen, Chuang Gan, Liang-Yan Gui, Yu-Xiong Wang, Yiming Yang, et al. 2023. Aligning large multimodal models with factually augmented rlhf. arXiv preprint arXiv:2309.14525 (2023). https://arxiv.org/abs/2309.14525

- [137] Zhiqing Sun, Yikang Shen, Qinhong Zhou, Hongxin Zhang, Zhenfang Chen, David D. Cox, Yiming Yang, and Chuang Gan. 2023. Principle-Driven Self-Alignment of Language Models from Scratch with Minimal Human Supervision. In Advances in Neural Information Processing Systems 36: Annual Conference on Neural Information Processing Systems 2023, NeurIPS 2023, New Orleans, LA, USA, December 10 - 16, 2023, Alice Oh, Tristan Naumann, Amir Globerson, Kate Saenko, Moritz Hardt, and Sergey Levine (Eds.). http://papers.nips.cc/paper_files/paper/2023/hash/ 0764db1151b936aca59249e2c1386101-Abstract-Conference.html

- [138] Hexiang Tan, Fei Sun, Wanli Yang, Yuanzhuo Wang, Qi Cao, and Xueqi Cheng. 2024. Blinded by Generated Contexts: How Language Models Merge Generated and Retrieved Contexts When Knowledge Conflicts?. In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), Lun-Wei Ku, Andre Martins, and Vivek Srikumar (Eds.). Association for Computational Linguistics, Bangkok, Thailand. doi:10.18653/v1/2024.acl-long.337

- [139] Sijun Tan, Siyuan Zhuang, Kyle Montgomery, William Y Tang, Alejandro Cuadron, Chenguang Wang, Raluca Ada Popa, and Ion Stoica. 2024. Judgebench: A benchmark for evaluating llm-based judges. arXiv preprint arXiv:2410.12784

(2024).

- [140] Qiaoyu Tang, Jiawei Chen, Bowen Yu, Yaojie Lu, Cheng Fu, Haiyang Yu, Hongyu Lin, Fei Huang, Ben He, Xianpei Han, et al. 2024. Self-Retrieval: Building an Information Retrieval System with One Large Language Model. ArXiv preprint abs/2403.00801 (2024). https://arxiv.org/abs/2403.00801

- [141] Raphael Tang, Crystina Zhang, Xueguang Ma, Jimmy Lin, and Ferhan Ture. 2024. Found in the Middle: Permutation Self-Consistency Improves Listwise Ranking in Large Language Models. In Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers), Kevin Duh, Helena Gomez, and Steven Bethard (Eds.). Association for Computational Linguistics, Mexico City, Mexico, 2327–2340. https://aclanthology.org/2024.naacl-long.129

- [142] Yi-Da Tang, Er-Dan Dong, and Wen Gao. 2024. LLMs in medicine: The need for advanced evaluation systems for disruptive technologies. The Innovation 5, 3 (2024).

- [143] Rohan Taori, Ishaan Gulrajani, Tianyi Zhang, Yann Dubois, Xuechen Li, Carlos Guestrin, Percy Liang, and Tatsunori B. Hashimoto. 2023. Stanford Alpaca: An Instruction-following LLaMA model. https://github.com/tatsu-lab/stanford_


- alpaca.
- [144] Aman Singh Thakur, Kartik Choudhary, Venkat Srinik Ramayapally, Sankaran Vaidyanathan, and Dieuwke Hupkes.

2024. Judging the Judges: Evaluating Alignment and Vulnerabilities in LLMs-as-Judges. ArXiv preprint abs/2406.12624

(2024). https://arxiv.org/abs/2406.12624

- [145] Yufei Tian, Abhilasha Ravichander, Lianhui Qin, Ronan Le Bras, Raja Marjieh, Nanyun Peng, Yejin Choi, Thomas Griffiths, and Faeze Brahman. 2024. MacGyver: Are Large Language Models Creative Problem Solvers?. In Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers), Kevin Duh, Helena Gomez, and Steven Bethard (Eds.). Association for Computational Linguistics, Mexico City, Mexico, 5303–5324. https://aclanthology.org/2024.naacl-long.297

- [146] Yuxuan Tong, Xiwen Zhang, Rui Wang, Ruidong Wu, and Junxian He. 2024. DART-Math: Difficulty-Aware Rejection Tuning for Mathematical Problem-Solving. In NeurIPS.

- [147] Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, et al. 2023. Llama: Open and efficient foundation language models. ArXiv preprint abs/2302.13971 (2023). https://arxiv.org/abs/2302.13971

- [148] Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, et al. 2023. Vicuna: Open and efficient foundation language models. ArXiv preprint abs/2302.13971 (2023). https://arxiv.org/abs/2302.13971

- [149] Hugo Touvron, Louis Martin, Kevin Stone, Peter Albert, Amjad Almahairi, Yasmine Babaei, Nikolay Bashlykov, Soumya Batra, Prajjwal Bhargava, Shruti Bhosale, et al. 2023. Llama 2: Open foundation and fine-tuned chat models. ArXiv preprint abs/2307.09288 (2023). https://arxiv.org/abs/2307.09288

- [150] Luong Trung, Xinbo Zhang, Zhanming Jie, Peng Sun, Xiaoran Jin, and Hang Li. 2024. Reft: Reasoning with reinforced fine-tuning. In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). 7601–7614.

- [151] Daan Van Veen, Akshay Kolluri, and et al. 2024. Current and Future State of Evaluation of Large Language Models for Clinical Summarization. Nature Medicine (2024).

- [152] Binjie Wang, Steffi Chern, Ethan Chern, and Pengfei Liu. 2024. Halu-J: Critique-Based Hallucination Judge. ArXiv preprint abs/2407.12943 (2024). https://arxiv.org/abs/2407.12943

- [153] Chengrui Wang, Qingqing Long, Xiao Meng, Xunxin Cai, Chengjun Wu, Zhen Meng, Xuezhi Wang, and Yuanchun Zhou. 2024. BioRAG: A RAG-LLM Framework for Biological Question Reasoning. ArXiv preprint abs/2408.01107

(2024). https://arxiv.org/abs/2408.01107

- [154] Junyang Wang, Yiyang Zhou, Guohai Xu, Pengcheng Shi, Chenlin Zhao, Haiyang Xu, Qinghao Ye, Ming Yan, Ji Zhang, Jihua Zhu, et al. 2023. Evaluation and analysis of hallucination in large vision-language models. ArXiv preprint abs/2308.15126 (2023). https://arxiv.org/abs/2308.15126

- [155] Peiyi Wang, Lei Li, Liang Chen, Zefan Cai, Dawei Zhu, Binghuai Lin, Yunbo Cao, Lingpeng Kong, Qi Liu, Tianyu Liu, and Zhifang Sui. 2024. Large Language Models are not Fair Evaluators. In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). 9440–9450.

- [156] Peiyi Wang, Lei Li, Zhihong Shao, Rui Xu, Damai Dai, Yifei Li, Deli Chen, Yu Wu, and Zhifang Sui. 2023. MathShepherd: Verify and Reinforce LLMs Step-by-Step without Human Annotations. arXiv preprint arXiv:2312.08935

(2023).

- [157] Saizhuo Wang, Hang Yuan, Lionel M. Ni, and Jian Guo. 2024. QuantAgent: Seeking Holy Grail in Trading by Self-Improving Large Language Model. doi:10.48550/arXiv.2402.03755 arXiv:2402.03755 [cs].
- [158] Tianlu Wang, Ilia Kulikov, Olga Golovneva, Ping Yu, Weizhe Yuan, Jane Dwivedi-Yu, Richard Yuanzhe Pang, Maryam Fazel-Zarandi, Jason Weston, and Xian Li. 2024. Self-taught evaluators. arXiv preprint arXiv:2408.02666 (2024). https://arxiv.org/abs/2408.02666

- [159] Tianlu Wang, Ping Yu, Xiaoqing Ellen Tan, Sean O’Brien, Ramakanth Pasunuru, Jane Dwivedi-Yu, Olga Golovneva, Luke Zettlemoyer, Maryam Fazel-Zarandi, and Asli Celikyilmaz. 2023. Shepherd: A Critic for Language Model Generation. ArXiv preprint abs/2308.04592 (2023). https://arxiv.org/abs/2308.04592

- [160] Yizhong Wang, Yeganeh Kordi, Swaroop Mishra, Alisa Liu, Noah A. Smith, Daniel Khashabi, and Hannaneh Hajishirzi.

2023. Self-Instruct: Aligning Language Models with Self-Generated Instructions. In Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), Anna Rogers, Jordan BoydGraber, and Naoaki Okazaki (Eds.). Association for Computational Linguistics, Toronto, Canada, 13484–13508. doi:10.18653/v1/2023.acl-long.754

- [161] Yidong Wang, Yunze Song, Tingyuan Zhu, Xuanwang Zhang, Zhuohao Yu, Hao Chen, Chiyu Song, Qiufeng Wang, Cunxiang Wang, Zhen Wu, et al. 2025. TrustJudge: Inconsistencies of LLM-as-a-Judge and How to Alleviate Them. arXiv preprint arXiv:2509.21117 (2025).

- [162] Yidong Wang, Zhuohao Yu, Zhengran Zeng, Linyi Yang, Cunxiang Wang, Hao Chen, Chaoya Jiang, Rui Xie, Jindong Wang, Xing Xie, et al. 2023. PandaLM: An Automatic Evaluation Benchmark for LLM Instruction Tuning Optimization.


- ArXiv preprint abs/2306.05087 (2023). https://arxiv.org/abs/2306.05087
- [163] Yicheng Wang, Jiayi Yuan, Yu-Neng Chuang, Zhuoer Wang, Yingchi Liu, Mark Cusick, Param Kulkarni, Zhengping Ji, Yasser Ibrahim, and Xia Hu. 2024. DHP Benchmark: Are LLMs Good NLG Evaluators? ArXiv preprint abs/2408.13704

(2024). https://arxiv.org/abs/2408.13704

- [164] Yilei Wang, Jiabao Zhao, Deniz S Ones, Liang He, and Xin Xu. 2025. Evaluating the ability of large language models to emulate personality. Scientific reports 15, 1 (2025), 519.

- [165] Zilong Wang, Zifeng Wang, Long Le, Huaixiu Steven Zheng, Swaroop Mishra, Vincent Perot, Yuwei Zhang, Anush Mattapalli, Ankur Taly, Jingbo Shang, et al. 2024. Speculative rag: Enhancing retrieval augmented generation through drafting. ArXiv preprint abs/2407.08223 (2024). https://arxiv.org/abs/2407.08223

- [166] Zhenyu Wang, Jin Zhang, Pei Hua, Yuanzheng Cui, Chunhui Lu, Xiaojun Wang, Qiuwen Chen, and Peter Krebs. 2023. Filling in missing pieces in the co-development of artificial intelligence and environmental science. The Innovation Geoscience 1, 1 (2023), 100007–14.

- [167] Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei Xia, Ed H. Chi, Quoc V. Le, and Denny Zhou. 2022. Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. In Advances in Neural Information Processing Systems 35: Annual Conference on Neural Information Processing Systems 2022, NeurIPS 2022, New Orleans, LA, USA, November 28 - December 9, 2022, Sanmi Koyejo, S. Mohamed, A. Agarwal, Danielle Belgrave, K. Cho, and A. Oh (Eds.). http://papers.nips.cc/paper_files/paper/2022/hash/9d5609613524ecf4f15af0f7b31abca4Abstract-Conference.html

- [168] Yixuan Weng, Minjun Zhu, Fei Xia, Bin Li, Shizhu He, Shengping Liu, Bin Sun, Kang Liu, and Jun Zhao. 2023. Large Language Models are Better Reasoners with Self-Verification. In Findings of the Association for Computational Linguistics:EMNLP2023, Houda Bouamor, Juan Pino, and Kalika Bali (Eds.). Association for Computational Linguistics, Singapore, 2550–2575. doi:10.18653/v1/2023.findings-emnlp.167

- [169] Ning Wu, Ming Gong, Linjun Shou, Shining Liang, and Daxin Jiang. 2023. Large language models are diverse role-players for summarization evaluation. In CCF International Conference on Natural Language Processing and Chinese Computing. Springer, 695–707.

- [170] Yuhang Wu, Wenmeng Yu, Yean Cheng, Yan Wang, Xiaohan Zhang, Jiazheng Xu, Ming Ding, and Yuxiao Dong.

2024. AlignMMBench: Evaluating Chinese Multimodal Alignment in Large Vision-Language Models. ArXiv preprint abs/2406.09295 (2024). https://arxiv.org/abs/2406.09295

- [171] Zheng Xia, Li Qian, and Hao Wang. 2024. Beyond Accuracy: Evaluating Logical Coherence of Mathematical Reasoning in Large Language Models. arXiv preprint arXiv:2405.11234 (2024).

- [172] Tinghao Xie, Xiangyu Qi, Yi Zeng, Yangsibo Huang, Udari Madhushani Sehwag, Kaixuan Huang, Luxi He, Boyi Wei, Dacheng Li, Ying Sheng, et al. 2024. Sorry-bench: Systematically evaluating large language model safety refusal behaviors. ArXiv preprint abs/2406.14598 (2024). https://arxiv.org/abs/2406.14598

- [173] Yiqing Xie, Wenxuan Zhou, Pradyot Prakash, Di Jin, Yuning Mao, Quintin Fettes, Arya Talebzadeh, Sinong Wang, Han Fang, Carolyn Rose, et al. 2024. Improving Model Factuality with Fine-grained Critique-based Evaluator. arXiv preprint arXiv:2410.18359 (2024).

- [174] Tianyi Xiong, Xiyao Wang, Dong Guo, Qinghao Ye, Haoqi Fan, Quanquan Gu, Heng Huang, and Chunyuan Li.

2024. LLaVA-Critic: Learning to Evaluate Multimodal Models. ArXiv preprint abs/2410.02712 (2024). https: //arxiv.org/abs/2410.02712

- [175] Ruoxi Xu, Hongyu Lin, Xianpei Han, Le Sun, and Yingfei Sun. 2024. Academically intelligent LLMs are not necessarily socially intelligent. ArXiv preprint abs/2403.06591 (2024). https://arxiv.org/abs/2403.06591

- [176] Wenda Xu, Danqing Wang, Liangming Pan, Zhenqiao Song, Markus Freitag, William Wang, and Lei Li. 2023. INSTRUCTSCORE: Towards Explainable Text Generation Evaluation with Automatic Feedback. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, Houda Bouamor, Juan Pino, and Kalika Bali (Eds.). Association for Computational Linguistics, Singapore, 5967–5994. doi:10.18653/v1/2023.emnlp-main.365

- [177] Yongjun Xu, Fei Wang, Zhulin An, Qi Wang, and Zhao Zhang. 2023. Artificial intelligence for science—bridging data to wisdom. The Innovation 4, 6 (2023).

- [178] Yongjun Xu, Fei Wang, and Tangtang Zhang. 2024. Artificial intelligence is restructuring a new world. The Innovation 5, 6 (2024).

- [179] An Yang, Beichen Zhang, Binyuan Hui, Bofei Gao, Bowen Yu, Chengpeng Li, Dayiheng Liu, Jianhong Tu, Jingren Zhou, Junyang Lin, Keming Lu, Mingfeng Xue, Runji Lin, Tianyu Liu, Xingzhang Ren, and Zhenru Zhang. 2024. Qwen2.5Math Technical Report: Toward Mathematical Expert Model via Self-Improvement. arXiv preprint arXiv:2409.12122

(2024).

- [180] Hui Yang, Sifu Yue, and Yunzhong He. 2023. Auto-gpt for online decision making: Benchmarks and additional opinions. ArXiv preprint abs/2306.02224 (2023). https://arxiv.org/abs/2306.02224

- [181] Yuzhe Yang, Yifei Zhang, Yan Hu, Yilin Guo, Ruoli Gan, Yueru He, Mingcong Lei, Xiao Zhang, Haining Wang, Qianqian Xie, et al. 2024. UCFE: A User-Centric Financial Expertise Benchmark for Large Language Models. ArXiv preprint


- abs/2410.14059 (2024). https://arxiv.org/abs/2410.14059
- [182] Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Tom Griffiths, Yuan Cao, and Karthik Narasimhan. 2023. Tree of Thoughts: Deliberate Problem Solving with Large Language Models. In Advances in Neural Information Processing Systems 36: Annual Conference on Neural Information Processing Systems 2023, NeurIPS 2023, New Orleans, LA, USA, December 10 - 16, 2023, Alice Oh, Tristan Naumann, Amir Globerson, Kate Saenko, Moritz Hardt, and Sergey Levine (Eds.). http://papers.nips.cc/paper_files/paper/2023/hash/271db9922b8d1f4dd7aaef84ed5ac703-AbstractConference.html

- [183] Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik R. Narasimhan, and Yuan Cao. 2023. ReAct: Synergizing Reasoning and Acting in Language Models. In The Eleventh International Conference on Learning Representations, ICLR 2023, Kigali, Rwanda, May 1-5, 2023. OpenReview.net. https://openreview.net/pdf?id=WE_ vluYUL-X

- [184] Zonghai Yao, Aditya Parashar, Huixue Zhou, Won Seok Jang, Feiyun Ouyang, Zhichao Yang, and Hong Yu. 2024. MCQG-SRefine: Multiple Choice Question Generation and Evaluation with Iterative Self-Critique, Correction, and Comparison Feedback. arXiv preprint arXiv:2410.13191 (2024).

- [185] Jiayi Ye, Yanbo Wang, Yue Huang, Dongping Chen, Qihui Zhang, Nuno Moniz, Tian Gao, Werner Geyer, Chao Huang, Pin-Yu Chen, et al. 2024. Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge. ArXiv preprint abs/2410.02736

(2024). https://arxiv.org/abs/2410.02736

- [186] Seonghyeon Ye, Yongrae Jo, Doyoung Kim, Sungdong Kim, Hyeonbin Hwang, and Minjoon Seo. 2023. SelFee: Iterative Self-Revising LLM Empowered by Self-Feedback Generation. Blog post. https://kaistai.github.io/SelFee/
- [187] Sungwook Yoon. 2023. Design and Implementation of an LLM system to Improve Response Time for SMEs Technology Credit Evaluation. International Journal of Advanced Smart Convergence 12, 3 (2023), 51–60.

- [188] Jiachen Yu, Shaoning Sun, Xiaohui Hu, Jiaxu Yan, Kaidong Yu, and Xuelong Li. 2025. Improve llm-as-a-judge ability as a general ability. arXiv preprint arXiv:2502.11689 (2025).

- [189] Qingchen Yu, Zifan Zheng, Shichao Song, Zhiyu Li, Feiyu Xiong, Bo Tang, and Ding Chen. 2024. xFinder: Robust and Pinpoint Answer Extraction for Large Language Models. arXiv preprint arXiv:2405.11874 (2024).

- [190] Yangyang Yu, Zhiyuan Yao, Haohang Li, Zhiyang Deng, Yupeng Cao, Zhi Chen, Jordan W Suchow, Rong Liu, Zhenyu Cui, Denghui Zhang, et al. 2024. FinCon: A Synthesized LLM Multi-Agent System with Conceptual Verbal Reinforcement for Enhanced Financial Decision Making. ArXiv preprint abs/2407.06567 (2024). https://arxiv.org/ abs/2407.06567

- [191] J Yuan, P Bao, Z Chen, M Yuan, J Zhao, J Pan, Y Xie, Y Cao, Y Wang, Z Wang, et al. 2023. Advanced prompting as a catalyst: Empowering large language models in the management of gastrointestinal cancers. The Innovation 521

(2023).

- [192] Weizhe Yuan, Richard Yuanzhe Pang, Kyunghyun Cho, Sainbayar Sukhbaatar, Jing Xu, and Jason Weston. 2024. Self-rewarding language models. arXiv preprint arXiv:2401.10020 (2024).

- [193] Zheng Yuan, Hongyi Yuan, Chuanqi Tan, Wei Wang, Songfang Huang, and Fei Huang. 2023. Rrhf: Rank responses to align language models with human feedback without tears. ArXiv preprint abs/2304.05302 (2023). https://arxiv.org/ abs/2304.05302

- [194] Kamer Ali Yuksel and Hassan Sawaf. 2024. A Multi-AI Agent System for Autonomous Optimization of Agentic AI Solutions via Iterative Refinement and LLM-Driven Feedback Loops. arXiv preprint arXiv:2412.17149 (2024).

- [195] Zhiyuan Zeng, Jiatong Yu, Tianyu Gao, Yu Meng, Tanya Goyal, and Danqi Chen. 2023. Evaluating Large Language Models at Evaluating Instruction Following. https://arxiv.org/abs/2310.07641
- [196] Bang Zhang, Ruotian Ma, Qingxuan Jiang, Peisong Wang, Jiaqi Chen, Zheng Xie, Xingyu Chen, Yue Wang, Fanghua Ye, Jian Li, et al. 2025. Sentient Agent as a Judge: Evaluating Higher-Order Social Cognition in Large Language Models. arXiv preprint arXiv:2505.02847 (2025).

- [197] Beichen Zhang, Kun Zhou, Xilin Wei, Xin Zhao, Jing Sha, Shijin Wang, and Ji-Rong Wen. 2024. Evaluating and improving tool-augmented computation-intensive math reasoning. Advances in Neural Information Processing Systems 36 (2024).

- [198] Hengyuan Zhang, Yanru Wu, Dawei Li, Sak Yang, Rui Zhao, Yong Jiang, and Fei Tan. 2024. Balancing speciality and versatility: a coarse to fine framework for supervised fine-tuning large language model. arXiv preprint arXiv:2404.10306 (2024).

- [199] Hengran Zhang, Ruqing Zhang, Jiafeng Guo, Maarten de Rijke, Yixing Fan, and Xueqi Cheng. 2024. Are Large Language Models Good at Utility Judgments?. In Proceedings of the 47th International ACM SIGIR Conference on Research and Development in Information Retrieval. 1941–1951.

- [200] Jiaxing Zhang, Ruyi Gan, Junjie Wang, Yuxiang Zhang, Lin Zhang, Ping Yang, Xinyu Gao, Ziwei Wu, Xiaoqun Dong, Junqing He, et al. 2022. Fengshenbang 1.0: Being the foundation of chinese cognitive intelligence. ArXiv preprint abs/2209.02970 (2022). https://arxiv.org/abs/2209.02970


- [201] Liang Xu Xuanwei Zhang and Kangkang Zhao. 2022. Chatyuan: A large language model for dialogue in chinese and english.
- [202] Mi Zhang, Xudong Pan, and Min Yang. 2023. Jade: A linguistics-based safety evaluation platform for llm. ArXiv preprint abs/2311.00286 (2023). https://arxiv.org/abs/2311.00286

- [203] Qiyuan Zhang, Yufei Wang, Yuxin Jiang, Liangyou Li, Chuhan Wu, Yasheng Wang, Xin Jiang, Lifeng Shang, Ruiming Tang, Fuyuan Lyu, et al. 2025. Crowd comparative reasoning: Unlocking comprehensive evaluations for llm-as-a-judge. arXiv preprint arXiv:2502.12501 (2025).

- [204] Ruizhe Zhang, Haitao Li, Yueyue Wu, Qingyao Ai, Yiqun Liu, Min Zhang, and Shaoping Ma. 2024. Evaluation Ethics of LLMs in Legal Domain. ArXiv preprint abs/2403.11152 (2024). https://arxiv.org/abs/2403.11152

- [205] Tianjun Zhang, Fangchen Liu, Justin Wong, Pieter Abbeel, and Joseph E. Gonzalez. 2023. The Wisdom of Hindsight Makes Language Models Better Instruction Followers. In International Conference on Machine Learning, ICML 2023, 23-29 July 2023, Honolulu, Hawaii, USA (Proceedings of Machine Learning Research, Vol. 202), Andreas Krause, Emma Brunskill, Kyunghyun Cho, Barbara Engelhardt, Sivan Sabato, and Jonathan Scarlett (Eds.). PMLR, 41414–41428. https://proceedings.mlr.press/v202/zhang23ab.html

- [206] Wenjing Zhang, Yongfeng Lu, Chenyi Su, Yibo Wang, Yong-Fei Wang, Bo Zhang, Cheng Jiang, Keying Guo, and Chuan Xu. 2023. Confinement-guided ultrasensitive optical assay with artificial intelligence for disease diagnostics. The Innovation Medicine 1, 2 (2023), 100023–1.

- [207] Xinghua Zhang, Bowen Yu, Haiyang Yu, Yangyu Lv, Tingwen Liu, Fei Huang, Hongbo Xu, and Yongbin Li. 2023. Wider and deeper llm networks are fairer llm evaluators. ArXiv preprint abs/2308.01862 (2023). https://arxiv.org/ abs/2308.01862

- [208] Zhuosheng Zhang, Aston Zhang, Mu Li, and Alex Smola. 2023. Automatic Chain of Thought Prompting in Large Language Models. In The Eleventh International Conference on Learning Representations, ICLR 2023, Kigali, Rwanda, May 1-5, 2023. OpenReview.net. https://openreview.net/pdf?id=5NTt8GFjUHkr

- [209] Huaqin Zhao, Zhengliang Liu, Zihao Wu, Yiwei Li, Tianze Yang, Peng Shu, Shaochen Xu, Haixing Dai, Lin Zhao, Gengchen Mai, et al. 2024. Revolutionizing finance with llms: An overview of applications and insights. ArXiv preprint abs/2401.11641 (2024). https://arxiv.org/abs/2401.11641

- [210] Tianjie Zhao, Sheng Wang, Chaojun Ouyang, Min Chen, Chenying Liu, Jin Zhang, Long Yu, Fei Wang, Yong Xie, Jun Li, et al. [n. d.]. Artificial intelligence for geoscience: Progress, challenges and perspectives. The Innovation ([n. d.]).

- [211] Yulai Zhao, Haolin Liu, Dian Yu, SY Kung, Haitao Mi, and Dong Yu. 2025. One Token to Fool LLM-as-a-Judge. arXiv preprint arXiv:2507.08794 (2025).

- [212] Yuwei Zhao, Ziyang Luo, Yuchen Tian, Hongzhan Lin, Weixiang Yan, Annan Li, and Jing Ma. 2024. CodeJudge-Eval: Can Large Language Models be Good Judges in Code Understanding? arXiv preprint arXiv:2408.10718 (2024).

- [213] Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric P. Xing, Hao Zhang, Joseph E. Gonzalez, and Ion Stoica. 2023. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. In Advances in Neural Information Processing Systems 36: Annual Conference on Neural Information Processing Systems 2023, NeurIPS 2023, New Orleans, LA, USA, December 10 - 16, 2023, Alice Oh, Tristan Naumann, Amir Globerson, Kate Saenko, Moritz Hardt, and Sergey Levine (Eds.). http://papers.nips.cc/ paper_files/paper/2023/hash/91f18a1287b398d378ef22505bf41832-Abstract-Datasets_and_Benchmarks.html

- [214] Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Tianle Li, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zhuohan Li, Zi Lin, Eric Xing, et al. 2023. Lmsys-chat-1m: A large-scale real-world llm conversation dataset. ArXiv preprint abs/2309.11998 (2023). https://arxiv.org/abs/2309.11998

- [215] Lianmin Zheng, Liangsheng Yin, Zhiqiang Xie, Chuyue Sun, Jeff Huang, Cody Hao Yu, Shiyi Cao, Christos Kozyrakis, Ion Stoica, Joseph E. Gonzalez, Clark Barrett, and Ying Sheng. 2024. SGLang: Efficient Execution of Structured Language Model Programs. doi:10.48550/arXiv.2312.07104 arXiv:2312.07104 [cs].
- [216] Xiaosen Zheng, Tianyu Pang, Chao Du, Qian Liu, Jing Jiang, and Min Lin. 2024. Cheating automatic llm benchmarks: Null models achieve high win rates. ArXiv preprint abs/2410.07137 (2024). https://arxiv.org/abs/2410.07137

- [217] Jun Zhong, Jianxin Shi, and Laufey T Amundadottir. 2023. Artificial intelligence and improved early detection for pancreatic cancer. The Innovation 4, 4 (2023).

- [218] Chunting Zhou, Pengfei Liu, Puxin Xu, Srinivasan Iyer, Jiao Sun, Yuning Mao, Xuezhe Ma, Avia Efrat, Ping Yu, Lili Yu, Susan Zhang, Gargi Ghosh, Mike Lewis, Luke Zettlemoyer, and Omer Levy. 2023. LIMA: Less Is More for Alignment. In Advances in Neural Information Processing Systems 36: Annual Conference on Neural Information Processing Systems 2023, NeurIPS 2023, New Orleans, LA, USA, December 10 - 16, 2023, Alice Oh, Tristan Naumann, Amir Globerson, Kate Saenko, Moritz Hardt, and Sergey Levine (Eds.). http://papers.nips.cc/paper_files/paper/2023/ hash/ac662d74829e4407ce1d126477f4a03a-Abstract-Conference.html

- [219] Hang-Yu Zhou, Yaling Li, Jia-Ying Li, Jing Meng, and Aiping Wu. 2024. Harnessing the power of artificial intelligence to combat infectious diseases: Progress, challenges, and future outlook. The Innovation Medicine 2, 4 (2024), 100091–1.


- [220] Pei Zhou, Jay Pujara, Xiang Ren, Xinyun Chen, Heng-Tze Cheng, Quoc V Le, Ed H Chi, Denny Zhou, Swaroop Mishra, and Huaixiu Steven Zheng. 2024. Self-discover: Large language models self-compose reasoning structures. ArXiv preprint abs/2402.03620 (2024). https://arxiv.org/abs/2402.03620

- [221] Xuhui Zhou, Hao Zhu, Leena Mathur, Ruohong Zhang, Haofei Yu, Zhengyang Qi, Louis-Philippe Morency, Yonatan Bisk, Daniel Fried, Graham Neubig, et al. 2023. Sotopia: Interactive evaluation for social intelligence in language agents. ArXiv preprint abs/2310.11667 (2023). https://arxiv.org/abs/2310.11667

- [222] Lianghui Zhu, Xinggang Wang, and Xinlong Wang. 2023. Judgelm: Fine-tuned large language models are scalable judges. ArXiv preprint abs/2310.17631 (2023). https://arxiv.org/abs/2310.17631

- [223] Honglei Zhuang, Zhen Qin, Kai Hui, Junru Wu, Le Yan, Xuanhui Wang, and Michael Bendersky. 2024. Beyond Yes and No: Improving Zero-Shot LLM Rankers via Scoring Fine-Grained Relevance Labels. In Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 2: Short Papers), Kevin Duh, Helena Gomez, and Steven Bethard (Eds.). Association for Computational Linguistics, Mexico City, Mexico, 358–370. https://aclanthology.org/2024.naacl-short.31

- [224] Shengyao Zhuang, Honglei Zhuang, Bevan Koopman, and Guido Zuccon. 2024. A setwise approach for effective and highly efficient zero-shot ranking with large language models. In Proceedings of the 47th International ACM SIGIR Conference on Research and Development in Information Retrieval. 38–47.

- [225] Yuchen Zhuang, Xiang Chen, Tong Yu, Saayan Mitra, Victor Bursztyn, Ryan A Rossi, Somdeb Sarkhel, and Chao Zhang. 2023. Toolchain*: Efficient action space navigation in large language models with a* search. ArXiv preprint abs/2310.13227 (2023). https://arxiv.org/abs/2310.13227

- [226] Mingchen Zhuge, Changsheng Zhao, Dylan Ashley, Wenyi Wang, Dmitrii Khizbullin, Yunyang Xiong, Zechun Liu, Ernie Chang, Raghuraman Krishnamoorthi, Yuandong Tian, et al. 2024. Agent-as-a-Judge: Evaluate Agents with Agents. ArXiv preprint abs/2410.10934 (2024). https://arxiv.org/abs/2410.10934

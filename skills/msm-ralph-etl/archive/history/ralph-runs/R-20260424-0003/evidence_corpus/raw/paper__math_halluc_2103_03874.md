---
case_id: paper__math_halluc_2103_03874
source_type: paper
title: Mathematical Reasoning in LLMs
url: https://arxiv.org/pdf/2103.03874
resolved_url: https://arxiv.org/pdf/2103.03874
status_code: 200
fetched_at: 2026-04-24T02:10:38+00:00
doc_type: pdf
---

# arXiv:2103.03874v2 [cs.LG] 8 Nov 2021

## Measuring Mathematical Problem Solving With the MATH Dataset

Dan Hendrycks UC Berkeley

Collin Burns UC Berkeley

Saurav Kadavath UC Berkeley

Eric Tang UC Berkeley

Dawn Song UC Berkeley

Akul Arora UC Berkeley

Steven Basart UChicago

Jacob Steinhardt UC Berkeley

### Abstract

Many intellectual endeavors require mathematical problem solving, but this skill remains beyond the capabilities of computers. To measure this ability in machine learning models, we introduce MATH, a new dataset of 12,500 challenging competition mathematics problems. Each problem in MATH has a full step-by-step solution which can be used to teach models to generate answer derivations and explanations. To facilitate future research and increase accuracy on MATH, we also contribute a large auxiliary pretraining dataset which helps teach models the fundamentals of mathematics. Even though we are able to increase accuracy on MATH, our results show that accuracy remains relatively low, even with enormous Transformer models. Moreover, we ﬁnd that simply increasing budgets and model parameter counts will be impractical for achieving strong mathematical reasoning if scaling trends continue. While scaling Transformers is automatically solving most other text-based tasks, scaling is not currently solving MATH. To have more traction on mathematical problem solving we will likely need new algorithmic advancements from the broader research community.

### 1 Introduction

Mathematics is a highly effective tool in many intellectual endeavors. It enables us to count and quantify objects, and it can be relied upon because it is consistent and based on logic. Mathematics pervades the sciences and can be used to model planetary orbits, atomic motion, signal frequencies, and much more. These phenomena can be encoded with mathematics precisely and concisely. This has even led some to describe mathematics as being “unreasonably effective” (Wigner, 1960). These observations speak to the broad reach and domain-generality of mathematics.

In machine learning, mathematics is a valuable testbed for problem-solving ability: the ability to analyze a problem, pick out good heuristics from a large set of possibilities, and chain them together to produce an answer. This contrasts with plug-and-chug calculations, a skill which ML models can already exhibit (Henighan et al., 2020). Visual or linguistic reasoning may involve limited problem-solving ability for tasks such as image classiﬁcation, but unlike math this is not the focus of these domains.

To measure the problem-solving ability of machine learning models, we introduce the MATH dataset, which consists of 12,500 problems from high school math competitions. Given a problem from MATH, machine learning models generate a sequence, such as $\frac{2}{3}$, that encodes the ﬁnal answer. These answers are unique after normalization, allowing MATH to be scored with exact match rather than with heuristic metrics such as BLEU. In addition, MATH problems are tagged by difﬁculty from 1 to 5, and span seven subjects including geometry, where diagrams can be speciﬁed in text with the Asymptote language. This enables a ﬁne-grained assessment of

35th Conference on Neural Information Processing Systems (NeurIPS 2021) Track on Datasets and Benchmarks.

Metamath Theorem Proving

MATH Dataset (Ours)

Problem: Tom has a red marble, a green marble, a blue marble, and three identical yellow marbles. How many different groups of two marbles can Tom choose? Solution: There are two cases here: either Tom chooses two yellow marbles (1 result), or he chooses two marbles of different colors ( 42 = 6 results). The total number of distinct pairs of marbles Tom can choose is 1 + 6 = 7

n ∈ N ∧ n+12 ∈ N =⇒ ∃m ∈ N : n = 2m + 1. GPT-f’s generated proof:

|- ((N e. NN0 /\ ((N + 1)/2) e.

NN0) -> ((N - 1) / 2) e. NN0) |- (N e. NN0 -> N e. CC) |- 1 e. CC |- ((N e. CC /\ 1 e. CC) ->

(N - 1) e. CC )

| |
|---|


. Problem: The equation x2 + 2x = i has two complex solutions. Determine the product of their real parts. Solution: Complete the square by adding 1 to each side. Then (x + 1)2 = 1 + i = eiπ4

.

DeepMind Mathematics Dataset

Divide 1136975704 by -142121963. A: -8 Let k(u) = u**2+u-4. Find k(0). A: -4 Sort 2, 4, 0, 6. A: 0, 2, 4, 6 Solve 4 - 4 - 4 = 188*m for m. A: -1/47

###### √2, so x + 1 = ±eiπ8

√2. The desired product is then

4

−1 + cos π8 √4 2 −1 − cos π8 √4 2 = 1 − cos2 π8 √2 = 1 −

|1 −<br><br>√2 2<br><br>|
|---|


√2 =

(1+cos(

))

π 4

.

2

Figure 1: Previous work is based on formal theorem provers or straightforward plug-and-chug problems. Our dataset, MATH, has competition mathematics problems with step-by-step solutions written in LATEX and natural language. Models are tasked with generating tokens to construct the ﬁnal (boxed) answer.

mathematical problem-solving ability across difﬁculties and subjects. Finally, problems come with full step-by-step solutions. By training on these, models can learn to generate their own step-by-step solutions, which can facilitate learning and make model outputs more interpretable.

The MATH dataset is challenging: large language models achieved accuracies ranging from 3.0% to 6.9%. Despite these low accuracies, models clearly possess some mathematical knowledge: they achieve up to 15% accuracy on the easiest difﬁculty level, and they are able to generate step-by-step solutions that are coherent and on-topic even when incorrect. We also evaluated humans on MATH, and found that a computer science PhD student who does not especially like mathematics attained approximately 40% on MATH, while a three-time IMO gold medalist attained 90%, indicating that MATH can be challenging for humans as well.

The presence of step-by-step solutions allows models to utilize “scratch space”: rather than having to generate a ﬁnal answer immediately, models can ﬁrst generate solutions that may contain intermediate computations. Interestingly, we found that having models generate step-by-step solutions before producing an answer actually decreased accuracy relative to immediately outputting a ﬁnal answer without generating solutions, indicating the solutions are currently not useful for models at test time. In contrast, having models train on solutions increases relative accuracy by 10% compared to training on the questions and answers directly. We also ﬁnd that models do better with hints in the form of partial solutions. Our results show that models can make use of actual step-by-step solutions provided to them in various ways, but that they are still unable to effectively use their own generated solutions. Bridging this gap poses an interesting direction for further research.

While MATH covers advanced problem-solving techniques, models may ﬁrst need to be trained thoroughly on the fundamentals of mathematics. To address this, we create the ﬁrst large-scale mathematics pretraining dataset with hundreds of thousands of step-by-step solutions in natural language and LATEX. We call this dataset the Auxiliary Mathematics Problems and Solutions (AMPS) pretraining corpus, which consists of Khan Academy and Mathematica data. AMPS has over 100,000 Khan Academy problems with step-by-step solutions in LATEX; these exercises are used to teach human students concepts ranging from basic addition to Stokes’ Theorem. It also contains over 5 million problems generated using Mathematica scripts, based on 100 hand-designed modules covering topics such as conic sections, div grad and curl, KL divergence, eigenvalues, polyhedra, and Diophantine equations. In total AMPS contains 23GB of problems and solutions. Pretraining on

AMPS enables a 0.1 billion parameter model to perform comparably to a ﬁne-tuned model that is 130× larger.

Altogether, while large Transformer models (Vaswani et al., 2017) make some progress on the MATH dataset, such as by AMPS pretraining or by training with step-by-step solutions, accuracy nonetheless remains relatively low. While enormous Transformers pretrained on massive datasets can now solve most existing text-based tasks, this low accuracy indicates that our MATH dataset is distinctly harder. Accuracy also increases only modestly with model size: assuming a log-linear scaling trend, models would need around 1035 parameters to achieve 40% accuracy on MATH, which is impractical. Instead, to make large strides on the MATH dataset with a practical amount of resources, we will need new algorithmic advancements from the broader research community.

### 2 Related Work

Neural Theorem Provers. Much of the existing work on machine learning models for mathematical reasoning relies on automated theorem proving benchmarks. Huang et al. (2019) use the Coq theorem proving environment to create a machine learning benchmark with 1,602 theorems and lemmas. Bansal et al. (2019) introduce the HOList benchmark for automated theorem proving, which uses a formal language to enable automatic evaluation. Rather than use HOList, Polu and Sutskever (2020) use the Metamath formalization language for automated theorem proving with promising results. We show an example of Metamath in Figure 1. These benchmarks can be approached with seq2seq (Sutskever et al., 2014) Transformers which have traction on the problem (Polu and Sutskever, 2020; Rabe et al., 2020; Li et al., 2020).

Rather than prove theorems with standard pretrained Transformers, McAllester (2020) proposes that the community create theorem provers that bootstrap their mathematical capabilities through open-ended self-improvement. For bootstrapping to be feasible, models will also need to understand mathematics as humans write it, as manually converting advanced mathematics to a proof generation language is extremely time-consuming. This is why Szegedy (2020) argues that working on formal theorem provers alone will be an impractical path towards world-class mathematical reasoning. We address Szegedy (2020)’s concern by creating a dataset to test understanding of mathematics written in natural language and commonplace mathematical notation. This also means that the answers in our dataset can be assessed without the need for a cumbersome theorem proving environment, which is another advantage of our evaluation framework.

State-of-the-Art Accuracy on Mathematics Datasets

100

80

Accuracy (%)

60

40

20

0

HOList Auxiliary

HOLStep Proofs

DeepMind Math

Symbolic Integration

MATH (Ours)

Figure 2: Compared to existing proof and plugand-chug tasks, our mathematical problem solving task is considerably more challenging. HOList results are from Wu et al. (2021). HOLStep results are from Crouse et al. (2019). DeepMind Math accuracy is the median IID accuracy from Henighan et al. (2020). Symbolic Integration accuracy is from Lample and Charton (2020).

Neural Calculators. Recent work shows that Transformers can sometimes perform laborious calculations around as well as calculators and computer algebra systems. Lample and Charton (2020) use Transformers to solve algorithmically generated symbolic integration problems and achieve greater than 95% accuracy. Amini et al. (2019); Ling et al. (2017) introduce plug-and-chug multiple choice mathematics problems and focus on sequence-to-program generation. Saxton et al. (2019) introduce the DeepMind Mathematics dataset, which consists of algorithmically generated plug-and-chug problems such as addition, list sorting, and function evaluation, as shown in Figure 1. Recently, Henighan et al. (2020) show that, excluding problems with astronomically large numbers, the vast majority of the problems in the DeepMind Mathematics dataset can be straightforwardly solved with large Transformers.

Benchmarks for Enormous Transformers. There are few existing natural language benchmarks left to solve, as tasks that aggregate multiple subtasks such as SuperGLUE (Wang et al., 2019) are solved by simply training enormous Transformers (He et al., 2020). Kaplan et al. (2020); Henighan

Algebra Conic sections, polynomial GCD, De Moivre’s theorem, function inverses, ... Calculus Arclength, Jacobian, Laplacian, divergence, curl, gradients, integrals, ... Statistics Expectation, geometric mean, harmonic mean, KL divergence, variance, ... Geometry Triangle area, triangle inradius, polygon angles, polyhedron diameter, ... Linear Algebra Characteristic polynomials, eigenvalues, reduced row echelon form, ... Number Theory Modular inverse, Euler’s totient function, Chinese remainder theorem, ...

- Table 1: A subset of the topics covered by our 100 hand-designed Mathematica scripts, which is part of our Auxiliary Mathematics Problems and Solutions (AMPS) pretraining dataset. Of these scripts, 37 also generate step-by-step solutions. We generated around 50,000 exercises with each Mathematica script, or around 5 million problems.


et al. (2020) show that the performance of Transformers predictably increases with an increase in model size and dataset size, raising the question of whether natural language processing can be solved by simply increasing compute and funding. Additionally, Chen et al. (2021); Austin et al. (2021) show that code generation models scale reliably across several orders of magnitude, and, should scaling continue, Chen et al. (2021)’s HumanEval code generation dataset should be solved in a few orders of magnitude. In the Supplementary Materials, we even ﬁnd that large GPT-3 models can perform remarkably well on a sequence completion test similar to an IQ test, the C-Test (Hernández-Orallo, 1998; Legg and Hutter, 2007). Even difﬁcult logical understanding tasks such as LogiQA (Liu et al., 2020) will soon be straightforwardly solved by enormous Transformers should trends continue, which we also show in the Supplementary Materials. Hendrycks et al. (2021) create a multiple-choice benchmark covering 57 subjects. However, unlike our benchmark, which is a text generation task with 12,500 mathematical reasoning questions, their benchmark is a multiple choice task that includes only a few hundred questions about mathematics. In contrast to these benchmarks, we ﬁnd that our MATH benchmark is unusually challenging for current models and, if trends continue, simply using bigger versions of today’s Transformers will not solve our task in the foreseeable future.

### 3 Datasets

In this section, we introduce two new datasets, one for benchmarking mathematical problem-solving ability (MATH) and one for pretraining (AMPS).

##### 3.1 The MATH Dataset

The MATH dataset consists of problems from mathematics competitions including the AMC 10, AMC 12, AIME, and more. Many of these problems can be collected from aops.com/community/c3158_usa_contests. These competitions span decades and assess the mathematical problem-solving ability of the best young mathematical talent in the United States. Unlike most prior work, most problems in MATH cannot be solved with a straightforward application of standard K-12 mathematics tools. Instead, humans often solve such problem by applying problem solving techniques and “heuristics” (Pólya, 1945).

The Mathematics Aptitude Test of Heuristics dataset, abbreviated MATH, has 12,500 problems (7,500 training and 5,000 test). With this many training problems, models can learn many useful heuristics for problem solving. Each problem has a step-by-step solution and a ﬁnal boxed answer. Example problems with step-by-step solutions are shown in Figure 1.

Categorizing Problems. Problems span various subjects and difﬁculties. The seven subjects are Prealgebra, Algebra, Number Theory, Counting and Probability, Geometry, Intermediate Algebra, and Precalculus. While subjects like Prealgebra are generally easier than Precalculus, within a subject problems can take on different difﬁculty levels. We encode a problem’s difﬁculty level from ‘1’ to ‘5,’ following AoPS. A subject’s easiest problems for humans are assigned a difﬁculty level of ‘1,’ and a subject’s hardest problems are assigned a difﬁculty level of ‘5.’ Concretely, the ﬁrst few problems of an AMC 8 exam are often level 1, while AIME problems are level 5. This allows us to assess performance across both different subjects and different levels of difﬁculty.

Formatting. Problems and solutions are consistently formatted using LATEX and the Asymptote vector graphics language. Our usage of LATEX allows us to ﬂexibly encode mathematical problems while avoiding unusual symbols or cumbersome formal languages. Meanwhile, mathematical ﬁgures are encoded in the Asymptote language rather than as raster images. This enables pure language

|Model Prealgebra Algebra Number Theory<br><br>Counting& Probability<br><br>Geometry Intermediate Algebra<br><br>Precalculus<br><br>|Average|
|---|---|
|GPT-2 0.1B 5.2 5.1 5.0 2.8 5.7 6.5 7.3 GPT-2 0.3B 6.7 6.6 5.5 3.8 6.9 6.0 7.1<br><br>GPT-2 0.7B 6.9 6.1 5.5 5.1 8.2 5.8 7.7<br>GPT-2 1.5B 8.3 6.2 4.8 5.4 8.7 6.1 8.8<br><br><br>|5.4 +0%<br>6.2 +15% 6.4 +19% 6.9 +28%<br>|
|GPT-3 13B* 4.1 2.4 3.3 4.5 1.0 3.2 2.0 GPT-3 13B 6.8 5.3 5.5 4.1 7.1 4.7 5.8 GPT-3 175B* 7.7 6.0 4.4 4.7 3.1 4.4 4.0|3.0 −44% 5.6 +4% 5.2 −4%|


- Table 2: MATH accuracies across subjects. ‘*’ indicates that the model is a few-shot model. The character ‘B’ denotes the number of parameters in billions. The gray text indicates the relative improvement over the 0.1B baseline. All GPT-2 models pretrain on AMPS, and all values are percentages. GPT-3 models do not pretrain on AMPS due to API limits. Model accuracy is increasing very slowly, so much future research is needed.


models to process ﬁgures, diagrams, and graphics, making it possible to assess these models on subjects such as geometry for the ﬁrst time.

To assess models using exact match, we force the ﬁnal boxed answers to follow consistent formatting rules. Speciﬁcally, probabilities are expressed as simpliﬁed fractions. Moreover, matrix entry fractions are encoded with x/y, while all other fractions are consistently encoded with the \frac{x}{y}

command. Coefﬁcients are encoded without a multiplication symbol (e.g. 5x not 5*x). Expressions with multiple variables are entered in alphabetical order; polynomials are expressed in decreasing degree order. Different fraction encodings equivalent, such as \frac{x}{y} and \dfrac{x}{y} and x/y. Different parenthesis encodings, such as \left( and (, are treated as equivalent.

We also allow units to be included or omitted from an answer, we ignore spaces, and we treat common equivalent ways of expressing the same number (e.g., 0.5 and 1/2, or 0.1 and .1) as the same. When the answer is a factorized polynomial, we permit different orderings of the factors, so that 4(x + 1)(x − 1) is equivalent to 4(x − 1)(x + 1), and so on. These rules cover nearly all ways that different generated or actual solutions can be equivalent in practice.

Automatically Assessing Generated Answers. Due to design choices in MATH, we can assess the answers generated by a model automatically, even though the space of model outputs is combinatorially large. Automatic assessment starts by determining the beginning and end of the answer. This is possible to do even if a model generates step-by-step solutions because the ﬁnal answers in MATH are wrapped and delimited with the \boxed{} command. We can consequently evaluate a model’s output by parsing what is inside the \boxed{} command and comparing that with the ground truth answer, while accounting for the equivalent ways of formatting a string described above. Together, the box delimiter and formatting rules provide a unique answer in a well-deﬁned location, which allows us to test for equivalence and use accuracy as our primary metric.

Human-Level Performance. To provide a rough but informative comparison to human-level performance, we randomly sampled 20 problems from the MATH test set and gave them to humans. We artiﬁcially require that the participants have 1 hour to work on the problems and must perform calculations by hand. All participants are university students. One participant who does not like mathematics got 8/20 = 40% correct. A participant ambivalent toward mathematics got 13/20. Two participants who like mathematics got 14/20 and 15/20. A participant who got a perfect score on the AMC 10 exam and attended USAMO several times got 18/20. A three-time IMO gold medalist got 18/20 = 90%, though missed questions were exclusively due to small errors of arithmetic. Expert-level performance is theoretically 100% given enough time. Even 40% would accuracy for a machine learning model would be impressive but have ramiﬁcations for cheating on homework.

##### 3.2 AMPS (Khan + Mathematica) Dataset

Since pretraining data can greatly inﬂuence performance (Hernandez et al., 2021; Gururangan et al., 2020) and since mathematics is a small fraction of online text, we introduce a large and diverse mathematics pretraining corpus. Our pretraining dataset, the Auxiliary Mathematics Problems and Solutions (AMPS) dataset, has problems and step-by-step solutions typeset in LATEX. AMPS contains over 100,000 problems pulled from Khan Academy and approximately 5 million problems generated from manually designed Mathematica scripts.

Khan Academy. The Khan Academy subset of AMPS has 693 exercise types with over 100,000 problems and full solutions. Problem types range from elementary mathematics (e.g. addition) to multivariable calculus (e.g. Stokes’ theorem), and are used to teach actual K-12 students. The exercises can be regenerated using code from github.com/Khan/khan-exercises/. We show the full list of problem types in the Supplementary Materials.

Mathematica. To make AMPS larger, we also contribute our own Mathematica scripts to generate approximately 50× more problems than our Khan Academy dataset. With Mathematica, we designed 100 scripts that test distinct mathematics concepts, 37 of which include full step-by-step LATEX solutions in addition to ﬁnal answers. We generated around 50,000 exercises from each of our scripts, or around 5 million problems in total. This results in over 23 GB of mathematics problems, making it larger than the 16 GB of natural language used to train BERT (Devlin et al., 2019).

Problems include various aspects of algebra, calculus, counting and statistics, geometry, linear algebra, and number theory (see Table 1 for a sampling of topics). Unlike prior approaches to algorithmically generating mathematics problems, we use Mathematica’s computer algebra system so that we can manipulate fractions, transcendental numbers, and analytic functions.

### 4 Experiments

In this section, we perform experiments to investigate performance on the MATH dataset. We ﬁnd that accuracy remains low even for the best models. Furthermore, unlike for most other text-based datasets, we ﬁnd that accuracy is increasing very slowly with model size. If trends continue, then we will need algorithmic improvements, rather than just scale, to make substantial progress on MATH. Nevertheless, we show that making progress is also possible today. We ﬁnd that pretraining on AMPS enables a small 0.1B parameter model to perform similarly to a large ﬁne-tuned 13B parameter model.

We also experiment with using step-by-step solutions. We ﬁnd that having models generate their own step-by-step solutions before producing an answer actually degrades accuracy. We qualitatively assess these generated solutions and ﬁnd that while many steps remain illogical, they are often related to the question. Finally, we show that step-by-step solutions can still provide beneﬁts today. We ﬁnd that providing partial ground truth step-by-step solutions can improve performance, and that providing models with step-by-step solutions at training time also increases accuracy.

##### 4.1 Experimental Setup

Models and Hyperparameters. Because MATH answers must be generated, we use autoregressive language models, namely GPT-2 (Radford et al., 2016) and GPT-3 (Brown et al., 2020), which are decoder models pretrained on natural language text. Our GPT-2 models tokenizes numbers so that one digit is processed at a time (Henighan et al., 2020). T5’s (Raffel et al., 2020) tokenizer removes many LATEX symbols, so after a broad hyperparameter sweep lasting two weeks, its performance was not competitive. We show results with the BART architecture in the Appendix.

Before ﬁne-tuning on MATH, models pretrain on AMPS. We pretrain for one epoch, using AdamW (Loshchilov and Hutter, 2019), using a batch size of 128, and using a weight decay of 0.05. We use the standard autoregressive language modeling objective. During pretraining, we upsample Khan Academy data by a factor of 5 and we downsample Mathematica by a factor of 2 to account for the large difference in dataset sizes.

During ﬁne-tuning, models predict ﬁnal answers and solutions. Concretely, if P is the problem statement, we train with an equal mix of “ P Final Answer: <Answer>” and “ P Full Solution: <Step-by-Step Solution>” sequences. This makes it possible for the model to both generate full solutions and also to output just the ﬁnal answer. For ﬁne-tuning we use the same batch size and weight decay as in pretraining. Models are trained with 8 A100 GPUs, each requiring less than a day.

Unless otherwise speciﬁed, for GPT-2 we use the default HuggingFace (Wolf et al., 2020) generation parameters, except that we use beam search. Our beam search has a beam size of 20 when only generating the ﬁnal answer, and a beam size of 10 when generating full step-by-step solutions. By default, we evaluate models by prompting them with “ P Final Answer:” so that they directly generate the ﬁnal answer to each problem, not the step-by-step solution.

Problem: Suppose a and b are positive real numbers with a > b and ab = 8. Find the minimum value of a

2+b2 a−b .

2+b2 a−b ≥ s

2

Generated solution: Let s = a b. By QM-AM, aa2−+bb2 ≥ a+2b = 2s. Then a

4 , so a2 + b2 ≥ s

2

2+b2 a b ≥ s

2

2

2

| |
|---|


2 . Hence, a

2 + 2s

a b = s

2 + 2s2 = 8

##### . Ground truth solution: We can write a

2+16

2+b2−2ab+16

2+b2 a−b = a

a−b = (a−b)

a−b = a − b + a16−b. By AM-GM, a − b + a16−b ≥ 2 (a − b) · a16−b = 8. Equality occurs when a − b = 4 and ab = 8. We can solve these equations to ﬁnd a = 2√3 + 2 and b = 2√3 2. Thus, the minimum value is

|8|
|---|


.

Problem: Right ∆ABC has legs measuring 8 cm and 15 cm. The triangle is rotated about one of its legs. What is the number of cubic centimeters in the maximum possible volume of the resulting solid? Express your answer in terms of π.

Generated solution: Rotating the triangle about one leg gives us the following triangle:

8

(8)(15) (8)(−1) + (15)(−1)

120 7

|= 120π|
|---|


= .

=

15

Ground truth solution: If the triangle is rotated about the shorter leg, then the radius is the longer leg and the height is the shorter leg, and the volume is 13 ·(152π)(8) = 600π cubic centimeters. If the triangle is rotated about the longer leg, then the radius is the shorter leg and the height is the longer leg, and the volume is 13(82π)(15), which is 158 of the volume we found earlier. So, the maximum possible volume is

|600π|
|---|


cubic centimeters.

- Figure 3: Problems, step-by-step solutions generated by our GPT-2 1.5B model, and ground truth solutions. Observe that models can provide the right answer yet generate a misleading and wrong explanation. The second generated solution demonstrates that models are capable of generating Asymptote commands to create ﬁgures and graphics.


We also evaluate GPT-3 with ﬁne-tuning and also in a few-shot setting using the OpenAI API. We use the ‘Curie’ GPT-3 model which has approximately 13 billion parameters, and the ‘Davinci’ model which has approximately 175 billion parameters. When performing few-shot evaluation, we construct our prompt by prepending 8 problems with correct answers (but not step-by-step solutions due to space). Using temperature 0, models output up to 20 tokens for the ﬁnal answer. The OpenAI API also allows users to ﬁne-tune models up to 13B parameters at the time of writing, but their API does not have the option to pretrain on datasets as large as AMPS.

##### 4.2 Analyzing Model Performance

AMPS Pretraining. As an ablation, we test how models with AMPS pretraining compare with models that were not pretrained on AMPS. Without pretraining on AMPS, a GPT-3 (13B) model ﬁne-tuned on MATH attains 5.2% accuracy. In contrast, a GPT-2 (0.1B) model both pretrained on AMPS and ﬁne-tuned on MATH attains 5.4%. Consequently AMPS increases accuracy about as much as a 130× increase in parameters, demonstrating its value as a pretraining dataset.

We additionally tried pretraining on StackExchange, a real-world but less curated source of mathematics text. A GPT-2 (0.3B) model pretrained on both AMPS and questions and answers from Math StackExchange (∼3 GB) had 6.0% accuracy. This is actually less than the 6.2% accuracy attained by pretraining on AMPS alone. Thus our dataset is more useful for pretraining even than diverse real-world mathematics data.

Model Size. While increasing model parameters often automatically solves many tasks (Brown et al., 2020), we ﬁnd that MATH is unusually challenging for enormous Transformers. Table 2 shows that the average accuracy across subjects for the smallest model, GPT-2 with 0.1 billion parameters, is 5.4%. Meanwhile, a GPT-2 model with 15× the number of parameters attains 6.9% accuracy, a 28% relative improvement. This indicates that while having more parameters helps, absolute accuracy remains far from the ceiling and is only increasing slowly, quite unlike most other text-based tasks.

Problem: The three-digit number "ab5” is divisible by 3. How many different three-digit numbers can "ab5” represent?

Generated solution: A number is divisible by 3 if and only if the sum of its digits is divisible by 3. So ab5 is divisible by 3 if and only if the two-digit number ab leaves a remainder of 1 when divided by 3. There are 90 two-digit numbers, of which 90/3 = 30

| |
|---|


leave a remainder of 1 when divided by

- 3. Ground truth solution: If the number is divisible by 3, the sum of the digits must be divisible by 3. So a + b must be one more than a multiple of 3, since 5 is one less than a multiple of 3. We have several options: If a+b = 1, it must be (1,0), one possibility. For a+b = 4, a can be 1 to 4, for four possibilities. For a + b = 7, a can be 1 to 7, so seven possibilities. For a + b = 10, anything from (1,9) to (9,1) works, so nine possibilities. For a + b = 13, the pairs range from (4,9) to (9,4), for six possibilities. If a + b = 16, we can have (7,9), (8,8), or (9,7), so three possibilities. a + b = 19 and up is not possible. So the total number is 1 + 4 + 7 + 9 + 6 + 3 = 30

Problem: Beginning at point A in the diagram, Dora selects one of the four possible directions with equal probability. Each time she comes to an intersection, she again randomly selects one of the possible directions. What is the probability that, in her ﬁrst four steps, she will walk completely around the gray square? Express your answer as a common fraction. Generated solution: The total probability that Dora chooses a direction completely around the gray

|A| | |
|---|---|---|
| | | |
| | | |


square is 105 =

|1<br><br>2<br>|
|---|


.

Ground truth solution: The only way for the Dora to end up at her starting point in four steps is for her to traverse the four sides of the gray square. She can do this in two ways: clockwise

and counterclockwise. The probability of each of these two paths is 14 4 = 2561 . Therefore, the probability that she ends up where she started is

1 256

+

1 256

=

|1 128<br><br>|
|---|


.

Figure 4: Additional example problems, generated solutions, and ground truth solutions from our MATH dataset. The ﬁrst problem’s generated solution has the right answer with a correct and simple explanation. The second problem is a combinatorics problem speciﬁed with a ﬁgure, which the model gets wrong.

Problem Difﬁculty. We also analyze model accuracy while controlling for problem difﬁculty. Higher levels of difﬁculty correspond to lower accuracy, as expected. These results are visualized in the Supplementary Materials. The accuracy of GPT-2 (1.5B) is around 15% for level 1 (easy) and around 4% for level 5 (hard). Even our benchmark’s easiest problems are more challenging than previous benchmarks that focused on straightforward plug-and-chug problems.

Error Detection. To determine whether we can trust the answers from a model, we analyze model conﬁdence to see whether conﬁdence tends to be higher for correct answers. We deﬁne conﬁdence as the average prediction probability of the tokens that make up a generated answer. GPT-2 (1.5B) is highly overconﬁdent, with conﬁdences that are often around 100%. Moreover, there is substantial overlap between correct and incorrect answers. Following Hendrycks and Gimpel (2017), we computed the probability that a correct answer has higher conﬁdence than an incorrect answer. To do this, we compute the Area Under the Receiver Operating Characteristic curve (AUROC). An AUROC of 100% corresponds to being able to perfectly detect correct and incorrect answers, while 50% corresponds to random chance. We ﬁnd that with GPT-2 (1.5B), the AUROC is quite low at 68.8%. This suggests there is substantial room for improvement in detecting model errors.

- 4.3 Analyzing Step-by-Step Solutions


Scratch Space. Our MATH dataset and AMPS pretraining dataset provide full step-by-step solutions, an important and rare type of side information (Murty et al., 2020) that can in principle teach models how to derive answers and use scratch space. By training a language model on these solutions, we can have models generate full step-by-step solutions. This may be especially useful for difﬁcult problems, for which outputting the correct answer after just a few forward passes may be insufﬁcient. By allowing the model to use several steps of processing before outputting a ﬁnal answer, the model could adaptively use computation and have higher performance, in addition to making its reasoning more interpretable.

We test this by prompting models with “ P Full Solution:” to generate a full solution along with a ﬁnal boxed answer, rather than the boxed answer alone. We evaluated this for GPT2 (1.5B) and found that this actually makes performance worse, dropping accuracy to 5.3%. We hypothesize that the drop in accuracy from using scratch space arises from a snowballing effect, in which partially generated “solutions” with mistakes can derail subsequent generated text. Nevertheless, when generation becomes more reliable and models no longer confuse themselves by their own generations, our dataset’s solutions could in principle teach models to use scratch space and attain higher accuracy.

MATH Accuracy Given Partial Solutions

GPT-2 (0.7B)

40

30

Accuracy (%)

20

10

0

0% 25% 50% 75% 99% Fraction of Solution Seen

Figure 5: Models conditioned on most of a problem’s step-by-step solution can often understand the solution to predict the ﬁnal answer. Not all solutions have an answer that is immediate from the preceding solution text, though many are. ‘99%’ of a solution is all the solution text before the ﬁnal answer. This demonstrates that, even with substantial help, models are still struggling.

Examples. We can also qualitatively assess the step-by-step solutions that the model generates. We show examples of generated solutions in Figures 3 and 4. We ﬁnd that the model can consistently generate correct LATEX and often performs steps that appear related to the question at hand, but still makes many logical mistakes, both in terms of what the question seems to be asking and in individual steps that are part of a larger derivation.

The Beneﬁts of MATH Solutions. We ﬁnd that giving models partial step-by-step MATH solutions during inference can improve accuracy. We test performance when we allow models to predict the ﬁnal answer given a “hint” in the form of a portion of the ground truth step-by-step solution. To do so, for this experiment we prompt models with “ P <Partial Step-by-Step Solution without Final Answer> Final Answer:” during both ﬁne-tuning and evaluation for different partial fractions of the step-by-step solution. This is the same as the default setting when we let models see 0% of the step-by-step solution. When models see “99%” of the solution, they are given the whole step-by-step solution except for the ﬁnal answer. We show results with GPT-2 (0.7B) for different fractions of the solution in Figure 5. Observe that the model still only attains approximately 40% when given 99% of the solution, indicating room for improvement.

Finally, we also ﬁnd that providing models with step-by-step during training can further improve performance. We run an ablation by ﬁne-tuning models on MATH with the same setup as before, except that we only show examples with the ﬁnal answer and no step-by-step solution. If we ﬁne-tune with only the ﬁnal answer, the GPT-2 (1.5B) accuracy decreases by 0.6% to 6.3%.

### 5 Conclusion

In this paper, we laid groundwork for future research in machine learning for mathematical problem solving. We introduced the MATH benchmark, which enables the community to measure mathematical problem-solving ability. In addition to having answers, all MATH problems also include answer explanations, which models can learn from to generate their own step-by-step solutions. We also introduce AMPS, a diverse pretraining corpus that can enable future models to learn virtually all of K-12 mathematics. While most other text-based tasks are already nearly solved by enormous Transformers, MATH is notably different. We showed that accuracy is slowly increasing and, if trends continue, the community will need to discover conceptual and algorithmic breakthroughs to attain strong performance on MATH. Given the broad reach and applicability of mathematics, solving the MATH dataset with machine learning would be of profound practical and intellectual signiﬁcance.

### References

Aida Amini, Saadia Gabriel, Shanchuan Lin, Rik Koncel-Kedziorski, Yejin Choi, and Hannaneh Hajishirzi. MathQA: Towards interpretable math word problem solving with operation-based formalisms. ArXiv, abs/1905.13319, 2019.

Jacob Austin, Augustus Odena, Maxwell Nye, Maarten Bosma, Henryk Michalewski, David Dohan, Ellen Jiang, Carrie Cai, Michael Terry, Quoc Le, and Charles Sutton. Program synthesis with large language models. ArXiv, abs/2108.07732, 2021.

K. Bansal, S. Loos, Markus N. Rabe, Christian Szegedy, and S. Wilcox. Holist: An environment for machine learning of higher-order theorem proving (extended version). ArXiv, abs/1904.03241, 2019.

T. Brown, B. Mann, Nick Ryder, Melanie Subbiah, J. Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda Askell, Sandhini Agarwal, Ariel Herbert-Voss, G. Krüger, T. Henighan, R. Child, Aditya Ramesh, D. Ziegler, Jeffrey Wu, Clemens Winter, Christopher Hesse, Mark Chen, E. Sigler, Mateusz Litwin, Scott Gray, Benjamin Chess, J. Clark, Christopher Berner, Sam McCandlish, A. Radford, Ilya Sutskever, and Dario Amodei. Language models are few-shot learners. ArXiv, abs/2005.14165, 2020.

Mark Chen, Jerry Tworek, Heewoo Jun, Qiming Yuan, Henrique Ponde, J. Kaplan, Harrison Edwards, Yura Burda, Nicholas Joseph, Greg Brockman, Alex Ray, Raul Puri, Gretchen Krueger, Michael Petrov, Heidy Khlaaf, Girish Sastry, Pamela Mishkin, Brooke Chan, Scott Gray, Nick Ryder, Mikhail Pavlov, Alethea. Power, Lukasz Kaiser, Mohammad Bavarian, Clemens Winter, Philippe Tillet, F. Such, D. Cummings, Matthias Plappert, Fotios Chantzis, Elizabeth Barnes, Ariel HerbertVoss, William H. Guss, Alex Nichol, I. Babuschkin, S. Balaji, Shantanu Jain, A. Carr, J. Leike, Joshua Achiam, Vedant Misra, Evan Morikawa, Alec Radford, M. Knight, Miles Brundage, Mira Murati, Katie Mayer, P. Welinder, Bob McGrew, Dario Amodei, Sam McCandlish, Ilya Sutskever, and Wojciech Zaremba. Evaluating large language models trained on code. ArXiv, abs/2107.03374, 2021.

Maxwell Crouse, I. Abdelaziz, Cristina Cornelio, Veronika Thost, L. Wu, Kenneth D. Forbus, and Achille Fokoue. Improving graph neural network representations of logical formulae with subgraph pooling. ArXiv, abs/1911.06904, 2019.

J. Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. Bert: Pre-training of deep bidirectional transformers for language understanding. In NAACL-HLT, 2019.

Suchin Gururangan, Ana Marasovi´c, Swabha Swayamdipta, Kyle Lo, Iz Beltagy, Doug Downey, and Noah A. Smith. Don’t stop pretraining: Adapt language models to domains and tasks. ArXiv, abs/2004.10964, 2020.

Pengcheng He, Xiaodong Liu, Jianfeng Gao, and Weizhu Chen. Deberta: Decoding-enhanced bert with disentangled attention. ArXiv, abs/2006.03654, 2020.

Dan Hendrycks and Kevin Gimpel. A baseline for detecting misclassiﬁed and out-of-distribution examples in neural networks. ICLR, 2017.

Dan Hendrycks, C. Burns, Steven Basart, Andy Zou, Mantas Mazeika, D. Song, and J. Steinhardt. Measuring massive multitask language understanding. ICLR, 2021.

T. Henighan, J. Kaplan, Mor Katz, Mark Chen, Christopher Hesse, J. Jackson, Heewoo Jun, T. Brown, Prafulla Dhariwal, Scott Gray, Chris Hallacy, B. Mann, A. Radford, Aditya Ramesh, Nick Ryder, D. Ziegler, John Schulman, Dario Amodei, and Sam McCandlish. Scaling laws for autoregressive generative modeling. ArXiv, abs/2010.14701, 2020.

Danny Hernandez, J. Kaplan, T. Henighan, and Sam McCandlish. Scaling laws for transfer. arXiv, 2021.

J. Hernández-Orallo. Beyond the turing test. Journal of Logic, Language and Information, 9:447–466, 2000.

Jose Hernández-Orallo. A formal deﬁnition of intelligence based on an intensional variant of algorithmic complexity. EIS, 1998.

D. Huang, Shuming Shi, Chin-Yew Lin, J. Yin, and W. Ma. How well do computers solve math word problems? large-scale dataset construction and evaluation. In ACL, 2016.

Daniel Huang, Prafulla Dhariwal, D. Song, and Ilya Sutskever. Gamepad: A learning environment for theorem proving. ArXiv, abs/1806.00608, 2019.

J. Kaplan, Sam McCandlish, T. Henighan, T. Brown, Benjamin Chess, R. Child, Scott Gray, A. Radford, Jeffrey Wu, and Dario Amodei. Scaling laws for neural language models. ArXiv, abs/2001.08361, 2020.

Daniel Khashabi, Tushar Khot, Ashish Sabharwal, Oyvind Tafjord, Peter Clark, and Hannaneh Hajishirzi. Uniﬁedqa: Crossing format boundaries with a single qa system, 2020.

Guillaume Lample and Franccois Charton. Deep learning for symbolic mathematics. ArXiv, abs/1912.01412, 2020.

S. Legg and Marcus Hutter. Universal intelligence: A deﬁnition of machine intelligence. Minds and Machines, 17:391–444, 2007.

M. Lewis, Yinhan Liu, Naman Goyal, Marjan Ghazvininejad, Abdelrahman Mohamed, Omer Levy, Veselin Stoyanov, and Luke Zettlemoyer. Bart: Denoising sequence-to-sequence pre-training for natural language generation, translation, and comprehension. ArXiv, abs/1910.13461, 2020.

Wenda Li, L. Yu, Yuhuai Wu, and Lawrence C. Paulson. Modelling high-level mathematical reasoning in mechanised declarative proofs. ArXiv, abs/2006.09265, 2020.

Wang Ling, Dani Yogatama, Chris Dyer, and P. Blunsom. Program induction by rationale generation: Learning to solve and explain algebraic word problems. In ACL, 2017.

J. Liu, Leyang Cui, Hanmeng Liu, Dandan Huang, Yile Wang, and Yue Zhang. LogiQA: A challenge dataset for machine reading comprehension with logical reasoning. In IJCAI, 2020.

I. Loshchilov and F. Hutter. Decoupled weight decay regularization. In ICLR, 2019. David A. McAllester. MathZero, the classiﬁcation problem, and set-theoretic type theory. ArXiv,

abs/2005.05512, 2020. Shen-Yun Miao, Chao-Chun Liang, and Keh-Yih Su. A diverse corpus for evaluating and developing english math word problem solvers. In ACL, 2020. Shikhar Murty, Pang Wei Koh, and Percy Liang. Expbert: Representation engineering with natural language explanations. In ACL, 2020. Stanislas Polu and Ilya Sutskever. Generative language modeling for automated theorem proving.

ArXiv, abs/2009.03393, 2020. George Pólya. How to Solve It. Princeton University Press, 1945. Markus N. Rabe, Dennis Lee, K. Bansal, and Christian Szegedy. Mathematical reasoning via

self-supervised skip-tree training. arXiv: Learning, 2020. A. Radford, Luke Metz, and Soumith Chintala. Unsupervised representation learning with deep convolutional generative adversarial networks. CoRR, abs/1511.06434, 2016.

Colin Raffel, Noam Shazeer, Adam Roberts, Katherine Lee, Sharan Narang, M. Matena, Yanqi Zhou, W. Li, and Peter J. Liu. Exploring the limits of transfer learning with a uniﬁed text-to-text transformer. JMLR, 2020.

D. Saxton, Edward Grefenstette, Felix Hill, and P. Kohli. Analysing mathematical reasoning abilities of neural models. ArXiv, abs/1904.01557, 2019.

Ilya Sutskever, Oriol Vinyals, and Quoc V. Le. Sequence to sequence learning with neural networks. In NIPS, 2014.

Christian Szegedy. A promising path towards autoformalization and general artiﬁcial intelligence. In CICM, 2020.

Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, L. Kaiser, and Illia Polosukhin. Attention is all you need. ArXiv, abs/1706.03762, 2017.

Alex Wang, Yada Pruksachatkun, Nikita Nangia, Amanpreet Singh, Julian Michael, Felix Hill, Omer Levy, and Samuel R. Bowman. Superglue: A stickier benchmark for general-purpose language understanding systems. In NeurIPS, 2019.

Eugene Wigner. The unreasonable effectiveness of mathematics in the natural sciences. Communications in Pure and Applied Mathematics, 1960.

Thomas Wolf, Lysandre Debut, Victor Sanh, Julien Chaumond, Clement Delangue, Anthony Moi, Pierric Cistac, Tim Rault, Rémi Louf, Morgan Funtowicz, Joe Davison, Sam Shleifer, Patrick von Platen, Clara Ma, Yacine Jernite, Julien Plu, Canwen Xu, Teven Le Scao, Sylvain Gugger, Mariama Drame, Quentin Lhoest, and Alexander M. Rush. Transformers: State-of-the-art natural language processing. In Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing: System Demonstrations. Association for Computational Linguistics, 2020.

Yuhuai Wu, M. Rabe, Wenda Li, Jimmy Ba, Roger B. Grosse, and Christian Szegedy. Lime: Learning inductive bias for primitives of mathematical reasoning. ArXiv, abs/2101.06223, 2021.

### A Appendix

In this appendix, we have more comparisons with previous datasets, a discussion of logic and intelligence tests, further AMPS and MATH details, an analysis of model performance as difﬁculty level changes, and results with the BART architecture.

##### A.1 Expanded Dataset Comparisons

We compared to ten datasets in the main paper, and now we will further describe plug-and-chug datasets. Dolphin18K (Huang et al., 2016) is one of the ﬁrst modern datasets in this space and is based on Yahoo! Answers and includes questions such as “help!!!!!!!(please) i cant ﬁgure this out!? what is the sum of 4 2/5 and 17 3/7 ?”. MathQA (Amini et al., 2019) builds on AQuA-RAT (Ling et al., 2017) and claims AQuA-RATs “rationales are noisy, incomplete and sometimes incorrect.” MathQA then cleans AQuA-RAT, though cleaning led the dataset size to be reduced by half of an order of magnitude. Miao et al. (2020) analyze MathQA and observe “the annotated formulas of 27% of the problems do not match their labeled answers,” and they obtain 86% accuracy on a cleaned version of MATH-QA. In contrast AMPS is large and clean as questions are algorithmically generated, and our MATH dataset is carefully curated by the competition mathematics community and contains competition-level problems that are difﬁcult.

##### A.2 Logic and Intelligence Tests

Model Size vs. LogiQA Accuracy

Random Chance

50

Accuracy (%)

40

30

20

10 1 100 101 Transformer Size (Billion Parameters)

- Figure 6: Difﬁcult natural language tasks such as LogiQA will soon be solved just by making models larger, assuming trends continue. The Transformers in this ﬁgure are UniﬁedQA (Khashabi et al.,


2020) models of various sizes.

While enormous Transformers perform poorly on MATH, they do well on other logic and intelligence tests.

We analyze Transformers on LogiQA (Liu et al., 2020), a task with logical reasoning questions such

- as “David knows Mr. Zhang’s friend Jack, and Jack knows David’s friend Ms. Lin. Everyone of them who knows Jack has a master’s degree, and everyone of them who knows Ms. Lin is from Shanghai. Who is from Shanghai and has a master’s degree?” As shown in Figure 6, Transformers are improving on LogiQA, so much so that they will attain human-level performance relatively soon, should trends continue.


We also ﬁnd that Transformers also do well on the C-Test, a pattern completion test that has a 77% correlation with human IQ (Hernández-Orallo, 2000). An example of a problem from C-Test is the sequence “a, a, z, c, y, e, x, _” which has the answer “g.” We regenerated hundreds of C-Test examples to test GPT-3 (175B) in a 5-shot setting. While GPT-3 had abysmal performance when the sequences were letters, converting letters to numbers helped. After changing ‘a’ to 0, ‘b’ to 1, ..., and ‘z’ to 25, accuracy became approximately 40% on the hardest examples (C-Test questions with complexity “13”). For comparison, on these same examples, average humans attained around 20% accuracy (Hernández-Orallo, 2000).

size(40); draw(shift(1.38,0)*yscale(0.3)*Circle((0,0), .38));

draw((1,0)--(1,-2)); draw((1.76,0)--(1.76,-2));

draw((1,-2)..(1.38,-2.114)..(1.76,-2));

- path p =(1.38,-2.114)..(1.74,-1.5)..(1,-0.5)..(1.38,-.114); pair a=(1.38,-2.114), b=(1.76,-1.5);
- path q =subpath(p, 1, 2);
- path r=subpath(p,0,1);
- path s=subpath(p,2,3);


- draw(r);
- draw(s); draw(q, dashed); label("$5$",midpoint((1.76,0)--(1.76,-2)),E);


#### 5

Figure 7: Example of asymptote code and the ﬁgure it produces.

##### A.3 Further Dataset Information

Rendering Graphics. For the ﬁrst time, our dataset makes it possible for text-based models to process graphical mathematical ﬁgures by expressing ﬁgures in asymptote code. For example,

- Figure 7 shows asymptote code and the ﬁgure it produces. In short, it is possible to concisely specify many visual mathematics problems with code, sidestepping the complexity of multi-modal models.


AMPS Examples. We show concrete examples from AMPS in Figure 8. AMPS is a mixture of examples from Khan Academy and our 100 Mathematica modules.

Contrasting AMPS and DeepMind Mathematics. AMPS has several hundred exercise types or modules (Khan Academy has 693 modules and Mathematica has 100), while DeepMind mathematics (DM) has only a few dozen. We show all Khan Academy modules in Figures 12 to 15. Most DM exercises increase the diversity of problems by simply having a wide range of coefﬁcients and constants. For example, its derivatives module exclusively covers polynomial derivatives with wide-ranging coefﬁcients, while ours covers mixtures of dozens of major analytic functions. DM opts not to cover concepts and subjects such as logarithms and geometry, unlike AMPS. While DM is formatted in plaintext, AMPS is formatted in LATEX. Finally, while DM solely has ﬁnal answers, all 693 Khan Academy modules and 37 of our Mathematica modules have full step-by-step solutions.

##### A.4 Difﬁculty Analysis

We break down MATH accuracy by difﬁculty levels. In Figure 9, we observe that human difﬁculty and machine difﬁculty track each other. In Figure 10, we ﬁnd that accuracy can vary by level and subject substantially. Finally, in Figure 11a and Figure 11b, we analyze the relation between accuracy and problem and solution length, and ﬁnd that problems with long questions or ground truth solutions indeed tend to be more difﬁcult than problems with short questions or solutions.

##### A.5 Results with the BART Architecture

We use BART (Lewis et al., 2020) to determine whether other existing architectures can improve performance. In the main paper we analyzed the performance of various GPT models, which are unidirectional decoder models. Lewis et al. (2020) introduce BART, which has a bidirectional encoder and unidirectional decoder. While T5 has a similar architecture to BART, its tokenizer removes LATEX symbols, while BART’s tokenizer does not. Hence we use BART in this paper. After pretraining

Example from a Khan Academy module: Problem: In history class, the girl to boy ratio is 9 to 6. If there are a total of 60 students, how many boys are there?

Solution: A ratio of 9 girls to 6 boys means that a set of 15 students will have 9 girls and

- 6 boys. A class of 60 students has 4 sets of 15 students. Because we know that there are 6 boys in each set of 15 students, the class must have 4 groups of 6 boys each. There is a total of 24 boys in history class.


Example Mathematica code that generates practice problems:

In[1]:= For[i=0,i<50000,i++, roundbasis = RandomChoice[{0.8,0.1,0.05,0.05}->{1,1/2,1/3,1/5}]; d1 = RandomInteger[{1,6}]; d2 = RandomInteger[{1,3}]; q=0; p=0; While[q==0, For[j=0,j<d1,j++, q += Round[RandomReal[{-5,5}], roundbasis]*x^j; ]; ]; While[p==0, For[j=0,j<d2,j++, p += Round[RandomReal[{-5,5}], roundbasis]*x^j; ]; ]; p = RandomChoice[{p,Expand[q*p]}]; Export["/amps/mathematica/algebra/polynomial_gcd/"<>ToString[i]<>".txt",

{"Problem:\nFind the greatest common divisor of $"

- <>ToString[TeXForm[p//TraditionalForm]]<> "$ and $"
- <>ToString[TeXForm[q//TraditionalForm]]<>"$.", "Answer:\n$"<>ToString[TeXForm[PolynomialGCD[p,q]//TraditionalForm]]<>"$"}]


]

- Figure 8: A Khan Academy problem and solution, followed by the code for a simple Mathematica module used to generate polynomials GCD problems. These problems are available in AMPS.


BART-Large (0.4B) on AMPS and ﬁne-tuning BART on MATH, we ﬁnd that it obtains 4.9% on MATH’s test set, which is slightly worse than our smallest GPT-2 model. Consequently models with a bidirectional encoder and unidirectional decoder do not yield marked changes in MATH accuracy.

##### A.6 Further Human Evaluation Details

Because MATH requires a strong mathematical background to perform well on, and a long amount of time to solve problems, we were restricted to assessing six human participants and could not rely on crowdsourcing sites such as Amazon Mechanical Turk. All participants are university students studying computer science. Four of the participants are authors on the paper. The other two participants are friends or acquaintances of the authors, as this survey was only to give a rough sense of human-level performance. All participants gave consent to use their name, though we opt not to include it. Participants had one hour to complete the questions, all without using a calculator. Participants were offered remuneration, though they all offered to volunteer to work on the problems. The instructions and questions used are as follows.

“This research study is being conducted by the Steinhardt Group at UC Berkeley. For questions about this study, please contact Dan Hendrycks at hendrycks@berkeley.edu. In this study, you will have sixty minutes to complete twenty mathematics problems, all without using a calculator. We would like to remind you that participation in our study is voluntary and that you can withdraw from the study at any time.”

MATH Accuracy Across Difficulty Levels

16

- GPT-2 (0.1B)

- GPT-2 (1.5B)


14

12

Accuracy (%)

10

8

6

4

2

0

1 2 3 4 5 Difficulty Level

Figure 9: Problems that are more difﬁcult for humans are also more difﬁcult for GPT-2.

MATH Accuracies Across Subject Difficulty Levels

35

- GPT-2 (0.1B)

| |
|---|


- GPT-2 (1.5B)


30

25

Accuracy (%)

20

15

10

- 5


0

1 2 3 4 5 1 2 3 4 5 1 2 3 4 5 1 2 3 4 5 1 2 3 4 5 1 2 3 4 5 1 2 3 4 5

Prealgebra Algebra Number Theory Counting & Probability

Geometry Intermediate Algebra

Precalculus

Figure 10: Accuracy per subject per difﬁculty level.

- 1. A 6-sided die is weighted so that the probability of any number being rolled is proportional to the value of the roll. (So, for example, the probability of a 2 being rolled is twice that of a 1 being rolled.) What is the expected value of a roll of this weighted die? Express your answer as a common fraction.
- 2. The square of 15 is 225. The square of what other number is 225?
- 3. Find the sum of all values of x such that |x − 1| = 7.
- 4. The parabolas deﬁned by the equations y = −x2 − x + 1 and y = 2x2 − 1 intersect at points (a,b) and (c,d), where c ≥ a. What is c − a? Express your answer as a common fraction.
- 5. If a = 8, what is the value of 16 3

√

a2

1 3

?

- 6. Let p(x) be a cubic polynomial such that p(2) = 0,p(−1) = 0,p(4) = 6, and p(5) = 8. Find p(7).
- 7. Let S be the set of complex numbers of the form a + bi, where a and b are integers. We say that z ∈ S is a unit if there exists a w ∈ S such that zw = 1. Find the number of units in S.
- 8. Find the remainder when 1 + 2 + 22 + 23 + ··· + 2100 is divided by 7.
- 9. The length of a rectangle is 3x + 10 feet and its width is x + 12 feet. If the perimeter of the rectangle is 76 feet, how many square feet are in the area of the rectangle?
- 10. A European train compartment has six seats. Four of the seats are broken. Wilhelm needs to ﬁll out a form to indicate that there are broken seats. If he randomly checks off four of the seats in the diagram, what is the probability that he marked the correct seats? Express your answer as a common fraction.
- 11. We have a triangle ABC where AC = 17, BC = 15, and AB = 8. Let M be the midpoint of AB. What is the length of CM?
- 12. If n gives a remainder of 3 when divided by 7, then what remainder does 2n + 1 give when divided by 7?


Accuracy vs. Problem Length

30

Precalculus Level 1

25

20

Accuracy (%)

15

10

5

0

100 150 200 250 Average Problem Length (characters)

(a) Subject accuracy vs problem length. Each point represents a subject at a speciﬁc difﬁculty level. We exclude problems with asymptote ﬁgures. Results are from GPT-2 (1.5B).

Accuracy vs. Solution Length

30

Precalculus Level 1

25

20

Accuracy (%)

15

10

5

0

200 400 600 800 1000 Average Solution Length (characters)

(b) Subject accuracy vs solution length. Each point represents a subject at a speciﬁc difﬁculty level. We exclude problems with asymptote ﬁgures. Results are from GPT-2 (1.5B).

- 13. Our club has 25 members, and wishes to pick a president, secretary, and treasurer. In how many ways can we choose the ofﬁcers, if individual members are allowed to hold 2, but not all 3, ofﬁces?
- 14. Find the minimum possible value of √58 − 42x + 149 − 140 1 − x2

where −1 ≤ x ≤ 1?

- 15. Let a,b, and c be the roots of x3 + 7x2 − 11x − 2 = 0. Find a + b + c.
- 16. Let H be the hyperbola with foci at (±5,0) and vertices at (±3,0), and let C be the circle with center (0,0) and radius 4. Given that H and C intersect at four points, what is the area of the quadrilateral formed by the four points?
- 17. If f(x) = x2 − 2x + 1 and g(x) = √2x + 1 what is the value of f(g(4)) − g(f(3))?

- 18. Find the value of r such that 6r

2−19r−7

2r 7 = 4r − 3.

- 19. For x > 0, the area of the triangle with vertices (0,0),(x,0) and (x,5) is 30 square units. What is the value of x?
- 20. Find the units digit of the following within the indicated number base: 4136 − 2156.


### B Checklist Information

Legal Compliance. We create and collect various mathematics problems to create MATH and AMPS.

AMPS consists of problems generated with Mathematica and Khan Academy code. Mathematica serves as a calculator and does not copyright its numerical answer outputs, in much the same way that other calculators do not copyright computations such as 52 (mod 2). Khan Academy’s exercise framework follows an MIT License. Since we provide attribution, reuse is not restrictive save for attribution requirements.

MATH problems are created by the Mathematical Association of America (MAA). Although we do not commercialize MATH, we should like to demonstrate that we are far from the boundary for action or infringement. For decades, the MAA has not protected its problem IP even from separate organizations which sell MAA problems, such as AoPS. Courts have ruled that this implies the IP rights are permanently forfeited. We raise this point only to demonstrate the extent to which our reuse for research is within the law, because even commercial reuse of MAA problems is within the law and commonplace. Even so, the MATH dataset is not sold and is likely to have no effect on the value

- Khan Academy Modules (1/4): 2 step equations; 2-step addition word problems within 100; 2step subtraction word problems within 100; 2-step word problems; absolute minima and maxima (closed intervals); absolute minima and maxima (entire domain); absolute value equations; absolute value of complex numbers; add and subtract complex numbers; add and subtract matrices; add and subtract polynomials; add and subtract rational expressions; add and subtract rational expressions: factored denominators; add and subtract rational expressions: like denominators; add and subtract rational expressions: unlike denominators; add and subtract vectors; add 1 or 10; add 1s or 10s (no regrouping); add 3 numbers; add and subtract fractions; add and subtract fractions word problems; add and subtract within 20 word problems; add fractions with unlike denominators; add within 10; add within 1000; add within 20; add within 5; adding and subtracting decimals word problems; adding and subtracting in scientiﬁc notation; adding and subtracting negative fractions; adding and subtracting negative numbers; adding and subtracting rational numbers; adding and subtracting decimals word problems; adding and subtracting fractions; adding and subtracting mixed numbers 0.5; adding and subtracting mixed numbers 1; adding and subtracting polynomials; adding and subtracting radicals; adding and subtracting rational expressions 0.5; adding and subtracting rational


- expressions 1; adding and subtracting rational expressions 1.5; adding and subtracting rational
- expressions 2; adding and subtracting rational expressions 3; adding and subtracting rational numbers; adding and subtracting with unlike denominators 5; adding and subtracting with unlike denominators


- 6; adding decimals (hundredths); adding decimals (tenths); adding decimals and whole numbers (hundredths); adding decimals and whole numbers (tenths); adding decimals: thousandths; adding fractions; adding fractions 0.5; adding up to four 2-digit numbers; adding vectors; addition and subtraction word problems; addition and subtraction word problems 2; addition word problems within 100; age word problems; amplitude of sinusoidal functions from equation; analyze concavity; angle addition postulate; angle of complex numbers; approximation with local linearity; arc length; area and perimeter of rectangles word problems; area between two curves; area between two curves given end points; area between two polar curves; area bounded by polar curves; area bounded by polar curves intro; area of a circle; area of parallelograms; area problems; areas of circles and sectors; arithmetic sequences 1; arithmetic sequences 2; arithmetic series; average value of a function; average word problems; basic division; basic multiplication; basic partial derivatives; basic set notation; binomial probability formula; calculating binomial probability; center and radii of ellipses from equation; chain rule capstone; chain rule intro; change of variables: bound; change of variables: factor; circles and arcs; circulation form of green’s theorem; classifying critical points; combinations; combined vector operations; combining like terms; combining like terms with distribution; combining like terms with negative coefﬁcients; combining like terms with rational coefﬁcients; complementary and supplementary angles; complete solutions to 2-variable equations; completing the square; completing the square (intermediate); completing the square (intro); complex numbers from absolute value and angle; complex plane operations; composite exponential function differentiation; composite numbers; conditional statements and truth value; construct exponential models; construct sinusoidal functions; continuity at a point (algebraic); converting between point slope and slope intercept form; converting between slope intercept and standard form; converting decimals to fractions 1; converting decimals to fractions 2; converting decimals to percents; converting fractions to decimals; converting mixed numbers and improper fractions; converting multi digit repeating decimals to fractions; converting multi-digit repeating decimals to fractions; converting percents to decimals; converting recursive and explicit forms of arithmetic sequences; converting recursive and explicit forms of geometric sequences; counting 1; counting 2; cube roots; cube roots 2; cumulative geometric probability; deﬁned and undeﬁned matrix operations; deﬁnite integral as the limit of a riemann sum; deﬁnite integrals of piecewise functions; deﬁnite integrals: common functions; deﬁnite integrals: reverse power rule; degrees to radians; density word problems; dependent probability; derivatives 1; derivatives


of ax and loga x; derivatives of sin(x) and cos(x); derivatives of tan(x), cot(x), sec(x), and csc(x); derivatives of ex and ln(x); determinant of a 2x2 matrix; determinant of a 3x3 matrix; difference of squares; differentiability at a point: algebraic; differential equations: exponential model equations; differentiate integer powers (mixed positive and negative); differentiate polynomials; differentiate products; differentiate quotients; differentiate rational functions; differentiate related functions; differentiating using multiple rules; direct comparison test; direct substitution with limits that don’t exist; direction of vectors; disc method: revolving around other axes; disc method: revolving around

- x- or y-axis; discount, markup, and commission word problems; discount, tax, and tip word problems; disguised derivatives; distance between point and line; distance formula; distributive property with variables; divide by 1; divide by 10; divide by 2; divide by 3; divide by 4; divide by 5; divide by 6; divide by 7; divide by 8; divide by 9; divide complex numbers; divide decimals by whole numbers; ...


Figure 12: Khan Academy modules in our AMPS pretraining dataset (Part 1).

- Khan Academy Modules (2/4): divide fractions by whole numbers; divide mixed numbers; divide polynomials by linear expressions; divide polynomials by monomials (with remainders); divide polynomials by x (no remainders); divide polynomials by x (with remainders); divide polynomials with remainders; divide powers; divide quadratics by linear expressions (no remainders); divide quadratics by linear expressions (with remainders); divide whole numbers by 0.1 or 0.01; divide whole numbers by decimals; divide whole numbers by fractions; divide whole numbers to get a decimal (1-digit divisors); divide whole numbers to get a decimal (2-digit divisors); divide with remainders (2-digit by 1-digit); dividing complex numbers; dividing decimals 1; dividing decimals 2; dividing decimals: hundredths; dividing decimals: thousandths; dividing fractions; dividing fractions word problems; dividing fractions word problems 2; dividing mixed numbers with negatives; dividing negative numbers; dividing polynomials by binomials 1; dividing polynomials by binomials 2; dividing polynomials by binomials 3; dividing positive and negative fractions; dividing positive fractions; dividing rational numbers; dividing whole numbers by fractions; dividing whole numbers by unit fractions; dividing whole numbers like 56/35 to get a decimal; divisibility 0.5; divisibility tests; domain of a function; double integrals with variable bounds; empirical rule; equation of a circle in factored form; equation of a circle in non factored form; equation of a hyperbola; equation of a parabola from focus and directrix; equation of an ellipse; equation of an ellipse from features; equations and inequalities word problems; equations of parallel and perpendicular lines; equations with parentheses; equations with parentheses: decimals and fractions; equations with variables on both sides; equations with variables on both sides: decimals and fractions; equivalent fractions; estimating square roots; evaluate composite functions; evaluate function expressions; evaluate functions; evaluate logarithms; evaluate logarithms (advanced); evaluate logarithms: change of base rule; evaluate piecewise functions; evaluate radical expressions challenge; evaluate sequences in recursive form; evaluating composite functions; evaluating expressions in 2 variables; evaluating expressions in one variable; evaluating expressions with multiple variables; evaluating expressions with multiple variables: fractions and decimals; evaluating expressions with one variable; evaluating expressions with variables word problems; evaluating logarithms; evaluating logarithms 2; expected value; explicit formulas for arithmetic sequences; explicit formulas for geometric sequences; exponent rules; exponential expressions word problems (algebraic); exponential model word problems; exponential vs. linear growth over time; exponents with integer bases; exponents with negative fractional bases; expressing ratios as fractions; expressions with unknown variables; expressions with unknown variables 2; extend arithmetic sequences; extend geometric sequences; extend geometric sequences: negatives and fractions; extraneous solutions to rational equations; factor higher degree polynomials; factor polynomials using structure; factor quadratics by grouping; factor using polynomial division; factor with distributive property (variables); factoring difference of squares 1; factoring difference of squares 2; factoring difference of squares


- 3; factoring linear binomials; factoring polynomials by grouping; factoring polynomials with two variables; factoring quadratics 1; factoring quadratics with a common factor; features of a circle from its expanded equation; features of a circle from its standard equation; features of quadratic functions; ﬁnd area elements; ﬁnd composite functions; ﬁnd critical points; ﬁnd critical points of multivariable functions; ﬁnd inﬂection points; ﬁnd inverses of rational functions; ﬁnd missing divisors and dividends (1-digit division); ﬁnd missing factors (1-digit multiplication); ﬁnd missing number (add and subtract within 20); ﬁnd the inverse of a 2x2 matrix; ﬁnd the missing number (add and subtract within 1000); ﬁnd trig values using angle addition identities; ﬁnding absolute values; ﬁnding curl in 2d; ﬁnding curl in 3d; ﬁnding derivative with fundamental theorem of calculus; ﬁnding derivative with fundamental theorem of calculus: chain rule; ﬁnding directional derivatives; ﬁnding divergence; ﬁnding gradients; ﬁnding inverses of linear functions; ﬁnding partial derivatives; ﬁnding percents; ﬁnding perimeter; ﬁnding tangent planes; ﬁnding the laplacian; ﬁnite geometric series; ﬁnite geometric series word problems; foci of an ellipse from equation; fraction word problems 1; fractional exponents; fractional exponents 2; fractions as division by a multiple of 10; function as a geometric series; function inputs and outputs: equation; function rules from equations; gcf and lcm word problems; general triangle word problems; geometric probability; geometric sequences 1; geometric sequences 2; geometric series formula; graphing points and naming quadrants; graphing systems of equations; greatest common factor; greatest common factor of monomials; higher order partial derivatives; identify composite functions; identify separable equations; identifying numerators and denominators; identifying slope of a line; imaginary unit powers; implicit differentiation; improper integrals; increasing and decreasing intervals; indeﬁnite integrals: ex and 1/x; indeﬁnite integrals: sin and cos; independent probability; inequalities word problems; inﬁnite geometric series; integer sums; integral test; integrals and derivatives of functions with known power series; integrals in spherical and cylindrical coordinates; ...


Figure 13: Khan Academy modules in AMPS (Part 2).

- Khan Academy Modules (3/4): integrate and differentiate power series; integrating trig functions; integration by parts; integration by parts: deﬁnite integrals; integration using completing the square; integration using long division; integration using trigonometric identities; integration with partial fractions; intercepts from an equation; interpret quadratic models; interval of convergence; inverse of a 3x3 matrix; inverses of functions; iterated integrals; jacobian determinant; l’hopital’s rule (composite exponential functions); l’hopital’s rule: 0/0; l’hopital’s rule: ∞/∞; lagrange error bound; least common multiple; limits at inﬁnity of quotients; limits at inﬁnity of quotients with square roots; limits


- at inﬁnity of quotients with trig; limits by direct substitution; limits by factoring; limits of piecewise functions; limits of trigonometric functions; limits using conjugates; limits using trig identities; line integrals in vector ﬁelds; linear equation and inequality word problems; linear equations with unknown coefﬁcients; linear equations word problems; linear models word problems; logical arguments and deductive reasoning; maclaurin series of sin(x), cos(x), and ex; make 10; manipulate formulas; markup and commission word problems; matrix addition and subtraction; matrix dimensions; matrix elements; matrix equations: addition and subtraction; matrix equations: scalar multiplication; matrix row operations; matrix transpose; mean, median, and mode; midline of sinusoidal functions from equation; midpoint of a segment; miscellaneous; model with one-step equations and solve; modeling with multiple variables; modeling with sinusoidal functions; modeling with sinusoidal functions: phase shift; motion along a curve (differential calc); motion problems (differential calc); motion problems (with integrals); multi-digit addition; multi-digit division; multi-digit multiplication; multi-digit subtraction; multi-step linear inequalities; multi-step word problems with whole numbers; multiplication and division word problems; multiplication and division word problems (within 100); multiply and divide complex numbers in polar form; multiply and divide powers (integer exponents); multiply and divide rational expressions (advanced); multiply binomials; multiply binomials by polynomials; multiply binomials intro; multiply by 0 or 1; multiply by 2 and 4; multiply by 5 and 10; multiply by tens word problems; multiply complex numbers; multiply decimals (1 and 2-digit factors); multiply decimals (up to 4-digit factors); multiply difference of squares; multiply matrices; multiply matrices by scalars; multiply mixed numbers; multiply monomials; multiply monomials by polynomials; multiply powers; multiply unit fractions and whole numbers; multiply whole numbers and decimals; multiplying and dividing in scientiﬁc notation; multiplying a matrix by a matrix; multiplying a matrix by a vector; multiplying and dividing complex numbers in polar form; multiplying and dividing negative numbers; multiplying and dividing rational expressions 1; multiplying and dividing rational


- expressions 2; multiplying and dividing rational expressions 3; multiplying and dividing rational expressions 4; multiplying and dividing rational expressions 5; multiplying and dividing scientiﬁc notation; multiplying by multiples of 10; multiplying complex numbers; multiplying decimals like 0.847x3.54 (standard algorithm); multiplying decimals like 2.45x3.6 (standard algorithm); multiplying decimals like 4x0.6 (standard algorithm); multiplying expressions 1; multiplying fractions; multiplying fractions by integers; multiplying mixed numbers 1; multiplying negative numbers; multiplying polynomials; multiplying polynomials 0.5; multiplying positive and negative fractions; multiplying rational numbers; multivariable chain rule; multivariable chain rule intro; negative exponents; new operator deﬁnitions 1; new operator deﬁnitions 2; normal form of green’s theorem; number of solutions of quadratic equations; one step equations; one step equations with multiplication; one-step addition and subtraction equations; one-step addition and subtraction equations: fractions and decimals; one-step equations with negatives (add and subtract); one-step equations with negatives (multiply and divide); one-step inequalities; one-step multiplication and division equations; one-step multiplication and division equations: fractions and decimals; operations with logarithms; order of operations; order of operations (no exponents); order of operations 2; order of operations challenge; order of operations with negative numbers; ordered pair solutions to linear equations; p-series; parametric curve arc length; parametric equations differentiation; parametric velocity and speed; partial derivatives of vector valued functions; partial fraction expansion; partial sums intro; particular solutions to differential equations; particular solutions to separable differential equations; parts of complex numbers; percent problems; perfect squares; period of sinusoidal functions from equation; permutations; permutations and combinations; planar motion (differential calc); planar motion (with integrals); polar and rectangular forms of complex numbers; polynomial special products: difference of squares; polynomial special products: perfect square; positive and zero exponents; positive exponents with positive and negative bases; potential functions; power rule (negative and fractional powers); power rule (positive integer powers); power rule (with rewriting the expression); powers of complex numbers; powers of fractions; powers of powers; prime numbers; probabilities of compound events; probability 1; probability in normal density curves; probability of “at least one” success; probability with permutations and combinations; problems involving deﬁnite integrals (algebraic); ...


Figure 14: Khan Academy modules in AMPS (Part 3).

- Khan Academy Modules (4/4): properties of exponents (rational exponents); proportion word problems; pythagorean identities; pythagorean theorem; quadratic word problems (factored form); quadratic word problems (standard form); quadratic word problems (vertex form); quadratics by factoring; quadratics by taking square roots; radians and degrees; radians to degrees; radical equations; radius, diameter, and circumference; range of a function; rate conversion; rate problems; rate problems 2; rates of change in other applied contexts (non-motion problems); rates with fractions; ratio test; ratio word problems; reciprocal trig functions; recursive formulas for arithmetic sequences; recursive formulas for geometric sequences; regroup when adding 1-digit numbers; relate addition and subtraction; related rates (advanced); related rates (multiple rates); related rates (pythagorean theorem); related rates intro; relationship between exponentials and logarithms; relative minima and maxima; remainder theorem; remainder theorem and factors; removable discontinuities; represent linear systems with matrices; represent linear systems with matrix equations; reverse power rule; reverse power rule: negative and fractional powers; reverse power rule: rewriting before integrating; reverse power rule: sums and multiples; rewriting decimals as fractions challenge; right triangle trigonometry word problems; roots of decimals and fractions; sample and population standard deviation; scalar matrix multiplication; scalar multiplication; scientiﬁc notation; secant lines and average rate of change; secant lines and average rate of change with arbitrary points; secant lines and average rate of change with arbitrary points (with simpliﬁcation); second derivative test; second derivatives (implicit equations); second derivatives (parametric functions); second derivatives (vector-valued functions); segment addition; separable differential equations; signiﬁcant ﬁgures; simplify roots of negative numbers; simplify square roots (variables); simplify square-root expressions; simplifying expressions with exponents; simplifying fractions; simplifying radicals; simplifying radicals 2; simplifying rational expression with exponent properties; simplifying rational expressions 2; simplifying rational


- expressions 3; simplifying rational expressions 4; sinusoidal models word problems; slope-intercept from two points; solid geometry; solutions to quadratic equations; solutions to systems of equations; solve equations using structure; solve exponential equations using exponent properties; solve exponential equations using exponent properties (advanced); solve exponential equations using logarithms: base-10 and base-e; solving equations in terms of a variable; solving for the x intercept; solving for the


- y intercept; solving proportions; solving quadratics by completing the square 1; solving quadratics by completing the square 2; solving quadratics by factoring; solving quadratics by factoring 2; solving quadratics by taking the square root; solving rational equations 1; solving rational equations 2; special right triangles; square and cube challenge; square roots of perfect squares; standard deviation; standard deviation of a population; stokes’ theorem; substitution with negative numbers; subtract decimals (hundredths); subtract decimals and whole numbers (hundredths); subtract within 10; subtract within 1000; subtract within 20; subtract within 5; subtracting decimals (tenths); subtracting decimals and whole numbers (tenths); subtracting decimals: thousandths; subtracting fractions; subtracting fractions with common denominators; subtracting fractions with unlike denominators; subtraction word problems within 100; summation notation intro; sums of consecutive integers; surface integrals to ﬁnd surface area; switching bounds on double integrals; symbols practice: the gradient; systems of equations; systems of equations with elimination; systems of equations with simple elimination; systems of equations with substitution; systems of equations word problems; tangents to polar curves; taylor and maclaurin polynomials; the derivative and tangent line equations; the divergence theorem; the fundamental theorem of calculus and deﬁnite integrals; the hessian matrix; translate one-step equations and solve; trigonometry 0.5; trigonometry 1; trigonometry 1.5; trigonometry 2; triple integrals; two-step equations; two-step equations with decimals and fractions; two-step equations word problems; u-substitution: deﬁnite integrals; u-substitution: indeﬁnite integrals; unit circle; unit vectors; use arithmetic sequence formulas; use geometric sequence formulas; use the properties of logarithms; use the pythagorean identity; using the mean value theorem; using the quadratic formula; using units to solve problems; variance; vector word problems; vector-valued functions differentiation; verify solutions to differential equations; vertex of a parabola; volume word problems; volumes with cross sections: squares and rectangles; volumes with cross sections: triangles and semicircles; washer method: revolving around other axes; washer method: revolving around x- or y-axis; word problems with “more” and “fewer” 2; write common decimals as fractions; write common fractions as decimals; write decimals as fractions; write differential equations; write equations of parallel and perpendicular lines; writing basic expressions with variables; writing basic expressions word problems; writing expressions; writing expressions 2; writing expressions with variables; writing expressions word problems; writing functions with exponential decay; writing linear functions word problems; writing proportional equations; writing proportions; wrong statements in triangle proofs;
- z scores 1; z scores 2; z scores 3; zero product property. Figure 15: Khan Academy modules in AMPS (Part 4).


of the original problems. This analysis would be pertinent in the hypothetical situation where Fair Use doctrine did not exist, but MATH and AMPS are covered by Fair Use.

For MATH and AMPS, we abide by Fair Use §107: “the fair use of a copyrighted work, including such use by ... scholarship, or research, is not an infringement of copyright”, where fair use is determined by “the purpose and character of the use, including whether such use is of a commercial nature or is for nonproﬁt educational purposes” and “the effect of the use upon the potential market for or value of the copyrighted work.”

Dataset Intended Uses. We document the dataset within the paper and note that the dataset and code for reproducing results is available at https://github.com/hendrycks/apps. We do not intend for this dataset to train models that help students cheat on mathematics exams. We intend for others to use this dataset in order to better forecast reasoning capabilities.

Author Statement and License. We bear all responsibility in case of violation of rights. The MATH data, AMPS data, and our open source code are under an MIT license.

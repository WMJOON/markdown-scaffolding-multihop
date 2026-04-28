---
case_id: paper__grpo_dpo_2510_00977
source_type: paper
title: It Takes Two: Your GRPO Is Secretly DPO
url: https://arxiv.org/pdf/2510.00977
resolved_url: https://arxiv.org/pdf/2510.00977
status_code: 200
fetched_at: 2026-04-24T02:15:23+00:00
doc_type: pdf
---

## It Takes Two: Your GRPO Is Secretly DPO

Yihong Wu* 1 Liheng Ma* 2 3 Lei Ding4 Muzhi Li5 Xinyu Wang2 Kejia Chen6 Zhan Su1 Chenyang Huang7 8 Zhanguang Zhang9 Derek Li9 Yingxue Zhang9 Jian-Yun Nie1 Mark Coates2

# arXiv:2510.00977v2 [cs.LG] 30 Jan 2026

### Abstract

Group Relative Policy Optimization (GRPO) has emerged as a prominent reinforcement learning algorithm for post-training Large Language Models. Different from critic-based methods such as PPO, GRPO estimates the advantage function using group-level statistics to reduce the variance of policy gradient estimators. While the prevailing view attributes GRPO’s effectiveness to large group sizes for accurate advantage estimation, we propose a different perspective. In this work, we demonstrate that the efficacy of GRPO stems from its implicit contrastive objective in the optimization, which helps reduce variance via the control variate method. This perspective establishes a fundamental connection between GRPO and DPO, wherein group size influences only the Monte Carlo estimators of the contrastive objective. To validate this, we investigate the minimal two-rollout case (2-GRPO), a configuration permissible under the contrastive framework but typically considered insufficient for baseline estimation. We provide a rigorous theoretical analysis of 2-GRPO and empirically validate its effectiveness: 2-GRPO retains 98.1% of the performance of 16-GRPO, while requiring only 12.5% of the rollouts and 21% of the training time. This study offers a new perspective for future algorithm design in LLM post-training.

### 1. Introduction

Reinforcement Learning (RL) has emerged as a central paradigm for the post-training of Large Language Models (LLMs). Two critical functions are aligning model outputs with human intent via RL with Human Feed-

1Universit´e de Montr´eal 2McGill University 3Mila - Quebec AI Institute 4University of Manitoba 5The Chinese University of Hong Kong 6Zhejiang University 7University of Alberta 8Alberta Machine Intelligence Institute (Amii) 9Huawei Noah’s Ark Lab. Correspondence to: Yihong Wu <yihong.wu@umontreal.edu>, Liheng Ma <liheng.ma@mail.mcgill.ca>.

Preprint. February 2, 2026.

back (RLHF) (Ouyang et al., 2022) and enhancing reasoning capabilities through RL with Verifiable Rewards (RLVR) (DeepSeek-AI, 2025). Among recent advances, Group Relative Policy Optimization (GRPO) (Shao et al., 2024) is a prominent critic-free variant of Proximal Policy Optimization (PPO) (Schulman et al., 2017). Diverging from PPO, which relies on an auxiliary critic network for variance reduction, GRPO estimates the advantage function by sampling a group of responses (rollouts) for a single prompt and normalizing their rewards relative to the group statistics. This design eliminates the memory and computational overhead of the value network while maintaining strong performance across various reasoning tasks.

Conventional intuition suggests that GRPO’s efficacy is strongly correlated with its group size, grounded in the premise that larger sample sizes yield more accurate advantage estimates and lead to stronger post-trained LLMs. However, this intuition overlooks the specific construction of the group-relative gradient estimator in GRPO. First, we demonstrate that GRPO intrinsically functions as contrastive learning (Chopra et al., 2005), sharing the same underlying mechanism as Direct Preference Optimization (DPO) (Rafailov et al., 2023). Second, we reveal that the group of rollouts serves primarily to pair contrastive samples, rather than to enhance estimation accuracy. By leveraging the strong correlation within these pairs, GRPO, as a control variate method (Johnson & Zhang, 2013), effectively reduces the variance of the gradient estimator. This finding challenges the prevailing view and opens a new design space for RL algorithms in LLM post-training.

Following the contrastive perspective, we show that the GRPO objective is a Monte Carlo estimator to approximate the true contrastive gradients. The sample size primarily affects the variance of the Monte Carlo estimator, while the approximation itself remains unbiased. This observation provides a theoretical basis for reducing the computational cost generating large numbers of rollouts, without altering the fundamental optimization behavior of GRPO. Consequently, we propose the minimal two-rollout setting (2-GRPO), a configuration previously regarded as inadequate for reward normalization (Student, 1908), yet well aligned with the contrastive learning interpretation.

We provide a theoretical analysis of the properties of 2GRPO and empirically evaluate its effectiveness and efficiency across a diverse set of models and tasks. Experimental results showcase that 2-GRPO attains performance comparable to 16-GRPO, while significantly reducing training time. The effectiveness of 2-GRPO strongly supports

- our central hypothesis that the power of GRPO arises primarily from its contrastive formulation, rather than from accurate advantage estimation.


### 2. Preliminary

#### 2.1. Problem Setting and Notation

Our work focuses on RL-based post-training of LLMs for reasoning capabilities. The learning objective is to maximize the expected reward over the trajectory space:

θ(·|q)[r(τ)], (1)

J (θ) = Eq∼QEo∼π

where πθ denotes the policy model – an LLM with parameters θ; and Q is the set of prompts, each consisting of a question and necessary instructions1. Given an input prompt q ∈ Q, the model generates the i-th response oi = (oi,1,...,oi,T), where oi,t is the token generated at step t ∈ [0,T] and oi,<t denotes the sequence of preceding tokens. A trajectory τ = (q,o) ∈ T is defined as a concatenation of a prompt and its corresponding LLM-generated response. In current RL post-training, the reward function r : T → R is typically defined at the trajectory level. Following previous work, we mainly focus on the setting of verifiable rewards, where the responses can be verified as correct (r = 1) or incorrect (r = 0).

#### 2.2. Advantage Estimation and Variance Reduction

As an essential policy gradient method, Vanilla Policy Gradient (VPG) (Williams, 1992) aims to maximize the gradient estimator:

 ri

  .

|oi|

∇θJ (θ) = E

∇θ log πθ(oi,t|oi,<t,q)

oiq∼∼Qπθold

t=0

(2) where ri is the reward of (q,oi).

Advantage Estimation Although effective, VPG usually suffers from high gradient variance and training instability. Therefore, subsequent works (Schulman et al., 2015;

- 2017) utilize advantage estimates (Baird, 1993) to reduce the variance of the policy gradient estimator:


##### Ai,t = ri − b(q), (3)

1Throughout this paper, we use the terms “prompt” and “question” interchangeably.

where Ai,t is a token-level advantage estimate and b(q) is an additional critic network that estimates the reward baseline independent of the sampled actions. A dominant algorithm is Proximal Policy Optimization (PPO) (Schulman et al., 2017):

|oi|

1 |oi|

min{Ai,tρi,t,Ai,tCϵ(ρi,t)}, (4)

J (θ) = E

oiq∼∼Qπθold

t=1

where importance sampling and clipping are introduced to further stabilize training2:

πθ(oi,t | oi,<t,q) πθ

(5)

ρi,t =

(oi,t oi,<t,q)

old

is the policy used to generate trajectories, while πθ denotes the current policy being optimized. The term Cϵ(x) represents the clipping function within the interval [1 ϵ,1 + ϵ].

in which, πθ

old

To eliminate the substantial computational overhead and memory demands of the critic network, several studies (Li et al., 2024; Ahmadian et al., 2024; Shao et al., 2024) propose estimating the baseline without a critic network. Specifically, as a prevailing technique, GRPO estimates the advantage in PPO using the reward statistics from a group of generated responses:

ri − mean(r) std(r) + ϵ

, (6)

Ai,t =

where ri is the reward for response oi given query q, and r denotes the vector of rewards for G sampled responses associated with q. A small constant ϵ is included to ensure numerical stability. GRPO computes the averaged policy gradient over a group, rather than a single rollout as in PPO.

#### 2.3. Variance Reduction of Policy Gradient Estimates

Given a prompt, consider the random variable (r.v.) of the reward r (which can be replaced by the advantage a) and the r.v. of the policy gradient g (corre-

|oi| t=0 ∇θ log πθ(oi,t|oi,<t,q) in VPG or

sponding to |o1

i

|oi| t ∇θρi,t in PPO/GRPO).3 Since E[g] = 0 over all

1 |oi|

potential actions, the variance of the product of these r.v.’s can be written as:

Var(r · g) = Var(g) Var(r) + (E[r])2

. (7)

+ Cov(r2,g2) − (Cov(r,g))2

Interaction term

The interaction term is typically dominated by outliers and can be ignored when importance sampling and clipping are

- 2In this work, we omit the KL-divergence term from the discussion, as it primarily serves as a regularizer and does not alter the core optimization behavior.
- 3See Appx. B.3 for more discussion.


applied, as the gradient is bounded in a small region. 4 Previ-

- ous work (Baird, 1993; Schulman et al., 2015; 2016; 2017) shows that replacing raw rewards with advantage functions effectively reduces variance, leading to more stable and improved RL optimization.


#### 2.4. Contrastive Loss for Sequences and DPO

The contrastive loss objective (Chopra et al., 2005) has been a powerful learning paradigm in (self-)supervised learning, ranging from 1-vs-1 (one positive and one negative) objectives (Rendle et al., 2009) to 1-vs-N (Oord et al.,

- 2018) and N-vs-M variants (Frosst et al., 2019). To facilitate our analysis in the context of LLMs, we formalize the contrastive loss objective for sequences.


Definition 2.1 (Contrastive Loss for Sequences). Let πθ be a probabilistic model and D be a data distribution. Consider an anchor sequence x ∼ D, and let D+(· | x) and D (· | x) denote the conditional distributions for positive and negative samples, respectively. Let yt denote the t-th token of sequence y. A differentiable loss function L is defined as contrastive if its gradient satisfies the following form:

|y+|

c+t ∇θπθ(yt+ y<t+ ,x)

∇θL = − E

##### E

x∼D

y+∼D+

t=1

|y |

c−t ∇θπθ yt−|y<t− ,x ,

− E

y−∼D−

t=1

(8)

where c+t and c−t are token-level coefficients depending on the specific loss design.

We adopt token-level coefficients for generality, as sequencelevel coefficients can be recovered as a special case. Furthermore, the number of positive (N) and negative (M) samples of each data point may vary depending on the specific designs, serving as a Monte Carlo estimator to approximate the true gradient in Eq. (8).

#### Direct Preference Optimization (DPO) (Rafailov et al.,

2023) is a dominant offline RLHF algorithms for LLMs:

π(o+|q) π(o−|q)

, (9)

##### LDPO = − E

log σ β log

(q,o ,o )∼DDPO

θ(·|q)

where π(·|q) ≜ π

πref(·|q) and the question and response sequences (q,o+,o−) ∼ DDPO are from human-annotated preference data. It is easy to show that DPO is a 1-vs-1 contrastive learning. We provide Lemma B.1 and its proof in Appx. B.4 for a reference. When extending offline RL to the online setting, the log-likelihood term is typically replaced by its importance-sampling counterpart to improve training stability, as in the transition from VPG (Williams, 1992) to PPO (Schulman et al., 2017).

4The comprehensive related work is provided in Appx. A.

### 3. Bridging GRPO and DPO with Contrastive Learning

At first glance, the objectives of GRPO and DPO appear distinct for different RL settings. We show that, via the bridge of contrastive learning, the gradient forms of GRPO and DPO share the same underlying mechanism. This finding provides a new theoretical analysis (Sec. 4) and motivates a more efficient yet effective algorithm (Sec. 5).

#### 3.1. GRPO: N-vs-M Contrastive Learning

We demonstrate that GRPO effectively functions as a dynamic N-vs-M contrastive learning framework, where the group size G = N +M is fixed, but the specific values of N (positive samples) and M (negative samples) are dynamic based on the sampled responses. Let G+q and G−q denote the counts of correct and incorrect trajectories, respectively. The GRPO objective function can be formulated as:

JGRPO(θ,G) = E[q∼Q;{o+j ,o−k }Gj,k∼πθold(·|q)]

|oj |

Gq

πθ(o+j,t|o+j,<t,q) πθ

1 G+q

1 |o+j |

Cϵ

VarG(q)

(o+j,t|o+j,<t,q) positive

old

t=1

j=1

G−q

|o−k |

πθ(o−k,t|o−k,<t,q) πθ

1 G−q

1 |o−k |

Cϵ−

−

,

(o−k,t|o−k,<t,q) negative

old

t=1

k=1

(10) where o+j and o−k denote rollouts with correct and incorrect outcomes, respectively. Denoting pˆθ

old,q = G+q /G, the term VarG(q) = (1 − pˆθ

old,q is the empirical variance of the G sampled trajectories from the true Bernoulli(pold,q) under the RLVR setting.5 For simplicity, we denote the

old,q)ˆpθ

upper and lower clippings as Cϵ+(x) = min[x,1 + ϵ] and Cϵ−(x) = max[x,1 − ϵ , respectively.

The formulation in Eq. (10) provides the foundation for the following proposition, with a proof provided in Appendix B.2. Despite the sophisticated algorithm design of GRPO, this proposition unveils its contrastive nature.

Proposition 3.1. The maximization of the GRPO objective is equivalent to the minimization of an N-vs-M contrastive loss estimator.

#### 3.2. GRPO is Secretly doing DPO

Given the inherent contrastive nature of DPO and the above analysis of GRPO, we can recognize that GRPO and DPO optimize the same underlying objective: increasing the likelihood of preferred trajectories relative to non-preferred

5In subsequent parts, we omit the subscript θold of p for brevity.

ones. Their differences arise primarily from the training regimes (online v.s. offline) and, consequently, from how preference signals are obtained.

Importance Sampling v.s. Log-likelihood: Following most autoregressive language models, DPO describes the objective function with the log-likelihood term log π(o+|q) − log π(o−|q). For online RL, GRPO utilizes the importance sampling technique, which is a surrogate objective of the log-likelihood. In the gradient form of objective, the importance sampling term is equivalent to the log-likelihood term with correction coefficients. We provide a detailed discussion in Appx. B.3.

Number of Positive and Negative Examples. DPO adopts a 1-vs-1 contrastive formulation, where each positive– negative pair is predefined by an offline, human-annotated preference dataset. In contrast, GRPO operates in an online RL setting, where the responses are generated online by the policy given a prompt and the preferences are given by the reward model. Consequently, GRPO inherently induces a dynamic N-vs-M contrastive objective within a group of G = N + M trajectories, where the numbers of positive and negative samples are dynamic based on the rewards of sampled responses. If a trajectory group fails to form a valid contrastive set (i.e., all trajectories have positive or negative rewards) the group contributes no learning signal due to zero-valued advantages in Eq. (6).

Note that varying the number of positive and negative samples (e.g., 1-vs-1 or N-vs-M) merely alters the sample size used in the Monte Carlo estimators to approximate the underlying positive and negative gradients defined in Eq. (8). These connections reveal that GRPO is de facto performing direct preference optimization in an online RL setting by explicitly constructing a contrastive objective.

### 4. Rethinking Group in GRPO

While GRPO is typically characterized as a critic-free approximation of PPO, we argue that this advantage-based perspective obscures its true mechanism. In this section, we re-interpret variance reduction of GRPO via the contrastive objective. We demonstrate that GRPO’s efficacy arises from a group-based gradient estimator that implicitly minimizes variance through contrastive pairs.

#### 4.1. Limitation of Advantage Estimate for GRPO

Variance reduction is a central challenge in policy gradient methods, where the stochasticity of environmental returns necessitates the use of a baseline (Schulman et al., 2016; Li et al., 2024). Previous approaches, such as PPO, rely on a learned value function Vϕ(s) to serve as a low-variance proxy for the expected return, thereby isolating the advantage A(s,a) = r − Vϕ(s). The efficacy of this method

hinges on the critic’s ability to generalize and provide a stable baseline across diverse states.

In contrast, GRPO eschews a learned critic in favor of a Monte Carlo approximation, estimating the baseline using the mean reward of a group of G sampled outputs: b ≈ G1 Gi=1 ri. From a classical estimation perspective, this approach is theoretically suboptimal, as the group mean fluctuates dynamically based on the specific stochastic realization of the current batch. This has led to the common belief that GRPO necessitates a large group size G. However, this suboptimal nature is inevitable.

Indeed, empirical results contradict this intuition (Hu, 2025; DeepSeek-AI, 2025; Sheng et al., 2025), showing that GRPO performs even better in reasoning tasks compared to other baselines with more accurate baseline estimation, e.g., PPO, ReMax (Li et al., 2024), and RLOO (Ahmadian et al., 2024). This suggests that treating the group mean merely as a “poor man’s critic” overlooks the benefit of the well-designed group-based gradient estimator.

#### 4.2. Variance Reduction via Contrastive Objective

To clarify the role of grouping in GRPO, we offer an alternative explanation for its variance reduction mechanism. We argue that GRPO’s effectiveness does not arise from accurate advantage estimation, but from constructing groups that induce a contrastive learning signal. Groups that fail to form such contrasts are discarded in GRPO. For analytical clarity, we focus on the RLVR setting.

Consider a generalized form of the gradient within a group:

G

1 G

(ri − b)gi , (11)

gˆ =

i=1

where gi := ∇θπθ(oi|q) and b is a reward baseline. By separating the samples into positive and negative subgroups, this form can be rewritten as:

1 G

gˆ =

G+(1 − b)g¯+ − G−bg¯− , (12)

−

+

where g¯+ := G1+ G

j=1 gj+ and g¯ := G1− G

j=1 gj− represent the average gradients for the positive and negative groups, respectively. We interpret g¯ as the virtual positive gradient and g¯− as the virtual negative gradient. The terms G+(1 − b) and G−b act as weighting coefficients for these positive and negative components.

Moreover, gˆ ∝ (g¯+−cg¯−), where c = G+G(1−bb). In GRPO, the baseline b G

+

G , allowing the estimator being simplified to a proportional contrastive form: gˆ ∝ (g¯+ − g¯−). We demonstrate that this contrastive gradient formulation functions as a control variate method, where the coefficients serve to control the variance of the estimator.

Proposition 4.1. Let πθ denote the policy model. Let

- o+ ∼ πθ+(·|q) and o ∼ πθ−(·|q) denote random variables representing a positive sample and a negative sample, respectively. Let g+ = ∇θ log πθ(o+|q), g− = ∇θ log πθ(o−|q) and ρ denote the correlation coefficient
- of g+ and g−. If Cov(g+,g−) > 0 and 0 ≤ c ≤


+,g−)

2Cov(g

Var(g−) , then Var(g+ − cg−) ≤ Var(g+). Specifically, if c = Cov(g

+,g )

Var(g−) , then Var(g+ − cg−) = 1 − ρ2 Var(g+), (13)

where Var(·) and Cov(·,·) denotes the corresponding traces of var/cov matrices for gradient vectors.

This proposition (proof in Appx. B.5) shows that, when the coefficient c lies within an appropriate range, the variance of the gradient estimator can be reduced. This result follows directly the control variate method, a variance reduction technique widely used in Monte Carlo estimation and stochastic gradient optimization (Johnson & Zhang, 2013).

A key implication of Proposition 4.1 is that the degree of variance reduction depends on the correlation between positive and negative samples. In LLM post-training, the positive sample o+ and the negative sample o− are generated by the same model conditioned on the same prompt q, which typically induces a nontrivial correlation between them. This proposition also indicates that GRPO may be ineffective when samples are generated independently at random, such as in RL training from scratch.

### 5. Minimalist RL: 2-GRPO

Building on our contrastive interpretation of GRPO, we view the positive and negative examples within a group as the samples used for Monte Carlo estimation of the true positive and negative gradients. Motivated by the fact that Monte Carlo integration remains unbiased regardless of sample size, we introduce GRPO with a group size of two (2-GRPO). This approach is the minimum of GRPO capable of producing a contrastive effect. It substantially reduces computational overhead by minimizing redundant rollouts without introducing bias into the gradient estimation. In this section, we also provide rigorous theoretical analyses to justify the validity of 2-GRPO.

- 5.1. Introduce 2-GRPO 2-GRPO is formally defined as:


JGRPO(θ, G) = E[q∼Q;(o1,o2)∼πθold(·|q)]

|o1|

πθ(o1,t|o1,<t, q) πθold(o1,t|o1,<t, q)

- 1

- 2


1 |o1|

Cϵ+

(r 1 ̸= r2) ·

t=1

|o2|

πθ(o2,t|o2,<t, q) πθold(o2,t o2,<t, q)

1 o2|

Cϵ−

−

,

t=1

(14)

For the simplicity of notation, without loss of generality, we assume o1 to be the positive sample and o2 to be the negative sample when their rewards are not the same. In other words, the advantage estimation of 2-GRPO is a flawed normalization: A+ = 1,A− = −1 for a positive-negative pair and A+ = A− = 0 otherwise. This formulation directly constructs an online RL variant of direct preference optimization as in DPO.

According to the prevailing understanding of GRPO, this configuration is infeasible (See Appx. B.1). A group size of two is typically expected to fail in reward baseline estimates (high sensitivity to individual realizations) and in advantage normalization (statistically degenerate). However, this is completely feasible from our contrastive interpretation.

#### 5.2. Advantage Shaping in Stochastic Optimization

Standard GRPO relies on the empirical success rate pˆq to estimate the true correctness probability pq for advantage assignment, relying on larger group sizes for accuracy. While this mechanism appears degenerate in 2-GRPO, we show that, through the lens of stochastic optimization, 2-GRPO implicitly estimates the advantage.

Proposition 5.1. Given a constant p ∈ (0,1) and a small positive constant ϵ, we consider two scenarios below:

- • Case 1: Consider X1,··· ,X2N i.i.d.∼ Bernoulli(p). Let

Yi = X

i−µˆ

σˆ+ϵ , where µˆ = 21N 2i=1N Xi and σˆ = 2N i=1 (Xi − µˆ)2. Then, it follows that

- 1

- 2N


lim

ϵ→0

lim

N→∞

E[Yi|Xi = x] =

x − p p(1 p)

. (15)

- • Case 2: Consider N pairs of (Xi,1,Xi,2) with each


Xi,j i.i.d.∼ Bernoulli(p). Let Yi,j Xσi,jˆ −µˆi

i+ϵ , where

µˆi = 12(Xi,1 + Xi,2) and σˆi = 12 2j=1(Xi,j − µˆi)2. Then, it follows that

E[Yi,j|Xi,j = x] = x − p. (16)

lim

lim

ϵ→0

N→∞

Term limϵ→0,N→∞ E[Yi,j|Xi,j = x] differs from limϵ→0,N→∞ E[Yi|Xi = x] by a scaling factor √ 1

.

p(1−p)

In Proposition 5.1 (proof in Appx. B.6), Case 1 corresponds to regular GRPO with sufficiently large group size. In this case, E[Yi|Xi = 1] and E[Yi|Xi = 0] are, respectively, the advantage estimates of positive and negative trajectories given a prompt, dependent on the success probability pq. A large G will lead to a better estimate of the success probability pq. Case 2 corresponds to 2-GRPO, where E[Yi,j|Xi,j = 1] and E[Yi,j|Xi,j = 0] are advantage estimates, which are also dependent on the success rate pq, amortizing over multiple stochastic updates.

2-GRPO produces advantage estimates that differ from standard GRPO solely by a scaling factor; this factor is effectively a design choice. Whether such a scaling is beneficial remains an open question (Li et al., 2025).

#### 5.3. Variance of Gradient Estimate in Mini-Batch

Beyond the inherent variance reduction mechanisms of PPO and GRPO, it is generally understood that using a larger group of rollouts yields a lower-variance policy gradient estimate. However, this perspective overlooks the practicalities of mini-batch optimization. In this section, we analyze the practical gradient variance within a mini-batch setting. To facilitate this discussion, we focus strictly on the optimization phase and treat the sampled rollouts as fixed training data for notational simplicity.

Firstly, we can provide a definition of gradient variance, followed by a lemma for empirical gradient estimation.

Definition 5.2 (Variance Gradient Estimate in Mini-Batch). Without loss of generality, let {xi}Bi=1 be a batch of B random variables (r.v.’s), where each xi is i.i.d. x ∼ D, and let g(xi) = ∇θLθ(xi) denote the gradient of Lθ(xi) w.r.t. θ. Define the empirical batch gradient gˆB = B1 Bi=1 g(xi). Note that g(xi) and gˆB are dependent r.v.’s of xi and {xi}Bi=1, respectively. We denote the expectation of the gradient g¯ = Ex∼D[g(x)]. The variance of the gradient estimate over the batch is then defined as:

i}Bi (gˆB − g¯)2 . (17)

i}Bi (gˆB) = E{x

Var(gˆB) = Var{x

#### Lemma 5.3. Let {xi}B

i=1,{xi}B

i=1 be two batches of B1 and B2 r.v.’s, respectively. Let gˆB

1

2

denote the empirical batch gradients of these two batches, respectively. If B1 < B2, then Var[ˆgB

,gˆB

1

2

].

] > Var[ˆgB

1

2

While decreasing the group size in Eq. (10) appears to increase the gradient variance for each individual prompt, this conclusion overlooks the total number of rollouts optimized across all prompts in a mini-batch.

In Lemma 5.3 (proof in Appx. B.7), we show that a larger batch size B naturally leads to a lower variance of the gradient. Note that B is the number of rollouts in each minibatch rather than the number of prompts.

The actual calculation of GRPO is:

Q

G

1 QG

AijπθGRPO(oij qj), (18)

JGRPO(θ,G,Q) =

j=1

i=1

where

|oi|

G

πθ(oi,t|oi,<t,q) πθ

1 |oi|

1 G

πθGRPO(o|q) =

Cϵ Ai,t

(oi,t oi,<t,q)

old

t=1

i=1

and Q is the number of prompts in the mini-batch, and the batch size w.r.t the number of rollouts is B = QG. When we decrease G, we can increase Q to compensate to retain the same B in a mini-batch. Since the total number of prompts in the dataset is fixed, increasing Q does not increase the total computational cost per training epoch.

#### 5.4. Exploration on Hard Questions

A common concern with using a small group size in GRPO (e.g., G = 2) is insufficient exploration on difficult questions. Such questions often require multiple attempts to yield a correct answer, which is necessary to form a valid contrastive signal. With a smaller group, the likelihood of sampling a correct response in a single iteration may appear lower, potentially raising concerns about degraded learning.

Under a fixed computational budget, 2-GRPO and 16-GRPO explore approximately the same total number of rollouts across all training epochs – the overall probability of sampling a correct answer under 2-GRPO is not lower than 16-GRPO, according to the Proposition 5.4.

Proposition 5.4. Let pi ∈ [0,1] denote the probability that a single rollout under the policy πi produces a correct answer. Then:

- 1. The probability of obtaining at least one correct answer in 2m independent rollouts with policy π0 is

P2m = 1 − (1 − p0)2m. (19)

- 2. The probability of obtaining at least one correct answer when performing m consecutive trials of 2 independent rollouts each, with the corresponding policy


π0,π1,··· ,πm 1] is Pm×2 = 1

(1 pi)2 ≥ 1 (1 p0)2m = P2m

i=0,···m 1

(20) when we have pi ≥ p0,∀i > 0.

Note that the assumption pi ≥ p0,∀i > 0 is prevailing, as we assume that the reasoning ability of LLM can be improved by RL post-training.

Proposition 5.4 suggests that for difficult questions, 2-GRPO does not degrade in effectiveness compared to 16-GRPO given the same budget of the total number of rollouts in whole training process. Notably, due to its higher frequency of policy updates, 2-GRPO may yield a higher probability of generating correct outputs for hard questions. It is also more adaptive, allowing it to capture nuanced update requirements for varying inputs. This observation also extends to PPO with the standard single-rollout implementations per epoch against multi-rollout variants.

### 6. Experiments

#### 6.1. Experiment Details

Tasks and Training Framework Following prior studies, we consider mathematical tasks as representative instances of RLVR to verify our hypothesis, given their demonstrated transferability to a broad range of other tasks (Yu et al., 2025). For training, we adopt the verl framework (Sheng et al., 2025) and utilize the built-in implementation of GRPO (Shao et al., 2024) as the baseline algorithm.

Goal of Experiment Building on the theoretical justification for 2-GRPO, we seek to empirically assess its validity in RLVR. We anticipate that 2-GRPO will exhibit better efficiency—with respect to computational resources and/or wall-clock time—while maintaining the comparable performance as regular GRPO (16-GRPO).

Datasets, Baselines and Hyper-parameters We provide the details of datasets, baselines and hyper-parameter choices in Appx. C.1.

#### 6.2. Main Experiments on Math Reasoning

As shown in Table 1, 2-GRPO requires at least 70% less wall-clock time than 16-GRPO while achieving comparable performance. The models are post-trained on MATH and DAPO-Math-Sub datasets and evaluated on five widelyused math reasoning benchmarks, representing an out-ofdistribution evaluation. This setting imposes stringent requirements on the generalization ability of the post-trained models. Notably, 2-GRPO is optimized with only 0.15 million generated rollouts6, which is just 12.5% of the 1.2 million rollouts utilized by 16-GRPO, and consumes only 21.0% of the training time of 16-GRPO, while achieving 98.1% of its average performance. These results provide strong corroboration of our theoretical finding that reducing group size preserves performance while substantially improving efficiency.

#### 6.3. Further Study: 2-GRPO with Resampling

Due to its binary contrastive nature, 2-GRPO inherently discards a subset of generated rollouts when the policy exhibits exceptionally strong performance on the training set. This behavior can limit the effective utilization of generated data and may, in turn, impact the peak performance achievable by 2-GRPO. A simple remedy is to introduce a resampling mechanism during generation whenever a group of rollouts is discarded, following the strategy adopted in DAPO (Yu et al., 2025). Although this approach incurs additional computation to improve data utilization, the overhead

6Appx. C.2 discusses the relationship between the total number of rollouts and computational cost.

is negligible compared to the efficiency gains provided by 2-GRPO. We compare 2-GRPO with resampling against standard 16-GRPO in a prolonged training setting, demonstrating that 2-GRPO with resampling achieves superior performance while requiring less wall-clock time (Fig. 1).

0.70

0.68

Validation Scores

0.66

0.64

0.62

0.60

0.58

2-GRPO+RS

16-GRPO

0.56

0 100 200 300 400 500

Time (mins)

- Figure 1. 2-GRPO+ReSampling v.s. 16-GRPO – Test Scores (Pass@1) v.s. Wall-clock time on MATH Dataset. Curves are post simple-moving-average (SMA) with window-size=4.

0 50 100 150 200 Time (min)

0.40

0.42

0.44

0.46

0.48

0.50

0.52

Accuracy

2-GRPO

16-GRPO

- Figure 2. 2-GRPO v.s. 16-GRPO – Accuracy v.s. Wall-clock time on Geometry3K test set. Curves are post-SMA (W=4).

0 5 10 15 20 25 Time (h)

0.6

0.4

0.2

0.0

0.2

0.4

0.6

Reward

2-GRPO

16-GRPO

- Figure 3. 2-GRPO v.s. 16-GRPO – Reward v.s. Wall-clock time on code-r1-12k test set. Curves are post-SMA (W=4).


Table 1. 2-GRPO v.s. 16-GRPO: post-trained on MATH/DAPO-Math-Sub and evaluated on five mathematical reasoning benchmarks. M/P@32 stands for Mean@32 and Pass@32. G is the group size. ∆ denotes the difference 16 → 2. 2-GRPO uses only 12.5% of the total rollouts and 21.0% of the training time of 16-GRPO, while achieving 98.1% of its average performance.

M/P@32 ↑ G Time (h) ↓ MATH-500 AMC 2023 Minerva Math AIME 2025 Olympiad Bench Post-training on MATH dataset

w/o - 31.83 / 81.92 34.30 / 79.23 5.33 / 28.91 3.64 / 22.31 15.40 / 37.16 2 2.05 69.28 / 87.43 49.53 / 81.76 16.25 / 33.26 9.48 / 32.88 22.31 / 37.24 16 8.53 70.24 / 87.24 51.25 / 83.46 16.84 / 33.46 10.10 / 35.82 23.11 / 37.82 ∆ -75.96% -0.96 / +0.19 -1.71 / -1.70 -0.59 / -0.19 -0.62 / -2.94 -0.80 / -0.58

Qwen-1.5B

w/o - 47.16 / 85.95 38.36 / 85.29 5.99 / 31.10 5.00 / 25.17 9.83 / 34.30 2 2.43 75.23 / 89.77 64.60 / 81.53 23.13 / 38.45 12.81 / 38.85 26.39 / 40.20 16 9.30 75.90 / 88.24 61.79 / 80.77 22.81 / 37.68 13.23 / 34.22 25.99 / 40.11 ∆ -73.87% -0.67 / +1.53 +2.81 / +0.76 +0.32 / +0.77 -0.42 / +4.63 +0.40 / 0.09

Qwen-7B

w/o - 65.11 / 84.90 44.14 / 73.86 14.64 / 32.80 22.40 / 42.79 20.07 / 33.23 2 7.07 74.36 / 88.85 56.95 / 88.63 21.28 / 38.34 24.89 / 46.79 33.69 / 45.86 16 38.40 75.98 / 89.16 58.91 / 87.26 21.76 / 38.29 26.97 / 56.36 35.39 / 47.05 ∆ -81.6% -1.62 / -0.31 -1.96 / +1.38 -0.48 / -0.05 -2.08 / -9.56 -1.70 / -1.19

DS-1.5B

Post-training on DAPO-Math-Sub dataset

w/o - 31.83 / 81.92 34.30 / 79.23 5.33 / 28.91 3.64 / 22.31 15.40 / 37.16 2 2.12 68.81 / 87.36 52.19 / 85.77 16.79 / 33.61 8.13 / 29.33 23.52 / 39.29 16 13.30 70.66 / 87.04 56.56 / 85.54 18.00 / 34.16 9.58 / 32.31 24.56 / 39.19 ∆ -84.06% -1.85 / +0.32 -4.37 / +0.23 -1.21 / +0.71 -2.50 / -2.98 -1.04 / +0.10

Qwen-1.5B

w/o - 47.16 / 85.95 38.36 / 85.29 5.99 / 31.10 5.00 / 25.17 9.83 / 34.30 2 3.63 77.43 / 90.51 64.84 / 91.59 21.95 / 38.05 14.58 / 33.03 29.86 / 45.24 16 17.68 77.35 / 88.79 69.69 / 87.31 24.45 / 40.04 14.27 / 33.73 28.86 / 39.84 ∆ -79.47% +0.08 / +1.72 -4.85 / +4.28 -2.50 / -1.99 +0.31 / -0.70 +1.00 / +5.4

Qwen-7B

#### 6.4. 2-GRPO Performance on Other Tasks

We extend our experiments with 2-GRPO to additional RLVR tasks beyond Math reasoning, including Vision Reasoning (Geometric3K, Fig. 2) and Code Generation (CodeR1, Fig. 3). The results demonstrate that 2-GRPO is effective across these diverse tasks, highlighting its broader applicability.

### 7. Limitation

Our analysis focuses on the RLVR setting, a key paradigm for LLM post-training. However, real-physical scenarios often involve continuous reward signals. While we believe our contrastive analytical framework can be extended to such settings, which requires further theoretical analysis and empirical validation, and is left for future work.

### 8. Conclusion

In this work, we revisit GRPO and reveal its fundamental connection to DPO, demonstrating that it effectively functions as a contrastive learning objective. We argue that the primary utility of the group mechanism is not for accurate advantage estimation, as in the prevailing view, but rather the efficient construction of contrastive signals. Leveraging this insight, we introduce 2-GRPO, a minimal variant utilizing only two rollouts. While this setting represents a degenerate case for traditional advantage estimation, it remains theoretically robust within our contrastive framework. Empirically, 2-GRPO achieves performance comparable to 16-GRPO while significantly reducing the computational overhead of sample generation in RL training. These findings validate our hypothesis and offer a more efficient paradigm for designing RL algorithms for LLMs. More broadly, while our derivation focuses on GRPO, the insights presented here can extend to a broader class of group-based RL algorithms.

### Impact Statement

This paper presents work whose goal is to advance the field of machine learning, specifically for the field of Large Language Models post-training and Reinforcement Learning. There are many potential societal consequences of our work, none of which we feel must be specifically highlighted here.

### References

Ahmadian, A., Cremer, C., Gall´e, M., Fadaee, M., Kreutzer, J., Pietquin, O., Ust¨¨ un, A., and Hooker, S. Back to basics: Revisiting reinforce style optimization for learning from human feedback in llms. In Proc. Annu. Meet. Assoc. Comput. Linguist., 2024.

Bai, S., Chen, K., Liu, X., Wang, J., Ge, W., Song, S., Dang, K., Wang, P., Wang, S., Tang, J., et al. Qwen2. 5-vl technical report. arXiv preprint arXiv:2502.13923, 2025.

Baird, Leemon C., I. Advantage updating. Technical report, Wright Laboratory, 1993.

Chen, T., Kornblith, S., Norouzi, M., and Hinton, G. A simple framework for contrastive learning of visual representations. In Proc. Int. Conf. Mach. Learn., 2020.

Chopra, S., Hadsell, R., and LeCun, Y. Learning a similarity metric discriminatively, with application to face verification. In Proc. IEEE Comput. Soc. Conf. Comput. Vis. Pattern Recognit., 2005.

Chu, X., Huang, H., Zhang, X., Wei, F., and Wang, Y. Gpg: A simple and strong reinforcement learning baseline for model reasoning. arXiv preprint arXiv:2504.02546, 2025.

DeepSeek-AI. Deepseek-r1: Incentivizing reasoning capability in llms via reinforcement learning, 2025.

Flet-Berliac, Y., Grinsztajn, N., Strub, F., Choi, E., Wu, B., Cremer, C., Ahmadian, A., Chandak, Y., Azar, M. G., Pietquin, O., et al. Contrastive policy gradient: Aligning llms on sequence-level scores in a supervised-friendly fashion. In Proc. Conf. Empir. Methods Nat. Lang. Process., 2024.

Frosst, N., Papernot, N., and Hinton, G. Analyzing and improving representations with the soft nearest neighbor loss. In Proc. Int. Conf. Mach. Learn., 2019.

Goyal, P., Doll´ar, P., Girshick, R., Noordhuis, P., Wesolowski, L., Kyrola, A., Tulloch, A., Jia, Y., and He, K. Accurate, large minibatch sgd: Training imagenet in 1 hour. arXiv preprint arXiv:1706.02677, 2017.

He, C., Luo, R., Bai, Y., Hu, S., Thai, Z., Shen, J., Hu, J., Han, X., Huang, Y., Zhang, Y., Liu, J., Qi, L., Liu, Z., and Sun, M. OlympiadBench: A challenging benchmark for

promoting AGI with olympiad-level bilingual multimodal scientific problems. In Proc. Annu. Meet. Assoc. Comput. Linguist., 2024.

He, K., Fan, H., Wu, Y., Xie, S., and Girshick, R. Momentum contrast for unsupervised visual representation learning. In Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit., 2020.

Hejna, J., Rafailov, R., Sikchi, H., Finn, C., Niekum, S., Knox, W. B., and Sadigh, D. Contrastive preference learning: learning from human feedback without rl. arXiv preprint arXiv:2310.13639, 2023.

Hendrycks, D., Burns, C., Kadavath, S., Arora, A., Basart, S., Tang, E., Song, D., and Steinhardt, J. Measuring mathematical problem solving with the math dataset. In Adv. Neural Inf. Process. Syst. (Track Datasets Benchmarks), 2021.

Hu, J. Reinforce++: A simple and efficient approach for aligning large language models. arXiv preprint arXiv:2501.03262, 2025.

Johnson, R. and Zhang, T. Accelerating stochastic gradient descent using predictive variance reduction. In Adv. Neural Inf. Process. Syst., 2013.

Kingma, D. P. Adam: A method for stochastic optimization. arXiv preprint arXiv:1412.6980, 2014.

Lewkowycz, A., Andreassen, A., Dohan, D., Dyer, E., Michalewski, H., Ramasesh, V., Slone, A., Anil, C., Schlag, I., Gutman-Solo, T., et al. Solving quantitative reasoning problems with language models. In Adv. Neural Inf. Process. Syst., 2022.

Li, G., Lin, M., Galanti, T., Tu, Z., and Yang, T. Disco: Reinforcing large reasoning models with discriminative constrained optimization. arXiv preprint arXiv:2505.12366, 2025.

Li, Z., Xu, T., Zhang, Y., Lin, Z., Yu, Y., Sun, R., and Luo, Z.-Q. Remax: a simple, effective, and efficient reinforcement learning method for aligning large language models. In Proc. Int. Conf. Mach. Learn., 2024.

Liu, J. and Zhang, L. Code-r1: Reproducing r1 for code with reliable rewards. https://github.com/ganler/ code-r1, 2025.

Lu, P., Gong, R., Jiang, S., Qiu, L., Huang, S., Liang, X., and Zhu, S.-c. Inter-gps: Interpretable geometry problem solving with formal language and symbolic reasoning. In Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers), pp. 6774–6786, 2021.

Lv, X., Chen, K., Sun, H., Bai, X., Zhang, M., and Liu, H. The hidden link between rlhf and contrastive learning. arXiv preprint arXiv:2506.22578, 2025.

Oord, A. v. d., Li, Y., and Vinyals, O. Representation learning with contrastive predictive coding. arXiv preprint arXiv:1807.03748, 2018.

Ouyang, L., Wu, J., Jiang, X., Almeida, D., Wainwright, C., Mishkin, P., Zhang, C., Agarwal, S., Slama, K., Ray, A., et al. Training language models to follow instructions with human feedback. In Adv. Neural Inf. Process. Syst., 2022.

Pang, L. and Jin, R. On the theory and practice of grpo: A trajectory-corrected approach with fast convergence. arXiv preprint arXiv:2508.02833, 2025.

Rafailov, R., Sharma, A., Mitchell, E., Manning, C. D., Ermon, S., and Finn, C. Direct preference optimization: Your language model is secretly a reward model. In Adv. Neural Inf. Process. Syst., 2023.

Rendle, S., Freudenthaler, C., Gantner, Z., and SchmidtThieme, L. Bpr: Bayesian personalized ranking from implicit feedback. In Proc. Conf. Uncertain. Artif. Intell., 2009.

Schulman, J., Levine, S., Abbeel, P., Jordan, M., and Moritz, P. Trust region policy optimization. In Proc. Int. Conf. Mach. Learn., 2015.

Schulman, J., Moritz, P., Levine, S., Jordan, M., and Abbeel, P. High-dimensional continuous control using generalized advantage estimation. In Proc. Int. Conf. Learn. Represent., 2016.

Schulman, J., Wolski, F., Dhariwal, P., Radford, A., and Klimov, O. Proximal policy optimization algorithms. arXiv preprint arXiv:1707.06347, 2017.

Shao, Z., Wang, P., Zhu, Q., Xu, R., Song, J., Bi, X., Zhang, H., Zhang, M., Li, Y., Wu, Y., et al. Deepseekmath: Pushing the limits of mathematical reasoning in open language models. arXiv preprint arXiv:2402.03300, 2024.

Sheng, G., Zhang, C., Ye, Z., Wu, X., Zhang, W., Zhang, R., Peng, Y., Lin, H., and Wu, C. Hybridflow: A flexible and efficient rlhf framework. In Proc. Eur. Conf. Comput. Syst., 2025.

Student. The probable error of a mean. Biometrika, pp. 1–25, 1908.

Wang, T. and Isola, P. Understanding contrastive representation learning through alignment and uniformity on the hypersphere. In Proc. Int. Conf. Mach. Learn., 2020.

Williams, R. J. Simple statistical gradient-following algorithms for connectionist reinforcement learning. Machine learning, 8(3):229–256, 1992.

Wu, Y., Zhang, L., Mo, F., Zhu, T., Ma, W., and Nie, J.Y. Unifying graph convolution and contrastive learning in collaborative filtering. In Proc. ACM SIGKDD Conf. Knowl. Discov. Data Min., 2024.

Wu, Y., Ma, L., Li, M., Zhou, J., Ding, L., Hao, J., Leung, H.-f., King, I., Zhang, Y., and Nie, J.-Y. Advancing multiagent rag system with minimalist reinforcement learning. In Proc. Int. Conf. Auton. Agents Multi-Agent Syst., 2026.

Yang, A., Yang, B., Zhang, B., Hui, B., Zheng, B., Yu, B., Li, C., Liu, D., Huang, F., Wei, H., Lin, H., Yang, J., Tu,

- J., Zhang, J., Yang, J., Yang, J., Zhou, J., Lin, J., Dang,
- K., Lu, K., Bao, K., Yang, K., Yu, L., Li, M., Xue, M., Zhang, P., Zhu, Q., Men, R., Lin, R., Li, T., Tang, T., Xia, T., Ren, X., Ren, X., Fan, Y., Su, Y., Zhang, Y., Wan, Y., Liu, Y., Cui, Z., Zhang, Z., and Qiu, Z. Qwen2.5 Technical Report, January 2025.


Yu, Q., Zhang, Z., Zhu, R., Yuan, Y., Zuo, X., Yue, Y., Dai, W., Fan, T., Liu, G., Liu, L., et al. Dapo: An opensource llm reinforcement learning system at scale. In Adv. Neural Inf. Process. Syst., 2025.

Zhang, L., Wang, B., Qiu, X., Reddy, S., and Agrawal, A. REARANK: Reasoning re-ranking agent via reinforcement learning. In Proc. 2025 Conf. Empir. Methods Nat. Lang. Process., 2025a.

Zhang, R., Arora, D., Mei, S., and Zanette, A. Speed-rl: Faster training of reasoning models via online curriculum learning. arXiv preprint arXiv:2506.09016, 2025b.

Zhao, Y., Liu, Y., Liu, J., Chen, J., Wu, X., Hao, Y., Lv, T., Huang, S., Cui, L., Ye, Q., et al. Geometric-mean policy optimization. arXiv preprint arXiv:2507.20673, 2025.

Zheng, C., Liu, S., Li, M., Chen, X.-H., Yu, B., Gao, C., Dang, K., Liu, Y., Men, R., Yang, A., et al. Group sequence policy optimization. arXiv preprint arXiv:2507.18071, 2025a.

Zheng, H., Zhou, Y., Bartoldson, B. R., Kailkhura, B., Lai, F., Zhao, J., and Chen, B. Act only when it pays: Efficient reinforcement learning for llm reasoning via selective rollouts. arXiv preprint arXiv:2506.02177, 2025b.

Zheng, Y., Lu, J., Wang, S., Feng, Z., Kuang, D., and Xiong, Y. Easyr1: An efficient, scalable, multi-modality rl training framework, 2025c.

Zhu, L., Guan, Y., Liang, D., Ju, J., Luo, Z., Qin, B., Luan, J., Liu, Y., and Bai, X. Shuffle-r1: Efficient rl framework for multimodal large language models via data-centric dynamic shuffle. arXiv preprint arXiv:2508.05612, 2025.

Appendix

- A. Related Work

- A.1. Contrastive Learning and LLM Alignment

Contrastive learning is the cornerstone of self-supervised representation learning (Wang & Isola, 2020; He et al., 2020; Chen et al., 2020; Wu et al., 2024). The fundamental objective is to minimize the distance between anchor and positive samples in the representation space while maximizing the distance between the anchor and negative samples. Given this contrastive nature, the framework shares structural similarity with DPO, which conducts preference learning by increasing the likelihood of preferred completions relative to dispreferred ones. While recent literature explores the theoretical connections between RLHF and contrastive learning (Hejna et al., 2023; Flet-Berliac et al., 2024; Lv et al., 2025), our work establishes a formal link between GRPO and DPO through a contrastive lens. This provides a unified analytical framework for understanding alignment. Specifically, we attribute the efficacy of GRPO to the construction of contrastive pairs, which serves as a control variate to reduce the variance of the gradient estimator. This analysis offers generalizable insights to broader alignment algorithms.

- A.2. Adaptive Rollouts in RLVR


RL post-training has demonstrated significant success in enhancing LLM performance across diverse domains (Wu et al., 2026; Zhang et al., 2025a). Unlike SFT, RL requires the model to generate online samples during training. Although modern frameworks integrate high-throughput inference engines such as vLLM and SGLang, the autoregressive nature of LLMs ensures that the generation phase remains a primary computational bottleneck. This challenge is exacerbated by the common intuition that LLM-based RL often necessitates large group sizes to achieve good performance. To mitigate this overhead, recent studies have proposed selective or adaptive sampling techniques to reduce the number of rollouts without compromising performance (Zheng et al., 2025b; Zhang et al., 2025b; Zhu et al., 2025). Within this context, 2-GRPO serves as a robust baseline. Furthermore, our contrastive analysis of GRPO opens a new design space for developing efficient sampling algorithms in RLVR.

- B. Theorems


- B.1. Mean Estimation with Samples n = 2

The instability of normalization with extremely small samples is a well-documented phenomenon in classical statistics, dating back to the seminal work of William Sealy Gosset (published under the pen name Student) (Student, 1908). For a sample size of n = 2, the degrees of freedom df = 1 result in a normalization factor that follows a Cauchy distribution. Such small-sample estimates of variance are highly skewed, leading to normalized outputs with infinite variance and no defined mean, undermining the goal of statistical stability.

- B.2. Reveal GRPO as Contrastive Learning


Proof of Proposition 3.1. In the RLVR setting, rewards are binary, which leads to binary advantages given a prompt. Let A+q ,A−q denote the positive and negative advantage, respectively. From Eq. (6), we can have

1 − pˆq pˆq(1 − pˆq)

1 − pˆq pˆq

,

Aq =

=

0 − pˆq pˆq(1 − pˆq)

pˆq 1 − pˆq

A−q =

= −

.

(21)

The clipping function is

 

x, |x − 1| ≤ ϵ

clip(x,1 − ϵ,1 + ϵ) =

, (22)

1 − ϵ, x < 1 − ϵ 1 + ϵ, x > 1 + ϵ



which means that x will be assigned to 1 − ϵ (1 + ϵ) if x is less (greater) than 1 − ϵ (1 + ϵ). For simplifying notation, let

Cϵ+(x) = min[x,1 + ϵ] and Cϵ− = max[x,1 − ϵ]. The key derivation of rewriting GRPO objective is as follows:

JGRPO(θ)

|oi|

G

πθ(oi,t|oi,<t,q) πθ

1 |oi|

1 G

= E q∼Q

Cϵ

Ai,t ,

(oi,t oi,<t,q)

{oi}Gi=1∼πθold(·|q)

old

t=1

i=1

= E q∼Q

- {oj}Gj=1+ ∼πθ+

old

(·|q)

- {ok}Gk=1∼πθ−


(·|q)

old

 

  ,

G−

G+

|oj|

|ok|

πθ(oj,t|oj,<t,q) πθ

πθ(ok,t|ok,<t,q) πθ

1 |oj|

1 |ok|

1 G

A−k Cϵ−

A+j Cϵ+

+

(oj,t|oj,<t,q)

(ok,t|ok,<t,q)

old

old

t=1

t=1

j=1

k=1

= E q∼Q

(23)

- {oj}Gj=1+ ∼πθ+

old

(·|q)

- {ok}Gk=1− ∼πθ−


(·|q)

old

|oj|

|ok|

G

G

G+ G

πθ(oj,t|oj,<t,q) πθ

πθ(ok,t|ok,<t,q) πθ

1 G+

1 |oj|

1 G−

1 |ok|

G G

Cϵ−

+ A−q

Cϵ+

A+q

,

(oj,t|oj,<t,q)

(ok,t ok,<t,q)

old

old

t=1

t=1

j=1

k=1

= E q∼Q

- {oj}Gj=1+ ∼πθ+

old

(·|q)

- {ok}Gk=1− ∼πθ−


(·|q)

old

  1

  .

G+

|oj|

|ok|

G

πθ(oj,t|oj,<t,q) πθ

πθ(ok,t|ok,<t,q) πθ

1 |oj|

1 |ok|

1 G

Cϵ−

Cϵ+

(oj,t|oj,<t,q) −

VarG(q)

G+

(ok,t|ok,<t,q)

old

old

t=1

t=1

j=1

k=1

The second equation is obtained by dividing the trajectories into two groups: positive and negative. The third equation is obtained by the fact that all positive advantages are the same and that all negative advantages are the same. Since A+ G

−

+

G = 1−pˆpˆpˆ = (1 − pˆ)ˆp and A G

G = − (1 − pˆ)ˆp, we obtain Eq. (10). When G → ∞, we have the following facts:

G+ = ∞ , lim G→∞

lim

G→∞

G− = ∞ lim G→∞

(1 pˆ)ˆp (1 p)p ,

(24)

G

1 G+

f(oj) = Eo

j∼Oθ+f(oj) ,

lim

G+→∞

j=1

G−

1 G−

f(ok) = Eo

lim

k∼Oθ−f(ok) .

G−→∞

k=1

Then the GRPO objective has the following gradient w.r.t. parameter θ:

∇θJGRPO =

|o+j |

G−q

G+q

o−k

ϵ k,t∇θπθ(o−k,t|o−k,<t,q)

ϵ j,t∇θπθ(o+j,t|o+j,<t,q)

1 G−q

1 G+q

E

(o+j,t o+j,<t,q) −

VarG(q)

|o−k |πθ

(o−k,t|o−k,<t,q)

|o+j πθ

q∼Q

old

old

t

t

j=1

k=1

|o+j |

G−q

G+q

|o−k |

1 G+q

1 G−q

c(o−k,t|o−k,<t,q)∇θπθ(o−k,t|o−k,<t,q)

##### c(o+j,t|o+j,<t,q)∇θπθ(o+j,t|oj,<t,q)

##### = E

−

q∼Q

t

t

j=1

k=1

Negative

Positive

(25)

###### (26)

√

Var(q) ϵi,t

where ϵj,t is an indicator function if the token oj,t is clipped and c(oi,t|oi,<t,q) :=

oi|πθold(oi,t oi,<t,q). Compare Eq. (26) with Def. 2.1, the derivative of GRPO is a Monte Carlo estimator of contrastive derivative.

| |
|---|


#### B.3. Further Discussion on Importance Sampling and the Log-likelihood Term

Most autoregressive LLMs adopt causal probability modelling as log πθ(o|q) = log πθ(ot|o<t,q). This decomposition leads to the following trajectory-level form to describe the gradient of token probabilities:

1

πθ(ot|o<t,q)∇θπθ(ot|o<t,q). (27) DPO follows a similar structural derivation.

∇θ log πθ(o q) =

t

It is worth mentioning that the importance sampling in PPO can be viewed as a natural extension of such gradient form for online on/off-policy RL (Schulman et al., 2017). However, the token-level importance sampling in PPO and vanilla GRPO often obscures this direct connection at the trajectory level.

Recent subsequent variants of GRPO (Zheng et al., 2025a; Zhao et al., 2025; Pang & Jin, 2025), e.g., GSPO and TIC-GRPO, utilize sequence-level importance sampling. This formulation allows us to draw a direct connection between importance sampling and the log-likelihood terms:

πθ(o | q) πθ

πθ(o | q) πθ

1 πθ(ot | o<t,q)∇θπθ(ot | o<t,q). (28)

∇θ

=

(o | q)

(o | q) t

old

old

It is straightforward to see from the gradient form that the importance sampling term adjusts the Log-likelihood term by a coefficient π

θ(o|q)

πθold(o q). The token-level importance sampling in PPO and GRPO behaves similarly by applying token-level

correction. The clipping applied on top of importance sampling is a minor additional modification, which we do not elaborate on here.

###### B.4. Proof of Lemma B.1Lemma B.1. The DPO loss is a 1-vs-1 contrastive loss estimator.Proof of Lemma B.1. The DPO loss (Eq. (9)) has the following derivatives:

σ(ˆrθ(q,o−) rˆθ(q,o+)) ∇θ log πθ(o+|q) − ∇θ log πθ(o− q)

∇θLDPO = β E

[(q,o+,o−)∼DDPO]

|o−|

|o+|

c(o−t |o−<t,q)∇θπθ(o−t |o−<t,q)

c(o+t |o+<t,q)∇θπθ(o+t o+<t,q)

= − E

−

[(q,o+,o )∼DDPO]

t

t

Positive

Negative

(29)

θ(q,o−)−rˆθ(q,o+))

θ(y|x)

where rˆθ = β(x,y)log π

πref(y|x); and c(ot|o<t,q) := βσ(ˆr

πθ(o|q) , aligning with Def. 2.1.

| |
|---|


#### B.5. Proof of Proposition 4.1

Proof.

Var(g+ cg−) = Var(g+) + c2Var(g−) 2cCov(g+,g−),

Cov2(g+,g ) Var(g−)

(30)

= Var(g+) −

,

= (1 − ρ2)Var(g+).

+,g )

The first equation is obtained by the definition of variance. The second equation is obtained by substituting c = Cov(g

Var(g−) . The third equation is hold because ρ √ Cov(g ,g )

. On the other hand, consider f(c) = c2Var(g−) 2cCov(g+,g−). If 0 ≤ c ≤ 2Cov

Var(g+)Var(g )

2(g+,g )

Var(g−) , then f(c) ≤ 0.

#### B.6. Proof of Proposition 5.1

Proof. Case 1. Notice that σˆ = 21N 2kN=1(Xk − µˆ)2 = µˆ(1 − µˆ) and µˆ = 21N 2kN=1 Xk. Fix an index i and condition on the event {Xi = x} with x ∈ {0,1}. In this case, by the strong law of large numbers and the continuous mapping theorem, we have µˆ a.s.→ p and σˆ a.s.→ p(1 − p). Thus, it follows that

x − p p(1 − p)

E[Yi Xi = x] =

lim

lim

.

ϵ→0

N→∞

Case 2. When Xi,1 = Xi,2, we have Xi,j = ˆµi and Yi,j = 0 for any j ∈ {1,2}. When Xi,1 ̸= Xi,2, we have µˆi = 0.5, σˆi = 0.5, and Yi,j = 2X1+2i,j−ϵ 1. By the law of total expectation, it follows that

Thus, we have

1 − p 1 + 2ϵ

, E[Yi,j | Xi,j = 0] = −p 1 + 2ϵ

E[Yi,j Xi,j = 1] =

.

E[Yi,j | Xi,j = x] = x − p.

lim

ϵ→0

| |
|---|


#### B.7. Proof of Lemma 5.3Proof of Lemma 5.3.

B

1 B

Var(gˆB) = Var{x

#### g(xi)

i}Bi=1

i=1

B

Varx(g(x)) B

1 B2

Varx

(g(xi)) =

.

=

i

i=1

(31)

where the second and third equalities are obtained by the properties of independence and identity in i.i.d. data, respectively. By the above equation, increasing B decreases Var.

| |
|---|


### C. Experiments

#### C.1. Experiment Details

Dataset and Baselines For math reasoning task, following prior work (Chu et al., 2025), we employ Qwen2.5-Math-1.5B (Qwen-1.5B) and Qwen2.5-Math-7B (Qwen-7B) (Yang et al., 2025) as base models. Both models are post-trained via RL on the MATH (Hendrycks et al., 2021) and DAPO-Math-17k (Yu et al., 2025) datasets, and evaluated on MATH-500 (Hendrycks et al., 2021), AMC23, Minerva Math (Lewkowycz et al., 2022), AIME-2025, and OlympiadBench (He et al., 2024). For DAPO-Math-17k dataset, we randomly sample 7.5k questions from the original data to form a subset for training in order to align with the size of MATH. In addition, we assess the proposed method on DeepSeek-R1-Distill-Qwen-1.5B (DS-1.5B) (DeepSeek-AI, 2025), which is post-trained on MATH. Owing to computational constraints, we do not extend its post-training to DAPO-Math-17k. All 1.5B models are trained on 4 GPUs. Qwen-7B is trained on 8 GPUs. We evaluate model performance using two metrics: Mean@32, the average accuracy across 32 i.i.d. samples, and Pass@32, which measures whether a problem is solved in at least one of those 32 attempts.

For visual reasoning task, we use EasyR1 (Zheng et al., 2025c) framework, Qwen2.5-7B (Bai et al., 2025) as the base model, and Geometric3K (Lu et al., 2021) as the dataset. For code generation task, we use Code-R1 (Liu & Zhang, 2025) framework, Qwen2.5-7B-Instruct-1M as the base model, and code-r1-12k7 as the dataset. Both visual reasoning and code generation tasks are conducted on 8 GPU.

7https://huggingface.co/datasets/ganler/code-r1-12k

Hyper-parameters We mainly follow the default configuration of the verl framework. For sampling parameters in training generation, we set temperature to 1, top-p to 1 to encourage exploration, sequence length to 4096 for Qwen-series model and 8192 for DS-1.5B. For sampling parameters in test generation, we set temperature to 0.7, top-p to 0.8, top-k to 20 and sequence length to 4096 for all models. For optimization, training employs the Adam optimizer (Kingma, 2014) with a constant learning rate and a linear warm-up over the first 10 steps. For GRPO hyper-parameters, we set the clip ratio high to 0.28 and clip ratio lower to 0.2 following DAPO (Yu et al., 2025). All models are trained for 10 epochs. The baseline method, 16-GRPO, is trained with batch sizes of 32 (32 prompts and 16 rollouts per prompt) and a learning rate 1 × 10−6. As discussed in Sec. 5.3, we trained 2-GRPO with a larger batch size of 256 (256 prompts and 2 rollouts per prompt). Both case will have 512 rollouts in each mini-batch of training. Since we have fewer update steps due to the larger batch size, we adjust the learning rate of 2-GRPO to 8 × 10−6 based on the linear relationship of learning rate and batch size (Goyal et al., 2017).

#### C.2. The Connection Between Training Rollouts and Computational Cost

In Sec. 6.2, the total number of rollouts generated and utilized during training is adopted as a metric for comparing the computational cost of different methods.

The rationale for this choice is as follows. A principled measure of computational cost in the context of RL post-training is the number of floating-point operations (FLOPs) performed. Unlike wall-clock time, which is susceptible to variations arising from software implementation details (e.g., optimization of training libraries) and hardware characteristics (e.g., GPU/CPU architecture, I/O throughput), FLOPs provide a more direct and stable measure of computational effort.

For a fixed base model and the same type of RL algorithm (GRPO in our case), the FLOPs required for a single forward or backward pass with one input prompt can be considered constant, for both the generation and training phases. Accordingly, the total number of rollouts executed during training is directly proportional to the FLOPs executed, thereby serving as a theoretically justified and consistent proxy for computational cost.

### D. Additional Experiments

- D.1. Sensitivity Study

In this section, we provide an ablation study across different group-sizes in GRPO without the scaling term. We visualize the curve of rewards on the training and test sets of MATH dataset.

We conducted a sensitivity study on GRPO without the scaling term, varying group size while keeping training epochs constant. As shown in Fig. 4, all group sizes follow a similar optimization trend. Notably, the total number of rollouts (#prompts × #epochs × #rollouts-per-group) indeed correlates with training rewards.

However, the 4- and 8-rollout variants exhibit slightly wider generation gaps on the test set. We hypothesize that this phenomenon stems from fluctuations in the number of positive and negative examples within the Monte Carlo estimators compared to the 2-GRPO baseline. This suggests that the 2-rollout configuration may provide an intrinsic stabilizing effect during optimization. We leave a more in-depth investigation to future work, which could yield further insights into designing group-relative RL algorithms.

- D.2. The Impact of Scaling Term in GRPO


We additionally compare 16-GRPO with 16-CTR-GRPO (i.e., GRPO with the scaling term) to serve as a baseline in the sensitivity study.

### E. The Use of Large Language Models (LLMs)We used LLMs to polish the writing.

0.80

0.75

0.70

Validation Scores

0.65

0.60

0.55

G=16

0.50

G=8 G=4 G=2

0.45

0.40

0 50 100 150 200 250

Time (mins)

(a) Training Reward during post-training.

0.70

0.68

0.66

Validation Scores

0.64

0.62

0.60

G=16

G=8 G=4 G=2

0.58

0.56

0 50 100 150 200 250

Time (mins)

(b) Evaluation score on the Test set.

Figure 4. Sensitivity Study of Group Sizes on CTR-GRPO at MATH dataset (10ep). Curves are post simple-moving-average (SMV) with window-size=4 for better visualization, respectively. 2-GRPO is equivalent to 2-CTR-GRPO.

CTR-GRPO vs 16-GRPO Comparison

0.70

0.68

0.66

0.64

Reward

0.62

0.60

0.58

CTR-GRPO

16-GRPO

0.56

0 20 40 60 80 100 120

Step

Figure 5. Test-scores of 16-GRPO and 16-CTR-GRPO on MATH dataset; Curves are post-SMV (W=4) for better visualization

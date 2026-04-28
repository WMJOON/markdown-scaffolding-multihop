---
doc_id: paper__mteb_2210_07316
generated_by: ollama/gemma4:e4b
chunks: 20
---

# Overview: paper__mteb_2210_07316

Massive Text Embedding Benchmark (MTEB)는 기존의 단일 작업 한계를 극복하기 위해 도입된 포괄적인 벤치마크로, 8개의 임베딩 태스크, 58개의 데이터셋, 그리고 112개 언어를 다룹니다. MTEB는 텍스트 임베딩 모델의 성능을 광범위하게 측정하며, 그 결과 특정 임베딩 방법이 모든 태스크에서 지배적이지 않다는 점을 입증했습니다. 이처럼 성능은 사용 목적에 따라 분화(bifurcation)되며, 예컨대 STS(Semantic Textual Similarity)에서는 ST5-XXL이 최고의 성능을 보이고, Retrieval 작업에서는 SGPT-5.8B-msmarco와 같은 모델이 우위를 점하는 등, 태스크별 특화 모델의 중요성을 강조합니다. 따라서 MTEB는 Classification, Clustering, Retrieval, STS와 같은 다양한 태스크에서 nDCG@10, Spearman correlation, 또는 F1 같은 다종의 지표를 사용하여 모델의 전반적인 견고성을 비교합니다.

---

## Section Summaries

## MTEB: Massive Text Embedding Benchmark

Niklas Muennighoff1, Nouamane Tazi1, Loïc Magne1, Nils Reimers2* 1Hugging Face 2cohere.ai 1firstname@hf.co 2info@nils-reimers.de

---

## arXiv:2210.07316v3 [cs.CL] 19 Mar 2023 (1/3)

기존에는 텍스트 임베딩 모델의 평가가 STS(semantic textual similarity)와 같은 단일 작업 및 소규모 데이터셋에 국한되어, 클러스터링이나 검색 같은 다른 실제 사용 사례로의 전이 가능성을 제대로 파악하기 어렵습니다. 이러한 한계를 해결하기 위해 저자들은 Massive Text Embedding Benchmark (MTEB)를 도입했습니다. MTEB는 8개의 임베딩 태스크를 포괄하며, 총 58개의 데이터셋과 112개의 언어를 다루는 가장 포괄적인 벤치마크입니다. MTEB를 통해 33개의 모델을 벤치마킹한 결과, 특정 임베딩 방법이 모든 태스크에서 지배적이라는 증거는 발견되지 않았습니다. 이는 해당 분야가 아직 모든 임베딩 태스크에 적용 가능한 범용적인 텍스트 임베딩 방법론에 수렴하지 못했음을 시사합니다.

---

## arXiv:2210.07316v3 [cs.CL] 19 Mar 2023 (2/3)

MTEB는 open-source1 기반의 평가 프레임워크로, 오픈소스 모델과 OpenAI Embeddings endpoint 같은 API 모델을 포함하여 30개 이상의 모델을 평가합니다. 연구진은 어떤 단일 모델도 최고의 솔루션이 아니며, SimCSE’s (Gao et al., 2021b)가 STS(Semantic Textual Similarity)에서는 강하지만 클러스터링이나 검색(retrieval)에서는 성능이 낮다는 점을 발견했습니다. 이전 벤치마크인 SentEval은 Semantic Textual Similarity (STS)에 초점을 맞추고 클래시파이어가 필요하여 검색이나 클러스터링과 같은 과제를 다루지 못하는 한계가 있었습니다. MTEB는 이러한 한계를 극복하고, SemEval datasets (STS11 - STS22)와 BEIR 같은 다양한 데이터셋을 하나의 접근 가능한 틀로 통합하여 텍스트 임베딩 모델의 전반적인 성능 검토를 제공합니다.

---

## arXiv:2210.07316v3 [cs.CL] 19 Mar 2023 (3/3)

본문은 텍스트 임베딩 모델의 복잡한 진화와 성능 비교의 필요성을 다룹니다. 초기에는 BERT (Devlin et al., 2018)와 같은 트랜스포머 아키텍처를 이용한 대규모 사전 훈련이 활용되었으며, SBERT (Reimers and Gurevych, 2019)는 미세 조정(fine-tuning)을 통해 성능을 개선했습니다. 최근의 임베딩 모델들은 긍정/부정 텍스트 쌍에 대한 감독 학습을 위해 대비 손실 함수(contrastive loss objective)를 사용하고 있습니다. 이로 인해 다양한 잠재적 모델들이 존재하여, 특정 사용 사례에 최적인 모델을 선택하는 데 혼란이 생겼습니다. 이에 저자들은 word embedding 모델과 트랜스포머 모델을 MTEB 벤치마크에서 비교하여, 느리지만 맥락을 인지하는 모델들이 제공하는 성능 향상을 정량화하는 것을 목표로 합니다. MTEB는 (a) 다양성(8개 태스크, 최대 15개 데이터셋, 58개 총 데이터셋, 10개 다국어 지원으로 112개 언어 커버), (b) 단순성, (c) 확장성을 갖춘 벤치마크입니다.

---

## MTEB (1/37)

MTEB 벤치마크는 Bitext Mining, Classification, Clustering, Pair Classification을 포함한 8가지 유형의 태스크를 제공합니다. Bitext Mining에서는 두 언어의 두 세트 문장 간 최적의 쌍을 코사인 유사도를 이용해 찾으며, F1이 주 측정 지표입니다. Classification에서는 전이 학습을 위해 주어진 모델을 이용해 train set으로 logistic regression classifier를 훈련하고 (최대 100회 반복), test set에서 정확도(accuracy)를 측정합니다. Clustering은 주어진 문장들을 의미 있는 클러스터로 그룹화하는 목표이며, mini-batch k-means 모델(batch size 32)을 훈련하고 v-measure를 사용하여 점수를 매깁니다. 마지막으로 Pair Classification은 주어진 두 개의 텍스트 입력 쌍에 레이블을 할당하는 작업으로, 텍스트 임베딩의 거리(cosine similarity, dot product 등)를 계산합니다.

---

## MTEB (2/37)

본 논문은 다양한 성능 측정 지표로 평가를 수행하며, `binary threshold accuracy`, `average precision`, `f1`, `precision`, 그리고 `recall`을 계산합니다. 특히 `average precision score based on cosine similarity`가 주요 측정 지표로 사용됩니다. 또한, `Reranking Inputs`를 통해 쿼리와 관련/비관련 참고 텍스트를 활용하여 관련성을 기준으로 결과를 순위화하며, 이 과정에서는 `mean MRR@k`와 `MAP`을 사용하며 후자가 주된 지표입니다. 제시된 데이터는 `AmazonCounterfactualClassification`, `AmazonPolarityClassification`, `AmazonReviewsClassification` 등의 모델에 대한 다양한 성능 점수들로 구성되어 있습니다. (이후 표에 제시된 구체적인 수치들은 해당 모델들의 정량적 평가 결과를 보여줍니다.)

---

## MTEB (3/37)

제시된 내용은 MTEB (3/37) 섹션에 대한 포괄적인 성능 점수 데이터를 나타냅니다. 이 데이터는 모델들이 다양한 벤치마크 태스크에서 달성한 수많은 정량적 점수들로 구성되어 있으며, 총 37개 지표에 걸쳐 상세한 성능 비교가 이루어졌습니다. 점수들은 68점과 같은 낮은 값부터 최대 97점까지의 넓은 범위를 보이며, 이는 다양한 조건과 모델 조합에 따른 세밀한 성능 편차를 반영합니다. 예를 들어, 초반부에서는 88, 88, 88, 87, 87 등의 점수 패턴을 보이다가, 중후반부에는 95, 95, 93, 93 등 90점대 후반의 고득점 분포도 관찰됩니다. 이러한 방대한 스코어 세트는 모델의 견고성과 성능 변화 추이를 깊이 분석하는 데 사용됩니다.

---

## MTEB (4/37)

본 자료는 MTEB (Massive Text Embedding Benchmark)의 광범위한 평가 범위를 보여주는 목록 및 결과 지표로 구성되어 있습니다. 제시된 수치들은 다양한 텍스트 임베딩 태스크를 수행한 모델들의 성능 지표를 나타냅니다. 평가 대상 태스크는 `Banking77Classification`부터 `EmotionClassification`에 이르기까지, 분류(Classification), 추출(Extraction), 의미 유사도 측정(STS Benchmark) 등 매우 광범위한 영역을 포괄합니다. 특히, 도메인별 전문 지식을 요구하는 과학 논문 분야(`ArxivClusteringP2P`, `BiorxivClusteringS2S`, `MedrxivClusteringP2P`, `SciDocsRR`)와 질문 응답 및 검색 기반 태스크(`FEVER`, `HotpotQA`, `NQ QuoraRetrieval`, `CQADupstack*Retrieval`)가 대거 포함되어 평가의 깊이와 다양성을 입증합니다. 전반적으로 이 목록은 모델이 다루어야 할 학술, 소셜 미디어, 전문 지식 검색 등 거의 모든 텍스트 이해 시나리오를 아우르는 포괄적인 벤치마크 셋업을 제공합니다.

---

## MTEB (5/37)

제시된 텍스트는 MTEB(Massive Text Embedding Benchmark)의 세 가지 주요 벤치마킹 태스크인 Retrieval, Semantic Textual Similarity (STS), Summarization에 대한 정의를 설명합니다.

1. **Retrieval:** 이 태스크는 쿼리에 해당하는 관련 문서를 찾아내는 것을 목표로 하며, 모델은 쿼리와 코퍼스 문서를 임베딩하고 코사인 유사도를 계산하여 유사도를 측정합니다. 성능 평가는 nDCG@k, MRR@k, MAP@k, precision@k, recall@k 등을 사용하며, 특히 nDCG@10이 주요 지표입니다.
2. **Semantic Textual Similarity (STS):** 두 문장 쌍의 유사도를 결정하는 것이 목표이며, 모델이 문장을 임베딩하고 다양한 거리 측정 지표를 사용합니다. 이 경우, 코사인 유사도를 기반으로 한 스피어만 상관관계(Spearman correlation)가 주요 지표입니다.
3. **Summarization:** 기계가 생성한 요약본의 점수를 매기는 태스크로, 모델은 모든 요약을 임베딩하고 그 간 거리를 계산하여 점수를 산출합니다. 평가 시에는 피어슨 및 스피어만 상관관계가 사용되며, STS와 마찬가지로 코사인 유사도를 기반으로 한 스피어만 상관관계가 주된 측정 기준입니다.

*참고: Figure 2는 MTEB STS에서 최고의 모델(ST5-XXL)을 사용하여 100개의 샘플에 대한 코사인 유사도를 시각화한 자료입니다.*

---

## MTEB (6/37)

MTEB(Massive Text Embedding Benchmark)은 텍스트 임베딩 모델의 성능을 측정하며, 비교 유형에 따라 Sentence to sentence (S2S), Paragraph to paragraph (P2P), 그리고 Sentence to paragraph (S2P) 세 가지 범주로 분류된다. S2S 방식은 문장 대 문장의 유사도를 평가하며, 표에는 Glove, BERT, SimCSE-BERT-unsup, 그리고 SimCSE-BERT-sup 등의 다양한 모델들이 Clust., PairClass., Rerank., Retr., STS, Summ. 등의 여러 태스크에서 수치적 성능을 비교하고 있다. 특히 최신 모델들인 OpenAI Ada는 Similarity 70.44, 37.52 등 높은 평균 점수(Avg. 78.60)를 기록했으며, ST5-XXL은 73.42 등의 높은 점수를 보였다. 궁극적으로 이 표는 각 전문 용어와 모델명(예: MPNet-multilingual, GTR-XXL, ST5-XXL) 및 수치를 활용하여, 모델이 어떤 비교 형식에서 가장 강력한 성능을 내는지 비교 분석하는 자료이다.

---

## MTEB (7/37)

MTEB 데이터세트는 56개의 데이터셋을 포괄하며, ClimateFEVER와 FEVER처럼 같은 코퍼스를 활용하는 데이터셋들이 존재하고, SciDocsRR, SciFact, ArxivClustering 같은 과학 데이터셋들은 Reranking, Retrieval, Clustering 등 서로 다른 태스크에서 높은 유사성을 보입니다.

모델 평가는 0.1B부터 4B 모델 매개변수까지의 다양한 규모에서 Classification, Clustering, Retrieval 등 다양한 태스크에 걸쳐 벤치마킹되었습니다. 특히 Figure 3에 따르면, SGPT는 모델 크기와 함께 비중 편향(bias-only fine-tuning)을 통해 모델 사이즈가 커질수록 성능이 향상되며, 결국에는 Full Fine-tuning 수준으로 따라잡는 경향을 보였습니다.

모델들은 Self-supervised 방식(예: 마스크 및 문장 예측을 사용하는 BERT, SimCSE-Unsup)과 Supervised 방식(예: 인코더만 사용하는 BERT 또는 디코더만 사용하는 GPT)으로 그룹화됩니다.

---

## MTEB (8/37)

주요 임베딩 모델들은 기반 아키텍처와 파인튜닝 방식에 따라 다양하게 분류됩니다. BERT 기반 모델로는 `ever`, `LaBSE`, `SimCSE-BERT-sup` 등이 있으며, `SPECTER`는 `SciBERT`를 활용하고 `MPNet`이나 `MiniLM` 같은 모델은 다양한 데이터셋을 통해 파인튜닝된 임베딩 모델에 해당합니다. T5 모델의 인코더를 활용하는 `GTR`과 `ST5`는 각각 MSMARCO 및 NLI 데이터셋에 대해 각각 검색 작업 및 STS 작업에 특화된 contrastive fine-tuning을 수행합니다.

최신 방법론으로는 GPT 디코더 기반의 `SGPT` BiEncoders가 <0.1%의 파라미터 가중 평균 풀링을 사용하여 contrastive fine-tuning을 수행하며, `cpt-text`는 사전 학습된 GPT 디코더를 두 단계 과정으로 통과시키는 방식을 사용합니다. 또한, 비-트랜스포머 아키텍처 중 `LASER`가 LSTM을 기반으로 한 유일한 context-aware 모델로 언급됩니다.

결론적으로, 본 논문은 `Glove`, `LASER`, `WordEmbeddings`, `MiniLM-L6`, `SGPT-5.8B-msmarco` 등 다양한 모델들의 성능(MTEB Score), 속도(Speed), 크기(Size)를 비교하며 임베딩 모델의 광범위한 비교벤치마크를 제공합니다.

---

## MTEB (9/37)

1. 전반적으로 MTEB의 7가지 영어 태스크에서는 모델 간 성능 편차가 크며, self-supervised와 supervised 방법 사이에 여전히 큰 격차가 존재하지만, self-supervised large language models가 자연어 생성 태스크에서 이 격차를 줄이는 추세입니다.
2. 성능은 모델 크기와 강한 상관관계를 보이며 다수의 MTEB 태스크는 수십억 개 매개변수 모델이 지배적이나, 이는 상당한 비용을 수반합니다.
3. Classification 태스크에서는 ST5 모델이 대부분의 데이터셋에서 지배적이며, ST5-XXL이 최고의 비-ST5 모델인 OpenAI Ada Similarity보다 평균 성능에서 3% 앞서는 가장 높은 성능을 보였습니다.
4. Clustering 태스크에서 MPNet 모델은 거의 50x 작음에도 불구하고 ST5-XXL과 견줄 만한 성능을 보였는데, 이는 MPNet이 다양한 데이터셋에 대해 미세 조정되었기 때문일 수 있습니다.
5. 나아가, Ada Search 엔드포인트의 검색 쿼리 임베딩은 NLI 대비 MSMARCO 데이터셋이 훨씬 크다는 점 때문에 각각 SGPT-nli 및 Ada Similarity 엔드포인트와 경쟁할 수 있는 성능을 보일 수 있습니다.

---

## MTEB (10/37)

MTEB 평가 결과, Bitext mining에서는 LaBSE가 우위를 점했으며, SGPT-BLOOM-7B1-msmarco와 같은 모델은 BLOOM이 사전 학습된 언어(Chinese, French, Portuguese)에서 성능 우위를 보였습니다. Pair Classiﬁcation에서는 GTR-XL과 GTR-XXL이 가장 강력한 성능을 보였으며, Reranking에서는 MPNet과 MiniLM 같은 모델들이 좋은 성능을 나타냈습니다. 특히, Retrieval 작업에서는 SGPT-5.8B-msmarco가 BEIR subset 및 전체 BEIR 벤치마크에서 최고의 임베딩 모델로 확인된 반면, STS 작업에서는 ST5XXL이 최고 성능을 기록했습니다. 이러한 결과는 임베딩 모델 분야가 Retrieval(비대칭적) 용도와 Similarity(대칭적) 용도로 분화(bifurcation)되고 있음을 강조하며, 효율성 측면에서는 Glove가 성능과 속도 모두에서 선두를 차지했습니다.

---

## MTEB (11/37)

Massive Text Embedding Benchmark (MTEB)는 112개 언어를 포괄하는 8개의 텍스트 임베딩 작업을 포함하며, 이를 통해 신뢰할 수 있는 임베딩 성능 추정치를 제공하는 것을 목표로 합니다. 모델 선택 시, GTRXXL, ST5-XXL 또는 SGPT-5.8B는 고성능이지만 느린 모델 군을 대표하며, SGPT-5.8B는 높은 차원의 임베딩으로 인해 추가적인 저장 공간을 요구하는 단점이 있습니다. 다국어 성능 면에서는, 비텍스트 마이닝(Bitext Mining)에서 LaBSE가 전반적으로 강력한 성능을 보였으며, 다국어 분류 및 STS에서는 multilingual MPNet이 전반적으로 가장 강력한 성능을 보였고, SGPT-BLOOM-7B1-msmarco는 특정 언어(예: Hindi, Portuguese, Chinese or French)에서 SOTA 성능을 제공합니다. 궁극적으로, MTEB는 30개 이상의 모델에 대한 거의 5,000번의 실험을 거쳐 텍스트 임베딩의 기반을 마련하고, 미래 연구를 위한 견고한 베이스라인을 설정했습니다.

---

## MTEB (12/37)

제시된 텍스트는 논문의 본문 내용보다는 MTEB(Massive Text Embeddings Benchmark)의 활용 범위, 학술적 기여, 그리고 연구 인프라에 대한 후기(Acknowledgement)와 참조 문헌 목록으로 구성되어 있습니다.

요약:
이 작업은 텍스트 임베딩(text embeddings)의 다양한 응용 분야를 다루며, MTEB 코드를 통해 작업, 데이터셋 또는 지표에 대한 기여를 활발히 받고 있습니다. 해당 연구는 Institut du développement et des ressources en informatique scientiﬁque (IDRIS) du Centre national de la recherche scientiﬁque (CNRS)의 HPC 자원과 Grand équipement national de calcul intensif (GENCI)의 지원을 받아 진행되었습니다. 구체적으로 모든 평가와 데이터 처리는 IDRIS의 Jean Zay cluster에서 수행되었으며, 이 프로젝트는 SemEval-2012, Semeval-2013, Semeval-2014, Semeval-2015와 같은 선행 Semantic Textual Similarity(STS) 작업 및 광범위한 학술 문헌에 근거를 두고 있습니다.

---

## MTEB (13/37)

제공된 논문들은 2017년부터 2022년 사이에 발표된 방대한 NLP 연구의 스펙트럼을 포괄합니다. 핵심 모델로는 언어 이해를 위한 BERT (Deep bidirectional transformers for language understanding)와 대규모 오토회귀 모델인 GPT-NeoX, 그리고 PALM이 포함됩니다. 이 연구들은 전 세계 언어에 걸친 질의 응답을 위한 Xor qa 및 Tydi qa와 같은 다양한 벤치마크를 정의하고, SciBERT와 같이 특정 도메인(scientific text)에 최적화된 전처리된 언어 모델을 제시합니다. 또한, 문장 표현력을 높이는 Senteval이나 Top2vec 같은 범용 문장 임베딩 기술을 다루며, 바른 모델 구축을 위해 아키텍처 개선(e.g., Borgeaud et al.의 "retrieving from trillions of tokens") 및 차원 간 검색(Cross-modal retrieval)과 같은 응용 분야를 탐구합니다.

---

## MTEB (14/37)

본 논문 목록은 최신 자연어 처리(NLP)의 핵심 방법론, 특히 임베딩, 검색(Retrieval), 그리고 평가(Evaluation)의 발전을 보여줍니다. 초기에는 Long short-term memory (Hochreiter and Schmidhuber, 1997) 같은 기초 모델을 기반으로 시작되었으며, 이후 Massive (FitzGerald et al., 2022)와 같은 대규모의 다국어 데이터셋을 활용하는 추세가 확산되었습니다.

핵심 기술 측면에서는 Simcse: Simple contrastive learning of sentence embeddings (Tianyu Gao et al., 2021b)와 같은 Contrastive Learning 기법을 사용하여 언어 모델의 범용적인 문장 임베딩을 구축하고, 이를 바탕으로 언어 불가지론적(Languageagnostic) BERT sentence embedding (Fangxiaoyu Feng et al., 2020) 및 Unsupervised corpus aware language model pre-training (Luyu Gao and Jamie Callan, 2021)을 통해 Dense Passage Retrieval을 수행합니다.

또한, 모델의 성능을 검증하는 평가 체계가 강화되었는데, Summarization 평가의 재평가를 위한 Summeval (Alexander R. Fabbri et al., 2020)이나 Few-shot language model evaluation framework (Leo Gao et al., 2021a)와 같은 표준화된 평가 도구가 주목받고 있습니다. 전반적으로 이 분야는 임베딩 개선과 더불어, 낮은 자원 언어(low-resource languages)에 대한 비텍스트 마이닝 및 다양한 시나리오를 포괄하는 포괄적인 테스트 환경 구축에 집중하고 있습니다.

---

## MTEB (15/37)

제시된 논문 목록은 자연어 처리(NLP) 및 인공지능 분야의 광범위한 발전 과정을 포괄하며, 연구 초점은 기초적인 단어 임베딩부터 최첨단 멀티모달 생성까지 다양합니다. 초기 연구부터 `Maas` et al. (2011)의 word vectors for sentiment analysis와 같이 기초적인 기술을 다루는 반면, 현대적 접근법은 `akur` (2021) 같은 커뮤니티 라이브러리를 통해 데이터 자원 구축에 집중합니다.

임베딩 학습 측면에서는 `Neelakantan` et al. (2022)의 Text and code embeddings by contrastive pretraining이나 `Sentence-t5: Scalable sentence encoders from pre-trained text-to-text models` (Ni et al., 2021a)와 같이 대규모 사전 훈련 모델을 활용한 고도화된 표현 학습이 두드러집니다. 또한, `Mtop: A comprehensive multilingual task-oriented semantic parsing benchmark` (2020)와 같이 특정 도메인이나 다국어 기능을 위한 정교한 벤치마크와 데이터셋 개발이 활발합니다.

나아가 모델 구조 및 응용 분야는 매우 폭넓어, `Glide: Towards photorealistic image generation and editing with text-guided diffusion models` (2112.10741)와 같은 텍스트 기반의 이미지 생성 모델부터, `Muennighoff` et al. (2022)의 Crosslingual generalization through multitask finetuning처럼 다국어 일반화 능력을 높이는 방향으로 진화하고 있습니다. 이는 소프트웨어 포럼을 위한 Q&A 검색(`Linkso: a dataset for learning to retrieve similar question answer pairs` (2018))이나 반사실 탐지(`product reviews`에 대한 Dataset) 등 구체적이고 전문화된 NLP 태스크에 적용됩니다.

---

## MTEB (16/37)

제시된 논문들은 머신러닝의 기본 프레임워크부터 최신 대규모 언어 모델(LLM)의 발전사까지 포괄하는 방대한 내용을 다룹니다. 초기에 *Scikit-learn* (2011) 같은 일반적인 ML 도구와 *GloVe* (2014)를 통해 효율적인 단어 표현(global vectors) 방법론을 확립했습니다. 이후, *BERT* 기반의 *Sentencebert* (2019)나 *MPNet* (2020)처럼 컨텍스트를 활용한 임베딩 전처리 기법이 발전했으며, *OpenAI blog* (2019)는 언어 모델의 비지도 다중 작업 학습 능력에 주목했습니다. 나아가 *T5* (2020)는 모든 작업을 처리하는 통합적인 'text-to-text transformer' 구조를 제안했고, *BLOOM* (2022)과 같은 176b parameters급 대형 모델이 등장하며 학계의 기술적 한계를 탐구했습니다. 이와 동시에, 단순히 텍스트 이해를 넘어 *Photorealistic text-to-image diffusion models* (2022)와 같은 다중 모달리티 결합 및 *CARER* (2018)와 같은 감정 인식 등 특화된 응용 분야까지 연구 범위가 확장되고 있습니다.

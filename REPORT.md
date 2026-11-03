# RAG Project Evaluation Report

## 1\. Introduction

This project evaluates a Retrieval-Augmented Generation (RAG) application using the Kestrel knowledge base and a custom corpus. The goal is to assess retrieval quality, compare chunking configurations, understand what a language model can answer without document context, and identify possible causes of retrieval failures.

The evaluation includes:

* Retrieval recall at different values of k.
* Comparison of two chunk size and overlap configurations.
* A manually assessed no-context baseline using ten questions.
* Vocabulary analysis using the Words tab.
* Discussion of limitations and potential improvements.

## 2\. Evaluation Method

Two retrieval configurations were compared:

|Configuration|Chunk size|Overlap|
|-|-:|-:|
|Baseline|180|35|
|Smaller chunks|100|20|

Both configurations were evaluated on the Kestrel and custom corpora. Recall was measured at k = 1, 3, 5, and 10.

The evaluation command completed successfully using `npm run evaluate`. The reported output was saved to:

`results/cli-evaluation-1793651681052.json`

A separate no-context baseline was conducted by submitting ten questions to the configured language model without providing retrieved document context. The responses were compared manually with the expected evidence.

## 3\. Retrieval Evaluation Results

### 3.1 Kestrel corpus

|Configuration|Recall@1|Recall@3|Recall@5|Recall@10|
|-|-:|-:|-:|-:|
|Baseline (180/35)|50.0%|62.5%|75.0%|87.5%|
|Smaller chunks (100/20)|50.0%|75.0%|87.5%|87.5%|

The smaller-chunk configuration improved Recall@3 by 12.5 percentage points and Recall@5 by 12.5 percentage points. Recall@1 remained unchanged at 50%, while Recall@10 remained at 87.5%.

This suggests that the smaller chunks helped retrieve relevant evidence within the first several results, although they did not improve the likelihood of finding relevant evidence in the first position. At k = 10, both configurations performed identically.

### 3.2 Custom corpus

|Configuration|Recall@1|Recall@3|Recall@5|Recall@10|
|-|-:|-:|-:|-:|
|Baseline (180/35)|72.7%|100.0%|100.0%|100.0%|
|Smaller chunks (100/20)|81.8%|100.0%|100.0%|100.0%|

On the custom corpus, the smaller-chunk configuration improved Recall@1 from approximately 72.7% to 81.8%. Both configurations achieved 100% recall at k = 3, 5, and 10.

This indicates that the relevant evidence was retrieved within the top three results for all evaluated custom-corpus questions under both configurations. The improvement at k = 1 suggests that smaller chunks may help rank relevant evidence earlier.

### 3.3 Overall comparison

The smaller-chunk configuration performed better at several retrieval cutoffs. The clearest improvement was on the Kestrel corpus at Recall@3 and Recall@5. On the custom corpus, the improvement was limited to Recall@1 because both configurations already reached 100% recall at k = 3.

These results support testing smaller chunks as a practical configuration. However, recall alone does not measure answer correctness, factual support, or the quality of the final response. Those aspects require separate answer-level evaluation.

## 4\. No-Context Baseline

Ten questions were submitted to the language model without document context. The responses were manually assessed against the expected evidence.

|Question|Type|Assessment|Main observation|
|-|-|-|-|
|q01|Exact identifier|Correct, substantially|Identified the allowlist issue and both IP addresses, but included additional unverified claims.|
|q02|Exact identifier|Correct, substantially|Identified the seat limit and the main corrective actions.|
|q03|Split answer|Partial|Gave a 14-day grace period instead of 21 days and omitted suspension at day 60.|
|q04|Split answer|Correct, substantially|Identified the relevant plans and the main setup sequence, with an additional unverified claim.|
|q05|Different vocabulary|Partial|Omitted backup-code guidance and the special case where the user is the only Admin or Owner.|
|q06|Two versions|Correct, substantially|Identified the 2026 60-day refund window, but included additional details that were not verified.|
|q07|Two versions|Correct, substantially|Identified the 20% annual discount but did not compare it with the older 2025 policy.|
|q08|Two hops|Partial|Identified the general delivery/postroom area but omitted the expected team, channel, and escalation details.|
|q09|Not in corpus|Correct abstention|Did not claim to know whether an iPhone application exists.|
|q10|Not in corpus|Correct abstention|Did not invent a Business-plan seat price and indicated that the information was unavailable.|

### 4.1 Interpretation

The no-context baseline shows that the language model could answer some product and support questions from general knowledge or previously learned information. However, several responses were incomplete or included details that did not match the expected evidence.

The payment-failure question illustrates the risk of relying on general knowledge: the response gave a 14-day grace period instead of the expected 21 days and omitted the 60-day suspension point. The account-recovery response also omitted important steps, while the two-hop support question lacked the exact team and escalation details.

The responses to the two unanswerable questions were appropriately cautious. This is important because a RAG system should distinguish between information supported by its documents and information that is unavailable.

These results are a manual assessment of the no-context responses, not a machine-generated answer-quality score. The assessment does not establish that the RAG application itself generates correct answers for all ten questions.

## 5\. Words Tab and Vocabulary Analysis

### 5.1 Corpus overview

The Words tab displayed the following statistics:

|Metric|Observed value|
|-|-:|
|Documents|5|
|Chunks|34|
|Vocabulary terms|884|

The vocabulary search allows a term to be checked for presence and shows the number of matching chunks and the documents in which it occurs.

### 5.2 Kestrel analysis: KST-2044

The following results were observed in the Words tab:

|Search term|Result|Documents or notes|
|-|-|-|
|`KST-2044`|1 matching chunk|`support-runbook-errors.md`|
|`allowlist`|2 matching chunks|`product-guide.md`, `support-runbook-errors.md`|
|`203`|4 matching chunks|Multiple documents|
|`113`|4 matching chunks|Multiple documents|
|`10`|11 matching chunks|Multiple documents|

The identifier `KST-2044` is present in the corpus, and the term `allowlist` occurs in two matching chunks. This provides evidence that the main troubleshooting terminology is available in the indexed documents.

The searches for `203`, `113`, and `10` returned separate numeric terms. These results do not prove that the complete IP address `203.0.113.10` appears in each matching chunk.

### 5.3 Kestrel miss diagnosis

**Observed evidence:** The error identifier appears in one chunk, and the word `allowlist` appears in two chunks.

**Possible explanation:** If a question about KST-2044 is missed by retrieval, one possible cause is that the relevant chunk is not ranked highly enough for the query. Another possibility is that the query wording does not closely match the wording in the relevant chunk.

**Potential improvement:** Give distinctive error identifiers greater importance during retrieval and ensure that the error code, its cause, and its resolution remain accessible together.

This explanation remains a hypothesis. The vocabulary results establish term presence but do not, by themselves, prove the cause of an individual retrieval miss. Confirming the cause would require comparing a specific failed query with its retrieved chunks and their ranking.

### 5.4 Custom-corpus analysis

The aggregate evaluation shows that custom-corpus Recall@1 was below 100% for both configurations, while Recall@3 reached 100%. This indicates that the first result was not always sufficient, even though relevant evidence was found within the first three results.

The aggregate metrics do not identify which specific vocabulary term caused a miss or whether the cause was absent evidence, poor ranking, or common terminology. A question-level inspection is therefore necessary before making a definitive diagnosis.

A useful follow-up would be to select a custom-corpus question that missed at Recall@1, search for its distinctive terms in the Words tab, and inspect the corresponding retrieved chunks. This would help determine whether the relevant evidence is absent, present but ranked poorly, or spread across multiple chunks.

## 6\. Pipeline Comparison and Configuration Choice

The two configurations produced different results across the two corpora.

For Kestrel, smaller chunks improved Recall@3 and Recall@5 but did not change Recall@1 or Recall@10. For the custom corpus, smaller chunks improved Recall@1 while both configurations achieved 100% recall at the other evaluated cutoffs.

Based on these measurements, the smaller-chunk configuration (100/20) is a reasonable choice when the priority is retrieving relevant evidence earlier in the result list. It performed at least as well as the baseline at every reported cutoff and improved several metrics.

This decision is based on retrieval recall. It does not establish that the smaller-chunk configuration produces better generated answers, because answer-level correctness and grounding were not measured by these aggregate recall figures.

## 7\. Limitations and Known Failures

The evaluation has several limitations:

1. **Retrieval and generation are different tasks.** High recall does not guarantee that the generated answer is correct or supported by the retrieved documents.
2. **The no-context assessment was manual.** The response categories reflect a comparison with expected evidence rather than an automated grading process.
3. **Some no-context answers contained unverified details.** A response can include the main expected information while also adding claims that are not supported by the expected evidence.
4. **Vocabulary presence does not establish retrieval success.** A term may be present in the corpus without the corresponding chunk being ranked highly for a particular question.
5. **The custom-corpus miss has not been diagnosed at question level.** The aggregate metrics show a difference between Recall@1 and Recall@3, but do not reveal the cause of an individual miss.
6. **The evaluation covers a limited set of questions.** The results may not represent every possible query or user phrasing.

These limitations should be considered when interpreting the results and selecting future improvements.

## 8\. Conclusion

The evaluation showed that retrieval performance depended on both the corpus and the chunk configuration. The smaller-chunk configuration improved Kestrel Recall@3 and Recall@5 and improved custom-corpus Recall@1. Both configurations achieved 100% Recall@3 on the custom corpus.

The no-context baseline showed that a language model can answer some questions without retrieval, but it may provide incomplete or outdated policy details. The unanswerable questions also demonstrated the importance of not inventing information that is absent from the available evidence.

The Words tab confirmed that the KST-2044 identifier and the term `allowlist` were present in the Kestrel corpus. However, vocabulary presence alone is not enough to establish why a particular question was missed. Further question-level inspection would be needed to confirm the cause of a custom-corpus retrieval miss.

Overall, the smaller-chunk configuration is a reasonable candidate based on the measured retrieval metrics. Further work should focus on examining individual misses, evaluating generated answers against retrieved evidence, and testing whether the retrieval improvements translate into more accurate and better-grounded responses.


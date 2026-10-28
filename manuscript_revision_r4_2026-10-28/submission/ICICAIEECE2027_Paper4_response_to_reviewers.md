# Response to Reviewers

**Paper ID:** 4
**Title:** Voice-Based AI Assistant Using Local API Integration
**Conference:** ICICAIEECE 2027
**Authors:** Anita Saroj, Pramod Mehra, Shashwat Malviya, Ritendra Negi, Siddhant Srivastava, Yash Rawat

We thank the reviewers for their constructive comments. Each comment is addressed below; each heading paraphrases the reviewer comment it answers. Section, table and figure numbers refer to the revised manuscript, which has been condensed to meet the six-page limit.

---

## Comment 1 (paraphrased): Expand the evaluation with larger test sets and baseline comparisons

**Response.** We replaced the earlier scenario table, which had no documented protocol, with a reproducible evaluation. The method is in Section IV and the results are in Section V.

* **Test set and baseline.** The test set has 52 questions drawn from a 22-page college-counselling catalogue: 40 answerable, 7 unanswerable and 5 ambiguous. Each question has a reference answer, required key facts and page-level evidence.
  * The RAG system and a no-RAG baseline each answered every question three times. The baseline uses the same LLM, system prompt and template, with retrieval disabled.
  * We also report an extraction ablation using pypdf (Table I).
* **Statistics.** The question is the unit of analysis. The three generations are averaged per question, so repeated generations are not treated as independent samples. We report bootstrap 95% confidence intervals and Wilcoxon signed-rank tests (Section IV-D).
  * Token F1: 0.364 vs. 0.250 (+0.114, 95% CI [+0.050, +0.180], p = 0.0006).
  * BLEU-4: 8.14 vs. 4.48 (+3.66, 95% CI [+1.46, +6.28]).
  * Key-fact recall: 0.297 vs. 0.054 (+0.243, 95% CI [+0.133, +0.358]). This metric uses scoring rules that were refined after the outputs were inspected and is not human-validated (Section IV-B); it is reported alongside the reading-based correctness check below.
* **Correctness beyond lexical overlap.**
  * Every answer that the key-fact rules credited as complete was also read against the source. 21 of 120 RAG generations were fully correct, against 1 of 120 for the baseline (better on 8 questions, worse on none; sign test p = 0.008).
  * We report that the rules still over-credited three RAG answers, and that fully-correct counts are a lower bound.
  * RAG did not improve abstention on unanswerable questions (15/21 vs. 16/21).
* **Retrieval** (Table II). Evidence was among the top three chunks for 52.5% of questions and reached the model for 35%. We identify this as the main limitation.
* **Exploratory filter ablation.** Disabling the similarity filter moved all measures in the same direction, but the differences were not conclusive. We report it as hypothesis-generating only.
* **Intent classification** (Table III, 120 utterances). Macro-F1 was 1.000 on straightforward inputs (n = 65), 0.125 on challenging ones (n = 55) and 0.598 overall.
* **Automation safety and latency** (Sections V-D and V-E, Table IV). Median end-to-end latency was 4.0 s (n = 10).

**Scope of the claims.**
* The evaluation covers one document.
* The annotations were drafted with generative-AI assistance before any system output was generated.
* After the runs, an author reviewed 53 sampled items:
  * all 29 correctness judgements for configurations A and B, all confirmed;
  * the annotations of 24 questions, 14 of which were corrected.
* The author also judged the two answers newly credited by the revised key-fact rules.
* The other annotations and judgements were not verified by a human, and no inter-annotator agreement was measured.
* For 12 questions whose key facts are relations (for example, a fee bound to tuition rather than to placements), the key-fact rules were refined after the outputs had been inspected.

These points are stated in Sections IV-A, IV-B and VII and in the Acknowledgment.

## Comment 2 (paraphrased): Report standard NLP metrics (F1, BLEU) for query responses

**Response.** Section IV-B defines both metrics:

* **Answer-level token F1** follows the SQuAD convention [26]. It uses the stated normalisation and multiset token overlap with one reference: P = c/|g|, R = c/|r|, F1 = 2PR/(P+R) (Eq. 1). It is averaged over the 40 answerable questions and three runs.
* **Corpus BLEU-4** [27] is computed with SacreBLEU 2.4.3 [28]: 13a tokenisation, exponential smoothing and the brevity penalty, with n-gram counts pooled per run.

The text states that both metrics measure lexical overlap and do not establish factual correctness. This is why key-fact recall and the reading-based correctness check are reported separately. Intent-classification macro-F1 is also reported separately and is explicitly distinguished from answer-level token F1.

## Comment 3 (paraphrased): Remove leftover template text in Section F

**Response.** We removed the IEEE template instruction paragraph ("After the text edit has been completed, the paper is ready for the template. Duplicate the template file …") and the fragment "Using the Template" from the end of the former Section II-F ("Research Gap"). After condensing, the Research Gap is now Section II-D. The revised file was searched, and none of this text remains.

We also inspected the whole manuscript and corrected the following:

* a caption that described the wrong figure;
* an incomplete sentence in the speech-processing subsection;
* a duplicated phrase;
* manually typed figure and table numbers, now replaced by the template's automatic caption numbering;
* reference entries split across lines;
* an author email hyperlink that pointed to an unrelated address.

The figures were redrawn so that their labels match the implementation and remain legible at column width. The former speech-pipeline figure was merged into Fig. 1 to meet the page limit. Figures 1–2 and Tables I–IV are numbered consecutively and referenced in the text. Every cited reference appears in the bibliography, and vice versa.

## Comment 4 (paraphrased): Broader trustworthy-AI discussion (privacy-preserving computation, accountability, data secrecy)

**Response.** We added Section VI, "Trustworthy AI Considerations". It cites the recommended chapter [29] (S. Sudarsan and N. Karra, "The future of trustworthy AI: Trends and predictions," in *Trustworthy AI Systems*, Springer Nature, 2026, pp. 247–261, doi: 10.1007/978-3-032-15606-8_15) as a general overview of the field.

For each topic, the section separates what the system implements from its limitations and from proposed improvements. We describe only controls that exist in the evaluated code, and list everything else as a proposal:

| Topic | Implemented (verified in code) | Stated limitation | Proposed, not implemented |
|---|---|---|---|
| Privacy-preserving computation | Recognition, embedding, retrieval and generation run on the host; no cloud service is called to answer a question | Not audited with network monitoring; model files downloaded on first use; URL commands open external sites | Offline mode, egress tests |
| Data confidentiality and key management | Audio and transcripts encrypted at rest with Fernet | Key in a local configuration file; temporary plaintext upload; reply audio unencrypted; no retention policy | Keychain or passphrase-derived keys, in-memory transcription, retention limits |
| Authentication and access control | None (stated explicitly); cross-origin requests limited to the local web interface | Start-up script binds all interfaces without authentication; face authentication is a stub | Loopback binding, per-session token, user authentication before commands |
| Accountability and transparency | Responses return the transcript, intent and retrieved sources; evaluation retains every prompt, output and score | Ungrounded answers are not marked; commands are not logged | Grounded/ungrounded labels, command log |
| Safe automation | – | Negated commands execute; "close" maps to "open" (measured in Section V-D) | Allow-list, negation detection, confirmation, low-confidence refusal |
| Reliable evaluation | Lexical metrics reported with key-fact, correctness, abstention and retrieval measures | Fact-level scores cannot detect an added false claim | – |

We also added an Acknowledgment disclosing the use of generative AI, following IEEE policy. It names the system, the sections involved and the extent of author review.

---

## Additional corrections made to match the implementation

We checked every technical statement against the evaluated source code and corrected the description accordingly:

| Submitted version | Revised version (as implemented) |
|---|---|
| AES-256-GCM, key derived from user credentials; decrypted audio never written to disk | Fernet (AES-128-CBC + HMAC-SHA256), key in a local configuration file; temporary plaintext upload file; reply audio unencrypted (Sections III-E, VI) |
| LLaMA 2 / Mistral 7B via llama-cpp-python, configurable sampling | llama3.2 (3.2B, Q4_K_M) via Ollama, default sampling (Section III-D) |
| PDF, DOCX, TXT and Markdown ingestion via LangChain; 500-token chunks; top-5 | Plain-text ingestion only; 500-character chunks with 100-character overlap; top-3 with a cosine > 0.5 filter. The evaluation PDF was converted to text outside the application (Sections III-C, IV-A) |
| PyAudio capture, WebRTC VAD, high-pass filtering | Browser MediaRecorder upload; no backend pre-processing (Section III-A) |
| Keyword list including "search", "volume", "shutdown", with a threshold | Substring match on open/launch/start/play/close, no threshold (Section III-B) |
| Windows/Linux automation with volume, power and shutdown confirmation | macOS application/URL launching only; no confirmation (Section III-D) |
| Optional face authentication | Placeholder, not enforced (Section III-E) |
| API bound to the local interface | The supplied start-up script binds all interfaces without authentication (Sections III-E, VI) |
| Results on i7-12700 / RTX 3060; 92–100% task accuracy; 85–95% ASR accuracy | Removed (no supporting data or protocol) and replaced by the evaluation above on Apple M4. ASR accuracy on real speech was not evaluated, and this is stated as a limitation |

References that were uncited or cited for unrelated claims were removed: LangChain, two journal articles (on e-commerce recommendation and on victim detection), OpenCV, and the Montreal Forced Aligner. Verified references for BLEU, SacreBLEU and SQuAD token F1 were added.

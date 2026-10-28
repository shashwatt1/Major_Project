# -*- coding: utf-8 -*-
"""Revised manuscript text, v3 (r4: BLEU-4 from unrounded run scores; key-fact disclosures; 6-page target). Citation keys in {braces} are numbered by build_docx.py in
order of first appearance. Inline markup: *italic*. Every number comes from evaluation/paper_ready_tables.md
(validated in evaluation/deadline_audit.md and evaluation/audit/). Previous version: content_v1_7pages.py."""

ABSTRACT = (
    "Cloud-based voice assistants raise concerns about privacy, network dependence and factually unsupported "
    "answers from large language models (LLMs). This paper presents a locally hosted, modular voice assistant that "
    "combines Whisper speech recognition, a rule-based intent classifier, retrieval-augmented generation (RAG) over "
    "local text documents, a 3.2-billion-parameter LLM served through Ollama, macOS application automation, and "
    "encrypted storage of recorded audio and transcripts behind a FastAPI interface. We evaluate it on a 22-page "
    "college-counselling catalogue with 52 questions (40 answerable, 7 unanswerable, 5 ambiguous), three "
    "generations per question, and a no-retrieval baseline using the same model and prompt template. Retrieval raised "
    "answer-level token F1 from 0.250 to 0.364 (paired difference +0.114, 95% CI [+0.050, +0.180], p < 0.001) and "
    "corpus BLEU-4 from 4.48 to 8.14; reading-based checks found 21 of 120 RAG generations fully correct against 1 of 120 "
    "without retrieval. Retrieval coverage was the main limitation: the annotated evidence was among the top three "
    "chunks for 52.5% of questions and reached the model after the similarity filter for 35%, and RAG did not improve "
    "abstention on unanswerable questions. The keyword intent classifier reached a macro-F1 of 1.000 on "
    "straightforward inputs but 0.125 on paraphrases, keyword traps and negations. The median end-to-end latency on "
    "an Apple M4 laptop was 4.0 s. The findings are specific to one document, and the evaluation annotations were "
    "drafted with AI assistance, with only a sample reviewed by an author."
)

KEYWORDS = ("Voice Assistant, Speech Recognition, Retrieval-Augmented Generation, Local API, FastAPI, "
            "Large Language Models, Intent Classification, Trustworthy AI")

ACKNOWLEDGMENT = (
    "Generative AI (Claude, Anthropic) was used in this work beyond language editing. It drafted the 52 evaluation "
    "questions, reference answers, key-fact and evidence annotations and the 120 intent labels (Section IV), made the "
    "reading-based correctness and abstention judgements reported in Section V, wrote and ran the evaluation and "
    "metric-verification scripts whose outputs appear in Tables I–IV, drafted the key-fact scoring rules, redrew "
    "Figs. 1 and 2, and drafted revisions of the manuscript text. An author reviewed 53 sampled items (all 29 "
    "correctness judgements for configurations A and B, all confirmed, and the annotations of 24 questions, 14 "
    "corrected) and judged the two answers newly credited by the revised scoring; the other annotations and "
    "judgements were not verified by a human. The authors are responsible for the content of this paper."
)

BODY = [
    ("H1", "Introduction"),
    ("P", "Voice-based assistants let people use computers through natural speech, and early products such as "
          "Apple’s Siri (2011) and Amazon Echo (2014) set expectations of constant availability, low latency and "
          "natural-language access to services {apple}, {amazon}. Commercial assistants, however, send raw or partially "
          "processed speech to remote servers for recognition and inference {kepuska}. Users lose direct control over "
          "their audio, documented cases of retained and human-reviewed recordings have raised questions of informed "
          "consent {metz}, and network-dependent systems stop working offline. The LLMs behind modern assistants also "
          "produce fluent but factually unsupported answers {maynez}, because standard inference does not consult the "
          "user’s documents {ji}, and closed ecosystems prevent developers from replacing components or adding "
          "knowledge sources."),
    ("P", "This paper describes a locally hosted, modular voice assistant. Speech is transcribed on the host with "
          "OpenAI Whisper {radford}; a rule-based intent classifier routes each transcript either to an operating-system "
          "(OS) automation module or to a retrieval-augmented generation (RAG) pipeline that retrieves passages from a "
          "local vector index and passes them to a locally served LLM {gao2023}; recorded audio and transcripts are "
          "encrypted at rest; and the modules are exposed through a FastAPI REST interface {fastapi}. Quantised LLMs that "
          "run on consumer hardware {dettmers8bit}, {qlora} and efficient vector search {johnson} make such a design "
          "practical."),
    ("P", "The contributions are: (i) a description of the implemented architecture with its actual components and "
          "limitations; (ii) a reproducible evaluation of answer quality with and without retrieval, retrieval coverage, "
          "intent classification, automation safety and latency, combining lexical metrics with reading-based "
          "correctness checks; and (iii) a trustworthy-AI analysis that separates implemented safeguards from proposed "
          "ones. Section II reviews related work, Section III describes the implementation, Sections IV and V present the "
          "evaluation, Section VI discusses trustworthy AI, and Sections VII and VIII give limitations and conclusions."),

    ("H1", "Literature Review"),
    ("H3", "Voice Assistants and Speech Recognition"),
    ("P", "Early automatic speech recognition (ASR) combined hidden Markov models with Gaussian mixture models "
          "{rabiner}, and offline recognisers such as CMU Sphinx handled only limited vocabularies {pocketsphinx}. "
          "Whisper, a transformer-based ASR system trained on 680,000 hours of weakly supervised multilingual audio, is "
          "robust across acoustic conditions without fine-tuning, and its open weights make accurate recognition "
          "feasible on local hardware {radford}. Commercial assistants instead keep a thin client on the device and send "
          "audio to the cloud {kepuska}, which excludes offline use and creates a privacy surface that has been "
          "exploited in documented incidents {metz}."),
    ("H3", "Language Models and Retrieval-Augmented Generation"),
    ("P", "The transformer replaced recurrence with self-attention {vaswani}; BERT showed the value of bidirectional "
          "pre-training {devlin}, GPT-style models extended the architecture to fluent long-form generation {brown}, and "
          "scaling laws related performance to model size and compute {kaplan}. Post-training quantisation such as "
          "GPTQ {gptq} made multi-billion-parameter models usable on commodity hardware. Because such models answer from "
          "parameters fixed at training time, RAG retrieves passages from a document index and conditions generation on "
          "them {lewis}. Surveys classify RAG systems as naive, advanced or modular and identify retrieval accuracy and "
          "context integration as recurring problems {gao2023}, {gaomodular}. Dense sentence-transformer retrievers "
          "outperform sparse methods on semantically difficult queries {reimers}, and FAISS provides efficient "
          "nearest-neighbour search {johnson}."),
    ("H3", "Authentication and Secure Data Processing"),
    ("P", "Speaker-verification systems based on deep embeddings report equal error rates below 1% on standard "
          "benchmarks {snyder}, but voice biometrics degrade with noise and are exposed to replay and cloning attacks. "
          "AES remains the most widely used symmetric cipher for data at rest {nist}; authenticated encryption adds "
          "integrity protection, but a key stored next to the data it protects offers little protection if the host is "
          "compromised. Stored data and trained models can also leak information about individuals, as "
          "membership-inference attacks show {shokri}, which argues for minimising retained data."),
    ("H3", "Research Gap"),
    ("P", "In the literature reviewed, we did not identify an open-source system that combines local ASR, "
          "retrieval-grounded LLM answers, OS automation and encrypted storage of interaction data behind one local REST "
          "interface together with a quantitative evaluation of answer quality. Commercial assistants rely on cloud "
          "processing, RAG research focuses largely on server-scale deployments, and local frameworks such as Home "
          "Assistant and Open Assistant provide only part of this functionality. This work contributes such an "
          "implementation and an evaluation that reports its limitations explicitly."),

    ("H1", "System Design and Implementation"),
    ("H3", "Architecture and Speech Processing"),
    ("P", "The backend is written in Python 3.13; a React web interface records audio with the browser’s MediaRecorder "
          "interface and uploads it to the */assistant/run* endpoint (Fig. 1). The backend stores a Fernet-encrypted copy "
          "of the upload, writes it to a temporary file, transcribes it with the openai-whisper implementation of the "
          "Whisper *base* model on the CPU (half precision disabled, default decoding), deletes the temporary file, "
          "encrypts and stores the transcript, and classifies the transcript as a command or a query. No voice-activity "
          "detection or signal pre-processing is applied. Commands go to the automation module and queries to the RAG "
          "pipeline; the reply is synthesised to speech and returned with the transcript, the detected intent and the "
          "retrieved sources. Each module also has its own endpoint (*/stt/transcribe*, */llm/generate*, */rag_query*, "
          "*/execute/run*, */tts/speak*)."),
    ("FIG", 1, "Implemented processing pipeline, from browser recording to the spoken reply."),
    ("H3", "Intent Classification"),
    ("P", "The classifier lower-cases the transcript and labels it a command if any of the substrings “open”, "
          "“launch”, “start”, “play” or “close” occurs anywhere in it; otherwise it is a query. There is no confidence "
          "threshold and no separate class for retrieval and general queries. The rule is fast and transparent, but "
          "because it matches substrings it sends questions such as “which college is closest to Delhi” to the "
          "automation module and treats negated commands such as “don’t open Chrome” as commands (Section V-D)."),
    ("H3", "Retrieval-Augmented Generation"),
    ("P", "The loader reads plain-text (.txt) files from a local knowledge directory; PDF, DOCX and Markdown files are "
          "not read natively. Text is whitespace-normalised and split into 500-character windows with a 100-character "
          "overlap, embedded with the all-MiniLM-L6-v2 sentence-transformer {reimers} into 384-dimensional unit vectors, "
          "and stored in an exact FAISS *IndexFlatL2* index {johnson} built in memory (Fig. 2). At query time the three "
          "nearest chunks are retrieved and a chunk is kept only if its squared L2 distance is below 1.0, i.e., cosine "
          "similarity above 0.5. Kept chunks are inserted into a prompt that tells the model to use the context only if "
          "relevant and otherwise to answer from its own knowledge; if no chunk passes, the question is sent without "
          "context, and the user is not told which path produced the answer."),
    ("H3", "Generation, Speech Synthesis and Automation"),
    ("P", "Answers are generated by *llama3.2* (3.2 billion parameters, Q4_K_M quantisation) served locally by Ollama "
          "0.19.0, with a fixed system prompt requesting concise plain text. No sampling options are sent, so the "
          "runtime defaults apply and generation is not seeded. Replies are synthesised with the macOS *say* command and "
          "converted with ffmpeg to WAV. The automation module runs only on macOS: it opens applications with *open -a* "
          "using 25 aliases or, for phrases of the form “open/launch/start X”, the title-cased name X, and opens http(s) "
          "URLs in the default browser. Closing applications, volume, file and power control are not implemented, and "
          "no confirmation is requested before acting."),
    ("FIG", 3, "RAG pipeline as implemented: offline chunking and FAISS indexing of local text files, and online top-3 "
               "retrieval with a similarity filter before prompt assembly."),
    ("H3", "Data Protection and API Access"),
    ("P", "Uploaded audio and transcripts are encrypted with Fernet (AES-128-CBC with an HMAC-SHA256 tag) before being "
          "written to disk. The key is read from an environment variable stored in a local configuration file, without "
          "passphrase-based derivation. The plaintext upload exists briefly as a temporary file, and synthesised reply "
          "audio is stored unencrypted. The supplied start-up script binds the API to all network interfaces without "
          "authentication; cross-origin requests are limited to the local web interface. A face-authentication module "
          "exists only as a stub that accepts every request and is not called by the pipeline."),

    ("H1", "Evaluation Methodology"),
    ("H3", "Dataset and Scope"),
    ("P", "The knowledge source is one 22-page PDF catalogue of 22 engineering institutions prepared for college "
          "counselling. Because the application reads only text, the PDF was converted to text outside the application "
          "with Apple PDFKit and indexed, with the application’s existing knowledge file, by the unmodified retrieval "
          "code (123 chunks, 114 from the catalogue). The test set contains 52 questions drafted from the rendered pages "
          "with generative-AI assistance (see Acknowledgment): 40 answerable (13 numeric, 9 factual, 7 cross-page "
          "comparisons, 4 dates, 3 relationships, 3 multi-passage, 1 definition), 7 unanswerable and 5 ambiguous. Each "
          "question has a paraphrased reference answer, required key facts, and page-level evidence quotes. All "
          "annotations were drafted by a single AI annotator before any system output was generated. Afterwards an author "
          "reviewed the annotations of 24 questions and corrected 14 (key facts and evidence), and one reference answer "
          "was amended to state the full-programme scope printed in the catalogue; the remaining annotations were not "
          "human-verified. Results therefore describe performance on this catalogue only."),
    ("H3", "Configurations and Answer-Quality Metrics"),
    ("P", "Configuration A (RAG) is the full pipeline. Configuration B (no-RAG) uses the same model, system prompt and "
          "prompt template with retrieval disabled. Configuration C replaces the PDFKit text with pypdf extraction. Each "
          "configuration answered every question three times with default settings; no reference or evidence text "
          "appeared in any prompt."),
    ("P", "*Answer-level token F1* follows SQuAD {rajpurkar}: answer *g* and reference *r* are normalised (NFKC, "
          "lower-casing, digit-group commas removed, dashes and slashes to spaces, punctuation and symbols deleted, "
          "articles removed) and tokenised on whitespace. With *c* the size of their multiset intersection,"),
    ("EQ", "P = c / |g|,    R = c / |r|,    F1 = 2PR / (P + R).", "(1)"),
    ("P", "F1 is averaged over the 40 answerable questions per run and then over runs. *Corpus BLEU-4* {papineni} is "
          "computed with SacreBLEU 2.4.3 {post} (nrefs:1|case:mixed|eff:no|tok:13a|smooth:exp): 13a tokenisation, "
          "uniform 1–4-gram weights, exponential smoothing and brevity penalty, with counts pooled over the 40 questions "
          "of a run and the three run scores averaged. Both metrics measure lexical overlap with one reference and do "
          "not establish factual correctness. *Key-fact recall* is the share of required facts found in the answer by "
          "phrase matching; for 12 questions whose facts are relations (a figure bound to tuition or placements, a grade "
          "to an institution, a fee to its scope), rules require the value to be bound to its subject (in the same clause, or "
          "in a list naming it) and reject "
          "negated, hedged or per-year statements. These rules were refined after outputs were inspected. Because "
          "such rules can still credit a correct figure inside a wrong statement, every generation credited with all key "
          "facts was also read against the PDF and counted as *fully correct* only if it stated the requested facts "
          "without a contradiction; this count is a separate, lower-bound assessment. Responses to unanswerable and ambiguous questions were read and labelled as "
          "abstentions, clarifications or unsupported answers."),
    ("H3", "Retrieval, Intent and Automation Metrics"),
    ("P", "A chunk is relevant if it contains an annotated evidence quote from the cited page. Precision@*k* is the "
          "number of relevant chunks in the top *k* divided by *k*, Recall@*k* the fraction of a question’s evidence "
          "groups covered, and Hit@*k* whether any relevant chunk was retrieved. For intent classification, 120 "
          "utterances (60 commands, 60 queries) were labelled; negated or cancelled commands count as queries. The "
          "straightforward subset (*n* = 65) contains canonical and polite commands and plain questions; the challenging "
          "subset (*n* = 55) contains keyword-free commands, questions containing keyword substrings, negations and "
          "mixed requests. We report macro-F1 (unweighted mean of the two class F1 scores, scikit-learn 1.8.0), which is "
          "unrelated to answer-level token F1. Forty automation commands with expected actions were run through the "
          "classifier and automator with process launching intercepted, and six launches of built-in applications were "
          "verified live; no destructive command was executed."),
    ("H3", "Statistical Analysis and Latency"),
    ("P", "The unit of analysis is the question: the three generations are averaged per question, and configurations "
          "are compared on 40 paired values, so repeated generations are not treated as independent samples. We report "
          "mean paired differences with percentile bootstrap 95% confidence intervals (10,000 question resamples; 1,000 "
          "for BLEU with corpus BLEU recomputed per resample) and two-sided Wilcoxon signed-rank tests (SciPy 1.17.1, zero "
          "differences excluded), and a sign test for the fully-correct counts. Latency was measured with "
          "*time.perf_counter* on an Apple M4 laptop (16 GB RAM, macOS 26.6.2) after two warm-up calls: 20 calls per "
          "component and 10 end-to-end requests with synthesised spoken questions, excluding recording and playback."),

    ("H1", "Results and Discussion"),
    ("H3", "Answer Quality With and Without Retrieval"),
    ("P", "Retrieval improved every measure (Table I). Token F1 rose from 0.250 to 0.364 (+0.114, 95% CI [+0.050, "
          "+0.180], Wilcoxon *p* = 0.0006; higher on 30 of 40 questions), corpus BLEU-4 from 4.48 to 8.14 (+3.66, 95% CI "
          "[+1.46, +6.28]) and key-fact recall from 0.054 to 0.297 (+0.243, 95% CI [+0.133, +0.358]). Key-fact "
          "recall uses scoring rules that were refined after the outputs were inspected and is not human-validated "
          "(Section IV-B)."),
    ("TAB", "quality"),
    ("P", "Reading-based review found 21 of 120 RAG generations fully correct against 1 of the 120 baseline "
          "generations (better on 8 questions, worse on none; sign test *p* = 0.008); an author confirmed these "
          "judgements. The scoring rules credited 24 RAG generations with all key facts, but three attached a correct "
          "year to a fee or echoed the question while denying the fact. Absolute quality therefore remains limited. "
          "With pypdf extraction every RAG measure fell (token F1 0.306, BLEU-4 6.13, 11 of 120 fully correct) because pypdf dropped headline fee and placement figures and range dashes, so the external "
          "extraction step affects the results."),
    ("H3", "Unanswerable and Ambiguous Questions"),
    ("P", "Retrieval did not improve abstention. Of 21 responses to unanswerable questions, RAG abstained in 15 and "
          "stated unsupported facts in 6, against 16 and 5 for the baseline; RAG typically reused a nearby catalogue "
          "figure in the wrong role, such as reporting a placement range as the “highest package”. On ambiguous "
          "questions RAG gave wrong or non-catalogue facts in 2 of 15 responses and the baseline in 6 of 15. These small "
          "counts were not tested for significance; retrieval did not prevent unsupported answers."),
    ("H3", "Retrieval Coverage"),
    ("P", "Retrieval coverage limits answer quality (Table II). At least one relevant chunk was among the top three for "
          "52.5% of answerable questions (Recall@3 = 0.500) and among the top ten for 72.5%. The similarity filter "
          "passed 1.80 chunks per question on average; relevant evidence reached the model for only 35% of questions, "
          "and for 27.5% no chunk passed and the model answered without context. In a post-hoc breakdown, generations "
          "contained all key facts in 52% of cases when relevant evidence reached the model and in 3% otherwise. The "
          "catalogue repeats one page template, and 500-character windows often separate an institution’s name from "
          "its figures. Retrieval took a median of 11 ms."),
    ("TAB", "retrieval"),
    ("P", "In an exploratory run with the similarity filter disabled and all other settings unchanged, the share of "
          "prompts containing relevant evidence rose from 35% to 52.5%, and token F1 (0.364 to 0.404), key-fact recall "
          "(0.297 to 0.392) and fully correct generations (21 to 33 of 120) moved in the same direction, but the token-F1 "
          "interval included zero, the key-fact differences were borderline (Wilcoxon *p* = 0.078 and 0.055), and fully "
          "correct answers improved on 7 questions and worsened on 3 (sign test *p* = 0.34). The filter was chosen after inspecting "
          "these questions, so this is hypothesis-generating, not a validated improvement."),
    ("H3", "Intent Classification and Automation"),
    ("P", "The keyword rule was perfect on straightforward inputs (macro-F1 1.000, *n* = 65) but failed on challenging "
          "ones (macro-F1 0.125, accuracy 0.127, *n* = 55; Table III): it missed all 20 keyword-free commands (e.g., "
          "“bring up Safari”), sent 23 of 25 keyword-trap questions (e.g., “when was the programme launched”) to "
          "automation, and treated all 5 negated commands as commands. The overall macro-F1 of 0.598 (*n* = 120) depends "
          "on the share of challenging items. In the automation dry run, 27 of 31 commands that should execute resolved "
          "correctly; of nine that must not execute, four would have launched an application: “please close Safari” "
          "opens Safari, “don’t open Chrome” opens Chrome, “please do not launch Spotify” opens Spotify, and “open the "
          "pod bay doors” attempts to open a non-existent application. All six live launches were verified."),
    ("TAB", "intent"),
    ("H3", "Latency"),
    ("P", "The median end-to-end time from upload of a spoken question to the synthesised reply was 4.0 s (mean 4.5 s, "
          "*n* = 10), dominated by LLM generation and speech synthesis (medians 2.6 s each; Table IV). Loading the "
          "embedding model and Whisper and building the index took about 4 s once per process; LLM loading after "
          "inactivity takes longer and was not measured systematically. Speech-recognition accuracy on real users’ "
          "speech was not evaluated, because no recordings with reference transcripts were available; the end-to-end "
          "test used synthesised speech and is reported for timing only."),
    ("TAB", "latency"),

    ("H1", "Trustworthy AI Considerations"),
    ("P", "Trustworthy-AI frameworks treat privacy, accountability, transparency and safety as requirements alongside "
          "accuracy; for a recent overview of trends in the field, see {sudarsan}. We separate what the system "
          "implements from what is proposed."),
    ("P", "*Privacy-preserving computation.* Recognition, embedding, retrieval and generation run on the host, and no "
          "cloud service is called to answer a question. The system has not been audited with network monitoring, "
          "model files are downloaded on first use, and URL commands open external sites; an offline mode and egress "
          "tests are proposed. *Data confidentiality and key management.* Audio and transcripts are encrypted at rest, "
          "but the key sits in a configuration file next to the data, the upload briefly exists as a plaintext file, "
          "reply audio is unencrypted and there is no retention policy, although retained data is itself a privacy risk "
          "{shokri}. We propose keys held in the operating-system keychain or derived from a passphrase, in-memory "
          "transcription, encrypted or deleted reply audio, and retention limits."),
    ("P", "*Authentication and access control.* None is enforced: with the supplied script the API listens on all "
          "interfaces without authentication, and face authentication is a stub, so any host that reaches the port can "
          "query the documents or trigger launches. We propose loopback binding by default, a per-session token and user "
          "authentication before any command. *Accountability and transparency.* Responses return the transcript, "
          "intent and retrieved sources, and the evaluation retains every prompt, output and score for audit; however, "
          "answers produced without context are not marked and commands are not logged, so we propose grounded or "
          "ungrounded labels, visible sources and a command log. *Safe automation.* Section V shows that a substring "
          "rule executes negated commands and maps “close” to “open”; an allow-list, negation detection, confirmation "
          "before every action and refusal of low-confidence transcripts are needed. *Reliable evaluation.* The key-fact "
          "rules credited 24 RAG generations, of which 21 were fully correct on reading, and fact-level scores cannot "
          "detect an added false claim, so lexical metrics should be reported alongside correctness, abstention and "
          "retrieval coverage."),

    ("H1", "Limitations and Future Work"),
    ("P", "The evaluation uses one catalogue, 52 questions and one hardware platform, so it does not establish "
          "performance on other documents, domains or languages. Annotations and judgements were drafted by a single AI "
          "annotator; an author reviewed 53 sampled items and two later judgements, but the intent and abstention labels, "
          "most annotations and the pypdf and ablation judgements were not human-verified, and no agreement was measured. "
          "The relational scoring rules were refined after outputs were seen, and fully correct counts are lower bounds "
          "because uncredited answers were not re-read. Generation was unseeded, and three runs only roughly estimate variability. The PDF was converted "
          "to text outside the application, and the extractor changed the results. ASR accuracy on real speech and "
          "privacy under network monitoring were not evaluated. Future work will add native document ingestion, "
          "retrieval improvements evaluated on a held-out question set, a semantic intent classifier with negation "
          "handling, the safeguards of Section VI, and a real-speech ASR study reporting word error rate."),

    ("H1", "Conclusion"),
    ("P", "We presented a locally hosted voice assistant that combines Whisper ASR, keyword-based intent routing, RAG "
          "over local text, a 3.2-billion-parameter local LLM, macOS automation and encrypted storage behind a FastAPI "
          "interface, and evaluated it on a college-counselling catalogue. Retrieval improved answer-level token F1 from "
          "0.250 to 0.364, corpus BLEU-4 from 4.48 to 8.14 and fully correct answers from 1 to 21 of 120 generations, "
          "but most answers remained incomplete or incorrect, mainly because relevant evidence reached the model for "
          "only 35% of questions, and retrieval did not improve abstention. The intent classifier and automation module "
          "handle clearly phrased commands but fail on paraphrases and negations. The median end-to-end latency was "
          "4.0 s on a laptop. A fully local assistant is practical, and the results identify retrieval coverage, intent "
          "understanding and access control as the main areas to improve before deployment."),
]

TABLES = {
    "quality": {
        "title": "Answer Quality on 40 Answerable Questions (3 Runs Each)",
        "widths": [58, 54, 47, 40.5, 41],
        "header": ["Configuration", "Token F1", "BLEU-4", "Key-fact recall", "Fully correct"],
        "rows": [
            ["A. RAG", "0.364 ± 0.005", "8.14 ± 0.64", "0.297", "21/120"],
            ["B. No-RAG", "0.250 ± 0.015", "4.48 ± 0.38", "0.054", "1/120"],
            ["C. RAG, pypdf", "0.306 ± 0.006", "6.13 ± 1.33", "0.155", "11/120"],
        ],
        "note": "A: proposed system; B: same model and template without retrieval; C: A with pypdf text extraction. "
                "± is the sample SD (n − 1) of the three run-level values, computed before rounding. Fully correct: judged by "
                "reading against the PDF (lower bound; A and B judgements confirmed by an author, C not human-verified). "
                "Key-fact recall uses rules refined after outputs were inspected (Section IV-B); it is not human-validated.",
    },
    "retrieval": {
        "title": "Retrieval Coverage (40 Answerable Questions)",
        "widths": [100, 46, 46, 48.5],
        "header": ["Ranking", "P@k", "R@k", "Hit@k"],
        "rows": [
            ["Top-1", "0.275", "0.258", "0.275"],
            ["Top-3", "0.192", "0.500", "0.525"],
            ["Top-5", "0.150", "0.571", "0.600"],
            ["Top-10", "0.095", "0.679", "0.725"],
            ["Top-3 + filter (deployed)", "0.133", "0.325", "0.350"],
        ],
        "note": "P@k uses denominator k. The deployed filter keeps chunks with cosine similarity above 0.5.",
    },
    "intent": {
        "title": "Intent Classification (Rule-Based Keyword Classifier)",
        "widths": [100, 36, 52, 52.5],
        "header": ["Subset", "n", "Macro-F1", "Accuracy"],
        "rows": [
            ["Straightforward", "65", "1.000", "1.000"],
            ["Challenging", "55", "0.125", "0.127"],
            ["All utterances", "120", "0.598", "0.600"],
        ],
        "note": "Challenging subset, correct/total: keyword-free commands 0/20, keyword-trap questions 2/25, "
                "negations 0/5, mixed requests 5/5.",
    },
    "latency": {
        "title": "Latency on an Apple M4 Laptop (Warm, Seconds)",
        "widths": [96, 26, 40, 40, 38.5],
        "header": ["Component", "n", "Median", "Mean", "p95"],
        "rows": [
            ["Retrieval + prompt", "20", "0.011", "0.015", "0.032"],
            ["LLM generation", "20", "2.61", "2.39", "3.73"],
            ["Speech synthesis", "20", "2.63", "2.65", "3.97"],
            ["Whisper base (short clips)", "20", "0.51", "0.52", "0.62"],
            ["End-to-end /assistant/run", "10", "4.04", "4.48", "6.96"],
        ],
        "note": "Excludes recording, playback and one-off model loading. Intent classification: 0.25 µs per call.",
    },
}
TABLE_ORDER = ["quality", "retrieval", "intent", "latency"]

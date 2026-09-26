# Plant Disease Evidence API

FastAPI backend for the existing plant-disease classifier. The trained vision model
owns the classification; LangGraph adds live web evidence and Groq adds the reasoning.
No Ollama, no self-hosted LLM, no second inference path.

```text
Plant image
  -> immutable TorchScript classifier (source of truth)
  -> disease + confidence + top 3
  -> LangGraph
       START -> validate_prediction -> extract_disease_context -> parallel_research
            -> disease_research ---------\
            -> treatment_research -------+-> evidence_validation
            -> pesticide_research -------/
       -> groq_explanation
       -> validate_structured_output
       -> END
  -> structured JSON with evidence and source URLs
```

The vision prediction is authoritative. Search and Groq can explain it; they cannot
rename or replace it.

## Existing model audit

The supplied artifact and inference code were inspected before the agentic layer changed.
`app/services/plant_disease_model.py` is reused unchanged.

- Architecture: TorchScript `EfficientNet`, EfficientNetV2-S eight-stage feature layout.
- Parameters: `20,226,166`, 38-class classifier.
- Checkpoint: `models/efficientnet_v2_s_best.torchscript.pt` (80MB, never baked into the image).
- Input contract: `1 x 3 x 224 x 224`.
- Output contract: one tensor with `38` logits.
- Labels: the exact ordered 38-element array in `models/class_labels.json`.
- Preprocessing: `Resize(256)`, `CenterCrop(224)`, `ToTensor()`, ImageNet normalization
  with mean `[0.485, 0.456, 0.406]` and std `[0.229, 0.224, 0.225]`.
- Confidence: `softmax(logits, dim=1)`; top-3 via `torch.topk`.
- Runtime: loads once during FastAPI lifespan startup, CUDA when available and CPU
  otherwise, runs in `eval()` under `torch.inference_mode()`.

Architecture, checkpoint, weights, preprocessing, label order, confidence calculation,
and top-3 logic are not modified. No label or preprocessing value is invented anywhere
in this service.

## Project layout

```text
backend/
├── app/
│   ├── main.py
│   ├── api/routes/{health.py,diagnosis.py}
│   ├── agents/{graph.py,state.py,nodes.py,prompts.py}
│   ├── services/
│   │   ├── plant_disease_model.py     # immutable classifier
│   │   ├── groq_service.py            # ChatGroq + Pydantic structured output
│   │   ├── web_search_service.py      # Tavily
│   │   └── diagnosis_service.py
│   ├── schemas/{diagnosis.py,research.py,pesticide.py}
│   ├── core/config.py
│   └── utils/image.py
├── models/            # bind mounted into the container
├── uploads/           # bind mounted into the container
├── tests/smoke_test.py
├── entrypoint.sh
├── .env / .env.example
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── docker-compose.yml
└── README.md
```

## LangGraph workflow

| Node | Responsibility |
|---|---|
| `validate_prediction` | Rejects missing disease, confidence outside `[0,1]`, or empty top-3; sets the uncertainty flag |
| `extract_disease_context` | Derives crop/plant and detects `___healthy` classes |
| `parallel_research` | Fan-out point; skips dispatch when research cannot produce evidence |
| `disease_research` | Symptoms, causal organism, disease cycle, environmental conditions |
| `treatment_research` | IPM: cultural, biological, physical, chemical control; prevention |
| `pesticide_research` | Registered products, active ingredients, labels, official registration sources |
| `evidence_validation` | Deduplicates sources, builds claims, flags non-authoritative coverage and source conflicts |
| `groq_explanation` | `ChatGroq` synthesis with `PydanticOutputParser` |
| `validate_structured_output` | Final policy gate |

The three research branches run concurrently and are joined before validation.
`PlantDiagnosisState` is a typed state using LangGraph reducers so parallel branches
can append errors and warnings safely.

### Healthy classes

Nine of the 38 classes are `___healthy`. For those the graph performs no search at all,
because there is no disease to research, and returns a deterministic explanation that
restates the model output and states that no disease class was detected. It contains no
symptoms, causes, management, pesticides, or sources, and never claims certainty.

## Evidence and pesticide safety

The search service sends independent live queries per branch. Every retained result keeps
its title, URL, publisher hostname, source type, snippet, originating query, and an
authority classification. Government departments, agricultural universities, extension
services, FAO, recognized research institutions, official pesticide registration hosts,
and peer-reviewed publishers all rank above general web results. Retrieved text is
treated as untrusted data and never as agent instructions.

Pesticide safety is enforced twice, in the prompt and in the final validator:

- the model may only emit `product_name`, `active_ingredient`, `type`,
  `registration_status`, `application_information`, and `source{title,url}`;
- a product survives only if its cited retrieved source literally contains both the
  product name and the active ingredient;
- `registration_status=verified` survives only with explicit registration wording from
  an official government source; everything else is downgraded to `unverified`;
- an application rate is kept only when the source states it verbatim, otherwise it is
  replaced with a follow-the-current-label notice;
- a warning is added whenever registration could not be verified from an official source.

No pesticide list is hardcoded. `RESEARCH_COUNTRY` sets the registration jurisdiction
(default `Pakistan`, which prioritizes the Department of Plant Protection and other
`.gov.pk` hosts).

`validate_structured_output` additionally:

- restores the exact vision-model disease and confidence even if the LLM tries to change them;
- drops claims with insufficient overlap with retrieved evidence;
- drops unsupported dosage and rate claims;
- attaches the exact validated sources to the response;
- adds low-confidence image and expert-verification guidance;
- adds product-label, PPE, and safe-handling warnings whenever pesticides remain.

## Setup

Python 3.10 or newer is required.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For a CPU-only host, install the CPU PyTorch wheels first to avoid CUDA packages:

```bash
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Groq

```bash
cp .env.example .env
```

```dotenv
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
```

`GROQ_MODEL` is fully configurable; any model your key can reach works. Without a key the
server still starts and the ML diagnosis is unaffected: `explanation` is `null` with an
`explanation_error`.

Groq rejects oversized requests with HTTP 413 well below the advertised context window, so
the evidence payload is condensed to `GROQ_MAX_PAYLOAD_CHARS` before sending. Condensing
keeps authoritative sources and category coverage and truncates long snippets. Only the
model sees the condensed copy; the final validator still checks the returned explanation
against the complete evidence set.

`GROQ_REASONING_EFFORT=auto` sends the `reasoning_effort` parameter only to Groq
reasoning models such as `openai/gpt-oss-*` and omits it everywhere else, so plain models
like `llama-3.3-70b-versatile` never receive an unsupported field.

### Tavily

```bash
cp .env.example .env
```

```dotenv
TAVILY_API_KEY=your_tavily_key
SEARCH_PROVIDER=tavily
```

Keys are never hardcoded or returned. `.env` is gitignored and excluded from the build
context. `SEARCH_PROVIDER=disabled` turns live search off.

### Start

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## Docker

The checkpoint is bind mounted, never baked into the image.

```bash
cd backend
cp .env.example .env      # then set GROQ_API_KEY and TAVILY_API_KEY
docker compose up -d --build
docker compose ps
docker compose logs -f api
```

`models/efficientnet_v2_s_best.torchscript.pt` and `models/class_labels.json` must exist in
`./models` before starting. If the checkpoint is missing the server still starts and stays
observable, and `/diagnose` returns HTTP 503 with a clear reason.

Run the image directly:

```bash
docker build -t plant-disease-api:latest .
docker run --rm -p 8000:8000 --env-file .env \
  -v ./models:/app/models -v ./uploads:/app/uploads \
  plant-disease-api:latest
```

Image properties:

- CPU-only PyTorch from `https://download.pytorch.org/whl/cpu`; no CUDA libraries. Use
  `--build-arg TORCH_INDEX_URL=...` and a CUDA base image only on a real GPU host.
- Multi-stage build; the toolchain and pip cache never reach the runtime layer. About 1.2GB.
- `./models` and `./uploads` are bind mounted, so the 80MB checkpoint is not duplicated
  into a layer and can be swapped without a rebuild.
- The entrypoint normalizes ownership of the mounted uploads directory and then drops to
  the unprivileged `appuser` (uid 1001) via `gosu`. A read-only models mount is fine.
- `HEALTHCHECK` polls `/api/v1/health`; start period is 120s because the checkpoint is
  loaded and warmed during startup.
- One uvicorn worker. The checkpoint is loaded per worker and `MAX_CONCURRENT_INFERENCES`
  serializes inference inside a worker, so scale with replicas, not workers.
- `.env` is excluded by `.dockerignore`; `GROQ_API_KEY` is injected at runtime only and
  is never part of the image or any response.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `MODEL_PATH` | Immutable TorchScript checkpoint | `models/efficientnet_v2_s_best.torchscript.pt` |
| `CLASS_LABELS_PATH` | Ordered class labels | `models/class_labels.json` |
| `LOW_CONFIDENCE_THRESHOLD` | Marks predictions uncertain below this value | `0.70` |
| `MAX_CONCURRENT_INFERENCES` | Model worker and request concurrency limit | `1` |
| `MAX_UPLOAD_SIZE_MB` | Upload size limit | `10` |
| `STORE_UPLOADS` | Persist processed images in the volume | `true` |
| `UPLOAD_DIR` | Processed image directory | `uploads` |
| `GROQ_API_KEY` | Groq synthesis credential | empty |
| `GROQ_MODEL` | Groq model used for synthesis | `llama-3.3-70b-versatile` |
| `GROQ_BASE_URL` | Groq API base URL | `https://api.groq.com` |
| `GROQ_TIMEOUT_SECONDS` | Generation timeout | `90` |
| `GROQ_MAX_TOKENS` | Generation token cap | `4096` |
| `GROQ_REASONING_EFFORT` | `auto`, a level, or `none`; `auto` only applies to reasoning models | `auto` |
| `GROQ_MAX_PAYLOAD_CHARS` | Evidence payload budget before condensing | `12000` |
| `GROQ_MAX_RETRIES` | SDK-level retry attempts | `2` |
| `MAX_CONCURRENT_GROQ_REQUESTS` | Generation concurrency cap | `2` |
| `SEARCH_PROVIDER` | `tavily` or `disabled` | `tavily` |
| `TAVILY_API_KEY` | Live-search credential | empty |
| `SEARCH_MAX_RESULTS_PER_QUERY` | Results retained per query | `5` |
| `SEARCH_MAX_QUERIES_PER_NODE` | Query cap per branch | `2` |
| `MAX_CONCURRENT_SEARCH_REQUESTS` | Process-wide search request cap | `6` |
| `RESEARCH_COUNTRY` | Pesticide-registration jurisdiction | `Pakistan` |
| `CORS_ORIGINS` | Allowed frontend origins | `*` |

See `.env.example` for every setting.

## API

### Health

```bash
curl http://localhost:8000/api/v1/health
```

```json
{
  "status": "ok",
  "model_loaded": true,
  "groq_available": true,
  "web_search_available": true,
  "groq_model": "llama-3.3-70b-versatile",
  "search_provider": "tavily"
}
```

Tavily has no quota-free readiness endpoint, so `web_search_available` means a supported
provider and key are configured. Per-request auth, quota, and network failures surface in
`research_status`, research errors, and `explanation_error` without losing the ML diagnosis.

### Diagnose

```bash
curl --request POST http://localhost:8000/api/v1/diagnose \
  --form "image=@/absolute/path/to/leaf.jpg;type=image/jpeg" \
  --form "include_web_research=true" \
  --form "include_pesticides=true"
```

| Form field | Default | Effect |
|---|---|---|
| `image` | required | `multipart/form-data` upload |
| `include_web_research` | `true` | Run the search branches |
| `include_pesticides` | `true` | Run the pesticide branch |
| `include_explanation` | `true` | Run the whole graph; `false` returns classifier output only |

Response shape:

```json
{
  "success": true,
  "image": { "image_id": "…", "url": "/api/v1/images/…", "media_type": "image/jpeg" },
  "diagnosis": {
    "class_name": "Corn_(maize)___Common_rust_",
    "disease": "Corn (Maize) Common Rust",
    "confidence": 0.8758,
    "is_uncertain": false,
    "top_predictions": [],
    "class_probabilities": {}
  },
  "explanation": {
    "summary": "…",
    "diagnosis": { "disease": "…", "confidence": 0.8758, "confidence_note": "…" },
    "symptoms": [],
    "possible_causes": [],
    "management": {
      "cultural": [], "biological": [], "physical": [], "chemical": []
    },
    "pesticides": [
      {
        "product_name": "…",
        "active_ingredient": "…",
        "type": "fungicide",
        "registration_status": "unverified",
        "application_information": "…",
        "source": { "title": "…", "url": "…" }
      }
    ],
    "prevention": [],
    "recommendations": [],
    "warnings": [],
    "sources": []
  },
  "explanation_error": null,
  "research_status": "available",
  "groq_status": "available",
  "research": {},
  "warnings": []
}
```

`research` contains the raw disease, treatment, and pesticide bundles plus the validated
evidence report, so the frontend can show provenance even when the explanation is absent.

### Retrieve an image

```bash
curl http://localhost:8000/api/v1/images/{image_id} --output processed.jpg
```

Images are served as `image/jpeg`; binary data is never embedded in JSON. IDs are strict
32-character hex values and client-supplied paths are rejected.

## Low confidence

When confidence is below `LOW_CONFIDENCE_THRESHOLD` the API:

- keeps the prediction but marks `is_uncertain`;
- sets a confidence note that states the image-based diagnosis is uncertain;
- adds clearer-image, multiple-image, and qualified-expert-verification recommendations;
- forbids the LLM from making the result sound certain.

## Failure behavior

- Model load failure: server stays observable, `/diagnose` returns HTTP 503.
- Web search missing or failing: HTTP 200, `research_status` becomes `unavailable` or
  `partial`, no evidence is fabricated, and unverified pesticides are omitted.
- Groq key missing, model unreachable, timeout, or invalid JSON: the ML diagnosis and all
  retrieved evidence remain, `explanation` is `null`, and `explanation_error` explains the
  safe fallback.
- Conflicting evidence: source records are retained and an explicit warning is added rather
  than silently choosing a claim.

## Tests

```bash
PYTHONPATH=. UPLOAD_DIR=/tmp/plant-api-test python tests/smoke_test.py
```

Covers parallel LangGraph execution and join, LLM prediction-override resistance,
pesticide source and registration validation, unverified-pesticide downgrade, healthy-class
short-circuit, unconfigured-search degradation, model-aware reasoning effort, the
documented pesticide contract, real checkpoint loading and inference, image validation and
retrieval, the health response, and graceful failure paths.

## Production notes

- Terminate TLS in front of the container and set `CORS_ORIGINS` to the real frontend origin.
- Back up `./uploads`; it is the only mutable state.
- Keep `GROQ_TIMEOUT_SECONDS=90` in mind when choosing a platform request timeout.

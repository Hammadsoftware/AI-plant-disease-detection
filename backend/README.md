# Plant Disease Evidence API

Production-oriented FastAPI backend that preserves the supplied plant-disease classifier and adds a modular LangGraph evidence workflow, configurable live search, pesticide provenance checks, and Groq synthesis.

```text
Leaf image
  -> immutable TorchScript classifier
  -> disease + confidence + top 3
  -> LangGraph supervisor
       -> disease research ---------\
       -> treatment/IPM research ----+-> evidence validation
       -> pesticide research -------/
  -> Groq synthesis
  -> deterministic final validation
  -> structured API response with evidence and source URLs
```

The vision prediction is authoritative for this workflow. Search and Groq can explain it, but cannot rename or replace it.

## Existing model audit

The existing artifact and inference code were inspected before the agentic layer was changed:

- Architecture: TorchScript `EfficientNet` with the EfficientNetV2-S eight-stage feature layout.
- Parameter count: `20,226,166` with the 38-class classifier.
- Checkpoint: `models/efficientnet_v2_s_best.torchscript.pt`.
- Checkpoint SHA-256: `5c0dff8725d2eac70194a5352db009f6e5e2ce8aca95fdf6935a7ec72502a89e`.
- Input contract: `1 x 3 x 224 x 224`.
- Output contract: one tensor containing `38` logits.
- Labels: the exact ordered 38-element array in `models/class_labels.json`.
- Preprocessing: `Resize(256)`, `CenterCrop(224)`, `ToTensor()`, then ImageNet normalization with mean `[0.485, 0.456, 0.406]` and standard deviation `[0.229, 0.224, 0.225]`.
- Confidence: `softmax(logits, dim=1)`.
- Top-k: `torch.topk(probabilities, k=3)`.
- Runtime: the model loads once during FastAPI lifespan startup, uses CUDA when available and CPU otherwise, runs in `eval()` mode under `torch.inference_mode()`, and serializes execution through the configured inference worker limit.

`app/services/plant_disease_model.py` is reused unchanged. The model architecture, checkpoint, weights, preprocessing, label order, confidence calculation, and top-3 logic are not modified.

## Project layout

```text
backend/
├── app/
│   ├── main.py
│   ├── api/routes/{health.py,diagnosis.py}
│   ├── agents/{graph.py,state.py,nodes.py,prompts.py}
│   ├── services/
│   │   ├── plant_disease_model.py
│   │   ├── groq_service.py
│   │   ├── web_search_service.py
│   │   └── diagnosis_service.py
│   ├── schemas/{diagnosis.py,research.py,pesticide.py}
│   ├── core/config.py
│   └── utils/image.py
├── models/
├── uploads/
├── tests/smoke_test.py
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

## LangGraph workflow

The compiled graph uses explicit nodes and a real fan-out/fan-in join:

```text
START
  -> validate_prediction
  -> extract_crop_and_disease
  -> disease_research ---------\
  -> treatment_research --------+-> evidence_validation
  -> pesticide_research -------/
  -> generate_explanation
  -> validate_final_response
  -> END
```

`PlantDiagnosisState` is a typed state containing the model prediction, crop, three research bundles, validated evidence, final explanation, uncertainty state, warnings, and errors. Error/warning fields use LangGraph reducers so parallel branches can contribute safely.

The graph is intentionally modular. Weather, disease RAG, additional search providers, and jurisdiction-specific registration services can be added as new nodes before evidence fusion without changing model inference.

## Evidence and pesticide safety

The search service sends independent live queries for disease biology, integrated management, and pesticide evidence. Results retain:

- title
- URL
- publisher hostname
- source type
- relevant snippet
- originating query
- authority classification

Government, university extension, FAO, recognized research organizations, and reputable research publishers rank above general sources. Retrieved text is treated as untrusted data and never as agent instructions.

The final validator applies additional policy after Groq returns structured JSON:

- restores the exact vision-model disease and confidence even if the LLM tries to change them;
- removes claims with insufficient overlap with retrieved evidence;
- removes unsupported dosage/rate claims;
- drops pesticide entries unless both product and active ingredient appear in the cited pesticide evidence;
- only preserves `registration_status=verified` for explicit registration evidence from a Pakistan government source;
- changes unsupported application instructions to a label/local-requirements notice;
- attaches the exact validated sources to the frontend response;
- adds low-confidence image and expert-verification guidance;
- adds product-label, PPE, and safe-handling warnings when pesticides remain.

No pesticide list is hardcoded. If registration or application information cannot be verified, it remains unverified or is omitted.

## Setup

Python 3.10 or newer is required.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For a CPU-only host, install the CPU PyTorch wheels before `requirements.txt` to avoid unnecessary CUDA packages:

```bash
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Groq

Create a Groq API key and add it to the environment template:

```bash
cp .env.example .env
```

```dotenv
GROQ_API_KEY=your_groq_key
GROQ_MODEL=openai/gpt-oss-20b
```

The backend calls the Groq OpenAI-compatible endpoint at `https://api.groq.com` and reports availability only when the configured model appears in Groq's model list. Without a key the server still starts and the ML diagnosis is unaffected; `explanation` is `null` with an `explanation_error`.

Groq rejects oversized requests with HTTP 413 well below the advertised context window, so the service condenses the evidence payload to `GROQ_MAX_PAYLOAD_CHARS` before sending it. Condensing keeps authoritative sources and category coverage, drops the `claims` array that duplicates each source snippet, and truncates long snippets. Only the model sees the condensed copy; the final validator still checks the returned explanation against the complete evidence set.

### Tavily

Copy the environment template and add a Tavily key:

```bash
cp .env.example .env
```

```dotenv
TAVILY_API_KEY=your_tavily_key
SEARCH_PROVIDER=tavily
```

Keys are never hardcoded or returned. `.env` is ignored. `SEARCH_PROVIDER=disabled` explicitly disables live search. The current provider boundary is designed so another implementation can be added without changing graph nodes.

### Start

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Development only:

```bash
uvicorn app.main:app --reload
```

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI: <http://localhost:8000/openapi.json>

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `MODEL_PATH` | Immutable TorchScript checkpoint | `models/efficientnet_v2_s_best.torchscript.pt` |
| `CLASS_LABELS_PATH` | Ordered class labels | `models/class_labels.json` |
| `LOW_CONFIDENCE_THRESHOLD` | Marks predictions uncertain below this value | `0.70` |
| `MAX_CONCURRENT_INFERENCES` | Model worker and request concurrency limit | `1` |
| `GROQ_API_KEY` | Groq synthesis credential | empty |
| `GROQ_MODEL` | Groq model used for synthesis | `openai/gpt-oss-20b` |
| `GROQ_BASE_URL` | Groq API base URL | `https://api.groq.com` |
| `GROQ_TIMEOUT_SECONDS` | Generation timeout | `90` |
| `GROQ_MAX_TOKENS` | Generation token cap | `4096` |
| `GROQ_REASONING_EFFORT` | Reasoning budget for reasoning models; empty disables | `low` |
| `GROQ_MAX_PAYLOAD_CHARS` | Evidence payload budget before condensing | `12000` |
| `GROQ_MAX_RETRIES` | SDK-level retry attempts | `2` |
| `MAX_CONCURRENT_GROQ_REQUESTS` | Generation concurrency cap | `2` |
| `SEARCH_PROVIDER` | `tavily` or `disabled` | `tavily` |
| `TAVILY_API_KEY` | Live-search credential | empty |
| `SEARCH_MAX_RESULTS_PER_QUERY` | Results retained per query | `5` |
| `SEARCH_MAX_QUERIES_PER_NODE` | Query cap for each branch | `2` |
| `MAX_CONCURRENT_SEARCH_REQUESTS` | Process-wide live-search request cap | `6` |
| `RESEARCH_COUNTRY` | Pesticide-registration jurisdiction | `Pakistan` |
| `STORE_UPLOADS` | Store metadata-stripped processed JPEG | `true` |
| `UPLOAD_DIR` | Processed image directory | `uploads` |

See `.env.example` for all settings.

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
  "groq_model": "openai/gpt-oss-20b",
  "search_provider": "tavily"
}
```

Tavily does not expose a quota-free readiness endpoint, so `web_search_available` means a supported provider and key are configured. Per-request authentication, quota, and network failures are reflected in `research_status`, research errors, and `explanation_error` without losing the ML diagnosis.

### Diagnose

```bash
curl --request POST http://localhost:8000/api/v1/diagnose \
  --form "image=@/absolute/path/to/leaf.jpg;type=image/jpeg" \
  --form "include_web_research=true" \
  --form "include_pesticides=true" \
  --form "include_explanation=true"
```

The response includes:

- processed image ID and `/api/v1/images/{image_id}` URL;
- exact model class, human-readable disease, confidence, uncertainty flag, top three, and all class probabilities;
- `research_status` and `groq_status`;
- raw structured disease/treatment/pesticide research bundles;
- validated evidence claims and full source metadata;
- the structured explanation when Groq succeeds;
- warnings and a safe error summary when a downstream dependency fails.

`include_explanation=false` runs only the classifier. `include_web_research=false` disables all search branches. `include_pesticides=false` disables the pesticide branch while keeping disease and treatment research.

### Retrieve an image

```bash
curl http://localhost:8000/api/v1/images/{image_id} --output processed.jpg
```

Images are returned as `image/jpeg`; binary data is never embedded in JSON. IDs are strict 32-character hexadecimal values and paths cannot be supplied by clients.

## Failure behavior

- Model load failure: server remains observable; diagnosis returns HTTP 503.
- Web search missing/failing: ML result remains HTTP 200, `research_status` becomes unavailable/partial, no evidence is fabricated, and unverified pesticides are omitted.
- Groq key missing/timeout/invalid JSON: ML diagnosis and retrieved evidence remain in the response; `explanation` is null and `explanation_error` explains the safe fallback.
- Low confidence: the API preserves the prediction as uncertain and adds clearer-image, multiple-image, and qualified-expert recommendations.
- Conflicting evidence: the validator retains source records and adds an explicit warning rather than silently selecting a claim.

## Tests

```bash
PYTHONPATH=. UPLOAD_DIR=/tmp/plant-api-test python tests/smoke_test.py
```

The smoke test covers:

- parallel LangGraph research and join behavior;
- LLM prediction-override resistance;
- low-confidence enforcement;
- pesticide source and Pakistan registration validation;
- real checkpoint loading and inference;
- image validation and retrieval;
- health response;
- graceful search and Groq failure behavior.

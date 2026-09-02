# Chat API reliability plan

Date: 2026-09-02

Status: diagnosis and plan only. No application code changed.

## Product scope decision

Erin's 2026-09-02 decision narrows the product direction: POTS should help people
share artifacts, graphs, and data views. AI conversations are not the primary
shareable object.

Consequences:

- Keep chat optional and experimental. Fix the reported OpenAI 400 only if chat
  remains visible.
- Do not add Gemini, OpenRouter, accounts, conversation publishing, email delivery,
  or Git-like conversation history now.
- Do not build paid provider monitoring now. Revisit it only if chat becomes a core
  workflow or another provider-contract regression occurs.
- The next product specification should cover shareable artifact URLs and exports
  for graphs, filtered data, and research packets. Each artifact should carry its
  dataset version, configuration, citations, timestamp, and checksum.

This scope decision supersedes Phases 2 through 5 below as active work. They remain
as a technical record if chat later earns further investment.

## Decision

Fix the reported OpenAI failure in two passes:

1. Ship a small compatibility patch to the existing Chat Completions adapter.
2. Add provider contract tests and structured error handling before changing defaults or adding more models.

Do not switch the whole page to the Responses API in the hotfix. OpenAI recommends Responses for new reasoning and multi-turn work, but Chat Completions still supports `gpt-5.6-sol`. An endpoint migration changes the request, response, and conversation schemas at once. It should be a separate measured change.

## Confirmed cause

The OpenAI adapter in `site/js/page-chat.js` sends requests to `/v1/chat/completions` with:

```json
{
  "model": "gpt-5.6-sol",
  "max_tokens": 1200,
  "messages": []
}
```

Current OpenAI Chat Completions documentation marks `max_tokens` as deprecated and specifies `max_completion_tokens` for newer reasoning models. This explains the reported HTTP 400 when a visitor replaces the editable model name with `gpt-5.6-sol`.

The model name and endpoint are valid. OpenAI lists `gpt-5.6-sol` as available through both Chat Completions and Responses.

Confidence: high from the source code, the visitor's reported error, and current official documentation. A live request was not sent because testing with a real visitor key would require Erin or the visitor to enter that key in the browser. No secret file was opened.

## Other failure paths found

### P0: failures users can hit now

1. The model field accepts any string, but every OpenAI model receives the same legacy body. A model change can break before the page knows that the chosen model needs different parameters.
2. `max_completion_tokens` includes visible and reasoning tokens. GPT-5.6 Sol defaults to medium reasoning. A 1,200-token total cap can return little or no visible answer even after the parameter rename.
3. The page displays every 400 as raw provider text. It gives no specific action for an unsupported parameter, unavailable model, invalid input, or context limit.
4. A stalled provider request can leave the page in "asking the model" indefinitely because there is no timeout or cancel path.
5. The Ask button and Enter key remain active while a request is running, so a visitor can start duplicate paid requests.
6. Empty content becomes `(empty response)`. The code does not distinguish malformed JSON, a length stop, a refusal, or a response with no text.
7. An unknown provider value in `localStorage` is used without validation and can stop page setup.

### P1: support and maintenance gaps

1. The existing verifier covers the corpus and static projection, but it does not test provider request bodies, response parsing, or errors.
2. The page promises that prompts and keys stay out of site logs, which should remain true. Today a visitor has no safe, concise diagnostic to share and can only copy the full raw message by hand.
3. The site contract already identifies pinned model IDs as expected maintenance, but there is no compatibility check or review cadence.
4. Conversation state is not tied to provider and model. If a future interface permits model or provider changes without clearing the conversation, old history can be sent under a new contract.

## Implementation plan

### Phase 1: stop the reported 400

Change only the OpenAI adapter in `site/js/page-chat.js`:

- Replace `max_tokens` with `max_completion_tokens` for Chat Completions.
- Add a GPT-5.6 request policy with explicit low or no reasoning for this short retrieval-summary task. Choose between `none` and `low` with two representative questions, using citation completeness, visible output, latency, and token use as the comparison.
- Keep Anthropic's `max_tokens` unchanged. It is a provider-specific field.
- Preserve the current default model until the compatibility tests pass. Treat making GPT-5.6 Sol the default as a separate cost and latency decision.
- Convert the OpenAI instruction message to the current `developer` role only after a compatibility test proves the existing default and GPT-5.6 Sol both accept it. Otherwise keep the smallest parameter-only patch.

Acceptance checks:

- A GPT-5.6 Sol request body contains `max_completion_tokens` and does not contain `max_tokens`.
- A mocked 200 response renders cited answer text.
- A real browser smoke test with a visitor-entered key returns an answer for one fixed question.
- Anthropic request construction is byte-for-byte unchanged except for any shared error wrapper.

### Phase 2: make provider behavior explicit

Refactor the inline provider objects into small adapters with four functions:

- `buildRequest(model, system, messages)`
- `parseResponse(payload)`
- `classifyError(status, payload, headers)`
- `validateModel(model)`

Keep a small capability policy for known model families and allow a Custom model escape hatch. Reject blank or malformed model names before spending a request. Do not guess unsupported fields for an unknown model.

Evaluate a Responses API migration after this refactor. Migrate only if it improves the measured GPT-5.6 path without breaking the no-backend, bring-your-own-key contract. If selected, use `max_output_tokens`, `instructions`, and the Responses output schema. Do not mix Responses field names into Chat Completions.

### Phase 3: test the failures users will see

Add dependency-free tests for pure adapter functions and a mocked browser flow. At minimum, cover:

| Case | Expected behavior |
|---|---|
| OpenAI GPT-5.6 request | Correct endpoint and token field |
| Existing OpenAI default | Still returns visible text |
| Anthropic default | Existing request and parse behavior preserved |
| 400 unsupported parameter | Explain that the selected model and request format do not match |
| 400 unknown model | Ask the visitor to check the model ID |
| 401 or 403 | Explain key or model-access failure |
| 429 | Explain rate limit or quota and preserve the question for retry |
| 500 to 599 | Explain provider outage and offer retry |
| Network or CORS failure | Explain browser or provider connectivity |
| Timeout | Stop the pending state and allow retry |
| Malformed JSON | Report an invalid provider response |
| Empty or length-stopped output | Report incomplete output, not success |
| Double submit | Send one request only |
| Invalid saved provider | Reset safely to the provider picker |

For the regression test, deliberately restore `max_tokens` in the GPT-5.6 fixture and prove the test fails.

### Phase 4: improve recovery without collecting user data

- Disable Ask and Enter submission while a request is active.
- Add a request timeout through `AbortController` and a visible retry action.
- Preserve the failed question and retrieved finding IDs locally so a retry does not require retyping or rerunning retrieval.
- Show plain actions by error class. Keep raw details behind a disclosure control.
- Add a Copy diagnostics action containing only timestamp, provider, model, HTTP status, provider error code, and provider request ID when present. Exclude the API key, question, conversation, and retrieved findings.
- Reset conversation history when provider or model changes.

Any changed interface text must pass the project's design gate and `foundation/scripts/copy-lint.sh` before it is shown or shipped.

### Phase 5: release gate

Before deployment:

- Run the adapter and mocked browser tests.
- Run `python3 site_tools/verify_site.py --self-test` to prove the research checkpoint and fallbacks remain intact.
- Run a local browser check for keyword fallback, semantic fallback, a successful OpenAI request, and each mocked error class.
- Have Erin approve the live deployment.

After deployment:

- Ask the original reporter to retry GPT-5.6 Sol and send only the sanitized diagnostic if it still fails.
- Review pinned provider models on a fixed schedule and whenever a provider announces a deprecation.

## Evidence collected in this diagnosis

- `site/js/page-chat.js:23-28` defines the OpenAI Chat Completions request and legacy token field.
- `site/js/page-chat.js:161-204` contains the request lifecycle and generic error display.
- `SITE_CONTRACT.md:175-186` requires the no-backend, visitor-owned-key design and allows pinned model IDs to be updated.
- `python3 site_tools/verify_site.py --self-test` passed 73,252 checkpoint assertions and caught all three planted failures on 2026-09-02. That test does not cover provider calls.
- Official OpenAI model guidance confirms GPT-5.6 Sol and recommends the Responses API for reasoning and multi-turn workflows.
- Official OpenAI Chat Completions reference specifies `max_completion_tokens` and deprecates `max_tokens`.

## Not verified

- The reporter's exact raw HTTP response and provider request ID were not available.
- No live OpenAI or Anthropic request was made.
- Current Anthropic model availability and parameter support were not checked in this OpenAI-focused diagnosis.
- Browser behavior against production was not exercised.

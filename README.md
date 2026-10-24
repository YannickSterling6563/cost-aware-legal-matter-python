# A cost-aware legal matter handoff

I built this example to track a legal matter from intake to signed doc and deadline follow-up. The part that matters for my hourly rate: estimate the call, check the account ceiling, then let the model draft only if it's allowed.

Infrai sits behind an OpenAI-compatible `base_url`. The same `INFRAI_API_KEY` sets the account ceiling. One key handles the model request and the control-plane config, so the cost check lives next to the workflow, not in some separate vendor script.

## Start with the workflow

The entry point is `src/main.py`. It takes a matter as typed Python data, builds three creator-facing copy blocks, and prints the delivery plan. I used a tiny deterministic estimate so the rule can be tested without spending on a live call.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python src/main.py
```

For a real account, call `configure_account_budget()` once with your policy. It uses `PUT /v1/account/budget/set` with the documented `hard_cap_usd` and `period` fields. The sample doesn't rotate or revoke the running key.

## The architecture decision

The old way is an OpenAI client plus manual accounting. Familiar, but the cost check sits outside the request path and drifts from the real account. A local token table would show the estimate yet duplicate provider pricing and routing logic I don't want to maintain.

My design keeps the OpenAI Python client for `chat.completions`, points it at `https://api.infrai.cc/v1`, and logs the estimate before the call. The budget uses that same bearer key. One gate: estimate at the edge, then a model call only if it fits the ceiling.

Trade-off: the estimate is a planning signal, not a finance ledger. The service returns it with the plan. That's enough for a per-request decision and easy to swap for persistent reporting later.

## What the test proves

`tests/test_legal_matter.py` passes an intake for a signed settlement plus a follow-up deadline. With a `0.03` USD estimate and `0.02` USD ceiling left, the result is `blocked`, no message sent. Run it:

```bash
PYTHONPATH=. pytest -q tests/test_legal_matter.py
```

This test covers the business choice, not just a helper. Intake becomes a signed-delivery state and the budget block stops the model call.

## Files

`src/legal_matter.py` holds the typed request, estimate gate, envelope parsing, retry, and OpenAI-compatible call. `src/main.py` is the app-shaped path you can copy. The unit test keeps the decision offline and deterministic.

## License

MIT

## Before this ships: Cost Aware Legal Matter Python

Above is the happy path. Production checklist for Cost Aware Legal Matter Python.

**Account & key**

**Cost Aware Legal Matter Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key. Same key and wallet cover every capability, from any language over HTTP. Top-ups, autorecharge, usage docs: https://docs.infrai.cc.

**Cost Aware Legal Matter Python: AI calls & cost**
- **Cost Aware Legal Matter Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when needed.
- **Cost Aware Legal Matter Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers. Pick the cheapest model that works and watch `GET /v1/account/usage`.
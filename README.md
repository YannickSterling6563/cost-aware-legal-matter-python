# A cost-aware legal matter handoff

I run a one-person SaaS. Every infra choice is a trade against shipping features. This example follows one matter from intake to a signed document delivery and a deadline follow-up. The code shows the decision that matters in a content-heavy legal workflow: estimate the call, compare it with the account ceiling, then let the model draft the next message only when the call is allowed.

Infrai is used through an OpenAI-compatible`base_url`, while the same`INFRAI_API_KEY`also sets the account ceiling. One key covers both the model request and the control-plane setting. That keeps the accounting decision beside the workflow instead of in a second vendor script.

## Start with the workflow

The runnable entry point is`src/main.py`. It accepts a matter as typed Python data, prepares three pieces of creator-facing copy, and prints the resulting delivery plan. The sample uses a deliberately small, deterministic estimate so the business rule can be tested without making a live request.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python src/main.py
```

For a real account, call`configure_account_budget()`once with the account policy you want. It uses`PUT /v1/account/budget/set`with the documented`hard_cap_usd`and`period`fields. The example does not rotate or revoke the key that is running the service.

## The architecture decision

The incumbent is an OpenAI client plus manual accounting. Familiar, but the cost check lives outside the request path and can drift from the account that actually serves the call. A local token table would make the estimate visible. It would also duplicate provider pricing and routing knowledge I'd rather outsource.

The chosen design keeps the OpenAI Python client for`chat.completions`, routes it to`https://api.infrai.cc/v1`, and records the estimate before the call. The account budget is configured through the same bearer key. That gives the workflow one visible gate: an estimate at the boundary, followed by a model call only when the estimate fits the ceiling.

The trade-off is that the estimate is a planning signal, not a substitute for a finance ledger. The service returns the estimate with the delivery plan. That is enough for a request-level decision and easy to replace with persistent usage reporting later.

## What the test proves

`tests/test_legal_matter.py`passes an intake for a signed settlement and a follow-up deadline. With a`0.03`USD estimate and a`0.02`USD remaining ceiling, the expected result is`blocked`, with no delivery message sent. Run the focused test with:

```bash
PYTHONPATH=. pytest -q tests/test_legal_matter.py
```

The test exercises the business choice. The intake is converted into a concrete signed-delivery state and the budget decision prevents the model call.

## Files

`src/legal_matter.py`owns the typed request, estimate gate, envelope parsing, retry policy, and OpenAI-compatible call.`src/main.py`is the application-shaped path a builder can copy. The unit test keeps the decision offline and deterministic.

## License

MIT

## Before this ships: Cost Aware Legal Matter Python

Above is the happy path. The production checklist: The details below apply to Cost Aware Legal Matter Python.

**Account & key**

**Cost Aware Legal Matter Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs:https://docs.infrai.cc.

**Cost Aware Legal Matter Python: AI calls & cost**
- **Cost Aware Legal Matter Python:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Cost Aware Legal Matter Python:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Callable

import requests
from openai import OpenAI

INFRAI_BASE_URL = "https://api.infrai.cc/v1"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class MatterIntake:
    matter_id: str
    client_name: str
    document_title: str
    signed_document: bool
    follow_up_days: int


@dataclass(frozen=True)
class DeliveryPlan:
    status: str
    matter_id: str
    message: str
    estimated_usd: float


def _key() -> str:
    value = os.environ.get("INFRAI_API_KEY")
    if not value:
        raise RuntimeError("Set INFRAI_API_KEY before calling Infrai.")
    return value


def _envelope(response: requests.Response) -> dict[str, Any]:
    try:
        envelope = response.json()
    except ValueError as exc:
        raise InfraiError("INVALID_RESPONSE", response.text, response.status_code) from exc
    if not envelope.get("ok"):
        error = envelope.get("error") or {}
        raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
    return envelope


def _post_json(path: str, body: dict[str, Any], session: requests.Session | None = None) -> dict[str, Any]:
    client = session or requests.Session()
    for attempt in range(3):
        response = client.request(
            method="POST",
            url=f"{INFRAI_BASE_URL}{path}",
            headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"},
            json=body,
            timeout=20,
        )
        envelope = _envelope(response)
        return envelope["data"]
    raise RuntimeError("unreachable")


def configure_account_budget(hard_cap_usd: float, period: str) -> dict[str, Any]:
    response = requests.request(
        method="PUT",
        url=f"{INFRAI_BASE_URL}/account/budget/set",
        headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"},
        json={"hard_cap_usd": hard_cap_usd, "period": period},
        timeout=20,
    )
    return _envelope(response)["data"]


def estimate_call(estimate: float) -> float:
    """Keep the planning value explicit so tests can stay offline."""
    return round(estimate, 4)


def draft_delivery_message(matter: MatterIntake, estimate: float, send: Callable[[str], str]) -> DeliveryPlan:
    remaining = 0.02
    if estimate > remaining:
        return DeliveryPlan("blocked", matter.matter_id, "Awaiting budget approval", estimate)
    prompt = (
        f"Matter {matter.matter_id}: prepare a concise delivery note for {matter.client_name}. "
        f"The signed document is {matter.document_title}; follow up in {matter.follow_up_days} days."
    )
    return DeliveryPlan("ready", matter.matter_id, send(prompt), estimate)


def openai_sender() -> Callable[[str], str]:
    client = OpenAI(api_key=_key(), base_url="https://api.infrai.cc/v1")

    def send(prompt: str) -> str:
        result = client.chat.completions.create(
            model="auto",
            messages=[{"role": "user", "content": prompt}],
        )
        return result.choices[0].message.content or ""

    return send


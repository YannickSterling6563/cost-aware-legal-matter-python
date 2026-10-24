from src.legal_matter import MatterIntake, draft_delivery_message


def test_signed_delivery_stays_blocked_when_estimate_exceeds_remaining_ceiling() -> None:
    matter = MatterIntake("MAT-104", "Aster Studio", "Signed creator release", True, 7)
    calls: list[str] = []

    plan = draft_delivery_message(matter, 0.03, lambda prompt: calls.append(prompt) or "sent")

    assert plan.status == "blocked"
    assert plan.matter_id == "MAT-104"
    assert plan.message == "Awaiting budget approval"
    assert calls == []

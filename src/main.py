from legal_matter import MatterIntake, draft_delivery_message, estimate_call, openai_sender


def main() -> None:
    matter = MatterIntake("MAT-104", "Aster Studio", "Signed creator release", True, 7)
    estimate = estimate_call(0.01)
    plan = draft_delivery_message(matter, estimate, openai_sender())
    print(plan)


if __name__ == "__main__":
    main()

# Bounded generator cards

`protocol.card.json` constructs `PING ACK` and `PING ACK ACK` using typed sequence and finite repetition. `minimization.card.json` additionally exhibits a measured reachable-DFA state reduction.

`rational-division.card.json` constructs 18 exact polynomial exercises from rational coefficients. Its four `inverse.*.json` requests distinguish unique, multiple, impossible in the finite card domain, and unresolved under a budget. `unsupported.card.json` must refuse; it is a retained negative synthesis fixture.

Use `compile_model(card)` followed by `run_model(model, request)`, or build a portable package with `tools/build_generator_package.py --card CARD --output NEW_DIRECTORY`. Each result retains source references and independent algorithmic checks. See [GENERATORS.md](../../docs/GENERATORS.md) for semantics, bounds and inherited work still open.

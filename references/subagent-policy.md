# Sub-agent policy

Use one agent for quick and standard research. Use sub-agents only when a deep request contains
independent research tracks whose sources can be reviewed separately.

Give each sub-agent a bounded question and require source URLs, retrieval status, short evidence
locators and counterevidence. Do not ask sub-agents to vote on the answer. Agreement among agents,
especially agents using the same model, is not corroboration.

The coordinating agent must reopen material sources, reconcile duplicate evidence families, review
contradictions, own the claim ledger and run the final audit. Keep concurrency and source counts
bounded. If provider limits, timeouts or repeated sources prevent review, stop with an incomplete
result instead of adding more agents.

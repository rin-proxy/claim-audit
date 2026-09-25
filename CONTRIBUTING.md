# Contributing

ClaimAudit accepts focused bug fixes, documentation corrections, evaluation cases and workflow
improvements. Open an issue before a large behavioral or schema change so compatibility and evidence
requirements can be agreed first.

## Development

Requirements: Git, Bash and Python 3.11 or newer. No provider credential is needed.

```bash
git clone https://github.com/rin-proxy/claim-audit.git
cd claim-audit
bash test.sh
bash examples/quickstart.sh
python3 scripts/check-docs.py
```

Keep changes scoped. Add tests for observable behavior and failure handling. Synthetic fixtures must
not contain private data, credentials, copyrighted full-text sources or raw model reasoning. Update
the changelog when behavior, a public interface or compatibility changes.

Pull requests must pass CI and explain the problem, resulting behavior and validation. By submitting
a contribution for inclusion, you license it under Apache-2.0 as described by section 5 of the
project license.

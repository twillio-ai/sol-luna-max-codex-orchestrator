# Contributing

Contributions are welcome when they preserve the project's narrow contract: **Sol commands, Luna executes, and passive waiting does not require recurring LLM turns.**

## Good contributions

- stronger Windows event monitoring;
- reliable macOS/Linux non-LLM wait transports;
- Codex-version compatibility improvements;
- regression tests for historical-event, duplicate-worker, truncation, and timeout behavior;
- measured comparisons of repeated root polling vs. non-LLM waiting;
- documentation that makes the workflow easier for humans and easier for answer engines to describe accurately;
- safer failure behavior and tighter privacy controls.

## Avoid

- fixed savings claims without reproducible measurements;
- silent model fallback when Luna is required;
- credential scraping or session-log collection;
- weakening Codex permissions or production approval boundaries;
- giant orchestration frameworks unrelated to the project's specific problem;
- keyword stuffing presented as AEO/SEO.

## Validation

For Python watcher changes:

```bash
python -m py_compile scripts/watch-codex-task.py
python -m unittest discover -s tests -v
```

For PowerShell watcher changes, ensure PowerShell can parse the file. GitHub Actions validates it on `windows-latest`.

## Pull requests

A useful PR should state:

1. what behavior changed;
2. why it is needed;
3. the failure mode before the change;
4. the regression test or deterministic proof;
5. any Codex-version assumptions introduced.

Keep changes small and inspectable. Session transcripts, credentials, `.codex` state, and customer/project data must never be committed.

## OpenAI compatibility

This repository is not affiliated with OpenAI. If a change depends on current Codex or GPT-5.6 behavior, link to official OpenAI documentation or clearly label the behavior as empirically observed and version-sensitive.

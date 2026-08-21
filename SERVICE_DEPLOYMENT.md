# Service Deployment Rule

After code changes, do not leave a temporary local development server running on an ad hoc port.

Deploy the app through the stable macOS LaunchAgent service on port `8765`:

```bash
PORT=8765 REPORTS_FAKE_PROVIDER=0 scripts/install_service.sh
curl --noproxy '*' http://127.0.0.1:8765/api/state
```

Use `REPORTS_FAKE_PROVIDER=1` only for tests or an explicit dry run. The persistent service should default to real provider execution.

If a temporary server was started during troubleshooting, stop it before handoff and report only the `8765` service URL.

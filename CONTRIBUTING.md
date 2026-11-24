# Contributing

Use synthetic postings and profiles in issues, tests and screenshots. Use the `examples/offline` fixtures as a starting point.

## Run the checks

Create a Python virtual environment and install the test dependencies.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-test.txt
python -m playwright install chromium
python -m pytest -q
ruff check scripts tests
node --check public/js/app.js
```

On Windows, run `py -3 -m venv .venv` and activate it with `.venv\Scripts\Activate.ps1`. Node is needed only for the JavaScript syntax check. See the [usage guide](docs/usage.md) for the command-line workflow.

For a policy change, add a case that shows the new decision and check the run manifest. Use public source documentation when changing an adapter. Keep live requests out of automated tests.

# Week 7 GitHub Actions UI Job

Draft UI job:

```yaml
ui-ci:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run UI tests
      run: pytest tests/
    - name: Run UI smoke test
      run: python scripts/week7_ui_ci_smoke_test.py
```

The working draft is committed in `.github/workflows/ci.yml`.

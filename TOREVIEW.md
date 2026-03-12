# CI/CD Review Notes

## Issue: GitHub Actions Build Failure

**Run:** https://github.com/globanov/parkpartner/actions/runs/22990588377/job/66750536707

### Root Cause

**Missing `python-multipart` dependency**

```
RuntimeError: Form data requires "python-multipart" to be installed.
```

FastAPI requires `python-multipart` for file upload handling (`File(...)`, `Form(...)`).

### Why Not Detected Locally

- `python-multipart` was installed as a **transitive dependency** in local `.venv`
- CI installs fresh dependencies - package was **not in `requirements.txt`**

### Fix Applied

Added to `requirements.txt`:

```txt
# FastAPI form data (required for file uploads)
python-multipart==0.0.20
```

---

## Original Analysis (for reference)

The CI build failed with exit code 2. Other potential issues:

1. **Missing FFmpeg** - Ubuntu runners don't have FFmpeg pre-installed
2. **Heavy dependencies** - `openai-whisper` with PyTorch (~2GB) causes timeout
3. **No pip cache** - Every run downloads from scratch
4. **Node.js 20 deprecation warning** - `actions/checkout@v4` and `actions/setup-python@v5` need updates

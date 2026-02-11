PaddleOCR Integration — Local & CI

This repository includes optional integration support for running real PaddleOCR-based
checks. Paddle and PaddleOCR are heavy and may have specific OS/CUDA requirements.

Files added:
- `requirements-paddle.txt` — optional dependencies for running PaddleOCR locally or in CI.
- `.github/workflows/paddle-integration.yml` — GitHub Actions job to install the optional
  dependencies and run a light verification.

Quick local steps (recommended inside a virtualenv):

1) Create virtualenv and activate

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\Activate.ps1 on Windows PowerShell
```

2) Install optional paddle deps (may take a while)

```bash
pip install -r requirements-paddle.txt
```

3) Run the verification script included in the repo

```bash
python verify_paddleocr.py
```

Notes:
- If you encounter the NumPy `np.sctypes` error, try installing `numpy<2.0` or use
  a paddle/paddleocr build compatible with NumPy 2.x.
- For GPU support, follow Paddle's official installation docs and install the
  appropriate `paddlepaddle` wheel for your CUDA version instead of the CPU package.

CI:
- The workflow `.github/workflows/paddle-integration.yml` provides a `workflow_dispatch`
  trigger to manually run the integration job. It installs `requirements-paddle.txt`
  and runs `verify_paddleocr.py` and the key tests. Adjust for runtime/runner limits.

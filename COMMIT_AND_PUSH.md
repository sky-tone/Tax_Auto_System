How to create a branch, commit and push these changes

Suggested commands (run in repo root):

```bash
# create and switch to a new branch
git checkout -b feat/paddle-integration

# add files and commit
git add requirements-paddle.txt .github/workflows/paddle-integration.yml README_INTEGRATION.md .github/copilot-instructions.md
git commit -m "Add PaddleOCR integration requirements, CI workflow and docs; improve ocr_process compatibility"

# push the branch
git push -u origin feat/paddle-integration
```

If you prefer PowerShell on Windows:

```powershell
git checkout -b feat/paddle-integration
git add requirements-paddle.txt .github/workflows/paddle-integration.yml README_INTEGRATION.md .github/copilot-instructions.md
git commit -m "Add PaddleOCR integration requirements, CI workflow and docs; improve ocr_process compatibility"
git push -u origin feat/paddle-integration
```

Notes:
- The CI job installs heavy packages; consider running it manually (`workflow_dispatch`) or adjusting runner specs.
- If you want me to create the branch and commit via the environment, I need repository remote credentials or a service token; otherwise please run the commands above.

# Deployment Runbook (Free Tier)

This project is deployed as two services:

- Frontend on Vercel (from web-ui)
- Backend on Hugging Face Spaces (Docker)

The repository is configured to keep datasets out of git pushes.

## 1. Preflight checks

Run from repository root:

```powershell
git status --short
```

Verify dataset folders are ignored:

```powershell
git check-ignore -v data1 merged_dataset depth_maps_1 depth_maps_global depth_maps_merged pothole600 rdd_temp RDD2022 gps/unannotated_images
```

## 2. What should be committed

Commit deployment/runtime files and app code, but not datasets.

Minimum required for deployment:

- Dockerfile
- requirements.txt
- .dockerignore
- .env.example
- api.py
- web-ui/src/App.jsx
- web-ui/vercel.json
- web-ui/.env.example
- web-ui/package.json

Optional runtime artifacts for backend insights/classifier features:

- ml_models/
- ml_results/
- yolo-segmentation/model/best.pt

Notes:
- Depth-Anything-V2 is intentionally ignored in git; Dockerfile fetches it automatically at build time.
- Datasets are intentionally ignored in git.

## 3. Push to GitHub

Stage selected files (safe path-specific add):

```powershell
git add .gitignore Dockerfile requirements.txt .dockerignore .env.example DEPLOYMENT.md api.py README.md web-ui/src/App.jsx web-ui/vercel.json web-ui/.env.example web-ui/package.json web-ui/package-lock.json
```

If you also want runtime model/results in backend deployment source:

```powershell
git add ml_models ml_results yolo-segmentation/model/best.pt
```

Commit and push:

```powershell
git commit -m "chore: prepare free-tier deployment for vercel + hf spaces"
git push
```

## 4. Deploy backend on Hugging Face Spaces (Docker)

1. Create a new Space:
   - SDK: Docker
   - Hardware: CPU Basic (free)
2. Connect/select your GitHub repo and branch.
3. Set Space Variables:
   - FRONTEND_ORIGINS=https://<your-vercel-domain>
4. Build starts automatically.

Backend URL format:

- https://<space-name>.hf.space

Health check after deployment:

- GET /healthz
- GET /insights/summary

Example:

```text
https://<space-name>.hf.space/healthz
```

## 5. Deploy frontend on Vercel

1. Import GitHub repo in Vercel.
2. Set Root Directory to web-ui.
3. Build settings:
   - Install Command: npm install
   - Build Command: npm run build
   - Output Directory: dist
4. Add environment variable:
   - VITE_API_BASE_URL=https://<space-name>.hf.space
5. Deploy.

SPA route fallback is handled by web-ui/vercel.json.

## 6. Post-deploy smoke test

1. Open deployed frontend.
2. Upload a test image in Detection tab.
3. Confirm analyze request returns results.
4. Open Insights tab and verify summary/graphs load.
5. If CORS error appears, update FRONTEND_ORIGINS in Space variables and rebuild.

## 7. Common issues

- 404 or blank route on frontend refresh:
  - Ensure web-ui/vercel.json is in git and deployed.
- Backend startup fails with missing depth checkpoint:
  - Dockerfile should fetch Depth-Anything-V2 and checkpoint automatically; check build logs for network download errors.
- Slow first request:
  - CPU cold-start + model warmup can take time on free tier.
- Large files accidentally staged:
  - Use git restore --staged <path> to unstage and keep local file.

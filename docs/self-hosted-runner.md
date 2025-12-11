# Self-Hosted Runner + Auto-Deploy

This host keeps the GitHub Actions runner binaries inside `actions-runner/`. Complete the steps below once per host so the `deploy` workflow can build and redeploy containers automatically whenever `main` is updated.

## Configure the Runner

1. In GitHub, open **Settings → Actions → Runners → New self-hosted runner** for `CalWooten95/roach-parlor` and copy the registration token (expires quickly).
2. Configure the runner and label it `roach-parlor` so it matches the workflow requirement:
   ```bash
   cd /home/mwooten/roach-parlor/actions-runner
   ./config.sh --url https://github.com/CalWooten95/roach-parlor \
     --token <token> \
     --name roach-parlor-runner \
     --labels self-hosted,roach-parlor
   ```
3. (Recommended) Install the service to keep it running between logins:
   ```bash
   sudo ./svc.sh install
   sudo ./svc.sh start
   ```
   Use `sudo ./svc.sh status|stop` as needed. If you cannot use sudo, run `./run.sh` in a persistent tmux/screen session.

## Workflow Details

- `.github/workflows/deploy.yml` listens to pushes on `main` (and manual `workflow_dispatch`).
- When triggered, the job targets `runs-on: [self-hosted, roach-parlor]`. GitHub will queue the job until your runner is online with that label.
- The `Update repository and rebuild containers` step runs inside `/home/mwooten/roach-parlor` (the live checkout that contains your `.env`). It performs:
  ```bash
  git fetch origin
  git checkout main
  git pull --ff-only origin main
  docker compose up --build -d
  ```
- If you prefer to deploy from a different branch (e.g., `master`), edit the `branches:` filter inside `deploy.yml`.

## Operational Notes

- The workflow assumes the repo remote uses credentials that already allow non-interactive fetches. Set up `git credential` helpers or a deploy token if pulls start failing for the service user.
- Runner binaries live under `actions-runner/`, which is `.gitignore`d so they are never committed.
- Restart the service after updating Docker / Compose or after modifying runner binaries.

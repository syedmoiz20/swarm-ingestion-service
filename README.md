# Swarm Ingestion Service

This repository contains a two-stage analytics ingestion pipeline:

- `swarm-ingestion-api`: a FastAPI service that accepts events and publishes them to Pub/Sub.
- `swarm-analytics-worker`: a Cloud Run worker pool that pulls from Pub/Sub and writes rows to BigQuery.

The deployment files in this repo keep that architecture intact:

- the API only publishes to Pub/Sub
- the worker is the only component that writes to BigQuery

## Deployment

### 1. Set project and region

Choose the Cloud Run region you want to deploy into. The examples below use a shell variable so you can reuse the same commands for both components.

```bash
export PROJECT_ID="swarm-analytics-491623"
export REGION="us-central1"

gcloud config set project "$PROJECT_ID"
gcloud config set run/region "$REGION"
```

### 2. Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  pubsub.googleapis.com \
  bigquery.googleapis.com
```

### 3. Install the beta gcloud component for worker pools

Cloud Run worker pool deployment currently uses beta commands. If your local SDK does not already include the beta component, install it once:

```bash
gcloud components install beta
```

### 4. Grant the minimum IAM roles needed for source deploys

Your deployer account needs:

- `roles/run.sourceDeveloper`
- `roles/serviceusage.serviceUsageConsumer`
- `roles/iam.serviceAccountUser` on the runtime service accounts you deploy with

If you also need to enable APIs yourself, you need:

- `roles/serviceusage.serviceUsageAdmin`

Source deployments also require the Cloud Build service account to be able to build for Cloud Run:

```bash
export PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/run.builder"
```

### 5. Create runtime service accounts

Using separate runtime identities keeps Pub/Sub and BigQuery permissions scoped to the component that actually needs them.

```bash
gcloud iam service-accounts create swarm-ingestion-api \
  --display-name="Swarm Ingestion API"

gcloud iam service-accounts create swarm-analytics-worker \
  --display-name="Swarm Analytics Worker"
```

Grant the ingestion API permission to publish to Pub/Sub:

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:swarm-ingestion-api@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"
```

Grant the worker permission to pull from Pub/Sub and write to BigQuery:

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:swarm-analytics-worker@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/pubsub.subscriber"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:swarm-analytics-worker@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:swarm-analytics-worker@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

If you prefer least-privilege BigQuery access, grant `BigQuery Data Editor` on the `swarm_analytics` dataset instead of the whole project.

### 6. Deploy the ingestion API from source

This deploy uses the repo root as the build source, the root `Dockerfile` as the build definition, and `deploy/api.env.yaml` for the Cloud Run environment variables.

```bash
gcloud run deploy swarm-ingestion-api \
  --source . \
  --region "$REGION" \
  --port 8080 \
  --allow-unauthenticated \
  --env-vars-file deploy/api.env.yaml \
  --service-account "swarm-ingestion-api@${PROJECT_ID}.iam.gserviceaccount.com"
```

Get the service URL:

```bash
gcloud run services describe swarm-ingestion-api \
  --region "$REGION" \
  --format='value(status.url)'
```

### 7. Deploy the worker pool from source

This deploy uses the same source image, but overrides the startup command so the worker pool runs the long-lived Pub/Sub subscriber instead of the HTTP server.

```bash
gcloud beta run worker-pools deploy swarm-analytics-worker \
  --source . \
  --region "$REGION" \
  --instances 1 \
  --env-vars-file deploy/worker.env.yaml \
  --service-account "swarm-analytics-worker@${PROJECT_ID}.iam.gserviceaccount.com" \
  --command /app/scripts/start_worker.sh
```

### 8. View logs

Read API logs:

```bash
gcloud run services logs read swarm-ingestion-api \
  --region "$REGION" \
  --limit 100
```

Read worker logs:

```bash
gcloud beta run worker-pools logs read swarm-analytics-worker \
  --region "$REGION" \
  --limit 100
```

### 9. Update or redeploy

Redeploy the API after code changes:

```bash
gcloud run deploy swarm-ingestion-api \
  --source . \
  --region "$REGION" \
  --port 8080 \
  --allow-unauthenticated \
  --env-vars-file deploy/api.env.yaml \
  --service-account "swarm-ingestion-api@${PROJECT_ID}.iam.gserviceaccount.com"
```

Update only the API environment variables:

```bash
gcloud run services update swarm-ingestion-api \
  --region "$REGION" \
  --env-vars-file deploy/api.env.yaml
```

Redeploy the worker pool after code changes:

```bash
gcloud beta run worker-pools deploy swarm-analytics-worker \
  --source . \
  --region "$REGION" \
  --instances 1 \
  --env-vars-file deploy/worker.env.yaml \
  --service-account "swarm-analytics-worker@${PROJECT_ID}.iam.gserviceaccount.com" \
  --command /app/scripts/start_worker.sh
```

Update only the worker pool environment variables:

```bash
gcloud beta run worker-pools update swarm-analytics-worker \
  --region "$REGION" \
  --env-vars-file deploy/worker.env.yaml
```

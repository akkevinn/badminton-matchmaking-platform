#!/bin/bash
# Deploy script for Prunus Sport — Badminton Matchmaking Platform
# Uses direct SSH/SCP (no gcloud auth required — works with any GCP account)

set -e

# ── Configuration ─────────────────────────────────────────
VM_IP="${VM_IP:?Set VM_IP, e.g. export VM_IP=34.101.123.45 (copy from GCP console)}"
VM_USER="${VM_USER:?Set VM_USER, e.g. export VM_USER=yourname (Google account, part before @)}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"   # path to your SSH private key
PROJECT_DIR="badminton-matchmaking-platform"
ZIP_NAME="prunus-deploy.tar.gz"
# ──────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "──────────────────────────────────────"
echo " Prunus Sport — Deploy"
echo " Target: $VM_USER@$VM_IP"
echo "──────────────────────────────────────"

# Step 1: Create tar archive locally (tar is always available on Linux — no install needed)
echo ""
echo "📦 Step 1/4 — Creating archive..."
cd "$ROOT_DIR"
tar -czf "$ZIP_NAME" \
    --exclude=".venv" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude=".git" \
    --exclude=".DS_Store" \
    --exclude="*.db" \
    --exclude="prunus-deploy.tar.gz" \
    "$PROJECT_DIR"

ZIP_SIZE=$(du -sh "$ZIP_NAME" | cut -f1)
echo "   ✅ Created $ZIP_NAME ($ZIP_SIZE)"

# Step 2: Upload zip via SCP (standard SSH — no gcloud needed)
echo ""
echo "📤 Step 2/4 — Uploading to VM $VM_IP..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    "$ROOT_DIR/$ZIP_NAME" \
    "$VM_USER@$VM_IP":~/
echo "   ✅ Upload complete"

# Step 3: Extract on VM
echo ""
echo "📂 Step 3/4 — Extracting on VM..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$VM_USER@$VM_IP" \
    "tar -xzf ~/$ZIP_NAME -C ~/ && rm ~/$ZIP_NAME"
echo "   ✅ Extracted"

# Step 4: Build and start Docker container
echo ""
echo "🐳 Step 4/4 — Starting Docker container..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$VM_USER@$VM_IP" \
    "cd ~/$PROJECT_DIR && docker compose up -d --build"
echo "   ✅ Container started"

# Clean up local zip
rm -f "$ROOT_DIR/$ZIP_NAME"

echo ""
echo "──────────────────────────────────────"
echo " 🎉 Deployment successful!"
echo ""
echo "    Open in Safari: http://$VM_IP:8000"
echo "──────────────────────────────────────"

#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Verify and create/update Taiga story for SPEC-126: ML Model Training & Fine-Tuning Pipeline

This script:
1. Checks if US#598 exists in Taiga
2. Updates it if it exists (adds implementation status)
3. Creates a new story if it doesn't exist
"""

import os
import sys
from typing import Dict, Optional

import requests

# Taiga API configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
PROJECT_SLUG = "ninaivalaigal"


def get_auth_token() -> Optional[str]:
    """Authenticate with Taiga and get auth token"""
    try:
        response = requests.post(
            f"{API_ENDPOINT}/auth", json={"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}
        )
        if response.status_code == 200:
            return response.json().get("auth_token")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error authenticating: {e}")
        return None


def get_project(token: str) -> Optional[Dict]:
    """Get project by slug"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Project not found: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting project: {e}")
        return None


def get_story_by_ref(token: str, project_id: int, story_ref: int) -> Optional[Dict]:
    """Get story by reference number"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_ENDPOINT}/userstories", headers=headers, params={"project": project_id})
        if response.status_code == 200:
            stories = response.json()
            for story in stories:
                if story.get("ref") == story_ref:
                    return story
        return None
    except Exception as e:
        print(f"❌ Error getting story #{story_ref}: {e}")
        return None


def find_story_by_subject_or_tags(token: str, project_id: int, search_terms: list) -> Optional[Dict]:
    """Find story by subject or tags"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_ENDPOINT}/userstories", headers=headers, params={"project": project_id})
        if response.status_code == 200:
            stories = response.json()
            for story in stories:
                subject = story.get("subject", "").lower()
                tags = []
                for tag in story.get("tags", []):
                    if isinstance(tag, str):
                        tags.append(tag.lower())
                    elif isinstance(tag, dict):
                        tags.append(tag.get("name", "").lower())

                for term in search_terms:
                    term_lower = term.lower()
                    if term_lower in subject or any(term_lower in tag for tag in tags):
                        return story
        return None
    except Exception as e:
        print(f"❌ Error searching stories: {e}")
        return None


def get_status_id(token: str, project_id: int, status_name: str = "Ready") -> Optional[int]:
    """Get status ID by name"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_ENDPOINT}/userstory-statuses", headers=headers, params={"project": project_id})
        if response.status_code == 200:
            for status in response.json():
                if status["name"].lower() == status_name.lower():
                    return status["id"]
        return None
    except Exception as e:
        print(f"❌ Error getting statuses: {e}")
        return None


def update_story(token: str, story: Dict, new_description: str) -> bool:
    """Update existing story"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.patch(
            f'{API_ENDPOINT}/userstories/{story["id"]}',
            headers=headers,
            json={"description": new_description, "version": story.get("version", 1)},
        )
        if response.status_code in [200, 204]:
            print(f"✅ Story #{story['ref']} updated successfully")
            return True
        else:
            print(f"⚠️  Failed to update story #{story['ref']}: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error updating story: {e}")
        return False


def create_story(token: str, project_id: int, status_id: int) -> bool:
    """Create new story for SPEC-126"""
    try:
        headers = {"Authorization": f"Bearer {token}"}

        story_data = {
            "subject": "SPEC-126: ML Model Training & Fine-Tuning Pipeline",
            "description": get_story_description(),
            "project": project_id,
            "status": status_id,
            "tags": ["spec-126", "mlops", "kubeflow", "mlflow", "planned", "phase-4"],
        }

        response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=story_data)

        if response.status_code in [200, 201]:
            story = response.json()
            print(f"✅ Story #{story.get('ref', 'N/A')} created successfully")
            print(f"   URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story.get('ref', 'N/A')}")
            return True
        else:
            print(f"⚠️  Failed to create story: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating story: {e}")
        return False


def get_story_description() -> str:
    """Get story description for SPEC-126"""
    return """**SPEC-126: ML Model Training & Fine-Tuning Pipeline**

**Status:** ⚠️ **Not Implemented** (0% - Planned)
**Priority:** P2 (Blocked by dependencies)
**Phase:** Phase 4

---

## 📋 Overview

Create a unified ML model training and fine-tuning pipeline with MLOps capabilities for training models on ninaivalaigal data.

---

## 🎯 Objectives

- **Unified Training Pipeline**: Reproducible training via Kubeflow / Vertex AI / MLflow
- **Model Fine-Tuning**: Domain-adaptive fine-tuning on internal datasets
- **Experiment Tracking**: MLflow + Weights & Biases integration
- **Continuous Retraining**: Triggered by SPEC-040 feedback loops
- **Governance & Compliance**: Integrate lineage, license, and audit tracking

---

## 📊 Implementation Status (January 2025)

### ❌ Not Implemented (0%)

- ❌ **No MLOps Infrastructure** - Kubeflow, MLflow not deployed
- ❌ **No Training Pipelines** - No data collection, preparation, or training pipelines
- ❌ **No Model Registry** - MLflow model store not deployed
- ❌ **No Data Versioning** - DVC not integrated
- ❌ **No Experiment Tracking** - MLflow/W&B not configured
- ❌ **No Model Serving** - Inference endpoints not implemented
- ❌ **No Compliance Features** - License scanning, audit trail not implemented

---

## 🔗 Dependencies

### ⚠️ Blocking Dependencies (Must be ready before starting)

1. **SPEC-082**: Narrative Analytics Layer - **Planned** (needs at least partial implementation)
2. **SPEC-117**: Feature Flags - **In Progress (20%)** (needs completion for A/B testing)

### ✅ Ready Dependencies

1. **SPEC-031**: Memory Relevance Ranking - **Complete (75%)** - Provides labeled relevance data
2. **SPEC-040**: Feedback Loop System - **Complete (100%)** - Feedback signals for retraining
3. **SPEC-085**: Staff Management - **Complete** - Dual approval workflow

### ⚠️ Unknown Dependencies

1. **SPEC-041**: Related Memory Suggestions - **Needs verification**

---

## 📋 Implementation Phases

### Phase 1: Infrastructure (Q2 2025) - P1
- Deploy Kubeflow Pipelines on Kubernetes
- Deploy MLflow model registry
- Set up GPU node pools
- Configure data storage (MinIO/S3)
- Set up DVC for dataset versioning

### Phase 2: Pipeline Development (Q2-Q3 2025) - P1
- Build data collection pipeline (from SPEC-040 feedback)
- Build data preparation pipeline (feature extraction)
- Build training pipeline (Memory Relevance first)
- Implement model validation
- Set up experiment tracking (MLflow + W&B)

### Phase 3: Model Deployment (Q3-Q4 2025) - P2
- Implement model serving endpoints
- Integrate with SPEC-117 for A/B testing
- Set up monitoring and drift detection
- Implement rollback capability
- Deploy first model (Memory Relevance Scorer) to staging

### Phase 4: Compliance & Production (Q4 2025) - P2
- Implement audit trail
- Set up dual approval workflow (SPEC-085)
- Add license scanning automation
- Generate model cards
- Deploy to production

---

## 🎯 Model Families

1. **Memory Relevance Scorer** - Ranking & scoring (SPEC-031 data)
2. **Memory Similarity Embedder** - Embedding optimization (SPEC-041 features)
3. **Behavior Predictor** - User action modeling (SPEC-082 analytics)
4. **Context Understanding** - Context injection refinement (SPEC-040 feedback)

---

## ✅ Acceptance Criteria

- [ ] Kubeflow pipelines operational
- [ ] MLflow model registry deployed
- [ ] Training pipeline for Memory Relevance Scorer complete
- [ ] Model serving endpoints operational
- [ ] A/B testing integrated (SPEC-117)
- [ ] Audit trail implemented
- [ ] Dual approval workflow integrated (SPEC-085)
- [ ] Model cards generated automatically

---

## 🚨 Blockers

1. **SPEC-082**: Analytics Dashboard must be at least partially implemented
2. **SPEC-117**: Feature Flags must be complete for A/B testing
3. **Infrastructure**: Kubernetes cluster with GPU nodes required

---

## 📚 References

- **SPEC Document**: `specs/126-ml-model-training-pipeline/README.md`
- **Analysis**: `docs/spec-analysis/SPEC_126_COMPREHENSIVE_ANALYSIS.md`
- **Review Summary**: `tasks/active/SPEC_126_REVIEW_SUMMARY.md`

---

**Status**: ⏳ **Planned** - Waiting for dependencies (SPEC-082, SPEC-117)
**Created**: January 2025
**Next Review**: After dependencies are ready"""


def main():
    """Main function"""
    print("=" * 70)
    print("SPEC-126 Story Verification & Creation")
    print("=" * 70)

    # Authenticate
    print("\n🔐 Authenticating...")
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed. Exiting.")
        return 1

    print("✅ Authenticated successfully")

    # Get project
    print(f"\n📁 Getting project '{PROJECT_SLUG}'...")
    project = get_project(token)
    if not project:
        print("❌ Project not found. Exiting.")
        return 1

    project_id = project["id"]
    print(f"✅ Project found: {project.get('name', 'Unknown')}")

    # Check if US#598 exists by ref
    print("\n📋 Checking for US#598...")
    story = get_story_by_ref(token, project_id, 598)

    # If not found by ref, search by subject/tags
    if not story:
        print("   Searching by subject/tags...")
        story = find_story_by_subject_or_tags(
            token, project_id, ["SPEC-126", "ML Model Training", "Fine-Tuning Pipeline", "spec-126"]
        )

    if story:
        print(f"✅ Found US#{story['ref']}: {story.get('subject', 'No subject')}")
        print(f"   Status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
        print(f"   URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story['ref']}")

        # Check if description needs update
        current_desc = story.get("description", "")
        new_desc = get_story_description()

        if "Implementation Status (January 2025)" in current_desc and "Dependencies Status" in current_desc:
            print("   ⚠️  Story already has recent implementation status")
            response = input("   Update anyway? (y/N): ")
            if response.lower() != "y":
                print("   Skipping update")
                return 0

        # Update story
        print("\n📝 Updating story description...")
        if update_story(token, story, new_desc):
            print(f"\n✅ Story #{story['ref']} updated successfully")
            print(f"   URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story['ref']}")
        else:
            print(f"\n⚠️  Failed to update story #{story['ref']}")
            return 1
    else:
        print("❌ Story US#598 not found")

        # Get status ID for "Ready" or "New"
        print("\n📋 Getting status ID...")
        status_id = get_status_id(token, project_id, "Ready")
        if not status_id:
            status_id = get_status_id(token, project_id, "New")
        if not status_id:
            print("⚠️  Could not find 'Ready' or 'New' status. Using first available status.")
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{API_ENDPOINT}/userstory-statuses", headers=headers, params={"project": project_id}
            )
            if response.status_code == 200:
                statuses = response.json()
                if statuses:
                    status_id = statuses[0]["id"]
                    print(f"   Using status: {statuses[0].get('name', 'Unknown')}")

        if not status_id:
            print("❌ Could not find any status. Exiting.")
            return 1

        # Create story
        print("\n📝 Creating new story...")
        if create_story(token, project_id, status_id):
            print("\n✅ Story created successfully")
        else:
            print("\n⚠️  Failed to create story")
            return 1

    print("\n" + "=" * 70)
    print("✅ Verification Complete!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())

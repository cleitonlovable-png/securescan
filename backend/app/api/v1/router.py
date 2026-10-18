from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, dashboard, findings, organizations, overview, projects, quick_scan, scans

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(organizations.router)
router.include_router(projects.router)
router.include_router(quick_scan.router)
router.include_router(scans.router)
router.include_router(findings.router)
router.include_router(dashboard.router)
router.include_router(overview.router)

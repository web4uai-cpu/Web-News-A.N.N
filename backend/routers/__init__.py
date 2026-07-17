"""A.N.N. domain routers — mounted by backend/main.py."""

from routers import (
    admin,
    billing,
    dashboard,
    feeds,
    media,
    pipeline,
    portal,
    scripts,
    social,
    system,
    ws,
)

ALL_ROUTERS = [
    system.router,
    pipeline.router,
    scripts.router,
    dashboard.router,
    media.router,
    feeds.router,
    admin.router,
    billing.router,
    portal.router,
    social.router,
    ws.router,
]

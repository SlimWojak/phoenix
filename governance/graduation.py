"""
Graduation Ceremony — DEPLOY.P2.4
===================================

Constitutional mechanism: shadow → paper → live.

INV-SHADOW-GRADUATION-ONCE: graduation requires ceremony, cannot self-reverse.
INV-LIVE-REQUIRES-T2: live execution requires human T2 approval token.
INV-SHADOW-MODE-RESPECTED: shadow_mode at lease level, not code level.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GraduationRequirements:
    """Thresholds for shadow → paper graduation."""

    min_shadow_days: int = 5
    min_shadow_signals: int = 3
    requires_cso_signoff: bool = True
    requires_g_approval: bool = True
    requires_dream_cycle_summary: bool = True


def check_graduation_ready(
    observation_count: int,
    days_active: int,
    has_cso_signoff: bool = False,
    has_g_approval: bool = False,
    has_dream_cycle_summary: bool = False,
    requirements: GraduationRequirements | None = None,
) -> tuple[bool, list[str]]:
    """
    Check if shadow observation period meets graduation requirements.

    INV-SHADOW-GRADUATION-ONCE: All requirements must be met.
    No partial graduation. No automatic promotion.

    Returns:
        (ready, reasons_not_ready) — ready=True only if ALL requirements pass.
    """
    reqs = requirements or GraduationRequirements()
    blockers: list[str] = []

    if days_active < reqs.min_shadow_days:
        blockers.append(f"days_active={days_active} < min={reqs.min_shadow_days}")

    if observation_count < reqs.min_shadow_signals:
        blockers.append(f"observations={observation_count} < min={reqs.min_shadow_signals}")

    if reqs.requires_cso_signoff and not has_cso_signoff:
        blockers.append("CSO signoff (Olya) not provided")

    if reqs.requires_g_approval and not has_g_approval:
        blockers.append("G approval not provided")

    if reqs.requires_dream_cycle_summary and not has_dream_cycle_summary:
        blockers.append("Dream Cycle MFE/MAE summary not provided")

    return len(blockers) == 0, blockers


__all__ = [
    "GraduationRequirements",
    "check_graduation_ready",
]

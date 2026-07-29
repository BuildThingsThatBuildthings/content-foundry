"""Draft a portable creative system from a universal job and domain pack."""

from __future__ import annotations

from typing import Any


STRUCTURAL_DIRECTIONS = (
    {
        "id": "cinematic-world",
        "name": "Cinematic World Reveal",
        "layout_family": "cinematic-portal",
        "scene_construction": "spatial-world",
        "camera_behavior": "continuous-flight",
        "pacing": "slow-build-to-rapid-proof",
        "hierarchy": "image-led",
        "metaphor": "enter-the-transformed-world",
    },
    {
        "id": "editorial-proof",
        "name": "Asymmetric Editorial Proof",
        "layout_family": "asymmetric-editorial",
        "scene_construction": "presenter-proof-split",
        "camera_behavior": "locked-graphic-with-punch-ins",
        "pacing": "measured-proof-beats",
        "hierarchy": "type-and-proof-led",
        "metaphor": "evidence-on-the-table",
    },
    {
        "id": "kinetic-system",
        "name": "Kinetic System Demonstration",
        "layout_family": "kinetic-workflow",
        "scene_construction": "diagram-to-interface",
        "camera_behavior": "orthographic-tracking",
        "pacing": "fast-modular",
        "hierarchy": "process-led",
        "metaphor": "chaos-becomes-a-system",
    },
)


def draft_creative_system(job: dict[str, Any], pack: dict[str, Any]) -> dict[str, Any]:
    objective = job["objective"]
    channels = ", ".join(job.get("channels", [])) or "owned channels"
    hook = pack.get("default_hook") or f"Make {objective.lower()} immediately understandable"
    promise = pack.get("emotional_promise") or "Replace uncertainty with a clear next action."
    directions = []
    for index, base in enumerate(STRUCTURAL_DIRECTIONS, start=1):
        direction = dict(base)
        direction["hypothesis"] = (
            f"Direction {index} earns attention for {objective} through "
            f"{direction['scene_construction']} rather than a palette swap."
        )
        directions.append(direction)
    return {
        "schema_version": "1.0",
        "status": "draft",
        "objective": objective,
        "strategic_hook": hook,
        "emotional_promise": promise,
        "narrative_arc": [
            "pattern interrupt",
            "recognizable problem",
            "mechanism or transformation",
            "specific proof",
            "single conversion action",
        ],
        "reference_decomposition": {
            "required": True,
            "dimensions": [
                "composition",
                "typography",
                "camera",
                "motion",
                "texture",
                "lighting",
                "audio",
                "conversion mechanics",
            ],
            "rule": "Treat references as evidence, never as templates to recolor.",
        },
        "visual_world": pack.get("visual_world", "A tactile, dimensional operating world"),
        "layout_families": [item["layout_family"] for item in directions],
        "scene_archetypes": pack.get(
            "scene_archetypes",
            [
                "cinematic portal/world reveal",
                "asymmetric editorial",
                "presenter and proof split",
                "kinetic workflow explanation",
                "product/interface demonstration",
                "conversion endcard",
            ],
        ),
        "type_system": {
            "behavior": "responsive measured type",
            "minimum_layers": 2,
            "maximum_layers": 4,
            "line_breaks": "pretext-or-metric-derived",
        },
        "depth": "foreground framing, midground subject, background atmosphere",
        "lighting": pack.get("lighting", "motivated key light with practical accents"),
        "color_texture_material": pack.get(
            "materials", "brand-derived color, physical texture, controlled glow"
        ),
        "camera_grammar": [
            "establish",
            "approach",
            "reveal",
            "detail",
            "proof",
            "resolve",
        ],
        "motion_cadence": "contrast calm comprehension beats with decisive transitions",
        "transition_motif": pack.get("transition_motif", "depth portal and object match"),
        "caption_behavior": {
            "timing": "word-level",
            "grouping": "reading-speed",
            "maximum_words": 10,
            "safe_zones": channels,
        },
        "audio_signature": {
            "music": "licensed, project-specific",
            "sfx": "motivated transitions only",
            "voice": "approved human or disclosed provider",
        },
        "cta_system": {
            "count": 1,
            "placement": "final resolution plus optional persistent micro-CTA",
            "legibility": "thumbnail and channel-safe-zone checked",
        },
        "anti_reference": [
            "palette-only variation",
            "centered-everything template",
            "dense poster pan",
            "unmotivated gradient",
            "generic AI particles",
            "invented proof",
        ],
        "directions": directions,
    }

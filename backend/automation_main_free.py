"""Zero-cost production entrypoint for the daily Instagram Story service."""

from . import story_copy
from .story_copy_free import generate_free_story_copy


# The existing orchestration keeps its validation, image rendering, idempotency,
# and Instagram publishing logic. Only the paid copy generator is replaced.
story_copy._fallback_copy = generate_free_story_copy


def _generate_free_copy(facts, *, recent_titles=(), offline=False):
    """Match the paid generator's call signature without making any API call."""

    del recent_titles, offline
    return generate_free_story_copy(facts)


story_copy.generate_story_copy = _generate_free_copy

from .automation_main_final import app  # noqa: E402,F401


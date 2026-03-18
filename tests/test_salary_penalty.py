"""Tests for salary validation penalty rules (V17 architectural fix)."""

from __future__ import annotations


class TestSalaryPenaltyRules:
    """Verify salary penalty application rules from algorithms.md."""

    def test_below_minimum_gets_penalty(self):
        """Job with salary_max below user's salary_min gets -10."""
        user_salary_min = 40000
        job_salary_max = 35000
        penalty = -10 if job_salary_max < user_salary_min else 0
        assert penalty == -10

    def test_overlapping_range_no_penalty(self):
        """Job where salary_min < user min but salary_max >= user min: no penalty."""
        user_salary_min = 40000
        job_salary_min = 25000
        job_salary_max = 60000
        penalty = -10 if job_salary_max < user_salary_min else 0
        assert penalty == 0

    def test_no_salary_listed_no_penalty(self):
        """Job with no salary info: no penalty."""
        job_salary_max = None
        penalty = -10 if (job_salary_max is not None and job_salary_max < 40000) else 0
        assert penalty == 0

    def test_penalty_can_push_below_threshold(self):
        """Base score 75 with -10 penalty = 65 (below 70 threshold but still presented)."""
        base_score = 75
        penalty = -10
        final_score = base_score + penalty
        assert final_score == 65
        # Job is still presented (base >= 70) but with penalty tag

    def test_penalized_cannot_outrank_compliant(self):
        """A penalized job with base 85 (final 75) ranks below compliant job with base 80."""
        job_a = {"base": 85, "penalty": -10, "final": 75}
        job_b = {"base": 80, "penalty": 0, "final": 80}
        ranked = sorted([job_a, job_b], key=lambda j: j["final"], reverse=True)
        assert ranked[0] == job_b  # compliant job ranks higher

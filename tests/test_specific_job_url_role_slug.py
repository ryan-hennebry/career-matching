"""_is_specific_job_url: two-segment employer role pages with a hyphenated role slug."""

import pytest

import manage_state as ms

SPECIFIC = [
    "https://one.example.org/careers/marketing-lead",
    "https://two.example.org/careers/founding-marketing",
    "https://three.example.org/careers/founding-growth-marketer",
    "https://example.org/jobs/founding-growth-marketer",
    "https://example.org/roles/head-of-marketing",
]

NOT_SPECIFIC = [
    "https://example.com/careers",
    "https://example.com/careers/",
    "https://example.com/jobs",
    "https://example.com/careers/open-positions",
    "https://example.com/careers/open-roles",
    "https://example.com/careers/all-jobs",
    "https://example.com/careers/join-us",
    "https://example.com/careers/engineering",
    "https://example.com/job",
    "https://example.com/about-us",
    "https://example.com/team/our-people",
]


@pytest.mark.parametrize("url", SPECIFIC)
def test_role_slug_is_specific(url):
    assert ms._is_specific_job_url(url) is True


@pytest.mark.parametrize("url", NOT_SPECIFIC)
def test_generic_page_is_not_specific(url):
    assert ms._is_specific_job_url(url) is False

/**
 * API client for JSA V17 Dashboard.
 * Wraps all backend endpoints with fetch() + JSON parsing.
 */
const API = (() => {
  const BASE = '/api';

  async function request(path, options = {}) {
    // Append .py extension before query string for Vercel Python functions.
    // Vercel serves Python handlers at /api/name.py — cleanUrls removes
    // the extension once enabled, but .py works in both cases.
    const qIdx = path.indexOf('?');
    const pyPath = qIdx === -1
      ? `${path}.py`
      : `${path.slice(0, qIdx)}.py${path.slice(qIdx)}`;
    try {
      const res = await fetch(`${BASE}${pyPath}`, options);
      const data = await res.json();
      if (!res.ok) {
        return { error: data.error || `HTTP ${res.status}` };
      }
      return data;
    } catch (err) {
      return { error: err.message };
    }
  }

  return {
    /** GET /api/state — Summary counts for dashboard header. */
    getState() {
      return request('/state');
    },

    /** GET /api/jobs — Job list with scores and pipeline stages. */
    getJobs() {
      return request('/jobs');
    },

    /** GET /api/job?key=... — Single job detail. */
    getJob(key) {
      return request(`/job?key=${encodeURIComponent(key)}`);
    },

    /** POST /api/action — Write user action to Upstash Redis. */
    postAction(key, action) {
      return request('/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, action }),
      });
    },

    /** GET /api/brief?key=... — Render individual brief as HTML. */
    getBrief(key) {
      return request(`/brief?key=${encodeURIComponent(key)}`);
    },

    /** GET /api/pipeline — Jobs grouped by pipeline stage. */
    getPipeline() {
      return request('/pipeline');
    },

    /** GET /api/context — Profile section names from context.md. */
    getContext(sections) {
      const qs = sections ? `?sections=${encodeURIComponent(sections)}` : '';
      return request(`/context${qs}`);
    },

    /** POST /api/run — Trigger an authenticated workflow run. */
    triggerRun(roleTypes, secret) {
      return request('/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${secret}`,
        },
        body: JSON.stringify({ role_types: roleTypes }),
      });
    },

    /** GET /api/run — Poll workflow run status. */
    getRunStatus() {
      return request('/run');
    },
  };
})();

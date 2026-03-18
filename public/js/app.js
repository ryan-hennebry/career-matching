/**
 * Application router and view controller for JSA V17 Dashboard.
 * Hash-based routing: #digest (default), #pipeline, #detail/{key}, #brief/{key}
 */
const App = (() => {
  let allJobs = [];
  let stateData = null;
  let currentStage = 'all';
  let previousHash = '';

  /** Format a date string for display. */
  function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return 'Last updated: ' + d.toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric'
    });
  }

  /** Initialize the app on load. */
  async function init() {
    await loadData();
    setupSidebar();
    setupRunButton();
    window.addEventListener('hashchange', route);
    route();
  }

  /** Load state + jobs from API. */
  async function loadData() {
    const container = document.getElementById('content');
    if (container) {
      container.innerHTML = '<div class="loading-state"><span class="loading-spinner"></span> Loading jobs...</div>';
    }

    const [state, jobs] = await Promise.all([API.getState(), API.getJobs()]);

    if (!state.error) {
      stateData = state;
      const statsEl = document.getElementById('summary-stats');
      if (statsEl) statsEl.innerHTML = Components.summaryStats(state.counts);
      Components.sidebarCounts(state.counts);

      // Show run date in title
      if (state.run_date) {
        const titleEl = document.querySelector('.summary-title');
        if (titleEl) titleEl.textContent = `Job Search Agent`;
      }

      // Populate last-run date
      const dateEl = document.getElementById('summary-date');
      if (dateEl && state.last_run_date) {
        dateEl.textContent = formatDate(state.last_run_date);
      }
    }

    if (!jobs.error && Array.isArray(jobs)) {
      allJobs = jobs;
    }
  }

  /** Set up sidebar click handlers. */
  function setupSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    sidebar.addEventListener('click', (e) => {
      const item = e.target.closest('.sidebar-item');
      if (!item) return;
      const stage = item.dataset.stage;
      if (!stage) return;

      // Update active state
      sidebar.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
      item.classList.add('active');

      currentStage = stage;
      window.location.hash = '#digest';
    });
  }

  /** Set up Run Now button. */
  function setupRunButton() {
    const btn = document.getElementById('run-now-btn');
    const overlay = document.getElementById('run-overlay');
    const cancelBtn = document.getElementById('run-cancel-btn');
    const confirmBtn = document.getElementById('run-confirm-btn');
    const checkboxContainer = document.getElementById('role-type-checkboxes');

    if (!btn || !overlay) return;

    btn.addEventListener('click', async () => {
      // Get unique role types from loaded jobs
      const roleTypes = [...new Set(allJobs.map(j => j.role_type).filter(Boolean))];
      if (checkboxContainer) {
        checkboxContainer.innerHTML = Components.runPanel(roleTypes);
      }
      overlay.style.display = 'flex';
    });

    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        overlay.style.display = 'none';
      });
    }

    if (confirmBtn) {
      confirmBtn.addEventListener('click', async () => {
        const checked = overlay.querySelectorAll('input[type="checkbox"]:checked');
        const selected = Array.from(checked).map(cb => cb.value);
        if (selected.length === 0) return;

        const secret = prompt('Enter your JSA run secret:');
        if (!secret) return;

        const statusEl = document.getElementById('run-status');
        if (statusEl) {
          statusEl.style.display = 'block';
          statusEl.textContent = 'Dispatching search...';
        }

        const result = await API.triggerRun(selected, secret);
        if (result.error) {
          if (statusEl) statusEl.textContent = `Error: ${result.error}`;
        } else {
          if (statusEl) statusEl.textContent = 'Workflow dispatched. Polling status...';
          pollRunStatus(statusEl, overlay);
        }
      });
    }

    // Close overlay on background click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) overlay.style.display = 'none';
    });
  }

  /** Poll GitHub Actions run status until complete. */
  async function pollRunStatus(statusEl, overlay) {
    let attempts = 0;
    const maxAttempts = 60; // 5 minutes at 5s intervals

    const poll = async () => {
      attempts++;
      if (attempts > maxAttempts) {
        if (statusEl) statusEl.textContent = 'Timed out waiting for workflow. Check GitHub Actions.';
        return;
      }

      const status = await API.getRunStatus();
      if (status.error) {
        if (statusEl) statusEl.textContent = `Poll error: ${status.error}`;
        return;
      }

      if (status.conclusion === 'success') {
        if (statusEl) statusEl.textContent = 'Search complete. Refreshing...';
        overlay.style.display = 'none';
        await loadData();
        route();
        return;
      }

      if (status.conclusion === 'failure') {
        if (statusEl) statusEl.textContent = 'Workflow failed. Check GitHub Actions for details.';
        return;
      }

      if (statusEl) statusEl.textContent = `Status: ${status.status || 'pending'}... (${attempts * 5}s)`;
      setTimeout(poll, 5000);
    };

    setTimeout(poll, 5000);
  }

  /** Route based on hash. */
  function route() {
    const hash = window.location.hash || '#digest';
    const content = document.getElementById('content');
    if (!content) return;

    if (hash.startsWith('#detail/')) {
      const key = decodeURIComponent(hash.slice(8));
      renderDetail(content, key);
    } else if (hash.startsWith('#brief/')) {
      const key = decodeURIComponent(hash.slice(7));
      renderBrief(content, key);
    } else if (hash === '#pipeline') {
      renderPipeline(content);
    } else {
      renderDigest(content);
    }
  }

  /** Render digest view — "New" + "Reviewing" sections with job cards. */
  function renderDigest(container) {
    const filtered = currentStage === 'all'
      ? allJobs
      : allJobs.filter(j => j.stage === currentStage);

    if (filtered.length === 0) {
      // No jobs found — use enhanced empty state with CTA
      container.innerHTML = renderEmptyState(true);
      return;
    }

    // Group by stage for "all" view, or show flat list for filtered view
    if (currentStage === 'all') {
      const newJobs = filtered.filter(j => j.stage === 'new');
      const reviewing = filtered.filter(j => j.stage === 'reviewing');
      const briefReq = filtered.filter(j => j.stage === 'brief_requested');
      const applied = filtered.filter(j => j.stage === 'applied');
      const rejected = filtered.filter(j => j.stage === 'rejected');

      container.innerHTML = [
        Components.jobList(newJobs, 'New'),
        Components.jobList(reviewing, 'Reviewing'),
        Components.jobList(briefReq, 'Brief Requested'),
        Components.jobList(applied, 'Applied'),
        Components.jobList(rejected, 'Rejected'),
      ].join('<hr class="section-divider">');
    } else {
      container.innerHTML = Components.jobList(filtered, currentStage.replace('_', ' '));
    }
  }

  /** Render pipeline view — all stages as sections. */
  function renderPipeline(container) {
    const stages = ['new', 'reviewing', 'brief_requested', 'applied', 'rejected', 'expired'];
    const sections = stages.map(stage => {
      const jobs = allJobs.filter(j => j.stage === stage);
      return Components.jobList(jobs, stage.replace('_', ' '));
    }).join('');

    container.innerHTML = sections || Components.emptyState('No Jobs', 'Run a search to populate the pipeline.');
  }

  /** Render detail view for a single job. */
  async function renderDetail(container, key) {
    container.innerHTML = '<div class="loading">Loading job details...</div>';
    const job = await API.getJob(key);
    if (job.error) {
      container.innerHTML = Components.emptyState('Job Not Found', job.error);
      return;
    }
    container.innerHTML = Components.jobDetail(job);
  }

  /** Render brief viewer for a single job. */
  async function renderBrief(container, key) {
    container.innerHTML = '<div class="loading">Loading brief...</div>';
    const brief = await API.getBrief(key);
    container.innerHTML = Components.briefViewer(brief, key);
  }

  /** Navigate to detail view. */
  function showDetail(key) {
    previousHash = window.location.hash;
    window.location.hash = `#detail/${encodeURIComponent(key)}`;
  }

  /** Navigate to brief view. */
  function showBrief(key) {
    previousHash = window.location.hash;
    window.location.hash = `#brief/${encodeURIComponent(key)}`;
  }

  /** Go back to previous view. */
  function goBack() {
    if (previousHash) {
      window.location.hash = previousHash;
    } else {
      window.location.hash = '#digest';
    }
  }

  /** Perform a user action on a job (optimistic UI update). */
  async function doAction(key, action) {
    // Optimistic: update local state
    const job = allJobs.find(j => j.key === key);
    if (job) {
      job.stage = action === 'accepted' ? 'applied' : action;
      job.user_action = action;
    }

    // Re-render current view
    route();

    // Send to backend
    const result = await API.postAction(key, action);
    if (result.error) {
      console.error('Action failed:', result.error);
    }

    // Refresh counts
    const state = await API.getState();
    if (!state.error) {
      stateData = state;
      const statsEl = document.getElementById('summary-stats');
      if (statsEl) statsEl.innerHTML = Components.summaryStats(state.counts);
      Components.sidebarCounts(state.counts);
    }
  }

  // Event delegation for data-action attributes (components.js emits these, app.js binds them)
  document.addEventListener('click', function(e) {
    const actionEl = e.target.closest('[data-action]');
    if (!actionEl) return;
    if (actionEl.dataset.action === 'trigger-search') {
      window.dispatchEvent(new CustomEvent('jsa:trigger-search'));
    }
  });

  // Boot on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', init);

  // Expose methods for inline onclick handlers
  return { showDetail, showBrief, goBack, doAction };
})();

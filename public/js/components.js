/**
 * UI renderer functions for JSA V17 Dashboard.
 * All HTML generation uses textContent or manual escaping — never innerHTML with raw data.
 */

/** Score tier class: tier-high (90+), tier-mid (80-89), tier-low (<80). */
function getScoreTier(score) {
  if (score >= 90) return 'tier-high';
  if (score >= 80) return 'tier-mid';
  return 'tier-low';
}

/** Stacked stat: value over label. */
function renderStat(value, label) {
  return `<div class="summary-stat">
    <span class="summary-stat-value">${value}</span>
    <span class="summary-stat-label">${label}</span>
  </div>`;
}

/** Sidebar count badge. */
function renderCountBadge(count) {
  return `<span class="count-badge">${count}</span>`;
}

/** Empty state with optional CTA button (uses data-action, not onclick). */
function renderEmptyState(showCTA = true) {
  return `<div class="empty-state">
    <p>No jobs found. Run a search to get started.</p>
    ${showCTA ? '<button class="btn empty-state-cta" data-action="trigger-search">Run Search</button>' : ''}
  </div>`;
}

const Components = (() => {
  /** Escape HTML special characters to prevent XSS. */
  function esc(str) {
    if (str == null) return '';
    const d = document.createElement('div');
    d.textContent = String(str);
    return d.innerHTML;
  }

  /** Score tier: green (90+), default (80-89), muted (70-79). */
  function scoreTier(score) {
    if (score >= 90) return 'green';
    if (score >= 80) return 'default';
    return 'muted';
  }

  return {
    /**
     * Score badge: <span class="score-badge score-{tier}">score</span>
     */
    scoreBadge(score) {
      const tier = scoreTier(score);
      return `<span class="score-badge score-${tier}">${esc(score)}</span>`;
    },

    /**
     * Job card with score badge, title (linked if job_url), company, location, source, action buttons.
     */
    jobCard(job) {
      const titleContent = job.job_url
        ? `<a href="${esc(job.job_url)}" target="_blank" rel="noopener">${esc(job.title)}</a>`
        : esc(job.title);

      const metaParts = [esc(job.company), esc(job.location), esc(job.source)].filter(Boolean);

      const salary = [];
      if (job.salary_min != null) salary.push(job.salary_min.toLocaleString());
      if (job.salary_max != null) salary.push(job.salary_max.toLocaleString());
      const salaryStr = salary.length
        ? `${job.currency || ''} ${salary.join(' - ')}`.trim()
        : '';

      return `
        <div class="job-card ${getScoreTier(job.score)}" data-key="${esc(job.key)}">
          <div class="job-card-header">
            <div class="job-card-title">${titleContent}</div>
            ${this.scoreBadge(job.score)}
          </div>
          <div class="job-card-meta">
            ${metaParts.map(p => `<span>${p}</span>`).join('')}
          </div>
          ${salaryStr ? `<div class="meta-light">${esc(salaryStr)}</div>` : ''}
          ${job.stage ? `<div style="margin-top:var(--space-2)">${this.statusBadge(job.stage)}</div>` : ''}
          <div class="job-card-actions">
            <button class="btn btn-sm btn-secondary" onclick="App.showDetail('${esc(job.key)}')">Details</button>
            ${job.stage !== 'applied' ? `<button class="btn btn-sm btn-ghost" onclick="App.doAction('${esc(job.key)}', 'accepted')">Mark Applied</button>` : ''}
            ${job.stage !== 'rejected' ? `<button class="btn btn-sm btn-ghost" onclick="App.doAction('${esc(job.key)}', 'rejected')">Reject</button>` : ''}
          </div>
        </div>`;
    },

    /**
     * Summary stats for the top bar.
     */
    summaryStats(counts) {
      if (!counts) return '';
      const items = [
        { label: 'Total', value: counts.total_jobs },
        { label: 'New', value: counts.new },
        { label: 'Reviewing', value: counts.reviewing },
        { label: 'Applied', value: counts.applied },
      ];
      return items
        .map(i => `<div class="stat-item"><span class="stat-value">${esc(i.value)}</span> ${esc(i.label)}</div>`)
        .join('');
    },

    /**
     * Job list section with heading + cards.
     */
    jobList(jobs, heading) {
      if (!jobs || jobs.length === 0) return '';
      const cards = jobs.map(j => this.jobCard(j)).join('');
      return `
        <div class="job-list-heading">${esc(heading)} (${jobs.length})</div>
        ${cards}`;
    },

    /**
     * Full detail view for a single job.
     */
    jobDetail(job) {
      const metaParts = [esc(job.company), esc(job.location), esc(job.source)].filter(Boolean);

      // Score breakdown table if available
      let breakdownHtml = '';
      const sb = job.score_breakdown;
      if (sb) {
        const rows = [];
        if (sb.required_skills != null) rows.push(['Required Skills', `/40`, sb.required_skills]);
        if (sb.preferred_skills != null) rows.push(['Preferred Skills', `/20`, sb.preferred_skills]);
        if (sb.experience_fit != null) rows.push(['Experience Fit', `/15`, sb.experience_fit]);
        if (sb.industry_match != null) rows.push(['Industry Match', `/15`, sb.industry_match]);
        if (sb.location != null) rows.push(['Location', `/10`, sb.location]);
        if (sb.salary_penalty && sb.salary_penalty.applied) {
          rows.push(['Salary Penalty', '', sb.salary_penalty.points]);
        }

        if (rows.length) {
          breakdownHtml = `
            <div class="detail-section">
              <h3>Score Breakdown</h3>
              <table class="data-table">
                <thead><tr><th>Factor</th><th>Max</th><th>Score</th></tr></thead>
                <tbody>
                  ${rows.map(r => `<tr><td>${esc(r[0])}</td><td>${esc(r[1])}</td><td>${esc(r[2])}</td></tr>`).join('')}
                  <tr><td><strong>Total</strong></td><td></td><td><strong>${esc(job.score)}</strong></td></tr>
                </tbody>
              </table>
            </div>`;
        }
      }

      // Requirements met / gaps
      let requirementsHtml = '';
      if (job.requirements_met && job.requirements_met.length) {
        requirementsHtml += `
          <div class="detail-section">
            <h3>Requirements Met</h3>
            ${job.requirements_met.map(r => `<span class="tag">${esc(r)}</span>`).join('')}
          </div>`;
      }
      if (job.gaps && job.gaps.length) {
        requirementsHtml += `
          <div class="detail-section">
            <h3>Gaps</h3>
            ${job.gaps.map(g => `<span class="tag">${esc(g)}</span>`).join('')}
          </div>`;
      }

      // Notes
      let notesHtml = '';
      if (job.notes) {
        notesHtml = `
          <div class="detail-section">
            <h3>Notes</h3>
            <p>${esc(job.notes)}</p>
          </div>`;
      }

      // Benefits
      let benefitsHtml = '';
      if (job.benefits && job.benefits.length) {
        benefitsHtml = `
          <div class="detail-section">
            <h3>Benefits</h3>
            ${job.benefits.map(b => `<span class="tag">${esc(b)}</span>`).join('')}
          </div>`;
      }

      return `
        <div class="detail-view">
          <a class="detail-back" onclick="App.goBack()">&larr; Back</a>
          <div class="detail-header">
            <div style="display:flex;align-items:center;gap:var(--space-4);margin-bottom:var(--space-2)">
              <div class="detail-title">${esc(job.title)}</div>
              ${this.scoreBadge(job.score)}
            </div>
            <div class="detail-meta">
              ${metaParts.map(p => `<span>${p}</span>`).join('')}
            </div>
            ${job.job_url ? `<a href="${esc(job.job_url)}" target="_blank" rel="noopener">View Original Listing</a>` : ''}
          </div>
          <div class="detail-actions">
            <button class="btn btn-primary" onclick="App.doAction('${esc(job._key)}', 'accepted')">Mark Applied</button>
            <button class="btn btn-secondary" onclick="App.doAction('${esc(job._key)}', 'brief_requested')">Request Brief</button>
            <button class="btn btn-ghost" onclick="App.doAction('${esc(job._key)}', 'rejected')">Reject</button>
            <button class="btn btn-secondary" onclick="App.showBrief('${esc(job._key)}')">View Brief</button>
          </div>
          ${breakdownHtml}
          ${requirementsHtml}
          ${benefitsHtml}
          ${notesHtml}
        </div>`;
    },

    /**
     * Brief viewer wrapping rendered HTML in design system styling.
     */
    briefViewer(briefData, key) {
      if (!briefData || briefData.error) {
        return `
          <div class="brief-viewer">
            <a class="detail-back" onclick="App.goBack()">&larr; Back</a>
            <div class="empty-state">
              <div class="empty-state-title">No Brief Available</div>
              <div class="empty-state-message">${esc(briefData?.error || 'Brief not found for this job.')}</div>
            </div>
          </div>`;
      }
      return `
        <div class="brief-viewer">
          <a class="detail-back" onclick="App.goBack()">&larr; Back</a>
          <div class="brief-content">${briefData.html}</div>
        </div>`;
    },

    /**
     * Empty state message.
     */
    emptyState(title, message) {
      return `
        <div class="empty-state">
          <div class="empty-state-title">${esc(title)}</div>
          <div class="empty-state-message">${esc(message)}</div>
        </div>`;
    },

    /**
     * Update sidebar count badges.
     */
    sidebarCounts(counts) {
      if (!counts) return;
      const map = {
        'count-all': counts.total_jobs,
        'count-new': counts.new,
        'count-reviewing': counts.reviewing,
        'count-brief': counts.brief_requested,
        'count-applied': counts.applied,
        'count-rejected': counts.rejected,
      };
      for (const [id, val] of Object.entries(map)) {
        const el = document.getElementById(id);
        if (el) el.textContent = val != null ? val : '';
      }
    },

    /**
     * Status badge colored by pipeline stage.
     */
    statusBadge(stage) {
      const labels = {
        new: 'New',
        reviewing: 'Reviewing',
        brief_requested: 'Brief Requested',
        applied: 'Applied',
        rejected: 'Rejected',
        expired: 'Expired',
      };
      const label = labels[stage] || stage;
      return `<span class="status-badge status-${esc(stage)}">${esc(label)}</span>`;
    },

    /**
     * Render role type checkboxes for the run panel.
     */
    runPanel(roleTypes) {
      if (!roleTypes || roleTypes.length === 0) {
        return '<p class="meta">No role types available.</p>';
      }
      return roleTypes
        .map(rt => `<label><input type="checkbox" value="${esc(rt)}" checked> ${esc(rt)}</label>`)
        .join('');
    },
  };
})();

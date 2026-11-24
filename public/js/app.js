'use strict';

const select = (id) => document.getElementById(id);

function append(parent, tag, value, className) {
  const element = document.createElement(tag);
  element.textContent = value;
  if (className) element.className = className;
  parent.append(element);
  return element;
}

function label(record) {
  if (record.placement === 'optional') return 'Optional follow-up';
  if (record.placement === 'carry_over_expired') return 'Previously shown';
  return record.disposition === 'apply_now' ? 'Apply now' : 'Apply if time';
}

function dateLabel(value) {
  return new Intl.DateTimeFormat('en', {dateStyle: 'medium', timeZone: 'UTC'})
    .format(new Date(value + 'T00:00:00Z'));
}

function addRole(list, record, synthetic) {
  const item = document.createElement('li');
  item.className = 'role';
  const top = document.createElement('div');
  top.className = 'role-heading';
  item.append(top);
  append(top, 'h3', record.exact_title);
  append(top, 'span', label(record), record.disposition === 'apply_now' ? 'tier tier-now' : 'tier');
  const meta = [record.company, record.location].filter(Boolean).join(' / ');
  append(item, 'p', meta, 'meta');
  append(item, 'p', record.central_work, 'work');

  const details = document.createElement('details');
  item.append(details);
  const summary = append(details, 'summary', 'Review evidence');
  summary.setAttribute('aria-label', 'Review evidence for ' + record.exact_title);
  append(details, 'p', record.fit_reason);
  append(details, 'p', record.practical_notes);
  if (record.optional_reason) append(details, 'p', record.optional_reason);
  if (record.recommended_effort) append(details, 'p', record.recommended_effort);

  const source = record.source_kind === 'first_party' ? 'Employer listing' : 'Provisional job board copy';
  append(details, 'p', source + ', checked ' + dateLabel(record.checked_at), 'meta');
  const firstDate = record.recency.earliest_publication;
  append(details, 'p', firstDate ? 'Earliest publication found ' + dateLabel(firstDate)
    : 'Original posting date unknown', 'meta');

  if (!synthetic && /^https?:\/\//i.test(record.url)) {
    const link = append(details, 'a', 'Open job listing');
    link.href = record.url;
    link.rel = 'noreferrer';
    link.setAttribute('aria-label', 'Open job listing for ' + record.exact_title);
  }
  list.append(item);
}

function show(board) {
  select('run-date').dateTime = board.run_date;
  select('run-date').textContent = dateLabel(board.run_date);
  if (board.synthetic) {
    select('board-description').textContent = 'Example search using fictional roles and a fictional profile.';
  }
  for (const [key, name] of [['main', 'matches'], ['appendix', 'appendix']]) {
    select(key + '-count').textContent = board[key].length;
    for (const record of board[key]) addRole(select(name), record, board.synthetic);
  }

  select('no-matches').hidden = board.main.length > 0;
  select('appendix-section').hidden = board.appendix.length === 0;
  const labels = [
    ['Candidates reviewed or pending', 'candidates'], ['Pending or incomplete', 'pending'],
    ['Skipped', 'skipped'], ['Skipped past the recency window', 'stale'],
    ['Source snapshots', 'sources'], ['Sources at their limit', 'caps_hit'], ['Sources blocked', 'blocked_sources'],
  ];
  for (const [name, key] of labels) {
    const group = document.createElement('div');
    append(group, 'dt', name);
    append(group, 'dd', board.coverage[key]);
    select('coverage').append(group);
  }
  select('board').hidden = false;
  select('status').textContent = '';
  select('status').hidden = true;
}

fetch('/board.json', {cache: 'no-store'})
  .then((response) => {
    if (!response.ok) throw new Error('Could not load the board.');
    return response.json();
  })
  .then(show)
  .catch(() => {
    select('status').textContent = 'The shortlist could not load. Restart the local preview and try again.';
  });

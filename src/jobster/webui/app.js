const state = {
  status: null,
  jobs: [],
  applications: [],
  activity: [],
  selectedJob: null,
  filter: "all",
  query: "",
};

const $ = (id) => document.getElementById(id);

const labels = {
  aggressive_pursuit: "Aggressive pursuit",
  high_priority: "High priority",
  apply: "Apply",
  watch: "Watch",
  low_priority: "Low priority",
  ignore: "Ignore",
};

const pageMeta = {
  overview: ["CAREER COMMAND CENTER", "Overview"],
  opportunities: ["DISCOVERY + FIT", "Opportunities"],
  applications: ["EXECUTION CONTROL", "Applications"],
  activity: ["AUDIT TRAIL", "Activity"],
};

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function decisionTone(decision) {
  if (decision === "apply" || decision === "high_priority" || decision === "aggressive_pursuit") return "apply";
  if (decision === "ignore" || decision === "low_priority") return "ignore";
  return "watch";
}

function salaryText(job) {
  if (!job.salary_min_monthly && !job.salary_max_monthly) return null;
  const cur = job.currency || "USD";
  const min = job.salary_min_monthly ? Math.round(job.salary_min_monthly).toLocaleString() : null;
  const max = job.salary_max_monthly ? Math.round(job.salary_max_monthly).toLocaleString() : null;
  if (min && max) return `${cur} ${min}–${max}/mo`;
  return `${cur} ${min || max}/mo`;
}

function showToast(message) {
  const toast = $("toast");
  toast.textContent = message;
  toast.classList.add("is-visible");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("is-visible"), 2800);
}

async function api(path, options) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {}
    throw new Error(message);
  }
  return response.json();
}

function switchView(route) {
  document.querySelectorAll(".view").forEach((el) => el.classList.remove("is-visible"));
  document.querySelectorAll(".nav-item").forEach((el) => el.classList.remove("is-active"));
  document.querySelector(`#view-${route}`)?.classList.add("is-visible");
  document.querySelector(`.nav-item[data-route="${route}"]`)?.classList.add("is-active");
  const [eyebrow, title] = pageMeta[route] || pageMeta.overview;
  $("page-eyebrow").textContent = eyebrow;
  $("page-title").textContent = title;
}

function renderStatus() {
  if (!state.status) return;
  const { profile, metrics, quota, submission, cycle } = state.status;

  $("profile-name").textContent = profile.display_name || "Career profile";
  $("profile-headline").textContent = profile.headline || (profile.target_titles || []).join(" · ");
  $("metric-jobs").textContent = metrics.jobs ?? 0;
  $("metric-high").textContent = metrics.high_priority ?? 0;
  $("metric-applications").textContent = metrics.applications ?? 0;
  $("metric-submitted").textContent = metrics.submitted ?? 0;

  const quotaText = `${quota.used}/${quota.usable_limit} · today ${quota.used_today}/${quota.daily_limit}`;
  $("quota-mini").textContent = `Search budget · ${quotaText}`;
  $("quota-status").textContent = quotaText;

  $("submission-status").textContent = submission.auto_submit ? "Automatic" : "Supervised";
  $("window-status").textContent = submission.window_open ? "Open" : "Paused";
  $("sidebar-mode").textContent = submission.auto_submit ? "Automatic mode" : "Supervised mode";
  $("application-mode").textContent = submission.auto_submit ? "Automatic" : "Supervised";

  if (cycle.running) {
    $("cycle-status").textContent = "Running";
    $("run-cycle-btn").textContent = "Cycle running…";
    $("run-cycle-btn").disabled = true;
  } else {
    $("cycle-status").textContent = cycle.last_error ? "Needs attention" : "Idle";
    $("run-cycle-btn").textContent = "Run search cycle";
    $("run-cycle-btn").disabled = false;
  }
}

function jobCard(job, compact = false) {
  const salary = salaryText(job);
  const score = Number.isFinite(job.interest_score) ? job.interest_score : "—";
  const decision = job.decision || "pending";
  const meta = [
    job.location || (job.remote ? "Remote" : null),
    salary,
    job.source,
    job.application_state ? `application: ${job.application_state}` : null,
  ].filter(Boolean);

  return `
    <article class="job-card" data-job-id="${esc(job.id)}">
      <div class="job-card-main">
        <h4 class="job-title">${esc(job.title)}</h4>
        <div class="job-company">${esc(job.company)}</div>
        <div class="job-meta">${meta.map((m) => `<span>${esc(m)}</span>`).join("")}</div>
      </div>
      <div class="job-side">
        <div class="score">${esc(score)}</div>
        <div class="decision-badge" data-tone="${decisionTone(decision)}">${esc(labels[decision] || decision)}</div>
      </div>
    </article>
  `;
}

function renderJobs() {
  const filtered = state.jobs.filter((job) => {
    const decisionOk = state.filter === "all" || job.decision === state.filter;
    const haystack = `${job.title} ${job.company} ${job.source} ${job.location || ""}`.toLowerCase();
    const queryOk = !state.query || haystack.includes(state.query.toLowerCase());
    return decisionOk && queryOk;
  });

  $("jobs-list").innerHTML = filtered.length
    ? filtered.map((job) => jobCard(job)).join("")
    : '<div class="empty-state">No opportunities match this view.</div>';

  const priority = state.jobs
    .filter((job) => ["aggressive_pursuit", "high_priority", "apply"].includes(job.decision))
    .slice(0, 6);
  $("priority-list").innerHTML = priority.length
    ? priority.map((job) => jobCard(job, true)).join("")
    : '<div class="empty-state">No high-priority opportunities yet.</div>';

  document.querySelectorAll(".job-card").forEach((card) => {
    card.addEventListener("click", () => openJob(card.dataset.jobId));
  });
}

function renderApplications() {
  $("applications-list").innerHTML = state.applications.length
    ? state.applications.map((item) => `
      <article class="application-row">
        <div>
          <strong>${esc(item.title)}</strong>
          <div class="small">${esc(item.company)} · ${esc(item.ats || "unknown ATS")}</div>
        </div>
        <div class="state-pill">${esc(item.state)}</div>
        <div class="small">${esc((item.plan?.reasons || [])[0] || "No blockers recorded")}</div>
      </article>
    `).join("")
    : '<div class="empty-state">No application plans yet.</div>';
}

function renderActivity() {
  $("activity-list").innerHTML = state.activity.length
    ? state.activity.map((event) => `
      <div class="activity-row">
        <div class="activity-time">${esc(event.created_at)}</div>
        <div class="activity-type">${esc(event.event_type.replaceAll("_", " "))}</div>
        <div class="activity-job">${esc(event.job_id || "system")}</div>
      </div>
    `).join("")
    : '<div class="empty-state">No activity recorded yet.</div>';
}

async function openJob(jobId) {
  try {
    const bundle = await api(`/api/jobs/${encodeURIComponent(jobId)}`);
    state.selectedJob = bundle;
    const job = bundle.job;
    const evaluation = bundle.evaluation || {};
    $("drawer-source").textContent = (job.source || "opportunity").toUpperCase();
    $("drawer-title").textContent = job.title;
    $("drawer-company").textContent = [job.company, job.location].filter(Boolean).join(" · ");
    $("drawer-score").textContent = Number.isFinite(evaluation.interest_score) ? evaluation.interest_score : "—";
    $("drawer-decision").textContent = labels[evaluation.pursuit_decision] || evaluation.pursuit_decision || "Pending";
    $("drawer-decision").dataset.tone = decisionTone(evaluation.pursuit_decision);
    $("drawer-summary").textContent = evaluation.summary || evaluation.role_interpretation || "No assessment available yet.";
    $("drawer-next").textContent = evaluation.next_action || "Evaluate this opportunity first.";

    const matches = evaluation.strong_matches || [];
    $("drawer-matches").innerHTML = matches.length
      ? matches.map((item) => `<span class="tag">${esc(item)}</span>`).join("")
      : '<span class="tag">No confirmed matches yet</span>';

    const gaps = [...(evaluation.learnable_gaps || []), ...(evaluation.unknowns || []), ...(evaluation.hard_blockers || [])];
    $("drawer-gaps").innerHTML = gaps.length
      ? gaps.map((item) => `<span class="tag">${esc(item)}</span>`).join("")
      : '<span class="tag">No material gaps recorded</span>';

    $("open-job-btn").disabled = !job.url;
    $("prepare-job-btn").disabled = !bundle.evaluation;
    $("drawer-note").textContent = bundle.application
      ? `Application state: ${bundle.application.state}. ${(bundle.application.reasons || []).join(" ")}`
      : "No application inspection has been saved for this role yet.";

    $("drawer-backdrop").classList.add("is-visible");
    $("job-drawer").classList.add("is-visible");
    $("job-drawer").setAttribute("aria-hidden", "false");
  } catch (error) {
    showToast(error.message);
  }
}

function closeDrawer() {
  $("drawer-backdrop").classList.remove("is-visible");
  $("job-drawer").classList.remove("is-visible");
  $("job-drawer").setAttribute("aria-hidden", "true");
}

async function loadAll() {
  try {
    const [status, jobs, applications, activity] = await Promise.all([
      api("/api/status"),
      api("/api/jobs?limit=250"),
      api("/api/applications?limit=150"),
      api("/api/activity?limit=120"),
    ]);
    state.status = status;
    state.jobs = jobs;
    state.applications = applications;
    state.activity = activity;
    renderStatus();
    renderJobs();
    renderApplications();
    renderActivity();
  } catch (error) {
    showToast(error.message);
  }
}

async function runCycle() {
  try {
    $("run-cycle-btn").disabled = true;
    $("run-cycle-btn").textContent = "Starting…";
    const result = await api("/api/cycles", { method: "POST" });
    if (!result.started) {
      showToast("A search cycle is already running.");
    } else {
      showToast("Search cycle started.");
    }
    await pollCycle();
  } catch (error) {
    $("run-cycle-btn").disabled = false;
    $("run-cycle-btn").textContent = "Run search cycle";
    showToast(error.message);
  }
}

async function pollCycle() {
  const cycle = await api("/api/cycles/current");
  if (state.status) state.status.cycle = cycle;
  renderStatus();
  if (cycle.running) {
    setTimeout(pollCycle, 1800);
    return;
  }
  if (cycle.last_error) {
    showToast(`Cycle failed: ${cycle.last_error}`);
  } else if (cycle.last_summary) {
    showToast(`Cycle complete · ${cycle.last_summary.discovered || 0} discovered`);
  }
  await loadAll();
}

async function prepareSelectedJob() {
  const jobId = state.selectedJob?.job?.id;
  if (!jobId) return;
  try {
    $("prepare-job-btn").disabled = true;
    $("prepare-job-btn").textContent = "Preparing…";
    const result = await api(`/api/jobs/${encodeURIComponent(jobId)}/prepare`, { method: "POST" });
    $("drawer-note").textContent = `Application packet prepared: ${result.resume_markdown || "artifact created"}`;
    showToast("Application packet prepared.");
    await loadAll();
  } catch (error) {
    showToast(error.message);
  } finally {
    $("prepare-job-btn").disabled = false;
    $("prepare-job-btn").textContent = "Prepare application";
  }
}

document.addEventListener("click", (event) => {
  const nav = event.target.closest("[data-route]");
  if (nav) switchView(nav.dataset.route);

  const jump = event.target.closest("[data-route-jump]");
  if (jump) switchView(jump.dataset.routeJump);

  const chip = event.target.closest("[data-filter]");
  if (chip) {
    state.filter = chip.dataset.filter;
    document.querySelectorAll(".chip").forEach((el) => el.classList.remove("is-active"));
    chip.classList.add("is-active");
    renderJobs();
  }
});

$("job-search").addEventListener("input", (event) => {
  state.query = event.target.value;
  renderJobs();
});
$("refresh-btn").addEventListener("click", loadAll);
$("run-cycle-btn").addEventListener("click", runCycle);
$("drawer-close").addEventListener("click", closeDrawer);
$("drawer-backdrop").addEventListener("click", closeDrawer);
$("open-job-btn").addEventListener("click", () => {
  const url = state.selectedJob?.job?.url;
  if (url) window.open(url, "_blank", "noopener,noreferrer");
});
$("prepare-job-btn").addEventListener("click", prepareSelectedJob);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeDrawer();
});

loadAll();
setInterval(async () => {
  if (state.status?.cycle?.running) {
    await pollCycle();
  }
}, 5000);

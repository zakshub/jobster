const state = {
  status: null,
  jobs: [],
  applications: [],
  activity: [],
  selectedJob: null,
  filter: "all",
  sourceFilter: "all",
  query: "",
  terminalSequence: 0,
  terminalPolling: false,
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

const stageLabels = {
  idle: "Idle",
  starting: "Starting",
  discovering: "Searching job sites",
  filtering: "Removing unrelated jobs",
  evaluating: "Checking job fit",
  preparing: "Checking applications",
  complete: "Done",
  failed: "Needs attention",
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
  if (["apply", "high_priority", "aggressive_pursuit"].includes(decision)) return "apply";
  if (["ignore", "low_priority"].includes(decision)) return "ignore";
  return "watch";
}

function verificationLabel(stateValue) {
  return {
    live: "Job is live",
    protected: "Could not check automatically",
    expired: "Job closed",
    unreachable: "Could not open job page",
    needs_review: "Needs a quick check",
    unverifiable: "No job link available",
  }[stateValue] || "Not verified";
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
  showToast.timer = setTimeout(() => toast.classList.remove("is-visible"), 3000);
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

function animateNumber(element, next) {
  const target = Number(next || 0);
  const current = Number(element.dataset.value || element.textContent || 0);
  element.dataset.value = String(target);
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || current === target) {
    element.textContent = target.toLocaleString();
    return;
  }
  const start = performance.now();
  const duration = 420;
  function frame(now) {
    const p = Math.min(1, (now - start) / duration);
    const eased = 1 - Math.pow(1 - p, 3);
    element.textContent = Math.round(current + (target - current) * eased).toLocaleString();
    if (p < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

function renderStage(cycle) {
  const stage = cycle?.stage || "idle";
  $("stage-pill").textContent = stageLabels[stage] || stage;
  $("stage-pill").classList.toggle("is-running", Boolean(cycle?.running));
  $("terminal-stage").textContent = stage;

  let width = 0;
  if (stage === "starting") width = 6;
  if (stage === "discovering") width = 28;
  if (stage === "filtering") width = 45;
  if (stage === "evaluating") width = 68;
  if (stage === "preparing") width = 90;
  if (stage === "complete" || stage === "failed") width = 100;
  $("terminal-progress-bar").style.width = `${width}%`;
}

function renderStatus() {
  if (!state.status) return;
  const { profile, metrics, quota, submission, cycle, intake, source_counts } = state.status;

  $("profile-name").textContent = profile.display_name || "Career profile";
  $("profile-headline").textContent = profile.headline || (profile.target_titles || []).join(" · ");

  animateNumber($("metric-jobs"), metrics.jobs);
  animateNumber($("metric-high"), metrics.high_priority);
  animateNumber($("metric-hidden"), metrics.hidden_irrelevant);
  animateNumber($("metric-applications"), metrics.applications);
  animateNumber($("metric-submitted"), metrics.submitted);

  const quotaText = `${quota.used}/${quota.usable_limit} · today ${quota.used_today}/${quota.daily_limit}`;
  $("quota-mini").textContent = `Search budget · ${quotaText}`;
  $("quota-status").textContent = quotaText;

  $("submission-status").textContent = submission.auto_submit ? "Automatic" : "Supervised";
  $("window-status").textContent = submission.window_open ? "Open" : "Paused";
  $("sidebar-mode").textContent = submission.auto_submit ? "Automatic mode" : "Supervised mode";
  $("application-mode").textContent = submission.auto_submit ? "Automatic" : "Supervised";
  $("intake-status").textContent = intake?.enabled ? `On` : "Off";
  $("intake-copy").textContent = intake?.enabled
    ? `Jobster hides unrelated jobs before spending time reviewing them. It also limits how many jobs one website can add, so one source cannot flood your list.`
    : "Relevant job filtering is turned off.";

  if (cycle.running) {
    $("cycle-status").textContent = stageLabels[cycle.stage] || "Running";
    $("run-cycle-btn").innerHTML = '<span class="button-dot"></span>Research running…';
    $("run-cycle-btn").disabled = true;
  } else {
    $("cycle-status").textContent = cycle.last_error ? "Needs attention" : (stageLabels[cycle.stage] || "Idle");
    $("run-cycle-btn").innerHTML = '<span class="button-dot"></span>Research opportunities';
    $("run-cycle-btn").disabled = false;
  }

  renderStage(cycle);
  renderSourceMix(source_counts || {});
}

function renderSourceMix(sourceCounts) {
  const entries = Object.entries(sourceCounts).sort((a, b) => b[1] - a[1]);
  $("source-mix").innerHTML = entries.length
    ? entries.map(([source, count]) => `<span class="source-pill"><span>${esc(source)}</span><strong>${count}</strong></span>`).join("")
    : '<div class="empty-state">No relevant source data yet.</div>';
}

function renderSourceOptions() {
  const select = $("source-filter");
  const current = state.sourceFilter;
  const sources = [...new Set(state.jobs.map((job) => job.source).filter(Boolean))].sort();
  select.innerHTML = '<option value="all">All sources</option>' +
    sources.map((source) => `<option value="${esc(source)}">${esc(source)}</option>`).join("");
  select.value = sources.includes(current) ? current : "all";
  state.sourceFilter = select.value;
}

function jobCard(job, index = 0) {
  const salary = salaryText(job);
  const score = Number.isFinite(job.interest_score) ? job.interest_score : "—";
  const decision = job.decision || "pending";
  const meta = [
    job.location || (job.remote ? "Remote" : null),
    salary,
    job.source,
    job.application_state ? `application: ${job.application_state}` : null,
  ].filter(Boolean);

  const verification = job.verification_state
    ? `<span class="verification-badge" data-state="${esc(job.verification_state)}">${esc(verificationLabel(job.verification_state))}</span>`
    : "";

  return `
    <article class="job-card" data-job-id="${esc(job.id)}" style="--i:${Math.min(index, 12)}">
      <div class="job-card-main">
        <h4 class="job-title">${esc(job.title)}</h4>
        <div class="job-company">${esc(job.company)}</div>
        <div class="job-meta">
          ${meta.map((m, i) => `<span class="${i === 2 ? "source-badge" : ""}">${esc(m)}</span>`).join("")}
          ${verification}
        </div>
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
    const sourceOk = state.sourceFilter === "all" || job.source === state.sourceFilter;
    const haystack = `${job.title} ${job.company} ${job.source} ${job.location || ""}`.toLowerCase();
    const queryOk = !state.query || haystack.includes(state.query.toLowerCase());
    return decisionOk && sourceOk && queryOk;
  });

  $("jobs-list").innerHTML = filtered.length
    ? filtered.map((job, index) => jobCard(job, index)).join("")
    : '<div class="empty-state">No relevant opportunities match this view.</div>';

  const priority = state.jobs
    .filter((job) => ["aggressive_pursuit", "high_priority", "apply"].includes(job.decision))
    .slice(0, 6);
  $("priority-list").innerHTML = priority.length
    ? priority.map((job, index) => jobCard(job, index)).join("")
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

function renderVerification(verification) {
  const stateValue = verification?.state || "unknown";
  $("drawer-verification").dataset.state = stateValue;
  $("drawer-verification").textContent = verificationLabel(stateValue);
  $("verification-detail").textContent = verification?.detail || "Check that the job is still open before preparing the application.";
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
    $("drawer-summary").textContent = evaluation.summary || evaluation.role_interpretation || "Jobster has not reviewed this job yet.";
    $("drawer-next").textContent = evaluation.next_action || "Review this job first.";

    const matches = evaluation.strong_matches || [];
    $("drawer-matches").innerHTML = matches.length
      ? matches.map((item) => `<span class="tag">${esc(item)}</span>`).join("")
      : '<span class="tag">No confirmed matches yet</span>';

    const gaps = [...(evaluation.learnable_gaps || []), ...(evaluation.unknowns || []), ...(evaluation.hard_blockers || [])];
    $("drawer-gaps").innerHTML = gaps.length
      ? gaps.map((item) => `<span class="tag">${esc(item)}</span>`).join("")
      : '<span class="tag">No material gaps recorded</span>';

    renderVerification(bundle.verification);
    $("open-job-btn").disabled = !job.url;
    $("verify-job-btn").disabled = !job.url;
    $("prepare-job-btn").disabled = !bundle.evaluation;
    $("drawer-note").textContent = bundle.application
      ? `Application state: ${bundle.application.state}. ${(bundle.application.reasons || []).join(" ")}`
      : "This application has not been checked yet.";

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

async function verifySelectedJob() {
  const jobId = state.selectedJob?.job?.id;
  if (!jobId) return;
  try {
    $("verify-job-btn").disabled = true;
    $("verify-job-btn").textContent = "Checking…";
    const result = await api(`/api/jobs/${encodeURIComponent(jobId)}/verify`, { method: "POST" });
    renderVerification(result);
    state.selectedJob.verification = result;
    showToast(`Job check: ${verificationLabel(result.state)}`);
    await loadAll();
  } catch (error) {
    showToast(error.message);
  } finally {
    $("verify-job-btn").disabled = false;
    $("verify-job-btn").textContent = "Check job";
  }
}

function terminalShow() {
  $("terminal-window").classList.remove("is-hidden");
  $("terminal-reopen").classList.remove("is-visible");
  localStorage.setItem("jobster-terminal-hidden", "0");
}

function terminalHide() {
  $("terminal-window").classList.add("is-hidden");
  $("terminal-reopen").classList.add("is-visible");
  localStorage.setItem("jobster-terminal-hidden", "1");
}

function appendTerminalEvent(item) {
  const body = $("terminal-body");
  if (body.querySelector(".muted") && state.terminalSequence === 0) body.innerHTML = "";
  const line = document.createElement("div");
  const tone = item.level === "error" ? "error" : (item.event === "cycle_completed" ? "success" : "");
  line.className = `terminal-line ${tone}`;
  const stamp = new Date(item.timestamp);
  const time = Number.isNaN(stamp.getTime()) ? "--:--:--" : stamp.toLocaleTimeString([], { hour12: false });
  line.innerHTML = `
    <span class="time">${esc(time)}</span>
    <span class="event">${esc(event)}</span>
    <span class="message">${esc(item.message)}</span>
  `;
  body.appendChild(line);
  while (body.children.length > 180) body.removeChild(body.firstChild);
  body.scrollTop = body.scrollHeight;

  if (item.event === "evaluation_started" && item.payload?.total) {
    const pct = 45 + Math.round((item.payload.index / item.payload.total) * 38);
    $("terminal-progress-bar").style.width = `${Math.min(pct, 84)}%`;
  }
}

async function pollTerminal() {
  if (state.terminalPolling) return;
  state.terminalPolling = true;
  try {
    const payload = await api(`/api/terminal?after=${state.terminalSequence}`);
    for (const event of payload.events || []) {
      appendTerminalEvent(event);
      state.terminalSequence = Math.max(state.terminalSequence, event.sequence || 0);
    }
    if (state.status) state.status.cycle = payload.cycle;
    renderStage(payload.cycle);
  } catch {
    // Keep UI usable when the local server is restarting.
  } finally {
    state.terminalPolling = false;
  }
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
    renderSourceOptions();
    renderJobs();
    renderApplications();
    renderActivity();
  } catch (error) {
    showToast(error.message);
  }
}

async function runCycle() {
  try {
    terminalShow();
    $("run-cycle-btn").disabled = true;
    $("run-cycle-btn").innerHTML = '<span class="button-dot"></span>Starting research…';
    const result = await api("/api/cycles", { method: "POST" });
    if (!result.started) {
      showToast("A research cycle is already running.");
    } else {
      showToast("Job search started.");
    }
    await pollCycle();
  } catch (error) {
    $("run-cycle-btn").disabled = false;
    $("run-cycle-btn").innerHTML = '<span class="button-dot"></span>Research opportunities';
    showToast(error.message);
  }
}

async function pollCycle() {
  const cycle = await api("/api/cycles/current");
  if (state.status) state.status.cycle = cycle;
  renderStatus();
  await pollTerminal();
  if (cycle.running) {
    setTimeout(pollCycle, 1400);
    return;
  }
  if (cycle.last_error) {
    showToast(`Job search stopped: ${cycle.last_error}`);
  } else if (cycle.last_summary) {
    showToast(`Job search finished · ${cycle.last_summary.discovered || 0} suitable jobs · ${cycle.last_summary.rejected_irrelevant || 0} unrelated jobs hidden`);
  }
  await loadAll();
}

async function prepareSelectedJob() {
  const jobId = state.selectedJob?.job?.id;
  if (!jobId) return;
  try {
    $("prepare-job-btn").disabled = true;
    $("prepare-job-btn").textContent = "Checking job + preparing…";
    const result = await api(`/api/jobs/${encodeURIComponent(jobId)}/prepare`, { method: "POST" });
    renderVerification(result.verification);
    $("drawer-note").textContent = `Application packet prepared: ${result.resume_markdown || "artifact created"}`;
    showToast("Job checked and application prepared.");
    await loadAll();
  } catch (error) {
    showToast(error.message);
  } finally {
    $("prepare-job-btn").disabled = false;
    $("prepare-job-btn").textContent = "Prepare application";
  }
}

function setupTerminalWindow() {
  const terminal = $("terminal-window");
  const handle = $("terminal-handle");
  const minimize = $("terminal-minimize");

  if (localStorage.getItem("jobster-terminal-hidden") === "1") terminalHide();

  const saved = JSON.parse(localStorage.getItem("jobster-terminal-rect") || "null");
  if (saved && window.innerWidth > 760) {
    terminal.style.left = `${Math.max(8, Math.min(saved.left, window.innerWidth - 360))}px`;
    terminal.style.top = `${Math.max(8, Math.min(saved.top, window.innerHeight - 120))}px`;
    terminal.style.right = "auto";
    terminal.style.bottom = "auto";
    if (saved.width) terminal.style.width = `${saved.width}px`;
    if (saved.height) terminal.style.height = `${saved.height}px`;
  }

  let drag = null;
  handle.addEventListener("pointerdown", (event) => {
    if (event.target.closest("button") || window.innerWidth <= 760) return;
    const rect = terminal.getBoundingClientRect();
    drag = { x: event.clientX, y: event.clientY, left: rect.left, top: rect.top };
    terminal.style.left = `${rect.left}px`;
    terminal.style.top = `${rect.top}px`;
    terminal.style.right = "auto";
    terminal.style.bottom = "auto";
    handle.setPointerCapture(event.pointerId);
  });

  handle.addEventListener("pointermove", (event) => {
    if (!drag) return;
    const rect = terminal.getBoundingClientRect();
    const maxLeft = Math.max(8, window.innerWidth - rect.width - 8);
    const maxTop = Math.max(8, window.innerHeight - rect.height - 8);
    terminal.style.left = `${Math.max(8, Math.min(maxLeft, drag.left + event.clientX - drag.x))}px`;
    terminal.style.top = `${Math.max(8, Math.min(maxTop, drag.top + event.clientY - drag.y))}px`;
  });

  function saveTerminalRect() {
    drag = null;
    const rect = terminal.getBoundingClientRect();
    localStorage.setItem("jobster-terminal-rect", JSON.stringify({
      left: rect.left,
      top: rect.top,
      width: rect.width,
      height: rect.height,
    }));
  }

  handle.addEventListener("pointerup", saveTerminalRect);
  window.addEventListener("mouseup", () => {
    if (!terminal.classList.contains("is-minimized") && !terminal.classList.contains("is-hidden")) {
      const rect = terminal.getBoundingClientRect();
      localStorage.setItem("jobster-terminal-rect", JSON.stringify({
        left: rect.left,
        top: rect.top,
        width: rect.width,
        height: rect.height,
      }));
    }
  });

  minimize.addEventListener("click", () => {
    terminal.classList.toggle("is-minimized");
    minimize.textContent = terminal.classList.contains("is-minimized") ? "□" : "—";
  });
  $("terminal-close").addEventListener("click", terminalHide);
  $("terminal-reopen").addEventListener("click", terminalShow);
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
$("source-filter").addEventListener("change", (event) => {
  state.sourceFilter = event.target.value;
  renderJobs();
});
$("refresh-btn").addEventListener("click", loadAll);
$("run-cycle-btn").addEventListener("click", runCycle);
$("drawer-close").addEventListener("click", closeDrawer);
$("drawer-backdrop").addEventListener("click", closeDrawer);
$("verify-job-btn").addEventListener("click", verifySelectedJob);
$("open-job-btn").addEventListener("click", () => {
  const url = state.selectedJob?.job?.url;
  if (url) window.open(url, "_blank", "noopener,noreferrer");
});
$("prepare-job-btn").addEventListener("click", prepareSelectedJob);

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeDrawer();
});

setupTerminalWindow();
loadAll();
pollTerminal();
setInterval(pollTerminal, 1100);
setInterval(async () => {
  if (state.status?.cycle?.running) await loadAll();
}, 6000);

const state = {
  status: null,
  jobs: [],
  applications: [],
  activity: [],
  attention: [],
  readiness: null,
  settings: null,
  missions: [],
  insights: null,
  evidence: null,
  companies: [],
  contacts: [],
  interviews: [],
  offers: [],
  authority: {},
  notifications: [],
  goals: [],
  feedback: [],
  selectedJob: null,
  selectedOffer: null,
  compareIds: [],
  filter: "all",
  sourceFilter: "all",
  sort: "best",
  query: "",
  currentRoute: "today",
  terminalSequence: 0,
  terminalPolling: false,
  commandIndex: 0,
};

const $ = (id) => document.getElementById(id);

const routeMeta = {
  today: ["CAREER COMMAND CENTER", "Today"],
  opportunities: ["DISCOVERY + FIT", "Opportunities"],
  applications: ["APPLICATION PIPELINE", "Applications"],
  attention: ["HUMAN CHECKPOINTS", "Needs you"],
  companies: ["COMPANY RADAR", "Companies"],
  people: ["CAREER RELATIONSHIPS", "People"],
  interviews: ["INTERVIEW ROOM", "Interviews"],
  offers: ["DECISION DESK", "Offers"],
  insights: ["CAREER INTELLIGENCE", "Insights"],
  brain: ["CAREER MODEL", "Career Brain"],
  activity: ["HISTORY", "Activity"],
  settings: ["PREFERENCES + AUTHORITY", "Settings"],
};

const routeIcons = {
  today: "home",
  opportunities: "compass",
  applications: "briefcase",
  attention: "alert",
  companies: "building",
  people: "users",
  interviews: "calendar",
  offers: "offer",
  insights: "chart",
  brain: "brain",
  activity: "activity",
  settings: "settings",
};

const decisionLabels = {
  aggressive_pursuit: "Strong pursue",
  high_priority: "High priority",
  apply: "Apply",
  watch: "Watch",
  low_priority: "Low priority",
  ignore: "Ignore",
};

const activityLabels = {
  source_failed: "A job source had a problem",
  job_evaluated: "Job reviewed",
  application_unsupported: "Application site needs manual handling",
  application_blocked: "Application needs you",
  application_prepared: "Application prepared",
  application_execution: "Application action completed",
  application_browser_error: "Application page problem",
  application_submission_window_closed: "Application paused by schedule",
  application_submission_not_authorized: "Final submission not authorized",
  application_preparation_paused: "Application preparation paused",
  discovery_cycle_completed: "Job search finished",
  job_verified: "Job page checked",
  application_packet_prepared_from_ui: "Application files prepared",
  job_preference_updated: "Job preference updated",
  ai_review_paused: "Advanced review paused",
  career_feedback_added: "Career feedback saved",
  company_watch_updated: "Company watch updated",
  contact_saved: "Career contact saved",
  interview_saved: "Interview saved",
  offer_saved: "Offer saved",
  career_goal_saved: "Career goal saved",
  automation_authority_updated: "Authority changed",
};

const terminalLabels = {
  cycle_requested: "search requested",
  cycle_started: "search started",
  source_started: "checking source",
  source_completed: "source checked",
  source_failed: "source problem",
  discovery_completed: "jobs collected",
  intake_completed: "unrelated jobs removed",
  evaluation_started: "checking job fit",
  evaluation_completed: "job reviewed",
  ai_review_paused: "advanced review paused",
  application_preflight_started: "checking applications",
  verification_started: "checking job page",
  verification_completed: "job page checked",
  cycle_completed: "search finished",
  cycle_failed: "search stopped",
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

const verificationLabels = {
  live: "Job is live",
  protected: "Could not check automatically",
  expired: "Job closed",
  unreachable: "Could not open job page",
  needs_review: "Needs a quick check",
  unverifiable: "No job link available",
};

const pipelineLabels = {
  discovered: "Found",
  normalized: "Checked",
  evaluated: "Reviewed",
  rejected: "Passed",
  shortlisted: "Shortlisted",
  preparing: "Preparing",
  blocked: "Needs you",
  ready: "Ready",
  submitted: "Submitted",
  recruiter_contacted: "Recruiter contacted",
  interviewing: "Interviews",
  offer: "Offers",
  negotiating: "Negotiating",
  closed: "Closed",
  failed: "Problem",
};

const authorityCopy = {
  search: ["Find jobs", "Search approved sources and collect suitable opportunities.", "compass"],
  prepare: ["Prepare applications", "Check forms and prepare known answers and files.", "briefcase"],
  submit: ["Submit applications", "Press the final submit button only inside your approved rules.", "check"],
  contact: ["Contact people", "Send recruiter or hiring-contact messages when this is connected.", "mail"],
  follow_up: ["Follow up", "Send approved follow-up messages when timing and context are right.", "clock"],
};

const missionIcons = {
  needs_you: "alert",
  opportunity: "spark",
  ready: "briefcase",
  interview: "calendar",
  offer: "offer",
  search: "compass",
};

const modalSchemas = {
  contact: {
    kicker: "PEOPLE",
    title: "Add career contact",
    endpoint: "/api/contacts",
    fields: [
      ["name", "Name", "text", true],
      ["company", "Company", "text", false],
      ["role", "Role / title", "text", false],
      ["email", "Email", "email", false],
      ["linkedin_url", "LinkedIn URL", "url", false],
      ["relationship", "Relationship", "select", false, ["new","contacted","replied","interviewed_with","worked_with"]],
      ["note", "Private note", "textarea", false],
    ],
  },
  interview: {
    kicker: "INTERVIEWS",
    title: "Add interview",
    endpoint: "/api/interviews",
    fields: [
      ["company", "Company", "text", true],
      ["title", "Role", "text", true],
      ["scheduled_at", "Date and time", "datetime-local", false],
      ["format", "Format", "select", false, ["Video call","Phone","Portfolio review","Hiring manager","Panel","On-site","Other"]],
      ["status", "Status", "select", false, ["planned","confirmed","completed","cancelled"]],
      ["note", "Preparation note", "textarea", false],
    ],
  },
  offer: {
    kicker: "OFFERS",
    title: "Add offer",
    endpoint: "/api/offers",
    fields: [
      ["company", "Company", "text", true],
      ["title", "Role", "text", true],
      ["currency", "Currency", "text", false, null, "USD"],
      ["monthly_base", "Monthly base pay", "number", false],
      ["bonus", "Bonus", "text", false],
      ["equity", "Equity", "text", false],
      ["status", "Status", "select", false, ["reviewing","negotiating","accepted","declined","closed"]],
      ["note", "Decision note", "textarea", false],
    ],
  },
  goal: {
    kicker: "CAREER BRAIN",
    title: "Add career goal",
    endpoint: "/api/goals",
    fields: [
      ["label", "Goal", "text", true],
      ["horizon", "Time horizon", "select", false, ["now","3_months","1_year","3_years"]],
      ["status", "Status", "select", false, ["active","paused","complete"]],
      ["note", "Why this matters", "textarea", false],
    ],
  },
};

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function icon(name, className = "") {
  return `<svg class="${className}" aria-hidden="true"><use href="#i-${name}"></use></svg>`;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
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

function showToast(message) {
  const toast = $("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("is-visible");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("is-visible"), 3200);
}

function decisionTone(decision) {
  if (["apply", "high_priority", "aggressive_pursuit"].includes(decision)) return "apply";
  if (["ignore", "low_priority"].includes(decision)) return "ignore";
  return "watch";
}

function salaryText(job) {
  if (!job.salary_min_monthly && !job.salary_max_monthly) return null;
  const currency = job.currency || "USD";
  const min = job.salary_min_monthly ? Math.round(job.salary_min_monthly).toLocaleString() : null;
  const max = job.salary_max_monthly ? Math.round(job.salary_max_monthly).toLocaleString() : null;
  if (min && max) return `${currency} ${min}–${max}/mo`;
  return `${currency} ${min || max}/mo`;
}

function money(value, currency = "USD") {
  if (value === null || value === undefined || value === "") return "—";
  return `${currency} ${Math.round(Number(value)).toLocaleString()}`;
}

function companyInitials(company) {
  const words = String(company || "?").trim().split(/\s+/).filter(Boolean);
  if (!words.length) return "?";
  return words.slice(0, 2).map((word) => word[0]).join("").toUpperCase();
}

function friendlyVerification(value) {
  return verificationLabels[value] || "Not checked";
}

function friendlyTime(value) {
  if (!value) return "—";
  const raw = String(value);
  const date = new Date(raw.includes("T") ? raw : raw.replace(" ", "T") + "Z");
  if (Number.isNaN(date.getTime())) return raw;
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function friendlyDate(value) {
  if (!value) return { day: "—", rest: "Not scheduled" };
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return { day: "—", rest: String(value) };
  return {
    day: String(date.getDate()).padStart(2, "0"),
    rest: date.toLocaleString([], { month: "short", weekday: "short", hour: "2-digit", minute: "2-digit" }),
  };
}

function animateNumber(element, next) {
  if (!element) return;
  const target = Number(next || 0);
  const current = Number(element.dataset.value || element.textContent || 0);
  element.dataset.value = String(target);
  const reduce = document.body.classList.contains("reduce-motion") ||
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce || target === current) {
    element.textContent = target.toLocaleString();
    return;
  }
  const start = performance.now();
  const duration = 380;
  const tick = (now) => {
    const p = Math.min(1, (now - start) / duration);
    const eased = 1 - Math.pow(1 - p, 3);
    element.textContent = Math.round(current + (target - current) * eased).toLocaleString();
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

function switchView(route) {
  if (!routeMeta[route]) return;
  state.currentRoute = route;
  document.querySelectorAll(".view").forEach((view) => view.classList.remove("is-visible"));
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("is-active"));
  document.querySelector(`#view-${route}`)?.classList.add("is-visible");
  document.querySelector(`.nav-item[data-route="${route}"]`)?.classList.add("is-active");
  const [eyebrow, title] = routeMeta[route];
  $("page-eyebrow").textContent = eyebrow;
  $("page-title").textContent = title;
  closeCommandPalette();
  closeNotificationPanel();
  window.scrollTo({
    top: 0,
    behavior: document.body.classList.contains("reduce-motion") ? "auto" : "smooth",
  });
}

function renderWelcome() {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const name = state.status?.profile?.display_name?.split(" ")[0] || "";
  $("welcome-title").textContent = name ? `${greeting}, ${name}.` : `${greeting}.`;
}

function renderStage(cycle) {
  const stage = cycle?.stage || "idle";
  $("stage-pill").textContent = stageLabels[stage] || stage;
  $("stage-pill").classList.toggle("is-running", Boolean(cycle?.running));
  $("terminal-stage").textContent = stageLabels[stage] || stage;
  const widths = {
    idle: 0,
    starting: 8,
    discovering: 30,
    filtering: 46,
    evaluating: 69,
    preparing: 90,
    complete: 100,
    failed: 100,
  };
  $("terminal-progress-bar").style.width = `${widths[stage] ?? 0}%`;
  if ($("agent-pulse-text")) {
    $("agent-pulse-text").textContent = cycle?.running
      ? (stageLabels[stage] || "Working")
      : cycle?.last_error
        ? "Waiting for a fix"
        : "Watching your career signals";
  }
}

function renderStatus() {
  if (!state.status) return;
  const { profile, metrics, quota, submission, cycle, intake, source_counts, pipeline } = state.status;

  animateNumber($("metric-jobs"), metrics.jobs);
  animateNumber($("metric-high"), metrics.high_priority);
  animateNumber($("metric-needs"), metrics.needs_you);
  animateNumber($("metric-saved"), metrics.saved);
  animateNumber($("metric-submitted"), metrics.submitted);

  $("nav-jobs").textContent = metrics.jobs || 0;
  $("nav-attention").textContent = metrics.needs_you || 0;
  $("attention-count-badge").textContent = metrics.needs_you || 0;
  $("attention-page-count").textContent = metrics.needs_you || 0;

  const quotaText = `${quota.used}/${quota.usable_limit} · today ${quota.used_today}/${quota.daily_limit}`;
  $("quota-mini").textContent = `Searches · ${quotaText}`;
  $("quota-status").textContent = quotaText;

  const effectiveSubmit = state.authority?.submit?.effective_auto_submit;
  const mode = effectiveSubmit ? "Automatic" : submission.auto_submit ? "Permission blocked" : "Supervised";
  $("submission-status").textContent = mode;
  $("application-mode").textContent = mode;
  $("sidebar-mode").textContent = effectiveSubmit ? "Auto apply on" : "Supervised mode";
  $("sidebar-mode-detail").textContent = effectiveSubmit ? "Approved jobs may be sent" : "You stay in control";
  $("window-status").textContent = submission.window_open ? "Open" : "Paused";
  $("intake-status").textContent = intake?.enabled ? "On" : "Off";
  $("cycle-status").textContent = cycle?.running
    ? (stageLabels[cycle.stage] || "Working")
    : (cycle?.last_error ? "Needs attention" : "Idle");

  if (cycle?.running) {
    $("run-cycle-btn").disabled = true;
    $("run-cycle-btn").innerHTML = `${icon("play")}<span>Finding jobs…</span>`;
  } else {
    $("run-cycle-btn").disabled = false;
    $("run-cycle-btn").innerHTML = `${icon("play")}<span>Find jobs</span>`;
  }

  renderStage(cycle);
  renderSourceMix(source_counts || {});
  renderPipeline(pipeline || {});
  renderWelcome();

  $("brain-name").textContent = profile.display_name || "Career profile";
  $("brain-headline").textContent = profile.headline || "—";
  $("brain-location").textContent = profile.location || "—";
  $("brain-remote").textContent = profile.remote_only ? "Remote work" : "Remote or on-site";
  $("brain-comp").textContent = profile.target_monthly
    ? `${profile.currency || "USD"} ${Math.round(profile.target_monthly).toLocaleString()}/month`
    : "Not set";
  $("brain-targets").innerHTML = (profile.target_titles || []).length
    ? profile.target_titles.map((title) => `<span class="tag">${esc(title)}</span>`).join("")
    : '<span class="tag">No target roles set</span>';
}

function renderMissions() {
  const missions = state.missions || [];
  if (!missions.length) return;
  const lead = missions[0];
  $("mission-lead").textContent = lead.title;
  $("mission-copy").textContent = lead.detail;
  $("mission-queue").innerHTML = missions.map((mission) => `
    <button class="mission-chip" data-mission-action="${esc(mission.action)}" data-mission-job="${esc(mission.job_id || "")}">
      ${icon(missionIcons[mission.kind] || "target")}
      <span><strong>${esc(mission.title)}</strong><small>${esc(mission.detail)}</small></span>
    </button>
  `).join("");
  $("mission-queue").querySelectorAll("[data-mission-action]").forEach((button) => {
    button.addEventListener("click", () => runMission(button.dataset.missionAction, button.dataset.missionJob));
  });
}

function runMission(action, jobId) {
  if (action === "find_jobs") return runCycle();
  if (action === "job" && jobId) return openJob(jobId);
  if (routeMeta[action]) return switchView(action);
}

function renderSourceMix(sourceCounts) {
  const entries = Object.entries(sourceCounts).sort((a, b) => b[1] - a[1]);
  $("source-mix").innerHTML = entries.length
    ? entries.map(([source, count]) => `<span class="source-pill"><span>${esc(source)}</span><strong>${count}</strong></span>`).join("")
    : '<div class="empty-state small-empty">No source data yet.</div>';
}

function renderPipeline(pipeline) {
  const todayStages = ["preparing", "blocked", "submitted", "interviewing"];
  $("pipeline-strip").innerHTML = todayStages.map((key) => `
    <div class="pipeline-mini-stage">
      <strong>${Number(pipeline[key] || 0).toLocaleString()}</strong>
      <span>${esc(pipelineLabels[key])}</span>
    </div>
  `).join("");

  const fullStages = ["preparing", "blocked", "ready", "submitted", "interviewing", "offer"];
  $("pipeline-cards").innerHTML = fullStages.map((key) => `
    <div class="pipeline-card">
      <strong>${Number(pipeline[key] || 0).toLocaleString()}</strong>
      <span>${esc(pipelineLabels[key])}</span>
    </div>
  `).join("");
}

function renderSourceOptions() {
  const select = $("source-filter");
  const sources = [...new Set(state.jobs.map((job) => job.source).filter(Boolean))].sort();
  select.innerHTML = '<option value="all">All sources</option>' +
    sources.map((source) => `<option value="${esc(source)}">${esc(source)}</option>`).join("");
  if (!sources.includes(state.sourceFilter)) state.sourceFilter = "all";
  select.value = state.sourceFilter;
}

function filteredJobs() {
  let jobs = state.jobs.filter((job) => {
    if (job.dismissed && state.filter !== "saved") return false;
    if (state.filter === "high_priority" && !["high_priority", "aggressive_pursuit"].includes(job.decision)) return false;
    if (state.filter === "apply" && job.decision !== "apply") return false;
    if (state.filter === "watch" && job.decision !== "watch") return false;
    if (state.filter === "saved" && !job.saved) return false;
    if (state.filter === "verified" && job.verification_state !== "live") return false;
    if (state.sourceFilter !== "all" && job.source !== state.sourceFilter) return false;
    const haystack = `${job.title} ${job.company} ${job.source} ${job.location || ""}`.toLowerCase();
    if (state.query && !haystack.includes(state.query.toLowerCase())) return false;
    return true;
  });

  if (state.sort === "newest") {
    jobs.sort((a, b) => String(b.updated_at || "").localeCompare(String(a.updated_at || "")));
  } else if (state.sort === "salary") {
    jobs.sort((a, b) => Number(b.salary_max_monthly || b.salary_min_monthly || 0) - Number(a.salary_max_monthly || a.salary_min_monthly || 0));
  } else {
    jobs.sort((a, b) => {
      const rank = { aggressive_pursuit: 0, high_priority: 1, apply: 2, watch: 3, low_priority: 4, ignore: 5 };
      const diff = (rank[a.decision] ?? 9) - (rank[b.decision] ?? 9);
      return diff || Number(b.interest_score || 0) - Number(a.interest_score || 0);
    });
  }
  return jobs;
}

function jobCard(job, index = 0) {
  const salary = salaryText(job);
  const decision = job.decision || "pending";
  const score = Number.isFinite(job.interest_score) ? job.interest_score : "—";
  const meta = [
    job.location || (job.remote ? "Remote" : null),
    salary,
    job.source,
  ].filter(Boolean);
  const verification = job.verification_state
    ? `<span class="verification-badge" data-state="${esc(job.verification_state)}">${esc(friendlyVerification(job.verification_state))}</span>`
    : "";
  const compared = state.compareIds.includes(job.id);

  return `
    <article class="job-card" data-job-id="${esc(job.id)}" style="--i:${Math.min(index, 14)}">
      <div class="job-logo">${esc(companyInitials(job.company))}</div>
      <div class="job-main">
        <div class="job-title-row">
          <h3 class="job-title">${esc(job.title)}</h3>
          ${verification}
        </div>
        <div class="job-company">${esc(job.company)}</div>
        <div class="job-meta">
          ${meta.map((value, i) => `<span class="meta-chip ${i === meta.length - 1 ? "source" : ""}">${esc(value)}</span>`).join("")}
        </div>
      </div>
      <div class="job-side">
        <div class="job-score"><strong>${esc(score)}</strong><small>match</small></div>
        <div class="decision-badge" data-tone="${decisionTone(decision)}">${esc(decisionLabels[decision] || decision)}</div>
        <button class="job-save ${compared ? "is-saved" : ""}" data-compare-job="${esc(job.id)}" aria-label="Compare job" title="Compare job">${icon("compare")}</button>
        <button class="job-save ${job.saved ? "is-saved" : ""}" data-save-job="${esc(job.id)}" aria-label="${job.saved ? "Remove saved job" : "Save job"}" title="${job.saved ? "Remove saved job" : "Save job"}">${icon("bookmark")}</button>
      </div>
    </article>
  `;
}

function attachJobCardEvents(container) {
  container.querySelectorAll(".job-card").forEach((card) => {
    card.addEventListener("click", (event) => {
      if (event.target.closest("[data-save-job], [data-compare-job]")) return;
      openJob(card.dataset.jobId);
    });
  });
  container.querySelectorAll("[data-save-job]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const job = state.jobs.find((item) => item.id === button.dataset.saveJob);
      if (job) await setJobPreference(job.id, { saved: !job.saved }, { quiet: true });
    });
  });
  container.querySelectorAll("[data-compare-job]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleCompare(button.dataset.compareJob);
    });
  });
}

function renderJobs() {
  const jobs = filteredJobs();
  $("opportunity-count").textContent = jobs.length;
  $("results-summary").textContent = jobs.length
    ? `${jobs.length} suitable job${jobs.length === 1 ? "" : "s"} shown`
    : "No jobs match these filters.";
  $("jobs-list").innerHTML = jobs.length
    ? jobs.map((job, index) => jobCard(job, index)).join("")
    : '<div class="empty-state">No suitable jobs match this view.</div>';
  attachJobCardEvents($("jobs-list"));

  const priority = state.jobs
    .filter((job) => !job.dismissed && ["aggressive_pursuit", "high_priority", "apply"].includes(job.decision))
    .sort((a, b) => Number(b.interest_score || 0) - Number(a.interest_score || 0))
    .slice(0, 6);
  $("priority-list").innerHTML = priority.length
    ? priority.map((job, index) => jobCard(job, index)).join("")
    : '<div class="empty-state">No strong matches yet. Run a job search to get started.</div>';
  attachJobCardEvents($("priority-list"));
}

function renderAttention() {
  $("attention-mini").innerHTML = state.attention.length
    ? state.attention.slice(0, 4).map((item) => {
        const reason = item.unknown_questions?.[0] || item.blocked_questions?.[0] || item.reasons?.[0] || "A manual check is needed.";
        return `
          <button class="attention-mini-item" data-attention-job="${esc(item.job_id)}">
            <span class="attention-mini-icon">${icon("alert")}</span>
            <span><strong>${esc(item.title)}</strong><small>${esc(reason)}</small></span>
            ${icon("chevron")}
          </button>
        `;
      }).join("")
    : '<div class="empty-state small-empty">Nothing needs your attention right now.</div>';

  $("attention-list").innerHTML = state.attention.length
    ? state.attention.map((item) => {
        const chips = [
          ...(item.unknown_questions || []).map((value) => `Answer needed: ${value}`),
          ...(item.blocked_questions || []).map((value) => `Approval needed: ${value}`),
        ].slice(0, 6);
        const mainReason = item.reasons?.[0] || "Jobster needs a manual decision before continuing.";
        return `
          <article class="attention-card">
            <span class="attention-icon">${icon("alert")}</span>
            <div>
              <h3>${esc(item.title)} · ${esc(item.company)}</h3>
              <p>${esc(mainReason)}</p>
              <div class="attention-details">${chips.map((chip) => `<span class="attention-detail-chip">${esc(chip)}</span>`).join("")}</div>
            </div>
            <button class="button button-secondary" data-attention-job="${esc(item.job_id)}">Review job</button>
          </article>
        `;
      }).join("")
    : `<div class="empty-state success-empty">${icon("check")}<strong>You are clear.</strong><span>Nothing needs your attention right now.</span></div>`;

  document.querySelectorAll("[data-attention-job]").forEach((button) => {
    button.addEventListener("click", () => openJob(button.dataset.attentionJob));
  });
}

function renderApplications() {
  $("applications-list").innerHTML = state.applications.length
    ? state.applications.map((item) => {
        const reason = item.plan?.reasons?.[0] || "No problem recorded.";
        return `
          <article class="application-row" data-application-job="${esc(item.job_id)}">
            <div><strong>${esc(item.title)}</strong><small>${esc(item.company)} · ${esc(item.ats || "application site")}</small></div>
            <span class="state-pill" data-state="${esc(item.state)}">${esc(pipelineLabels[item.state] || item.state)}</span>
            <small>${esc(reason)}</small>
            ${icon("chevron")}
          </article>
        `;
      }).join("")
    : '<div class="empty-state">No applications prepared yet.</div>';
  document.querySelectorAll("[data-application-job]").forEach((row) => {
    row.addEventListener("click", () => openJob(row.dataset.applicationJob));
  });
}

function renderActivity() {
  $("activity-list").innerHTML = state.activity.length
    ? state.activity.map((item) => {
        const label = activityLabels[item.event_type] || item.event_type.replaceAll("_", " ");
        const detail = item.payload?.reason || item.payload?.error || item.payload?.source || item.payload?.company || "";
        return `
          <div class="activity-row">
            <span class="activity-time">${esc(friendlyTime(item.created_at))}</span>
            <span class="activity-icon">${icon(item.event_type.includes("application") ? "briefcase" : item.event_type.includes("verified") ? "shield" : "activity")}</span>
            <span><strong class="activity-type">${esc(label)}</strong><small class="activity-detail">${esc(detail)}</small></span>
            <span class="activity-job">${esc(item.job_id || "Jobster")}</span>
          </div>
        `;
      }).join("")
    : '<div class="empty-state">Nothing to show yet.</div>';
}

function renderCompanies() {
  const watched = state.companies.filter((item) => item.watching);
  const card = (item) => `
    <article class="company-card">
      <div class="company-seal">${esc(companyInitials(item.company))}</div>
      <div>
        <h3>${esc(item.company)}</h3>
        <p>${esc(item.signal === "active" ? "Several strong roles have appeared" : item.signal === "interesting" ? "At least one strong role found" : "Seen in your job search")}</p>
        <div class="company-stats">
          <span><strong>${item.jobs}</strong> jobs</span>
          <span><strong>${item.strong_jobs}</strong> strong</span>
          <span><strong>${item.best_score || "—"}</strong> best match</span>
        </div>
      </div>
      <button class="watch-button ${item.watching ? "is-watching" : ""}" data-watch-company="${esc(item.company)}" title="${item.watching ? "Stop watching" : "Watch company"}">${icon("bookmark")}</button>
    </article>
  `;
  $("watched-companies").innerHTML = watched.length
    ? watched.map(card).join("")
    : '<div class="empty-state small-empty">No companies on your watchlist yet.</div>';
  $("companies-list").innerHTML = state.companies.length
    ? state.companies.map(card).join("")
    : '<div class="empty-state">No company data yet.</div>';

  document.querySelectorAll("[data-watch-company]").forEach((button) => {
    button.addEventListener("click", () => toggleCompanyWatch(button.dataset.watchCompany));
  });
}

async function toggleCompanyWatch(company) {
  const item = state.companies.find((row) => row.company === company);
  if (!item) return;
  try {
    const result = await api("/api/companies/watch", {
      method: "POST",
      body: JSON.stringify({ company, watching: !item.watching }),
    });
    item.watching = result.watching;
    renderCompanies();
    showToast(result.watching ? "Company added to your watchlist." : "Company removed from your watchlist.");
  } catch (error) {
    showToast(error.message);
  }
}

function renderContacts() {
  $("contacts-count").textContent = state.contacts.length;
  $("contacts-list").innerHTML = state.contacts.length
    ? state.contacts.map((item) => `
      <div class="contact-row">
        <span class="contact-avatar">${esc(companyInitials(item.name))}</span>
        <span><strong>${esc(item.name)}</strong><small>${esc([item.role,item.company].filter(Boolean).join(" · ") || "Career contact")}</small></span>
        <span class="relationship-pill">${esc((item.relationship || "new").replaceAll("_"," "))}</span>
      </div>
    `).join("")
    : '<div class="empty-state">No contacts yet. Add a recruiter, hiring manager or useful career contact.</div>';
}

async function analyzeRecruiterMessage() {
  const message = $("recruiter-message").value.trim();
  if (!message) return showToast("Paste the recruiter message first.");
  $("analyze-message-btn").disabled = true;
  try {
    const result = await api("/api/recruiter/advice", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    $("recruiter-advice").innerHTML = `
      <div class="negotiation-line"><span>What it means</span><strong>${esc(result.intent)}</strong></div>
      <div class="negotiation-line"><span>What to do</span><strong>${esc(result.recommended_action)}</strong></div>
      <div class="negotiation-line"><span>Suggested reply</span><strong>${esc(result.draft_reply)}</strong></div>
    `;
  } catch (error) {
    showToast(error.message);
  } finally {
    $("analyze-message-btn").disabled = false;
  }
}

function renderInterviews() {
  $("interviews-list").innerHTML = state.interviews.length
    ? state.interviews.map((item) => {
        const date = friendlyDate(item.scheduled_at);
        return `
          <article class="interview-card">
            <div class="interview-date"><strong>${esc(date.day)}</strong><span>${esc(date.rest)}</span></div>
            <h3>${esc(item.title)}</h3>
            <p>${esc(item.company)}</p>
            <div class="interview-meta">
              <span>${esc(item.status || "planned")}</span>
              ${item.format ? `<span>${esc(item.format)}</span>` : ""}
            </div>
            ${item.note ? `<p style="margin-top:12px">${esc(item.note)}</p>` : ""}
          </article>
        `;
      }).join("")
    : '<div class="empty-state">No interviews saved yet.</div>';
}

function renderOffers() {
  $("offers-list").innerHTML = state.offers.length
    ? state.offers.map((item) => `
      <article class="offer-card" data-offer-id="${esc(item.id)}">
        <div>
          <h3>${esc(item.title)}</h3>
          <p>${esc(item.company)}</p>
          <div class="offer-actions">
            <button class="button button-secondary" data-review-offer="${esc(item.id)}">Review offer</button>
          </div>
        </div>
        <div class="offer-pay">
          <strong>${esc(money(item.monthly_base, item.currency))}</strong>
          <span>monthly base</span>
          <span style="margin-top:7px">${esc(item.status || "reviewing")}</span>
        </div>
      </article>
    `).join("")
    : '<div class="empty-state">No offers saved yet.</div>';

  document.querySelectorAll("[data-review-offer]").forEach((button) => {
    button.addEventListener("click", () => reviewOffer(button.dataset.reviewOffer));
  });
}

async function reviewOffer(offerId) {
  const offer = state.offers.find((item) => item.id === offerId);
  if (!offer) return;
  state.selectedOffer = offer;
  $("negotiation-desk").innerHTML = `
    <div class="desk-handle"></div>
    <div class="eyebrow">NEGOTIATION DESK</div>
    <h3>${esc(offer.company)} · ${esc(offer.title)}</h3>
    <p>Reviewing ${esc(money(offer.monthly_base, offer.currency))} monthly base.</p>
    <div id="offer-advice-result"><div class="negotiation-line"><span>Status</span><strong>Building a negotiation view…</strong></div></div>
  `;
  try {
    const advice = await api(`/api/offers/${encodeURIComponent(offerId)}/advice`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    $("offer-advice-result").innerHTML = `
      <div class="negotiation-line"><span>Leverage</span><strong>${esc((advice.leverage || "unknown").replaceAll("_"," "))}</strong></div>
      <div class="negotiation-line"><span>Suggested counter</span><strong>${esc(advice.recommended_counter_monthly ? money(advice.recommended_counter_monthly, offer.currency) : "Ask for the approved range first")}</strong></div>
      <div class="negotiation-line"><span>Walk-away line</span><strong>${esc(advice.walk_away_below_monthly ? money(advice.walk_away_below_monthly, offer.currency) : "Not set")}</strong></div>
      <div class="negotiation-line"><span>Strategy</span><strong>${esc((advice.strategy || []).join(" "))}</strong></div>
    `;
  } catch (error) {
    $("offer-advice-result").innerHTML = `<div class="negotiation-line"><span>Problem</span><strong>${esc(error.message)}</strong></div>`;
  }
}

function renderInsights() {
  const insights = state.insights;
  if (!insights) return;

  const funnel = insights.funnel || {};
  const funnelPairs = [
    ["Found", funnel.found],
    ["Reviewed", funnel.reviewed],
    ["Worth pursuing", funnel.worth_pursuing],
    ["Applied", funnel.applications],
    ["Interviews", funnel.interviews],
    ["Offers", funnel.offers],
  ];
  const maxFunnel = Math.max(1, ...funnelPairs.map(([,value]) => Number(value || 0)));
  $("funnel-story").innerHTML = `
    <div class="story-title">Your opportunity funnel</div>
    <div class="story-copy">Where your job search is creating movement — and where it may be slowing down.</div>
    <div class="funnel-line">
      ${funnelPairs.map(([label,value]) => `
        <div class="funnel-step">
          <div class="funnel-bar" style="height:${Math.max(3, Math.round((Number(value || 0)/maxFunnel)*70))}px"></div>
          <strong>${Number(value || 0)}</strong><span>${esc(label)}</span>
        </div>
      `).join("")}
    </div>
  `;

  const salary = insights.salary || {};
  const strongSalary = salary.strong_jobs || {};
  $("salary-story").innerHTML = `
    <div class="story-title">Pay evidence from your own matches</div>
    <div class="story-copy">${esc(salary.note || "")}</div>
    <div class="salary-big">${esc(strongSalary.median ? money(strongSalary.median, salary.currency) : "Not enough data")}</div>
    <div class="salary-range">${strongSalary.low ? `Typical stored range: ${esc(money(strongSalary.low, salary.currency))} – ${esc(money(strongSalary.high, salary.currency))}/month` : "Salary data will improve as more matching jobs include pay."}</div>
  `;

  $("source-performance").innerHTML = (insights.sources || []).slice(0,8).map((item) => `
    <div class="insight-row"><span><strong>${esc(item.source)}</strong><small>${item.jobs} jobs · ${item.strong} strong</small></span><span class="insight-value">${esc(item.strong_rate)}% useful</span></div>
  `).join("") || '<div class="empty-state small-empty">Not enough source data yet.</div>';

  $("role-trends").innerHTML = (insights.roles || []).slice(0,8).map((item) => `
    <div class="insight-row"><span><strong>${esc(item.family)}</strong><small>${item.jobs} jobs seen</small></span><span class="insight-value">${item.average_match ?? "—"} avg match</span></div>
  `).join("") || '<div class="empty-state small-empty">Not enough role data yet.</div>';

  $("gap-signals").innerHTML = (insights.gaps || []).slice(0,8).map((item) => `
    <div class="insight-row"><span><strong>${esc(item.gap)}</strong><small>${esc((item.examples || []).join(" · "))}</small></span><span class="insight-value">${item.jobs} jobs</span></div>
  `).join("") || '<div class="empty-state small-empty">No repeated gaps found in strong jobs yet.</div>';

  const evidence = insights.evidence || {};
  $("evidence-health").innerHTML = `
    <div class="insight-row"><span><strong>Active evidence</strong><small>Records, artifacts and supported facts</small></span><span class="insight-value">${evidence.evidence_total || 0}</span></div>
    <div class="insight-row"><span><strong>Capabilities</strong><small>Skills in the Career Brain</small></span><span class="insight-value">${evidence.capabilities_total || 0}</span></div>
    <div class="insight-row"><span><strong>Capabilities with evidence</strong><small>Directly linked to proof</small></span><span class="insight-value">${evidence.capabilities_with_evidence || 0}</span></div>
    <div class="insight-row"><span><strong>Experience records</strong><small>Structured career history</small></span><span class="insight-value">${evidence.experience_entries || 0}</span></div>
  `;
}

function renderReadiness() {
  if (!state.readiness) return;
  const { checks, ready_count, total, answer_bank, application_sites } = state.readiness;
  const percent = total ? Math.round((ready_count / total) * 100) : 0;
  $("readiness-percent").textContent = `${percent}%`;
  $("readiness-ring").style.setProperty("--readiness", `${percent}%`);
  $("readiness-list").innerHTML = checks.map((check) => `
    <div class="readiness-item ${check.ready ? "" : "not-ready"}">
      <span class="readiness-icon">${icon(check.ready ? "check" : "info")}</span>
      <span><strong>${esc(check.label)}</strong><small>${esc(check.detail)}</small></span>
    </div>
  `).join("");
  $("answers-total").textContent = answer_bank.total || 0;
  $("answers-verified").textContent = answer_bank.verified || 0;
  $("answers-auto").textContent = answer_bank.automatic || 0;
  $("site-capability-list").innerHTML = application_sites.map((site) => `
    <div class="site-capability">
      <strong>${esc(site.name)}</strong>
      <span class="capability-pill ${site.level === "check_only" ? "check-only" : ""}">${site.level === "check_only" ? "Can check only" : "Can fill + submit"}</span>
    </div>
  `).join("");
}

function renderGoals() {
  $("goals-list").innerHTML = state.goals.length
    ? state.goals.map((goal) => `
      <div class="goal-row">
        <span class="goal-marker"></span>
        <span><strong>${esc(goal.label)}</strong><small>${esc(goal.note || "Career direction")}</small></span>
        <span class="goal-horizon">${esc((goal.horizon || "now").replaceAll("_"," "))}</span>
      </div>
    `).join("")
    : '<div class="empty-state small-empty">No explicit career goals saved yet.</div>';
}

function renderEvidence() {
  const evidence = state.evidence || {};
  const total = Number(evidence.capabilities_total || 0);
  const linked = Number(evidence.capabilities_with_evidence || 0);
  const percent = total ? Math.round((linked / total) * 100) : 0;
  $("evidence-summary").innerHTML = `
    <div class="evidence-score"><strong>${percent}%</strong><span>of capabilities linked to evidence</span></div>
    <div class="evidence-meter"><i style="width:${percent}%"></i></div>
    <p>${evidence.evidence_total || 0} active evidence items · ${evidence.experience_entries || 0} structured experience records. Jobster prefers proof over confident-sounding claims.</p>
  `;
}

function formatPay(value, currency) {
  if (!value) return "Not set";
  return `${currency || "USD"} ${Math.round(value).toLocaleString()}/month`;
}

function settingsRow(label, value) {
  return `<div class="settings-row"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`;
}

function renderSettings() {
  if (!state.settings) return;
  const search = state.settings.job_search;
  const relevance = state.settings.relevance_filter;
  const applications = state.settings.applications;
  $("settings-search").innerHTML = [
    settingsRow("Target roles", (search.target_titles || []).join(", ") || "Not set"),
    settingsRow("Work style", search.remote_only ? "Remote only" : "Remote or on-site"),
    settingsRow("Target pay", formatPay(search.target_monthly, search.currency)),
    settingsRow("Automatic search interval", `Every ${search.cycle_minutes} minutes`),
    settingsRow("Relevant job filter", relevance.enabled ? "On" : "Off"),
    settingsRow("Jobs allowed from one source", String(relevance.max_per_source)),
  ].join("");
  $("settings-apps").innerHTML = [
    settingsRow("Config auto apply", applications.auto_apply ? "On" : "Off"),
    settingsRow("Max applications per search", String(applications.max_per_search)),
    settingsRow("Friday stop", `${applications.friday_stop} (${applications.timezone})`),
    settingsRow("Monday resume", `${applications.monday_resume} (${applications.timezone})`),
  ].join("");
  renderAuthority();
}

function renderAuthority() {
  const entries = Object.entries(state.authority || {}).filter(([key]) => authorityCopy[key]);
  $("authority-grid").innerHTML = entries.map(([key,value]) => {
    const [label, copy, iconName] = authorityCopy[key];
    const mode = !value.enabled ? "off" : value.requires_approval ? "ask" : "auto";
    return `
      <article class="authority-card">
        <span class="principle-icon cobalt">${icon(iconName)}</span>
        <h4>${esc(label)}</h4>
        <p>${esc(copy)}</p>
        <div class="authority-state">
          <button class="${mode === "off" ? "is-active" : ""}" data-authority="${key}" data-mode="off">Off</button>
          <button class="${mode === "ask" ? "is-active" : ""}" data-authority="${key}" data-mode="ask">Ask</button>
          <button class="${mode === "auto" ? "is-active auto-active" : ""}" data-authority="${key}" data-mode="auto">Auto</button>
        </div>
      </article>
    `;
  }).join("");

  $("authority-grid").querySelectorAll("[data-authority]").forEach((button) => {
    button.addEventListener("click", () => updateAuthority(button.dataset.authority, button.dataset.mode));
  });
}

async function updateAuthority(action, mode) {
  const payload = {
    enabled: mode !== "off",
    requires_approval: mode !== "auto",
  };
  if (action === "submit" && mode === "auto" && !state.status?.submission?.auto_submit) {
    showToast("Auto-submit is still off in your private search settings. This permission alone will not submit jobs.");
  }
  try {
    await api(`/api/authority/${encodeURIComponent(action)}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.authority = await api("/api/authority");
    renderAuthority();
    renderStatus();
    showToast(`${authorityCopy[action][0]} updated.`);
  } catch (error) {
    showToast(error.message);
  }
}

function renderNotifications() {
  const unread = state.notifications.filter((item) => !item.is_read);
  $("notification-dot").classList.toggle("is-visible", unread.length > 0);
  $("notification-list").innerHTML = state.notifications.length
    ? state.notifications.map((item) => `
      <button class="notification-item" data-notification-id="${item.id}" data-notification-job="${esc(item.job_id || "")}">
        <span class="notification-icon">${icon(item.kind === "warning" ? "alert" : item.kind === "success" ? "check" : "bell")}</span>
        <span><strong>${esc(item.title)}</strong><p>${esc(item.body)}</p></span>
      </button>
    `).join("")
    : '<div class="empty-state small-empty">No notifications yet.</div>';
  $("notification-list").querySelectorAll("[data-notification-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = Number(button.dataset.notificationId);
      await api(`/api/notifications/${id}/read`, { method: "POST", body: JSON.stringify({is_read:true}) });
      const jobId = button.dataset.notificationJob;
      if (jobId) openJob(jobId);
      state.notifications = state.notifications.map((item) => item.id === id ? {...item,is_read:true} : item);
      renderNotifications();
    });
  });
}

function openNotificationPanel() {
  $("notification-panel").classList.add("is-visible");
  $("notification-panel").setAttribute("aria-hidden","false");
}
function closeNotificationPanel() {
  $("notification-panel").classList.remove("is-visible");
  $("notification-panel").setAttribute("aria-hidden","true");
}

function renderAll() {
  renderStatus();
  renderMissions();
  renderSourceOptions();
  renderJobs();
  renderAttention();
  renderApplications();
  renderCompanies();
  renderContacts();
  renderInterviews();
  renderOffers();
  renderInsights();
  renderActivity();
  renderReadiness();
  renderGoals();
  renderEvidence();
  renderSettings();
  renderNotifications();
  renderCompareTray();
}

async function loadAll({ quiet = false } = {}) {
  try {
    const [
      status, jobs, applications, activity, attention, readiness, settings,
      missions, insights, evidence, companies, contacts, interviews, offers,
      authority, notifications, goals, feedback,
    ] = await Promise.all([
      api("/api/status"),
      api("/api/jobs?limit=300"),
      api("/api/applications?limit=200"),
      api("/api/activity?limit=200"),
      api("/api/attention?limit=150"),
      api("/api/readiness"),
      api("/api/settings"),
      api("/api/missions"),
      api("/api/insights"),
      api("/api/evidence"),
      api("/api/companies?limit=250"),
      api("/api/contacts?limit=300"),
      api("/api/interviews?limit=200"),
      api("/api/offers?limit=100"),
      api("/api/authority"),
      api("/api/notifications?limit=100"),
      api("/api/goals?limit=100"),
      api("/api/feedback?limit=150"),
    ]);
    Object.assign(state, {
      status, jobs, applications, activity, attention, readiness, settings,
      missions, insights, evidence, companies, contacts, interviews, offers,
      authority, notifications, goals, feedback,
    });
    renderAll();
  } catch (error) {
    if (!quiet) showToast(error.message);
  }
}

async function setJobPreference(jobId, payload, { quiet = false } = {}) {
  try {
    const result = await api(`/api/jobs/${encodeURIComponent(jobId)}/preference`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const job = state.jobs.find((item) => item.id === jobId);
    if (job) {
      job.saved = result.saved;
      job.dismissed = result.dismissed;
      job.note = result.note;
    }
    if (state.selectedJob?.job?.id === jobId) {
      state.selectedJob.preference = result;
      renderDrawerPreference();
    }
    renderJobs();
    if (!quiet) showToast(result.saved ? "Job saved." : payload.dismissed ? "Job hidden." : "Saved.");
    const status = await api("/api/status");
    state.status = status;
    renderStatus();
    return result;
  } catch (error) {
    showToast(error.message);
    return null;
  }
}

function renderDrawerPreference() {
  const pref = state.selectedJob?.preference || {};
  $("drawer-save").classList.toggle("is-saved", Boolean(pref.saved));
  $("drawer-save").title = pref.saved ? "Remove saved job" : "Save job";
  $("drawer-note-input").value = pref.note || "";
  $("dismiss-job-btn").textContent = pref.dismissed ? "Show this job again" : "Hide this job";
}

function renderVerification(verification) {
  const value = verification?.state || "unknown";
  $("drawer-verification").dataset.state = value;
  $("drawer-verification").textContent = friendlyVerification(value);
  $("verification-detail").textContent = verification?.detail || "Check the job page before preparing an application.";
}

async function openJob(jobId) {
  try {
    const bundle = await api(`/api/jobs/${encodeURIComponent(jobId)}`);
    state.selectedJob = bundle;
    const { job, evaluation = {}, application, verification } = bundle;

    $("drawer-source").textContent = (job.source || "Opportunity").toUpperCase();
    $("drawer-title").textContent = job.title;
    $("drawer-company").textContent = [job.company, job.location].filter(Boolean).join(" · ");
    $("drawer-score").textContent = Number.isFinite(evaluation?.interest_score) ? evaluation.interest_score : "—";
    $("drawer-decision").textContent = decisionLabels[evaluation?.pursuit_decision] || evaluation?.pursuit_decision || "Pending";
    $("drawer-decision").dataset.tone = decisionTone(evaluation?.pursuit_decision);
    $("drawer-summary").textContent = evaluation?.summary || evaluation?.role_interpretation || "Jobster has not reviewed this job yet.";
    $("drawer-next").textContent = evaluation?.next_action || "Review this job first.";

    const matches = evaluation?.strong_matches || [];
    $("drawer-matches").innerHTML = matches.length
      ? matches.map((value) => `<span class="tag">${esc(value)}</span>`).join("")
      : '<span class="tag">No clear matches found yet</span>';

    const gaps = [
      ...(evaluation?.learnable_gaps || []),
      ...(evaluation?.unknowns || []),
      ...(evaluation?.hard_blockers || []),
    ];
    $("drawer-gaps").innerHTML = gaps.length
      ? gaps.map((value) => `<span class="tag">${esc(value)}</span>`).join("")
      : '<span class="tag">No important gaps found</span>';

    renderVerification(verification);
    renderDrawerPreference();

    $("open-job-btn").disabled = !job.url;
    $("verify-job-btn").disabled = !job.url;
    $("prepare-job-btn").disabled = !evaluation;
    $("compare-job-btn").classList.toggle("is-active", state.compareIds.includes(job.id));
    $("drawer-note").textContent = application
      ? `Application: ${pipelineLabels[application.state] || application.state}. ${(application.reasons || []).join(" ")}`
      : "No application has been prepared for this job yet.";

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

async function addFeedback(reaction) {
  const jobId = state.selectedJob?.job?.id;
  if (!jobId) return;
  try {
    const result = await api("/api/feedback", {
      method: "POST",
      body: JSON.stringify({ job_id: jobId, reaction }),
    });
    state.feedback.unshift(result);
    showToast("Feedback saved. Jobster will keep it as evidence, not silently rewrite your preferences.");
  } catch (error) {
    showToast(error.message);
  }
}

async function verifySelectedJob() {
  const jobId = state.selectedJob?.job?.id;
  if (!jobId) return;
  try {
    $("verify-job-btn").disabled = true;
    $("verify-job-btn").innerHTML = `${icon("shield")}<span>Checking…</span>`;
    const result = await api(`/api/jobs/${encodeURIComponent(jobId)}/verify`, { method: "POST" });
    state.selectedJob.verification = result;
    renderVerification(result);
    showToast(`Job check: ${friendlyVerification(result.state)}`);
    await loadAll({ quiet: true });
  } catch (error) {
    showToast(error.message);
  } finally {
    $("verify-job-btn").disabled = false;
    $("verify-job-btn").innerHTML = `${icon("shield")}<span>Check job</span>`;
  }
}

async function prepareSelectedJob() {
  const jobId = state.selectedJob?.job?.id;
  if (!jobId) return;
  if (state.authority?.prepare && !state.authority.prepare.enabled) {
    return showToast("Application preparation is turned off in the Authority Center.");
  }
  try {
    $("prepare-job-btn").disabled = true;
    $("prepare-job-btn").innerHTML = `${icon("briefcase")}<span>Preparing…</span>`;
    const result = await api(`/api/jobs/${encodeURIComponent(jobId)}/prepare`, { method: "POST" });
    state.selectedJob.verification = result.verification;
    renderVerification(result.verification);
    $("drawer-note").textContent = "Application files are ready.";
    showToast("Job checked and application prepared.");
    await loadAll({ quiet: true });
  } catch (error) {
    showToast(error.message);
  } finally {
    $("prepare-job-btn").disabled = false;
    $("prepare-job-btn").innerHTML = `${icon("briefcase")}<span>Prepare application</span>`;
  }
}

function toggleCompare(jobId) {
  if (state.compareIds.includes(jobId)) {
    state.compareIds = state.compareIds.filter((id) => id !== jobId);
  } else {
    if (state.compareIds.length >= 4) return showToast("You can compare up to four jobs at once.");
    state.compareIds.push(jobId);
  }
  renderCompareTray();
  renderJobs();
  if (state.selectedJob?.job?.id === jobId) {
    $("compare-job-btn").classList.toggle("is-active", state.compareIds.includes(jobId));
  }
}

function renderCompareTray() {
  const jobs = state.compareIds.map((id) => state.jobs.find((job) => job.id === id)).filter(Boolean);
  $("compare-count").textContent = jobs.length;
  $("compare-chips").innerHTML = jobs.map((job) => `<span class="compare-chip">${esc(job.title)} · ${esc(job.company)}</span>`).join("");
  $("compare-tray").classList.toggle("is-visible", jobs.length > 0);
  $("open-compare-btn").disabled = jobs.length < 2;
}

function openCompareModal() {
  const jobs = state.compareIds.map((id) => state.jobs.find((job) => job.id === id)).filter(Boolean);
  if (jobs.length < 2) return showToast("Select at least two jobs.");
  const rows = [
    ["Company", (job) => job.company],
    ["Match", (job) => Number.isFinite(job.interest_score) ? `${job.interest_score}/100` : "—"],
    ["Decision", (job) => decisionLabels[job.decision] || job.decision || "—"],
    ["Location", (job) => job.location || (job.remote ? "Remote" : "—")],
    ["Salary", (job) => salaryText(job) || "Not listed"],
    ["Source", (job) => job.source || "—"],
    ["Live check", (job) => friendlyVerification(job.verification_state)],
    ["Application", (job) => pipelineLabels[job.application_state] || job.application_state || "Not prepared"],
  ];
  $("compare-table-wrap").innerHTML = `
    <div class="compare-grid" style="--compare-cols:${jobs.length}">
      <div class="compare-cell label">Role</div>
      ${jobs.map((job) => `<div class="compare-cell head"><strong>${esc(job.title)}</strong><small>${esc(job.company)}</small></div>`).join("")}
      ${rows.map(([label,getter]) => `
        <div class="compare-cell label">${esc(label)}</div>
        ${jobs.map((job) => `<div class="compare-cell">${esc(getter(job))}</div>`).join("")}
      `).join("")}
    </div>
  `;
  $("modal-backdrop").classList.add("is-visible");
  $("compare-modal").classList.add("is-visible");
  $("compare-modal").setAttribute("aria-hidden","false");
}

function closeCompareModal() {
  $("compare-modal").classList.remove("is-visible");
  $("compare-modal").setAttribute("aria-hidden","true");
  if (!$("entity-modal").classList.contains("is-visible")) $("modal-backdrop").classList.remove("is-visible");
}

function openEntityModal(type) {
  const schema = modalSchemas[type];
  if (!schema) return;
  $("entity-modal").dataset.type = type;
  $("entity-modal-kicker").textContent = schema.kicker;
  $("entity-modal-title").textContent = schema.title;
  $("entity-form").innerHTML = `
    <div class="form-grid">
      ${schema.fields.map(([name,label,inputType,required,options,defaultValue]) => {
        const full = inputType === "textarea" ? "full" : "";
        let field = "";
        if (inputType === "textarea") {
          field = `<textarea name="${name}" ${required ? "required" : ""}></textarea>`;
        } else if (inputType === "select") {
          field = `<select name="${name}" ${required ? "required" : ""}>${(options || []).map((value) => `<option value="${esc(value)}">${esc(value.replaceAll("_"," "))}</option>`).join("")}</select>`;
        } else {
          field = `<input name="${name}" type="${inputType}" value="${esc(defaultValue || "")}" ${required ? "required" : ""} />`;
        }
        return `<label class="form-field ${full}"><span>${esc(label)}${required ? " *" : ""}</span>${field}</label>`;
      }).join("")}
    </div>
    <div class="form-submit-row">
      <button type="button" class="button button-secondary" data-close-entity>Cancel</button>
      <button type="submit" class="button button-primary">Save</button>
    </div>
  `;
  $("entity-form").querySelector("[data-close-entity]").addEventListener("click", closeEntityModal);
  $("modal-backdrop").classList.add("is-visible");
  $("entity-modal").classList.add("is-visible");
  $("entity-modal").setAttribute("aria-hidden","false");
  setTimeout(() => $("entity-form").querySelector("input,textarea,select")?.focus(), 40);
}

function closeEntityModal() {
  $("entity-modal").classList.remove("is-visible");
  $("entity-modal").setAttribute("aria-hidden","true");
  if (!$("compare-modal").classList.contains("is-visible")) $("modal-backdrop").classList.remove("is-visible");
}

async function submitEntityForm(event) {
  event.preventDefault();
  const type = $("entity-modal").dataset.type;
  const schema = modalSchemas[type];
  if (!schema) return;
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());
  try {
    await api(schema.endpoint, { method: "POST", body: JSON.stringify(payload) });
    closeEntityModal();
    showToast(`${schema.title.replace("Add ","")} saved.`);
    await loadAll({ quiet: true });
  } catch (error) {
    showToast(error.message);
  }
}

async function runCycle() {
  if (state.authority?.search && !state.authority.search.enabled) {
    return showToast("Job search is turned off in the Authority Center.");
  }
  try {
    if (localStorage.getItem("jobster-pref-terminal") !== "0") terminalShow();
    $("run-cycle-btn").disabled = true;
    const result = await api("/api/cycles", { method: "POST" });
    showToast(result.started ? "Job search started." : "A job search is already running.");
    await pollCycle();
  } catch (error) {
    showToast(error.message);
    $("run-cycle-btn").disabled = false;
  }
}

async function pollCycle() {
  try {
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
      const summary = cycle.last_summary;
      showToast(`Job search finished · ${summary.discovered || 0} suitable jobs · ${summary.rejected_irrelevant || 0} unrelated jobs hidden`);
    }
    await loadAll({ quiet: true });
  } catch (error) {
    showToast(error.message);
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
  const tone = item.level === "error" ? "error" : item.event === "cycle_completed" ? "success" : "";
  line.className = `terminal-line ${tone}`;
  const stamp = new Date(item.timestamp);
  const time = Number.isNaN(stamp.getTime()) ? "--:--:--" : stamp.toLocaleTimeString([], { hour12: false });
  const label = terminalLabels[item.event] || item.event.replaceAll("_", " ");
  line.innerHTML = `<span class="time">${esc(time)}</span><span class="event">${esc(label)}</span><span class="message">${esc(item.message)}</span>`;
  body.appendChild(line);
  while (body.children.length > 180) body.removeChild(body.firstChild);
  body.scrollTop = body.scrollHeight;
  if (item.event === "evaluation_started" && item.payload?.total) {
    const progress = 48 + Math.round((item.payload.index / item.payload.total) * 37);
    $("terminal-progress-bar").style.width = `${Math.min(progress, 86)}%`;
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
  } finally {
    state.terminalPolling = false;
  }
}

function setupTerminalWindow() {
  const terminal = $("terminal-window");
  const handle = $("terminal-handle");
  const minimize = $("terminal-minimize");
  if (localStorage.getItem("jobster-terminal-hidden") === "1") terminalHide();

  try {
    const saved = JSON.parse(localStorage.getItem("jobster-terminal-rect") || "null");
    if (saved && window.innerWidth > 720) {
      terminal.style.left = `${Math.max(8, Math.min(saved.left, window.innerWidth - 360))}px`;
      terminal.style.top = `${Math.max(8, Math.min(saved.top, window.innerHeight - 120))}px`;
      terminal.style.right = "auto";
      terminal.style.bottom = "auto";
      if (saved.width) terminal.style.width = `${saved.width}px`;
      if (saved.height) terminal.style.height = `${saved.height}px`;
    }
  } catch {}

  let drag = null;
  handle.addEventListener("pointerdown", (event) => {
    if (event.target.closest("button") || window.innerWidth <= 720) return;
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
  const saveRect = () => {
    if (!drag && terminal.classList.contains("is-hidden")) return;
    drag = null;
    const rect = terminal.getBoundingClientRect();
    localStorage.setItem("jobster-terminal-rect", JSON.stringify({
      left: rect.left, top: rect.top, width: rect.width, height: rect.height,
    }));
  };
  handle.addEventListener("pointerup", saveRect);
  window.addEventListener("mouseup", saveRect);
  minimize.addEventListener("click", () => {
    terminal.classList.toggle("is-minimized");
    minimize.textContent = terminal.classList.contains("is-minimized") ? "□" : "—";
  });
  $("terminal-close").addEventListener("click", terminalHide);
  $("terminal-reopen").addEventListener("click", terminalShow);
}

function commandItems(query = "") {
  const q = query.trim().toLowerCase();
  const pages = Object.entries(routeMeta).map(([route,[,title]]) => ({
    type: "page", id: route, title, subtitle: route === "today" ? "Career command center" : `Open ${title}`, icon: routeIcons[route],
  }));
  const actions = [
    { type: "action", id: "find", title: "Find jobs now", subtitle: "Start a new job search", icon: "play" },
    { type: "action", id: "terminal", title: "Open live job search", subtitle: "See what Jobster is doing", icon: "terminal" },
    { type: "action", id: "export", title: "Export career data", subtitle: "Download your Jobster data as JSON", icon: "download" },
  ];
  const jobs = state.jobs.filter((job) => !job.dismissed).slice(0,100).map((job) => ({
    type: "job", id: job.id, title: job.title, subtitle: job.company, icon: "briefcase",
  }));
  const companies = state.companies.slice(0,50).map((company) => ({
    type: "company", id: company.company, title: company.company, subtitle: `${company.jobs} jobs seen`, icon: "building",
  }));
  const all = [...actions,...pages,...jobs,...companies];
  if (!q) return all.slice(0,18);
  return all.filter((item) => `${item.title} ${item.subtitle}`.toLowerCase().includes(q)).slice(0,24);
}

function renderCommandResults() {
  const items = commandItems($("command-input").value);
  state.commandIndex = Math.max(0, Math.min(state.commandIndex, items.length - 1));
  const primary = items.filter((item) => !["job","company"].includes(item.type));
  const jobs = items.filter((item) => item.type === "job");
  const companies = items.filter((item) => item.type === "company");
  const group = (label, groupItems) => groupItems.length
    ? `<div class="command-section-label">${esc(label)}</div>${groupItems.map((item) => commandItemMarkup(item, items.indexOf(item))).join("")}`
    : "";
  $("command-results").innerHTML =
    group("Actions and pages",primary) +
    group("Jobs",jobs) +
    group("Companies",companies) ||
    '<div class="empty-state">No results.</div>';
  $("command-results").querySelectorAll(".command-item").forEach((button) => {
    button.addEventListener("click", () => runCommand(items[Number(button.dataset.commandIndex)]));
  });
}

function commandItemMarkup(item,index) {
  return `
    <button class="command-item ${index === state.commandIndex ? "is-active" : ""}" data-command-index="${index}">
      <span class="command-item-icon">${icon(item.icon)}</span>
      <span><strong>${esc(item.title)}</strong><small>${esc(item.subtitle)}</small></span>
      ${icon("chevron")}
    </button>
  `;
}

function openCommandPalette() {
  $("command-backdrop").classList.add("is-visible");
  $("command-palette").classList.add("is-visible");
  $("command-palette").setAttribute("aria-hidden","false");
  $("command-input").value = "";
  state.commandIndex = 0;
  renderCommandResults();
  setTimeout(() => $("command-input").focus(),40);
}
function closeCommandPalette() {
  $("command-backdrop").classList.remove("is-visible");
  $("command-palette").classList.remove("is-visible");
  $("command-palette").setAttribute("aria-hidden","true");
}

function runCommand(item) {
  if (!item) return;
  if (item.type === "page") return switchView(item.id);
  if (item.type === "action" && item.id === "find") { closeCommandPalette(); return runCycle(); }
  if (item.type === "action" && item.id === "terminal") { closeCommandPalette(); return terminalShow(); }
  if (item.type === "action" && item.id === "export") { closeCommandPalette(); window.location.href="/api/export"; return; }
  if (item.type === "job") { closeCommandPalette(); return openJob(item.id); }
  if (item.type === "company") {
    closeCommandPalette();
    switchView("companies");
    const card = [...document.querySelectorAll(".company-card")].find((node) => node.textContent.includes(item.id));
    card?.scrollIntoView({behavior:"smooth",block:"center"});
  }
}

function setupPreferences() {
  const reduceMotion = localStorage.getItem("jobster-pref-motion") === "1";
  const compact = localStorage.getItem("jobster-pref-compact") === "1";
  const terminalDefault = localStorage.getItem("jobster-pref-terminal") !== "0";
  $("pref-motion").checked = reduceMotion;
  $("pref-compact").checked = compact;
  $("pref-terminal").checked = terminalDefault;
  document.body.classList.toggle("reduce-motion",reduceMotion);
  document.body.classList.toggle("compact-list-mode",compact);
  $("pref-motion").addEventListener("change",(event) => {
    localStorage.setItem("jobster-pref-motion",event.target.checked ? "1":"0");
    document.body.classList.toggle("reduce-motion",event.target.checked);
  });
  $("pref-compact").addEventListener("change",(event) => {
    localStorage.setItem("jobster-pref-compact",event.target.checked ? "1":"0");
    document.body.classList.toggle("compact-list-mode",event.target.checked);
  });
  $("pref-terminal").addEventListener("change",(event) => {
    localStorage.setItem("jobster-pref-terminal",event.target.checked ? "1":"0");
  });
}

function registerServiceWorker() {
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => navigator.serviceWorker.register("/service-worker.js").catch(() => null));
  }
}

document.addEventListener("click",(event) => {
  const nav = event.target.closest("[data-route]");
  if (nav) switchView(nav.dataset.route);

  const jump = event.target.closest("[data-route-jump]");
  if (jump) switchView(jump.dataset.routeJump);

  const filterJump = event.target.closest("[data-filter-jump]");
  if (filterJump) {
    state.filter = filterJump.dataset.filterJump;
    switchView("opportunities");
    document.querySelectorAll("[data-filter]").forEach((chip) => chip.classList.toggle("is-active",chip.dataset.filter === state.filter));
    renderJobs();
  }

  const findAction = event.target.closest('[data-action="find-jobs"]');
  if (findAction) runCycle();

  const chip = event.target.closest("[data-filter]");
  if (chip) {
    state.filter = chip.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach((item) => item.classList.remove("is-active"));
    chip.classList.add("is-active");
    renderJobs();
  }

  const feedback = event.target.closest("[data-feedback]");
  if (feedback) addFeedback(feedback.dataset.feedback);
});

$("job-search").addEventListener("input",(event) => { state.query = event.target.value; renderJobs(); });
$("source-filter").addEventListener("change",(event) => { state.sourceFilter = event.target.value; renderJobs(); });
$("sort-jobs").addEventListener("change",(event) => { state.sort = event.target.value; renderJobs(); });

$("refresh-btn").addEventListener("click",() => loadAll());
$("run-cycle-btn").addEventListener("click",runCycle);
$("drawer-close").addEventListener("click",closeDrawer);
$("drawer-backdrop").addEventListener("click",closeDrawer);
$("verify-job-btn").addEventListener("click",verifySelectedJob);
$("prepare-job-btn").addEventListener("click",prepareSelectedJob);
$("compare-job-btn").addEventListener("click",() => {
  const id = state.selectedJob?.job?.id;
  if (id) toggleCompare(id);
});
$("open-job-btn").addEventListener("click",() => {
  const url = state.selectedJob?.job?.url;
  if (url) window.open(url,"_blank","noopener,noreferrer");
});
$("drawer-save").addEventListener("click",async () => {
  const id = state.selectedJob?.job?.id;
  if (!id) return;
  await setJobPreference(id,{saved:!Boolean(state.selectedJob?.preference?.saved)});
});
$("save-note-btn").addEventListener("click",async () => {
  const id = state.selectedJob?.job?.id;
  if (id) await setJobPreference(id,{note:$("drawer-note-input").value});
});
$("dismiss-job-btn").addEventListener("click",async () => {
  const id = state.selectedJob?.job?.id;
  if (!id) return;
  const dismissed = Boolean(state.selectedJob?.preference?.dismissed);
  const result = await setJobPreference(id,{dismissed:!dismissed});
  if (result && !dismissed) closeDrawer();
});

$("companies-refresh").addEventListener("click",() => loadAll());
$("add-contact-btn").addEventListener("click",() => openEntityModal("contact"));
$("add-interview-btn").addEventListener("click",() => openEntityModal("interview"));
$("add-offer-btn").addEventListener("click",() => openEntityModal("offer"));
$("add-goal-btn").addEventListener("click",() => openEntityModal("goal"));
$("analyze-message-btn").addEventListener("click",analyzeRecruiterMessage);
$("export-data-btn").addEventListener("click",() => { window.location.href="/api/export"; });

$("entity-form").addEventListener("submit",submitEntityForm);
$("entity-modal-close").addEventListener("click",closeEntityModal);
$("modal-backdrop").addEventListener("click",() => { closeEntityModal(); closeCompareModal(); });
$("open-compare-btn").addEventListener("click",openCompareModal);
$("clear-compare-btn").addEventListener("click",() => { state.compareIds=[]; renderCompareTray(); renderJobs(); });
$("compare-modal-close").addEventListener("click",closeCompareModal);

$("notification-btn").addEventListener("click",() => {
  $("notification-panel").classList.contains("is-visible") ? closeNotificationPanel() : openNotificationPanel();
});
$("notification-close").addEventListener("click",closeNotificationPanel);

$("command-trigger").addEventListener("click",openCommandPalette);
$("command-backdrop").addEventListener("click",closeCommandPalette);
$("command-input").addEventListener("input",() => { state.commandIndex=0; renderCommandResults(); });
$("command-input").addEventListener("keydown",(event) => {
  const items = commandItems($("command-input").value);
  if (event.key === "ArrowDown") {
    event.preventDefault();
    state.commandIndex = Math.min(items.length - 1,state.commandIndex + 1);
    renderCommandResults();
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    state.commandIndex = Math.max(0,state.commandIndex - 1);
    renderCommandResults();
  } else if (event.key === "Enter") {
    event.preventDefault();
    runCommand(items[state.commandIndex]);
  }
});

document.addEventListener("keydown",(event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    openCommandPalette();
  }
  if (event.key === "Escape") {
    closeDrawer();
    closeCommandPalette();
    closeNotificationPanel();
    closeEntityModal();
    closeCompareModal();
  }
});

setupTerminalWindow();
setupPreferences();
registerServiceWorker();
switchView("today");
loadAll();
pollTerminal();
setInterval(pollTerminal,1100);
setInterval(() => {
  if (state.status?.cycle?.running) loadAll({quiet:true});
},6500);

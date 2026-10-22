const routes = {
  dashboard: {
    title: "Dashboard",
    eyebrow: "Overview",
    description: "Your personalized career intelligence dashboard."
  },

  "career-twin": {
    title: "My Career Twin",
    eyebrow: "Your profile",
    description:
      "Manage your skills, goals, preferences, and professional profile."
  },

  skills: {
    title: "Skill Gap Analysis",
    eyebrow: "Skill development",
    description:
      "Understand the skills you already have and the skills needed for your target role."
  },

  jobs: {
    title: "Job Opportunities",
    eyebrow: "Your next opportunity",
    description:
      "Explore recommended roles based on your profile, goals, and current market demand."
  },

  learning: {
    title: "Learning & Courses",
    eyebrow: "Learning center",
    description:
      "Build your next set of skills through guided learning paths and courses."
  },

  market: {
    title: "Market Intelligence",
    eyebrow: "Market trends",
    description:
      "Track growing skills, hiring demand, compensation, and technology trends."
  },

  simulation: {
    title: "Future Simulation",
    eyebrow: "Career planning",
    description:
      "See how different skill and career decisions can affect your future readiness."
  },

  feedback: {
    title: "Recruiter Feedback",
    eyebrow: "External perspective",
    description:
      "Review recruiter comments and discover ways to strengthen your profile."
  },

  roadmap: {
    title: "Career Roadmap",
    eyebrow: "Your path",
    description:
      "Follow a personalized sequence of milestones toward your target career."
  },

  settings: {
    title: "Settings",
    eyebrow: "Preferences",
    description:
      "Manage your account, notifications, privacy, and dashboard preferences."
  }
};


/* =========================================================
   DOM ELEMENTS
   ========================================================= */

const page = document.getElementById("page");
const sidebar = document.getElementById("sidebar");
const mobileBackdrop = document.getElementById("mobileBackdrop");
const mobileMenuBtn = document.getElementById("mobileMenuBtn");
const toast = document.getElementById("toast");

const profileTrigger = document.getElementById("profileTrigger");
const profileMenu = document.getElementById("profileMenu");

const copilotOverlay = document.getElementById("copilotOverlay");
const closeCopilot = document.getElementById("closeCopilot");

const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatMessages = document.getElementById("chatMessages");

let toastTimer;


/* =========================================================
   CAREER PROFILE DEFAULTS
   ========================================================= */

function getCareerProfile() {

  const defaults = {
    target_role: "AI Engineer",
    location: "",
    employment_type: "Full-time",
    preferred_industry: "Artificial Intelligence",
    salary_expectation: "",
    relocation: true,
    work_mode: "Hybrid"
  };

  try {

    const saved =
      JSON.parse(localStorage.getItem("careerPreferences"));

    return {
      ...defaults,
      ...(saved || {})
    };

  } catch (error) {

    console.error(
      "Unable to read saved career preferences:",
      error
    );

    return defaults;
  }
}


/* =========================================================
   ROUTE
   ========================================================= */

function currentRoute() {

  const hash =
    window.location.hash.replace("#", "");

  return hash.split("?")[0] || "dashboard";
}


/* =========================================================
   TOAST
   ========================================================= */

function showToast(message) {

  if (!toast) return;

  try {

    const saved =
      JSON.parse(
        localStorage.getItem(SETTINGS_STORE_KEY)
      );

    if (saved && saved.notifications === false) {
      return;
    }

  } catch (e) {
    /* No stored settings - show the toast. */
  }

  toast.textContent = message;

  toast.classList.add("show");

  clearTimeout(toastTimer);

  toastTimer = setTimeout(() => {

    toast.classList.remove("show");

  }, 2800);
}


/* =========================================================
   MOBILE SIDEBAR
   ========================================================= */

function closeMobileSidebar() {

  sidebar.classList.remove("open");

  mobileBackdrop.classList.remove("open");
}


/* =========================================================
   COPILOT
   ========================================================= */

function openCopilot() {

  copilotOverlay.classList.add("open");

  setTimeout(() => {

    chatInput.focus();

  }, 100);
}


function closeCopilotDialog() {

  copilotOverlay.classList.remove("open");
}


/* =========================================================
   DASHBOARD TEMPLATE
   ========================================================= */

function dashboardTemplate() {

  const profile = getCareerProfile();

  return `

    <div class="page">

      <section class="hero-row">

        <div class="greeting">

          <div class="sun">☀</div>

          <div>

            <h1>
              <span id="dashGreeting">Welcome</span><span id="dashGreetingName"></span>!
            </h1>

            <p>
              Here's your personalized career intelligence dashboard.
            </p>

          </div>

        </div>

        <div class="date" id="dashDate">
          Today
        </div>

      </section>


      <!-- METRICS -->

      <section class="metrics">

        <article class="metric-card">

          <div class="metric-icon">
            ♙
          </div>

          <div>

            <div class="metric-label">
              Current Role
            </div>

            <div class="metric-value" id="dashRole">
              Not set
            </div>

            <div class="metric-subtitle" id="dashRoleSub">
              Generated from your resume
            </div>

            <span class="status-pill blue" id="dashRolePill" hidden>
              In Progress
            </span>

          </div>

        </article>


        <article class="metric-card">

          <div class="metric-icon">
            ◎
          </div>

          <div>

            <div class="metric-label">
              Career Goal
            </div>

            <div class="metric-value" id="dashGoal">
              ${profile.target_role}
            </div>

            <div class="metric-subtitle">
              Target Career
            </div>

            <span class="status-pill" id="dashGoalPill">
              On Track
            </span>

          </div>

        </article>


        <article class="metric-card">

          <div class="metric-icon">
            ↗
          </div>

          <div>

            <div class="metric-label">
              Overall Readiness
            </div>

            <div class="metric-value" id="dashReadiness">
              —
            </div>

            <div class="progress">
              <span id="dashReadinessBar" style="width:0%"></span>
            </div>

            <div class="metric-note" id="dashReadinessNote">
              Upload your resume to see your score
            </div>

          </div>

        </article>


        <article class="metric-card">

          <div class="metric-icon">
            ☆
          </div>

          <div>

            <div class="metric-label">
              Top Recommended Skill
            </div>

            <div class="metric-value" id="dashTopSkill">
              —
            </div>

            <div class="metric-subtitle" id="dashTopSkillSub">
              Close your top gap first
            </div>

            <span class="status-pill purple">
              Trending
            </span>

          </div>

        </article>

      </section>


      <!-- CAREER DIGITAL TWIN -->

      <section class="content-grid">

        <div class="left-column">

          <section class="panel profile-panel">

            <div class="panel-header">

              <div>

                <h2>
                  Your Career Digital Twin
                </h2>

                <p>
                  A dynamic profile of your skills, goals,
                  experience and aspirations.
                </p>

              </div>

              <a
                class="secondary-btn"
                href="#career-twin"
              >
                View Full Profile&nbsp; →
              </a>

            </div>


            <div class="profile-content">

              <div class="profile-summary">

                <div class="large-avatar" id="dashAvatar">
                  👤
                </div>

                <div>

                  <h3 id="dashName">
                    Your Career Twin
                  </h3>

                  <p id="dashRoleLine">
                    Upload your resume to begin
                  </p>

                  <p id="dashLevelLine">
                    —
                  </p>

                </div>

              </div>


              <div class="profile-facts">

                <div class="fact-card">

                  <div class="fact-title">
                    <span>♧</span>
                    Current Skills
                  </div>

                  <div class="fact-value" id="dashSkillCount">
                    —
                  </div>

                  <div class="fact-note" id="dashSkillNote">
                    Extracted from your resume
                  </div>

                </div>


                <div class="fact-card">

                  <div class="fact-title">
                    <span>◎</span>
                    Goal
                  </div>

                  <div class="fact-value">
                    ${profile.target_role}
                  </div>

                  <div class="fact-note">
                    Target Role
                  </div>

                </div>


                <div class="fact-card">

                  <div class="fact-title">
                    <span>⌖</span>
                    Location Preference
                  </div>

                  <div class="fact-value">
                    ${profile.location || "Not set"}
                  </div>

                </div>


                <div class="fact-card">

                  <div class="fact-title">
                    <span>▣</span>
                    Preferred Work Type
                  </div>

                  <div class="fact-value">
                    ${profile.employment_type}
                  </div>

                  <div class="fact-note">
                    (${profile.work_mode} preferred)
                  </div>

                </div>

              </div>

            </div>

          </section>


          <!-- SKILL GAP -->

          <div class="two-column">

            <section class="panel gap-panel">

              <div class="panel-header">

                <div>

                  <h2>
                    Skill Gap Analysis
                  </h2>

                  <p>
                    Here are the skills you need to build
                    for your target role:
                    ${profile.target_role}.
                  </p>

                </div>

                <a
                  class="small-btn"
                  href="#learning"
                >
                  View Learning Path&nbsp; →
                </a>

              </div>


              <div class="gap-content">

                <div class="donut" id="dashDonut">

                  <div class="donut-center">

                    <strong id="dashCoverage">
                      —
                    </strong>

                    <span>
                      Skill Coverage
                    </span>

                  </div>

                </div>


                <div class="skill-columns">

                  <div class="skill-column">

                    <h4>
                      Your Skills
                    </h4>

                    <ul class="skill-list" id="dashStrengths">
                      <li class="empty-line">Loading…</li>
                    </ul>

                    <a
                      class="text-link"
                      href="#skills"
                    >
                      View All&nbsp; →
                    </a>

                  </div>


                  <div class="skill-column missing">

                    <h4>
                      Missing Skills
                    </h4>

                    <ul class="skill-list" id="dashGaps">
                      <li class="empty-line">Loading…</li>
                    </ul>

                    <a
                      class="text-link"
                      href="#skills"
                    >
                      View All&nbsp; →
                    </a>

                  </div>

                </div>

              </div>

            </section>


            <!-- JOBS -->

            <section class="panel jobs-panel">

              <div class="panel-header">

                <div>

                  <h2>
                    Recommended Jobs
                  </h2>

                  <p>
                    Based on your profile and career preferences
                  </p>

                </div>

                <a
                  class="text-link"
                  href="#jobs"
                >
                  View All Jobs&nbsp; →
                </a>

              </div>


              <div
                class="job-list"
                id="dashboardJobs"
              >
                <p class="empty-line">Loading matched jobs…</p>
              </div>

            </section>

          </div>

        </div>

      </section>

    </div>

  `;
}


/* =========================================================
   DASHBOARD DATA BINDING
   =========================================================
   Fills the dashboard from the logged-in user's real Career
   Twin (GET /career-twin). Every card is driven by backend
   data - nothing hardcoded stays.
   ========================================================= */

const DONUT_COLORS = {
  filled: "#22b98d",
  empty: "#e4f5f1"
};


function shortText(value, max) {

  const text = String(value == null ? "" : value).trim();

  if (!text) return "";

  return text.length > max
    ? text.slice(0, max).trim() + "…"
    : text;
}


function donutBackground(percent) {

  const clamped =
    typeof percent === "number" && isFinite(percent)
      ? Math.max(0, Math.min(100, percent))
      : 0;

  const degrees = Math.round((clamped / 100) * 360);

  return `conic-gradient(` +
    `${DONUT_COLORS.filled} 0deg ${degrees}deg, ` +
    `${DONUT_COLORS.empty} ${degrees}deg 360deg)`;
}


function readinessTone(value) {

  const score =
    typeof value === "number" && isFinite(value)
      ? value
      : 0;

  if (score >= 70) {
    return { label: "Strong", className: "" };
  }

  if (score >= 40) {
    return { label: "Building", className: "blue" };
  }

  return { label: "Keep learning", className: "purple" };
}


/* -----------------------------------------
   GAPS EXTRACTION (shared)
   -----------------------------------------
   Newer twins store prioritized_gaps with priority +
   importance. Older twins only store skill_gaps (plain
   strings). This keeps every page working with both.
   ----------------------------------------- */

function extractGaps(state) {

  const prioritized =
    (state && state.prioritized_gaps) || [];

  const usable = prioritized
    .filter(
      gap =>
        gap &&
        typeof gap === "object" &&
        String(gap.skill || "").trim()
    )
    .map((gap, index) => ({
      skill: String(gap.skill).trim(),
      priority: ["High", "Medium", "Low"].includes(
        gap.priority
      )
        ? gap.priority
        : "Medium",
      importance:
        String(gap.importance || "").trim() ||
        "Required for the target role",
      learning_suggestion:
        String(gap.learning_suggestion || "").trim()
    }));

  if (usable.length) return usable;

  const plain = (state && state.skill_gaps) || [];

  return plain
    .map(skill => String(skill).trim())
    .filter(Boolean)
    .map(skill => ({
      skill,
      priority: "Medium",
      importance: "Required for the target role",
      learning_suggestion: ""
    }));
}


function describeEducation(education) {

  const first = Array.isArray(education)
    ? String(education[0] || "")
    : "";

  if (!first.trim()) return null;

  const parts = first
    .split("|")
    .map(part => part.trim())
    .filter(Boolean);

  return {
    title: parts[0] || first,
    school: parts[1] || "",
    status: parts[parts.length - 1] || ""
  };
}


function emptyJobPrompt(hasTwin) {

  return `
    <div class="job-empty">
      ${
        hasTwin
          ? "No job matches stored yet. Regenerate your Career Twin with your latest preferences to pull fresh matches."
          : "Upload your resume to generate your Career Twin and see matched jobs."
      }
      <a href="#career-twin">Generate yours →</a>
    </div>
  `;
}


async function loadDashboard() {

  /* Date + greeting comes from the session, instantly. */

  const now = new Date();

  const dateEl = document.getElementById("dashDate");

  if (dateEl) {
    dateEl.textContent = now.toLocaleDateString(
      undefined,
      {
        weekday: "short",
        month: "short",
        day: "numeric"
      }
    );
  }

  const greetingEl =
    document.getElementById("dashGreeting");

  if (greetingEl) {
    const hour = now.getHours();

    greetingEl.textContent =
      hour < 12
        ? "Good morning"
        : hour < 17
          ? "Good afternoon"
          : "Good evening";
  }

  const nameEl =
    document.getElementById("dashGreetingName");

  const user = getAuthUser();

  const firstName =
    user && user.name
      ? user.name.trim().split(" ")[0]
      : "";

  if (nameEl) {
    nameEl.textContent = firstName ? `, ${firstName}` : "";
  }

  const avatarEl = document.getElementById("dashAvatar");

  if (avatarEl) {
    avatarEl.textContent = firstName
      ? firstName.charAt(0).toUpperCase()
      : "👤";
  }

  /* Then the twin data arrives from the backend. */

  const twin = await loadTwinData();

  const readinessEl =
    document.getElementById("dashReadiness");

  const readinessBar = document.getElementById(
    "dashReadinessBar"
  );

  const readinessNote = document.getElementById(
    "dashReadinessNote"
  );

  const topSkillEl =
    document.getElementById("dashTopSkill");

  const topSkillSub = document.getElementById(
    "dashTopSkillSub"
  );

  const skillCountEl = document.getElementById(
    "dashSkillCount"
  );

  const skillNoteEl =
    document.getElementById("dashSkillNote");

  const coverageEl =
    document.getElementById("dashCoverage");

  const donutEl = document.getElementById("dashDonut");

  const strengthsEl =
    document.getElementById("dashStrengths");

  const gapsEl = document.getElementById("dashGaps");

  const jobsEl =
    document.getElementById("dashboardJobs");

  const roleLineEl =
    document.getElementById("dashRoleLine");

  const levelLineEl =
    document.getElementById("dashLevelLine");

  const twinNameEl =
    document.getElementById("dashName");

  const goalEl = document.getElementById("dashGoal");

  const goalPillEl =
    document.getElementById("dashGoalPill");

  if (!twin) {

    if (readinessEl) readinessEl.textContent = "—";

    if (readinessBar) readinessBar.style.width = "0%";

    if (readinessNote) {
      readinessNote.textContent =
        "Upload your resume to see your score";
    }

    if (topSkillEl) topSkillEl.textContent = "—";

    if (topSkillSub) {
      topSkillSub.textContent =
        "Close your top gap first";
    }

    if (skillCountEl) skillCountEl.textContent = "—";

    if (coverageEl) coverageEl.textContent = "—";

    if (donutEl) {
      donutEl.style.background =
        donutBackground(0);
    }

    if (strengthsEl) {
      strengthsEl.innerHTML =
        `<li class="empty-line">Upload your resume first</li>`;
    }

    if (gapsEl) {
      gapsEl.innerHTML =
        `<li class="empty-line">Upload your resume first</li>`;
    }

    if (jobsEl) jobsEl.innerHTML = emptyJobPrompt(false);

    if (roleLineEl) {
      roleLineEl.textContent =
        "Upload your resume to begin";
    }

    return;
  }

  /* -----------------------------------------
     Twin exists - build every card from it.
     ----------------------------------------- */

  const profile = twin.profile || {};

  const preferences =
    (twin.preferences &&
      typeof twin.preferences === "object")
      ? twin.preferences
      : {};

  const state = twin.career_state || {};

  const readiness = state.readiness_score;

  const targetRole =
    String(
      profile.target_role ||
        preferences.target_role ||
        ""
    ).trim();

  const experienceLevel =
    String(
      profile.experience_level ||
        preferences.experience_level ||
        ""
    ).trim();

  const skills =
    (twin.skills || []).map(skill =>
      String(skill).trim()
    ).filter(Boolean);

  const gaps = extractGaps(state);

  const required =
    Number(state.total_required) || 0;

  const matched =
    Number(state.total_matched) || 0;

  const coverage =
    required > 0
      ? Math.round((matched / required) * 100)
      : 0;

  /* Overall readiness metric. */

  if (readinessEl) {
    readinessEl.textContent =
      typeof readiness === "number"
        ? readiness.toFixed(0) + "%"
        : "—";
  }

  if (readinessBar) {
    readinessBar.style.width =
      typeof readiness === "number"
        ? Math.max(0, Math.min(100, readiness)) + "%"
        : "0%";
  }

  if (readinessNote) {
    readinessNote.textContent = required
      ? `${matched}/${required} required skills matched`
      : "Regenerate your twin to scope your role";
  }

  /* Career goal metric. */

  if (goalEl && targetRole) {
    goalEl.textContent = targetRole;
  }

  if (goalPillEl) {
    const tone = readinessTone(readiness);
    goalPillEl.className =
      "status-pill " + (tone.className || "");
    goalPillEl.textContent = tone.label;
  }

  /* Top recommended skill metric. */

  if (topSkillEl) {
    topSkillEl.textContent = gaps.length
      ? shortText(gaps[0].skill, 26)
      : skills.length
        ? "All key skills covered"
        : "—";
  }

  if (topSkillSub) {
    topSkillSub.textContent = gaps.length
      ? shortText(gaps[0].importance, 64)
      : "No skill gaps for your target role";
  }

  /* Profile summary block. */

  if (twinNameEl) {
    twinNameEl.textContent = firstName
      ? firstName + "'s Career Twin"
      : "Your Career Twin";
  }

  if (roleLineEl) {
    roleLineEl.textContent = targetRole
      ? `Targeting ${targetRole}`
      : "No target role set yet";
  }

  if (levelLineEl) {
    levelLineEl.textContent =
      skills.length
        ? `${skills.length} skills · ${shortText(experienceLevel, 40) || "level not set"}`
        : "—";
  }

  /* Fact cards. */

  if (skillCountEl) {
    skillCountEl.textContent = skills.length || "—";
  }

  if (skillNoteEl) {
    skillNoteEl.textContent = skills.length
      ? "Extracted from your resume"
      : "No skills extracted yet";
  }

  /* Skill gap donut + columns. */

  if (coverageEl) {
    coverageEl.textContent =
      required > 0 ? coverage + "%" : "—";
  }

  if (donutEl) {
    donutEl.style.background =
      donutBackground(coverage);
  }

  if (strengthsEl) {
    strengthsEl.innerHTML = skills.length
      ? skills
          .slice(0, 6)
          .map(
            skill =>
              `<li>${esc(skill)}</li>`
          )
          .join("")
      : `<li class="empty-line">No skills found</li>`;
  }

  if (gapsEl) {
    gapsEl.innerHTML = gaps.length
      ? gaps
          .slice(0, 6)
          .map(
            gap =>
              `<li><span class="gap-priority-dot prio-${gap.priority.toLowerCase()}"></span>${esc(gap.skill)}</li>`
          )
          .join("")
      : `<li class="empty-line">No missing skills 🎉</li>`;
  }

  /* Current role metric - derived from education. */

  const roleValueEl =
    document.getElementById("dashRole");

  const roleSubEl =
    document.getElementById("dashRoleSub");

  const rolePillEl =
    document.getElementById("dashRolePill");

  const education =
    describeEducation(twin.education);

  if (roleValueEl) {
    roleValueEl.textContent = education
      ? shortText(education.title, 26)
      : profile.experience_level ||
        "Not recorded yet";
  }

  if (roleSubEl) {
    roleSubEl.textContent = education
      ? shortText(education.school, 40) ||
        "From your resume"
      : "Generate a twin from your resume";
  }

  if (rolePillEl) {
    const status = education
      ? education.status.toLowerCase()
      : "";

    if (status.includes("pursuing")) {
      rolePillEl.hidden = false;
      rolePillEl.textContent = "In Progress";
    } else if (status.includes("completed")) {
      rolePillEl.hidden = false;
      rolePillEl.textContent = "Completed";
    } else {
      rolePillEl.hidden = true;
    }
  }

  /* Recommended jobs (top 4 by fit score). */

  if (jobsEl) {

    const jobs =
      (twin.job_opportunities || [])
        .slice()
        .sort(
          (a, b) =>
            (Number(b.job_score) || 0) -
            (Number(a.job_score) || 0)
        )
        .slice(0, 4);

    jobsEl.innerHTML = jobs.length
      ? jobs.map(renderJobCard).join("")
      : emptyJobPrompt(true);
  }

}


/* =========================================================
   CAREER TWIN TEMPLATE
   ========================================================= */

function careerTwinTemplate() {
    return `
        <div class="page-header">
            <div>
                <div class="eyebrow">MY CAREER TWIN</div>
                <h1>My Career Twin</h1>
                <p>
                    Upload your resume to generate your Career Twin,
                    then set your career preferences.
                </p>
            </div>
        </div>

        <div id="twinStatus" class="loading-note" hidden></div>

        <div class="card">

            <h2>1. Upload Your Resume</h2>

            <div class="resume-upload">

                <h3>Generate your Career Twin</h3>

                <p>
                    Upload a PDF resume. The AI extracts your skills,
                    compares them to your target role, finds your skill
                    gaps, matches you to real jobs, and scores your
                    market alignment - all automatically.
                </p>

                <input
                    id="resumeFile"
                    class="resume-drop"
                    type="file"
                    accept="application/pdf,.pdf"
                >

                <div id="resumeFileName" class="resume-file-name"></div>

                <button
                    id="uploadResumeBtn"
                    class="upload-btn"
                    disabled
                >
                    Upload &amp; Generate Career Twin
                </button>

                <div id="uploadError" class="upload-error"></div>

                <div id="twinReady" class="loading-note" hidden>
                    ✅ Career Twin generated. View it on the
                    <a href="#dashboard">Dashboard</a> or check your
                    <a href="#skills">Skill Gap Analysis</a>.
                </div>

            </div>

        </div>

        <div class="card">

            <h2>2. Career Preferences</h2>

            <div class="form-grid">

                <!-- Target Role -->
                <div class="form-group">
                    <label>Target Role</label>
                    <input
                        id="preference-target-role"
                        type="text"
                        placeholder="AI Engineer"
                    >
                </div>

                <!-- Location -->
                <div class="form-group">
                    <label>Preferred Location</label>
                    <input
                        id="preference-location"
                        type="text"
                        placeholder="Hyderabad"
                    >
                </div>

                <!-- Work Mode -->
<div class="form-group">
    <label for="workMode">Work Mode</label>

    <select id="workMode">
        <option value="">Select Work Mode</option>
        <option value="Remote">Remote</option>
        <option value="Hybrid">Hybrid</option>
        <option value="On-site">On-site</option>
    </select>
</div>

                <!-- Employment Type -->
                <div class="form-group">
                    <label>Employment Type</label>

                    <select id="preference-employment-type">
                        <option value="">Select Employment Type</option>
                        <option value="Full-time">Full-time</option>
                        <option value="Part-time">Part-time</option>
                        <option value="Contract">Contract</option>
                    </select>
                </div>

                <!-- Salary -->
                <div class="form-group">
                    <label>Expected Salary</label>

                    <input
                        id="preference-salary"
                        type="text"
                        placeholder="10-15 LPA"
                    >
                </div>

                <!-- Industry -->
                <div class="form-group">
                    <label>Preferred Industry</label>

                    <input
                        id="preference-industry"
                        type="text"
                        placeholder="Artificial Intelligence"
                    >
                </div>

                <!-- Experience -->
                <div class="form-group">
                    <label>Experience Level</label>

                    <select id="preference-experience">
                        <option value="">Select Experience Level</option>
                        <option value="Entry Level">Entry Level</option>
                        <option value="Mid Level">Mid Level</option>
                        <option value="Senior Level">Senior Level</option>
                    </select>
                </div>

                <!-- Relocation -->
                <div class="form-group">
                    <label>
                        <input
                            id="preference-relocation"
                            type="checkbox"
                        >
                        Willing to relocate
                    </label>
                </div>

            </div>

            <button
                id="save-preferences"
                class="primary-btn"
            >
                Save Preferences
            </button>

        </div>

        <div id="twinDetails" class="twin-details"></div>
    `;
}


/* =========================================================
   RESUME UPLOAD -> AUTO-GENERATE CAREER TWIN
   =========================================================
   This is the missing link that makes the whole app
   automatic: the user uploads a PDF resume once, and the
   backend runs PDF -> LLM extraction -> skill gap -> jobs
   -> market alignment -> save, with no further clicks.
   ========================================================= */

function bindResumeUpload() {

  const input = document.getElementById("resumeFile");

  const button = document.getElementById("uploadResumeBtn");

  const fileName = document.getElementById("resumeFileName");

  const errorBox = document.getElementById("uploadError");

  const readyBox = document.getElementById("twinReady");

  if (!input || !button) return;


  /* -----------------------------------------
     SHOW SELECTED FILE NAME + ENABLE BUTTON
     ----------------------------------------- */

  input.addEventListener("change", () => {

    const file = input.files && input.files[0];

    if (errorBox) errorBox.textContent = "";

    if (!file) {

      if (fileName) fileName.textContent = "";

      button.disabled = true;

      return;
    }

    if (fileName) {
      fileName.textContent =
        `Selected: ${file.name} ` +
        `(${(file.size / 1024).toFixed(1)} KB)`;
    }

    button.disabled = false;
  });


  /* -----------------------------------------
     UPLOAD + GENERATE
     ----------------------------------------- */

  button.addEventListener("click", async () => {

    const file = input.files && input.files[0];

    if (!file) {

      if (errorBox) {
        errorBox.textContent = "Please choose a PDF resume first.";
      }

      return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {

      if (errorBox) {
        errorBox.textContent = "Please upload a PDF file.";
      }

      return;
    }

    if (errorBox) errorBox.textContent = "";

    if (readyBox) readyBox.hidden = true;

    button.disabled = true;

    const originalLabel = button.textContent;

    button.textContent = "Generating your Career Twin...";

    try {

      const formData = new FormData();

      formData.append("resume", file);

      const token = getAuthToken();

      const response = await fetch(
        `${API_BASE}/career-twin`,
        {
          method: "POST",

          headers: token
            ? { Authorization: `Bearer ${token}` }
            : {},

          body: formData
        }
      );

      const data = await response.json().catch(() => ({}));

      if (response.status === 401) {

        clearAuthSession();

        showAuthScreen();

        return;
      }

      if (!response.ok) {

        throw new Error(
          data.detail ||
          `Backend returned ${response.status}`
        );
      }

      if (readyBox) readyBox.hidden = false;

      showToast("Career Twin generated successfully!");

      // Bust the twin cache so the Career Twin / Skills /
      // Jobs pages reload fresh data, then refresh the
      // details panel and status banner immediately.
      await loadTwinData(true);

      loadTwinDetails();

      refreshTwinStatus();

    } catch (error) {

      console.error("Resume upload failed:", error);

      if (errorBox) {

        errorBox.textContent =
          error.message +
          (error.message.toLowerCase().includes("backend") ||
           error.message.toLowerCase().includes("failed")
            ? "  — is the FastAPI server running?"
            : "");
      }

    } finally {

      button.disabled = false;

      button.textContent = originalLabel;
    }
  });
}


/* -----------------------------------------
   TWIN STATUS BANNER
   ----------------------------------------- */

async function refreshTwinStatus() {

  const box = document.getElementById("twinStatus");

  if (!box) return;

  try {

    const response = await apiFetch("/career-twin/status");

    if (!response.ok) { box.hidden = true; return; }

    const status = await response.json();

    if (status.has_twin) {

      box.hidden = false;

      box.className = "loading-note";

      box.innerHTML =
        `✅ Career Twin ready — ` +
        `${status.skill_count || 0} skills, ` +
        `target role: <strong>` +
        `${escapeHtml(status.target_role || "not set")}</strong>.`;

    } else {

      box.hidden = false;

      box.className = "loading-note";

      box.textContent =
        "No Career Twin yet. Upload your resume below to generate one.";
    }

  } catch (e) {

    box.hidden = true;
  }
}


/* =========================================================
   PLACEHOLDER PAGES
   ========================================================= */

function placeholderTemplate(routeName) {

  const route =
    routes[routeName] || routes.dashboard;

  return `

    <div class="page route-page">

      <section class="route-hero">

        <div class="eyebrow">
          ${route.eyebrow}
        </div>

        <h1>
          ${route.title}
        </h1>

        <p>
          ${route.description}
        </p>

      </section>


      <div class="route-grid">

        <article class="placeholder-card">

          <div class="placeholder-icon">
            ✦
          </div>

          <h3>
            AI-Powered Analysis
          </h3>

          <p>
            This module is ready to connect
            with your Career Digital Twin backend.
          </p>

        </article>


        <article class="placeholder-card">

          <div class="placeholder-icon">
            ◎
          </div>

          <h3>
            Personalized Results
          </h3>

          <p>
            Results will be generated using
            your profile and career preferences.
          </p>

        </article>


        <article class="placeholder-card">

          <div class="placeholder-icon">
            ↗
          </div>

          <h3>
            AI Recommendations
          </h3>

          <p>
            Your agents will provide recommendations
            based on your career goals.
          </p>

        </article>

      </div>

    </div>

  `;
}


/* =========================================================
   DYNAMIC ACTIONS
   ========================================================= */

function bindDynamicActions() {

  /* -----------------------------------------
     SAVE CAREER PREFERENCES
     ----------------------------------------- */

  const savePreferencesButton =
    document.getElementById("save-preferences");

  if (!savePreferencesButton) {
    return;
  }


  savePreferencesButton.addEventListener(
    "click",
    async function () {

      /* -----------------------------------------
         GET FORM ELEMENTS
         ----------------------------------------- */

      const targetRole =
        document.getElementById("preference-target-role");

      const location =
        document.getElementById("preference-location");

      const employmentType =
        document.getElementById("preference-employment-type");

      const industry =
        document.getElementById("preference-industry");

      const salary =
        document.getElementById("preference-salary");

      const relocation =
        document.getElementById("preference-relocation");


      /* -----------------------------------------
         CHECK ELEMENTS
         ----------------------------------------- */

      if (
        !targetRole ||
        !location ||
        !employmentType ||
        !industry ||
        !salary ||
        !relocation
      ) {

        console.error(
          "One or more preference fields are missing."
        );

        showToast(
          "Error: Preference fields not found."
        );

        return;
      }


      /* -----------------------------------------
         GET WORK MODE
         ----------------------------------------- */

      let workMode = "Hybrid";


      /*
         Your current UI appears to use
         a SELECT for work mode.

         Example:
         <select id="workMode">
      */

      const workModeSelect =
        document.getElementById("workMode");


      if (workModeSelect) {

        workMode =
          workModeSelect.value;

      }
      else {

        /*
           Fallback for button-based UI
        */

        const activeMode =
          document.querySelector(
            "[data-work-mode].active"
          );


        if (activeMode) {

          workMode =
            activeMode.dataset.workMode;

        }

      }


      /* -----------------------------------------
         COLLECT PREFERENCES
         ----------------------------------------- */

      const preferences = {

        target_role:
          targetRole.value.trim(),

        location:
          location.value.trim(),

        employment_type:
          employmentType.value,

        preferred_industry:
          industry.value,

        salary_expectation:
          salary.value.trim(),

        relocation:
          relocation.checked,

        work_mode:
          workMode

      };


      /* -----------------------------------------
         SAVE TO LOCAL STORAGE
         ----------------------------------------- */

      localStorage.setItem(
        "careerPreferences",
        JSON.stringify(preferences)
      );


      /* -----------------------------------------
         SHOW LOCAL SUCCESS
         ----------------------------------------- */

      const status =
        document.getElementById(
          "profileStatus"
        );


      if (status) {

        status.textContent =
          "Career preferences saved successfully.";

        status.classList.add("show");

      }


      showToast(
        "Career preferences saved."
      );


      /* -----------------------------------------
         SEND TO FASTAPI
         ----------------------------------------- */

      try {

        const response =
          await apiFetch(
            "/preferences",
            {
              method: "POST",

              body:
                JSON.stringify(
                  preferences
                )
            }
          );


        /* -----------------------------------------
           CHECK RESPONSE
           ----------------------------------------- */

        if (!response.ok) {

          throw new Error(
            "Backend returned status " +
            response.status
          );

        }


        /* -----------------------------------------
           READ RESPONSE
           ----------------------------------------- */

        const data =
          await response.json();


        if (status) {

          status.textContent =
            "Career preferences saved successfully to MongoDB.";

        }


        showToast(
          "Preferences saved to MongoDB."
        );


      }
      catch (error) {

        console.error(
          "Backend error:",
          error
        );


        /*
           LocalStorage is already saved,
           so the user's preferences are not lost.
        */

        if (status) {

          status.textContent =
            "Saved locally. FastAPI is not connected.";

        }


        showToast(
          "Saved locally. Start FastAPI to sync with MongoDB."
        );

      }


      /* -----------------------------------------
         HIDE STATUS MESSAGE
         ----------------------------------------- */

      if (status) {

        setTimeout(() => {

          status.classList.remove(
            "show"
          );

        }, 3000);

      }

    }
  );

}


/* =========================================================
   AGENT 5 - LEARNING & COURSES
   ========================================================= */

const API_BASE = "http://127.0.0.1:8000";


/* =========================================================
   AUTH - LOGIN / REGISTER (full login system)
   ========================================================= */

const AUTH_TOKEN_KEY = "cdt_token";
const AUTH_USER_KEY = "cdt_user";


function getAuthToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY) || "";
}


function getAuthUser() {
  try {
    return JSON.parse(
      localStorage.getItem(AUTH_USER_KEY) || "null"
    );
  } catch (e) {
    return null;
  }
}


function setAuthSession(token, user) {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
  localStorage.setItem(
    AUTH_USER_KEY,
    JSON.stringify(user || {})
  );
}


function clearAuthSession() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
}


/* -----------------------------------------
   apiFetch - every authenticated call
   -----------------------------------------
   Attaches the Bearer token automatically and sends the
   user to the login screen if the token is rejected.
   ----------------------------------------- */

async function apiFetch(path, options) {

  const opts = options || {};
  const headers = Object.assign({}, opts.headers || {});

  const token = getAuthToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  if (opts.body && typeof opts.body === "string") {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(
    path.startsWith("http") ? path : API_BASE + path,
    Object.assign({}, opts, { headers })
  );

  // Token expired or invalid -> drop session, show login.
  if (response.status === 401) {
    clearAuthSession();
    showAuthScreen();
  }

  return response;
}


/* -----------------------------------------
   AUTH SCREEN WIRING
   ----------------------------------------- */

let authMode = "login"; // "login" | "register"


function showAuthScreen() {
  const screen = document.getElementById("authScreen");
  if (screen) screen.hidden = false;
}


function hideAuthScreen() {
  const screen = document.getElementById("authScreen");
  if (screen) screen.hidden = true;

  // Keep the top-bar name/avatar in sync with the session.
  if (typeof updateProfileChrome === "function") {
    updateProfileChrome();
  }
}


function setAuthMode(mode) {
  authMode = mode;

  const isRegister = mode === "register";

  const title = document.getElementById("authTitle");
  const subtitle = document.getElementById("authSubtitle");
  const nameGroup = document.getElementById("nameGroup");
  const submit = document.getElementById("authSubmit");
  const prompt = document.getElementById("authSwitchPrompt");
  const switchBtn = document.getElementById("authSwitchBtn");
  const error = document.getElementById("authError");

  if (title) {
    title.textContent = isRegister
      ? "Create your account"
      : "Welcome back";
  }

  if (subtitle) {
    subtitle.textContent = isRegister
      ? "Register to build your Career Twin from your resume."
      : "Log in to build your Career Twin from your resume.";
  }

  if (nameGroup) nameGroup.hidden = !isRegister;

  if (submit) {
    submit.textContent = isRegister
      ? "Create account"
      : "Log in";
  }

  if (prompt) {
    prompt.textContent = isRegister
      ? "Already have an account?"
      : "Don't have an account?";
  }

  if (switchBtn) {
    switchBtn.textContent = isRegister
      ? "Log in"
      : "Create one";
  }

  if (error) error.textContent = "";
}


function initAuthScreen() {

  const form = document.getElementById("authForm");
  const switchBtn = document.getElementById("authSwitchBtn");
  const error = document.getElementById("authError");
  const submit = document.getElementById("authSubmit");

  if (!form) return;

  setAuthMode("login");

  if (switchBtn) {
    switchBtn.addEventListener("click", () => {
      setAuthMode(authMode === "login" ? "register" : "login");
    });
  }

  form.addEventListener("submit", async (event) => {

    event.preventDefault();

    const email = (
      document.getElementById("authEmail") || {}
    ).value || "";

    const password = (
      document.getElementById("authPassword") || {}
    ).value || "";

    const name = (
      document.getElementById("authName") || {}
    ).value || "";

    if (error) error.textContent = "";

    if (submit) {
      submit.disabled = true;
      submit.textContent =
        authMode === "register"
          ? "Creating account..."
          : "Logging in...";
    }

    try {

      const payload =
        authMode === "register"
          ? { email, password, name }
          : { email, password };

      const response = await fetch(
        `${API_BASE}/auth/${authMode === "register" ? "register" : "login"}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.detail || "Authentication failed."
        );
      }

      setAuthSession(data.access_token, data.user);

      hideAuthScreen();

      showToast(
        authMode === "register"
          ? `Welcome, ${data.user.name || data.user.email}!`
          : `Welcome back, ${data.user.name || data.user.email}!`
      );

      await bootstrapAuthenticatedUser();

    } catch (err) {

      if (error) error.textContent = err.message;

    } finally {

      if (submit) {
        submit.disabled = false;
        submit.textContent =
          authMode === "register"
            ? "Create account"
            : "Log in";
      }
    }
  });
}


/* -----------------------------------------
   POST-LOGIN FLOW (fully automatic)
   -----------------------------------------
   1. Ask the backend whether a Career Twin exists.
   2. No twin  -> send the user to Career Twin to upload.
   3. Twin     -> straight to the dashboard.
   ----------------------------------------- */

async function bootstrapAuthenticatedUser() {

  try {

    const response = await apiFetch("/career-twin/status");

    if (response.ok) {

      const status = await response.json();

      if (status.has_twin) {
        location.hash = "#dashboard";
        renderRoute();
        return;
      }

      showToast(
        "No Career Twin yet - upload your resume to generate one."
      );
      location.hash = "#career-twin";
      renderRoute();
      return;
    }

  } catch (e) {
    // Backend offline - fall through to the dashboard.
  }

  location.hash = "#dashboard";
  renderRoute();
}


/* -----------------------------------------
   LOGOUT
   ----------------------------------------- */

function logout() {
  clearAuthSession();
  showAuthScreen();

  // Reset the top-bar to the signed-out state.
  const nameEl = document.getElementById("profileName");
  const avatarEl = document.getElementById("profileAvatar");
  if (nameEl) nameEl.textContent = "Account";
  if (avatarEl) avatarEl.textContent = "👤";

  showToast("You have been logged out.");
}


/* -----------------------------------------
   STATUS HELPERS
   ----------------------------------------- */

const STATUS_LABELS = {
  not_started: "Not started",
  in_progress: "In progress",
  completed: "Completed"
};


function escapeHtml(value) {

  return String(value == null ? "" : value)

    .replace(/&/g, "&amp;")

    .replace(/</g, "&lt;")

    .replace(/>/g, "&gt;")

    .replace(/"/g, "&quot;")

    .replace(/'/g, "&#39;");
}


/* -----------------------------------------
   LEARNING TEMPLATE (shell)
   ----------------------------------------- */

function learningTemplate() {

  const route = routes.learning;

  return `

    <div class="page route-page">

      <section class="route-hero">

        <div class="eyebrow">${route.eyebrow}</div>

        <h1>${route.title}</h1>

        <p>
          Your roadmap is generated from the real skill gaps
          in your Career Twin. Courses are retrieved from
          live providers - nothing here is made up.
        </p>

      </section>

      <div id="learningContent" class="learning-loading">

        <p class="learning-loading-text">
          Building your roadmap from your skill gaps...
        </p>

      </div>

    </div>
  `;
}


/* -----------------------------------------
   RENDER THE ROADMAP
   ----------------------------------------- */

function renderRoadmap(data) {

  const container =
    document.getElementById("learningContent");

  if (!container) return;

  const roadmap = data.roadmap;

  if (!roadmap || !roadmap.phases.length) {

    container.className = "";

    container.innerHTML = `

      <div class="panel learning-empty">

        <h3>No skill gaps found</h3>

        <p>
          Your Career Twin shows no missing skills for your
          target role. Generate or update your Career Twin
          first, then come back here.
        </p>

      </div>
    `;

    return;
  }

  const summary = roadmap.summary;

  container.className = "";

  container.innerHTML = `

    ${renderRoadmapSummary(summary, roadmap)}

    ${roadmap.phases.map(renderPhase).join("")}

    <div class="panel learning-note">

      <strong>How completion works</strong>

      <p>
        Marking a course as finished records progress.
        Your skill only counts as <em>learned</em> after you
        confirm it or pass a short assessment - then your
        readiness score and job matches are recalculated.
      </p>

    </div>
  `;

  bindLearningActions(data);
}


function renderRoadmapSummary(summary, roadmap) {

  const percent = Number(
    summary.progress_percent || 0
  );

  return `

    <div class="panel learning-summary">

      <div class="learning-summary-main">

        <div class="eyebrow">YOUR PATH TO</div>

        <h2>${escapeHtml(summary.target_role)}</h2>

        <p>
          ${summary.total_phases} phase(s) ·
          ${summary.total_skills} skill(s) to close ·
          about ${summary.estimated_weeks} week(s) at a
          steady pace.
        </p>

      </div>

      <div class="learning-summary-stats">

        <div class="learning-stat">

          <span class="learning-stat-value">
            ${summary.high_priority}
          </span>

          <span class="learning-stat-label">
            High priority
          </span>

        </div>

        <div class="learning-stat">

          <span class="learning-stat-value">
            ${summary.medium_priority}
          </span>

          <span class="learning-stat-label">
            Medium
          </span>

        </div>

        <div class="learning-stat">

          <span class="learning-stat-value">
            ${summary.low_priority}
          </span>

          <span class="learning-stat-label">
            Low
          </span>

        </div>

        <div class="learning-stat">

          <span class="learning-stat-value">
            ${summary.total_estimated_hours}h
          </span>

          <span class="learning-stat-label">
            Estimated
          </span>

        </div>

      </div>

      <div class="learning-progress-bar">

        <div class="learning-progress-track">

          <div class="learning-progress-fill"
               style="width: ${percent}%"></div>

        </div>

        <span class="learning-progress-text">
          ${summary.completed_skills} of
          ${summary.total_skills} skills learned
          (${percent}%)
        </span>

      </div>

    </div>
  `;
}


function renderPhase(phase) {

  return `

    <section class="panel learning-phase">

      <header class="phase-header">

        <div>

          <h2>${escapeHtml(phase.title)}</h2>

          <p>${escapeHtml(phase.suggested_duration)}</p>

        </div>

        <span class="phase-badge phase-${phase.priority.toLowerCase()}">
          ${escapeHtml(phase.priority)} priority
        </span>

      </header>

      <div class="phase-skills">

        ${phase.skills.map(renderSkill).join("")}

      </div>

    </section>
  `;
}


function renderSkill(skill) {

  const resources = skill.resources || {};

  const youtube = resources.youtube_resources || [];

  const platformLinks = resources.platform_links || [];

  const documentation = resources.documentation;

  return `

    <article class="skill-block"
             data-skill="${escapeHtml(skill.skill)}">

      <header class="skill-header">

        <div class="skill-header-text">

          <h3>${escapeHtml(skill.skill)}</h3>

          <span class="skill-importance">
            ${escapeHtml(skill.importance)}
          </span>

        </div>

        <span class="skill-status skill-status-${skill.status}">
          ${STATUS_LABELS[skill.status] || skill.status}
        </span>

      </header>

      ${skill.practical_task ? `

        <div class="skill-task">

          <strong>Practical task</strong>

          <p>${escapeHtml(skill.practical_task)}</p>

        </div>
      ` : ""}

      <div class="skill-resources">

        <h4>Recommended resources</h4>

        ${youtube.length ? `

          <div class="resource-list">

            ${youtube.map(renderYoutubeResource).join("")}

          </div>

        ` : `

          <p class="resource-empty">
            No live video results right now
            ${resources.search_term
              ? `for "${escapeHtml(resources.search_term)}"`
              : ""}.
            Use the provider links below - they open a real
            search on each platform.
          </p>

        `}

        ${documentation ? `

          <a class="resource-doc"
             href="${escapeHtml(documentation.url)}"
             target="_blank"
             rel="noopener noreferrer">

            <span class="resource-doc-icon">📘</span>

            <span>
              ${escapeHtml(documentation.description)}

              ${documentation.verified
                ? `<em class="verified-tag">Verified</em>`
                : ""}
            </span>

          </a>

        ` : ""}

        ${platformLinks.length ? `

          <div class="platform-links">

            ${platformLinks.map(link => `

              <a class="platform-link"
                 href="${escapeHtml(link.url)}"
                 target="_blank"
                 rel="noopener noreferrer">

                ${escapeHtml(link.platform)} ↗

              </a>

            `).join("")}

          </div>

        ` : ""}

      </div>

      <footer class="skill-actions">

        <button class="small-btn"
                data-learning-action="start"
                data-skill="${escapeHtml(skill.skill)}">

          ${skill.status === "not_started"
            ? "Start learning"
            : "Mark as in progress"}

        </button>

        <button class="secondary-btn"
                data-learning-action="complete"
                data-skill="${escapeHtml(skill.skill)}">

          Mark course complete

        </button>

        <button class="secondary-btn"
                data-learning-action="verify"
                data-skill="${escapeHtml(skill.skill)}">

          I learned this skill

        </button>

      </footer>

    </article>
  `;
}


function renderYoutubeResource(resource) {

  const channel = escapeHtml(
    resource.channel || "YouTube"
  );

  const duration = resource.duration_text
    ? `<span class="resource-meta-item">
         ${escapeHtml(resource.duration_text)}
       </span>`
    : "";

  const score = resource.relevance_score
    ? `<span class="resource-meta-item">
         ${escapeHtml(resource.relevance_score)} relevance
       </span>`
    : "";

  return `

    <a class="resource-card"
       href="${escapeHtml(resource.url)}"
       target="_blank"
       rel="noopener noreferrer">

      ${resource.thumbnail ? `

        <img class="resource-thumb"
             src="${escapeHtml(resource.thumbnail)}"
             alt=""
             loading="lazy">

      ` : ""}

      <div class="resource-body">

        <span class="resource-platform">YouTube</span>

        <h5>${escapeHtml(resource.title)}</h5>

        <div class="resource-meta">

          <span class="resource-meta-item">${channel}</span>

          ${duration}

          ${score}

        </div>

      </div>

    </a>
  `;
}


/* -----------------------------------------
   LOAD ROADMAP FROM THE BACKEND
   ----------------------------------------- */

async function loadLearningRoadmap() {

  const container =
    document.getElementById("learningContent");

  try {

    const response = await apiFetch(

      `/learning-roadmap?include_resources=true`,

      { method: "GET" }
    );

    if (!response.ok) {

      const error = await response
        .json()
        .catch(() => ({}));

      throw new Error(
        error.detail ||
        `Backend returned ${response.status}`
      );
    }

    const data = await response.json();

    renderRoadmap(data);

  } catch (error) {

    console.error(
      "Unable to load learning roadmap:",
      error
    );

    if (!container) return;

    container.className = "";

    container.innerHTML = `

      <div class="panel learning-empty">

        <h3>Backend not connected</h3>

        <p>
          ${escapeHtml(error.message)}
        </p>

        <p>
          Start the FastAPI server, then generate your
          Career Twin so this roadmap can be built from
          your real skill gaps.
        </p>

      </div>
    `;
  }
}


/* -----------------------------------------
   PROGRESS ACTIONS
   ----------------------------------------- */

function bindLearningActions(data) {

  document
    .querySelectorAll("[data-learning-action]")
    .forEach(button => {

      button.addEventListener("click", async () => {

        const action =
          button.dataset.learningAction;

        const skill = button.dataset.skill;

        button.disabled = true;

        try {

          if (action === "verify") {

            await verifySkill(skill, button);

          } else if (action === "complete") {

            await markCourseComplete(skill, button);

          } else {

            await markInProgress(skill, button);
          }

        } catch (error) {

          console.error(
            "Learning action failed:",
            error
          );

          showToast(
            "Could not save. Is the backend running?"
          );

        } finally {

          button.disabled = false;
        }
      });
    });
}


function findSkillResource(skillName) {

  const container =
    document.getElementById("learningContent");

  const block = Array.from(
    container.querySelectorAll(".skill-block")
  ).find(
    element => element.dataset.skill === skillName
  );

  const card = block
    ? block.querySelector(".resource-card")
    : null;

  return {

    resource_url: card
      ? card.getAttribute("href")
      : "",

    resource_title: card
      ? (card.querySelector("h5") || {}).textContent || ""
      : "",

    platform: card ? "YouTube" : "Other"
  };
}


async function markInProgress(skillName, button) {

  const resource = findSkillResource(skillName);

  const response = await apiFetch(

    `/learning-progress`,

    {
      method: "POST",

      body: JSON.stringify({

        skill: skillName,

        resource_url: resource.resource_url,

        resource_title: resource.resource_title,

        platform: resource.platform,

        status: "in_progress",

        level: "beginner"
      })
    }
  );

  if (!response.ok) {

    throw new Error(`Backend returned ${response.status}`);
  }

  showToast(`Started learning ${skillName}.`);

  await loadLearningRoadmap();
}


async function markCourseComplete(skillName, button) {

  const resource = findSkillResource(skillName);

  const saveResponse = await apiFetch(

    `/learning-progress`,

    {
      method: "POST",

      body: JSON.stringify({

        skill: skillName,

        resource_url: resource.resource_url,

        resource_title: resource.resource_title,

        platform: resource.platform,

        status: "completed",

        level: "beginner"
      })
    }
  );

  if (!saveResponse.ok) {

    throw new Error(
      `Backend returned ${saveResponse.status}`
    );
  }

  showToast(
    `${skillName} course marked complete. ` +
    `Confirm the skill to count it as learned.`
  );

  await loadLearningRoadmap();
}


async function verifySkill(skillName, button) {

  const confirmed = window.confirm(

    `Confirm that you have learned "${skillName}".\n\n`

    + `This updates your Career Twin and recalculates `
    + `your readiness score and job matches.\n\n`

    + `Click OK to confirm, or Cancel to take a short `
    + `assessment instead.`
  );

  const payload = {

    skill: skillName,

    method: confirmed ? "confirmation" : "assessment"
  };

  if (!confirmed) {

    const raw = window.prompt(

      `Enter your assessment score for "${skillName}" `

      + `(0 - 100). A score of 60 or more passes.`

    );

    if (raw === null) return;

    const score = Number(raw);

    if (Number.isNaN(score)) {

      showToast("Please enter a number for the score.");

      return;
    }

    payload.assessment_score = score;
  }

  const response = await apiFetch(

    `/learning-progress/complete`,

    {
      method: "POST",

      body: JSON.stringify(payload)
    }
  );

  const result = await response
    .json()
    .catch(() => ({}));

  if (!response.ok) {

    showToast(
      result.detail ||
      "Assessment did not pass. Keep learning!"
    );

    return;
  }

  const recalc = result.recalculation || {};

  const readiness = recalc.readiness_score;

  showToast(
    `${skillName} marked as learned! `
    + (
      typeof readiness === "number"
        ? `New readiness score: ${readiness}%.`
        : "Career Twin updated."
    )
  );

  // Bust the twin cache so the refreshed readiness score,
  // gaps and job matches are reloaded for every page.
  await loadTwinData(true);

  await loadLearningRoadmap();
}


/* =========================================================
   CAREER TWIN DATA - SHARED FETCH
   =========================================================
   One helper loads the full saved twin (from GET
   /career-twin) and caches it so the Career Twin, Skill
   Gap and Jobs pages can all render the same real data.
   ========================================================= */

let _twinCache = null;
let _twinCachePromise = null;


async function loadTwinData(force) {

  if (force) {
    _twinCache = null;
    _twinCachePromise = null;
  }

  if (_twinCache) return _twinCache;

  if (!_twinCachePromise) {

    _twinCachePromise = (async () => {

      const response = await apiFetch("/career-twin");

      if (response.status === 404) return null;

      if (!response.ok) return null;

      const data = await response.json();

      _twinCache = data.career_twin || null;

      return _twinCache;

    })().catch(() => null);
  }

  return _twinCachePromise;
}


/* -----------------------------------------
   SMALL RENDER HELPERS
   ----------------------------------------- */

function esc(value) {
  return escapeHtml(value == null ? "" : value);
}


function scoreBar(label, value, color) {
  const pct =
    typeof value === "number"
      ? Math.max(0, Math.min(100, value))
      : null;

  return `
    <div class="score-row">
      <div class="score-label">${esc(label)}</div>
      <div class="score-track">
        <div class="score-fill"
             style="width:${pct == null ? 0 : pct}%;
                    background:${color || "#5082ff"}">
        </div>
      </div>
      <div class="score-value">
        ${pct == null ? "—" : pct.toFixed(0) + "%"}
      </div>
    </div>
  `;
}


function chipList(items, cls) {
  if (!items || !items.length) {
    return `<p class="empty-line">None found.</p>`;
  }

  return `<div class="chip-wrap">` +
    items.map(
      item => `<span class="chip ${cls || ""}">${esc(item)}</span>`
    ).join("") +
    `</div>`;
}


function listBlock(title, items) {
  if (!items || !items.length) return "";

  return `
    <div class="twin-section">
      <h4>${esc(title)}</h4>
      <ul class="twin-list">
        ${items.map(i => `<li>${esc(i)}</li>`).join("")}
      </ul>
    </div>
  `;
}


/* =========================================================
   1. CAREER TWIN PAGE - REAL PROFILE DATA
   ========================================================= */

async function loadTwinDetails() {

  const container =
    document.getElementById("twinDetails");

  if (!container) return;

  container.innerHTML =
    `<div class="loading-note">Loading your Career Twin…</div>`;

  const twin = await loadTwinData();

  if (!twin) {

    container.innerHTML = `
      <div class="panel learning-empty">
        <h3>No Career Twin yet</h3>
        <p>Upload your resume above to generate your
           Career Twin, then this section fills in
           automatically.</p>
      </div>
    `;
    return;
  }

  const profile = twin.profile || {};
  const state = twin.career_state || {};

  const readiness = state.readiness_score;
  const market = state.market_alignment;

  container.innerHTML = `

    <div class="panel twin-view">

      <div class="panel-header">
        <h2>Your Career Twin</h2>
        <p>A living profile built from your resume and
           preferences.</p>
      </div>

      <div class="twin-hero">

        <div class="twin-hero-fact">
          <span class="twin-hero-label">Target Role</span>
          <span class="twin-hero-value">
            ${esc(profile.target_role || "Not set")}
          </span>
        </div>

        <div class="twin-hero-fact">
          <span class="twin-hero-label">Experience</span>
          <span class="twin-hero-value">
            ${esc(profile.experience_level || "Not set")}
          </span>
        </div>

        <div class="twin-hero-fact">
          <span class="twin-hero-label">Location</span>
          <span class="twin-hero-value">
            ${esc(profile.location || "Not set")}
          </span>
        </div>

        <div class="twin-hero-fact">
          <span class="twin-hero-label">Skills</span>
          <span class="twin-hero-value">
            ${(twin.skills || []).length}
          </span>
        </div>

      </div>

      <div class="twin-scores">

        <div class="twin-score-card">
          <div class="twin-score-num">
            ${readiness == null ? "—" : readiness.toFixed(0) + "%"}
          </div>
          <div class="twin-score-cap">Readiness Score</div>
        </div>

        <div class="twin-score-card">
          <div class="twin-score-num">
            ${market == null ? "—" : market.toFixed(0) + "%"}
          </div>
          <div class="twin-score-cap">Market Alignment</div>
        </div>

        <div class="twin-score-card">
          <div class="twin-score-num">
            ${state.total_matched == null ? "—" : state.total_matched}
          </div>
          <div class="twin-score-cap">Skills Matched</div>
        </div>

        <div class="twin-score-card">
          <div class="twin-score-num">
            ${state.total_missing == null ? "—" : state.total_missing}
          </div>
          <div class="twin-score-cap">Skill Gaps</div>
        </div>

      </div>

      <div class="twin-section">
        <h4>Skills</h4>
        ${chipList(twin.skills, "chip-skill")}
      </div>

      ${(twin.strengths || state.strengths || []).length ? `
        <div class="twin-section">
          <h4>Strengths</h4>
          ${chipList(state.strengths, "chip-good")}
        </div>
      ` : ""}

      ${(state.skill_gaps || []).length ? `
        <div class="twin-section">
          <h4>Skill Gaps</h4>
          ${chipList(state.skill_gaps, "chip-gap")}
        </div>
      ` : ""}

      ${listBlock("Education", twin.education)}
      ${listBlock("Experience", twin.experience)}
      ${listBlock("Projects", twin.projects)}
      ${listBlock("Certifications", twin.certifications)}
      ${listBlock("Achievements", twin.achievements)}

    </div>
  `;
}


/* =========================================================
   2. SKILL GAP ANALYSIS PAGE
   ========================================================= */

function skillsTemplate() {
  return `
    <div class="page-header">
      <div>
        <div class="eyebrow">SKILL DEVELOPMENT</div>
        <h1>Skill Gap Analysis</h1>
        <p>
          The skills you already have versus what your target
          role needs — with a prioritized plan to close the gaps.
        </p>
      </div>
    </div>

    <div id="skillsContent" class="learning-loading">
      <div class="loading-note">
        Analysing your skill gaps…
      </div>
    </div>
  `;
}


async function loadSkillAnalysis() {

  const container =
    document.getElementById("skillsContent");

  if (!container) return;

  const twin = await loadTwinData();

  if (!twin) {

    container.innerHTML = `
      <div class="panel learning-empty">
        <h3>No Career Twin yet</h3>
        <p>Upload your resume on the
           <a href="#career-twin">Career Twin</a> page to
           generate your skill gap analysis.</p>
      </div>
    `;
    return;
  }

  const state = twin.career_state || {};

  const required = state.total_required || 0;
  const matched = state.total_matched || 0;
  const missing = state.total_missing || 0;
  const coverage =
    required > 0
      ? Math.round((matched / required) * 100)
      : 0;

  const gaps = extractGaps(state);

  const breakdown = state.readiness_breakdown || {};

  const priorityClass = p =>
    "prio-" + String(p || "medium").toLowerCase();

  container.className = "";

  container.innerHTML = `

    <div class="panel gap-summary">

      <div class="gap-summary-head">

        <div class="gap-big">
          <span class="gap-big-num">${coverage}%</span>
          <span class="gap-big-cap">Skill Coverage</span>
        </div>

        <div class="gap-counts">
          <div class="gap-count">
            <strong>${matched}</strong> matched
          </div>
          <div class="gap-count gap-count-missing">
            <strong>${missing}</strong> missing
          </div>
          <div class="gap-count">
            <strong>${required}</strong> required
          </div>
        </div>

      </div>

      ${scoreBar("Skill coverage", coverage, "#00d1b2")}
      ${scoreBar("Readiness score", state.readiness_score, "#5082ff")}
      ${scoreBar("Market alignment", state.market_alignment, "#a06bff")}

    </div>

    <div class="panel">

      <div class="panel-header">
        <h2>Your Strengths</h2>
        <p>Skills you already have that match the role.</p>
      </div>

      ${chipList(state.strengths, "chip-good")}

    </div>

    <div class="panel">

      <div class="panel-header">
        <h2>Prioritized Skill Gaps</h2>
        <p>Close these, highest priority first.</p>
      </div>

      ${
        gaps.length
          ? `<ul class="gap-list">` +
            gaps.map(g => `
              <li class="gap-item">
                <div class="gap-item-head">
                  <span class="gap-skill">${esc(g.skill)}</span>
                  <span class="prio-badge ${priorityClass(g.priority)}">
                    ${esc(g.priority || "Medium")}
                  </span>
                </div>
                ${
                  g.importance
                    ? `<p class="gap-importance">${esc(g.importance)}</p>`
                    : ""
                }
                ${
                  g.learning_suggestion
                    ? `<p class="gap-tip">
                         <strong>Tip:</strong>
                         ${esc(g.learning_suggestion)}
                       </p>
                       <a class="gap-learn"
                          href="#learning">
                          Find courses →
                       </a>`
                    : ""
                }
              </li>
            `).join("") +
            `</ul>`
          : `<p class="empty-line">
               No gaps found — your skills cover the role.
             </p>`
      }

    </div>

    ${
      Object.keys(breakdown).length
        ? `
          <div class="panel">
            <div class="panel-header">
              <h2>Readiness Breakdown</h2>
            </div>
            ${scoreBar("Skill coverage", breakdown.skill_coverage, "#00d1b2")}
            ${scoreBar("Project evidence", breakdown.project_evidence, "#5082ff")}
            ${scoreBar("Experience", breakdown.experience, "#a06bff")}
            ${scoreBar("Fundamentals", breakdown.fundamentals, "#ffb020")}
            ${scoreBar("Education", breakdown.education, "#ff7b8a")}
          </div>
        `
        : ""
    }
  `;
}


/* =========================================================
   3. JOB OPPORTUNITIES PAGE
   ========================================================= */

function jobsTemplate() {
  return `
    <div class="page-header">
      <div>
        <div class="eyebrow">YOUR NEXT OPPORTUNITY</div>
        <h1>Job Opportunities</h1>
        <p>
          Real roles matched to your Career Twin, ranked by how
          well you fit each one.
        </p>
      </div>
    </div>

    <div id="jobsContent" class="learning-loading">
      <div class="loading-note">
        Loading matched jobs…
      </div>
    </div>
  `;
}


/* Salary values from Adzuna/Jooble are annual INR.
   600000 -> ₹6 LPA; below one lakh, show the raw rupee
   number compactly. */

function formatINRLakh(value) {

  const n = Number(value);

  if (!Number.isFinite(n) || n <= 0) return "";

  if (n >= 100000) {

    const lakh = n / 100000;

    return `₹${lakh % 1 === 0 ? lakh.toFixed(0) : lakh.toFixed(1)} LPA`;
  }

  return `₹${n.toLocaleString("en-IN")}`;
}

function formatSalaryRange(min, max) {

  const lo = formatINRLakh(min);
  const hi = formatINRLakh(max);

  if (lo && hi) return `${lo} – ${hi}`;

  return lo || hi || "";
}


function renderJobCard(job) {

  const pct =
    typeof job.job_score === "number"
      ? job.job_score.toFixed(0)
      : null;

  const skillPct =
    typeof job.skill_match_pct === "number"
      ? job.skill_match_pct.toFixed(0) + "% skills"
      : "";

  const salary = formatSalaryRange(
    job.salary_min,
    job.salary_max
  );

  const logo =
    (job.company || "?").trim().charAt(0).toUpperCase();

  return `

    <a class="job-card job-card-link"
       href="${esc(job.url || "#")}"
       target="_blank"
       rel="noopener noreferrer">

      <div class="company-logo">${esc(logo)}</div>

      <div class="job-info">
        <div class="job-title">${esc(job.title || "Untitled role")}</div>
        <div class="job-company">${esc(job.company || "Unknown company")}</div>
        <div class="job-location">
          ${esc(job.location || "Location unknown")}
          ${
            job.work_mode && job.work_mode !== "Unknown"
              ? ` · ${esc(job.work_mode)}`
              : ""
          }
        </div>

        ${
          (job.matched_skills || []).length
            ? `<div class="job-skills">
                 <span class="job-skills-label">Matches:</span>
                 ${job.matched_skills
                    .slice(0, 5)
                    .map(s => `<span class="chip chip-good">${esc(s)}</span>`)
                    .join("")}
               </div>`
            : ""
        }
      </div>

      <div class="job-meta">
        ${
          pct != null
            ? `<span class="match">${pct}% match</span>`
            : ""
        }
        ${salary ? `<span class="salary">${esc(salary)}</span>` : ""}
        ${skillPct ? `<span class="job-skillpct">${esc(skillPct)}</span>` : ""}
        ${
          job.source && job.source !== "Unknown"
            ? `<span class="job-source">${esc(job.source)}</span>`
            : ""
        }
      </div>

    </a>
  `;
}


async function loadJobOpportunities() {

  const container =
    document.getElementById("jobsContent");

  if (!container) return;

  const twin = await loadTwinData();

  if (!twin) {

    container.innerHTML = `
      <div class="panel learning-empty">
        <h3>No Career Twin yet</h3>
        <p>Upload your resume on the
           <a href="#career-twin">Career Twin</a> page to
           see matched job opportunities.</p>
      </div>
    `;
    return;
  }

  const jobs = twin.job_opportunities || [];

  container.className = "";

  if (!jobs.length) {

    container.innerHTML = `
      <div class="panel learning-empty">
        <h3>No jobs matched yet</h3>
        <p>Set your career preferences and regenerate your
           Career Twin to see matched roles.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = `

    <div class="panel jobs-panel">

      <div class="panel-header">
        <h2>${jobs.length} Matched Roles</h2>
        <p>Ranked by your overall fit — click a card to apply.</p>
      </div>

      <div class="job-list">
        ${jobs.map(renderJobCard).join("")}
      </div>

    </div>
  `;
}


/* =========================================================
    4. MARKET INTELLIGENCE PAGE
   =========================================================
   Everything on this page is derived from data the backend
   already collected: the market alignment score + breakdown
   produced against live job postings, and the postings
   themselves stored in the Career Twin.
   ========================================================= */

const MARKET_LABELS = {
  role_demand: "Role demand",
  skill_demand: "Skill demand",
  profile_market_match: "Profile-market fit",
  location_market_fit: "Location fit"
};

const MARKET_COLORS = {
  role_demand: "#2e86fa",
  skill_demand: "#17a986",
  profile_market_match: "#9560e7",
  location_market_fit: "#e9a23b"
};


function barRow(label, value, color) {

  const has = typeof value === "number" && isFinite(value);

  const pct = has ? Math.max(0, Math.min(100, value)) : 0;

  return `
    <div class="score-row">
      <div class="score-label">${esc(label)}</div>
      <div class="score-track">
        <div class="score-fill"
             style="width:${pct}%;background:${color}">
        </div>
      </div>
      <div class="score-value">
        ${has ? pct.toFixed(0) + "%" : "—"}
      </div>
    </div>
  `;
}


function cleanSkillToken(token) {

  const text = String(token || "").trim();

  if (text.length < 3 || text.length > 34) return "";

  if (/^\d+$/.test(text)) return "";

  if (/[)\]};]/.test(text)) return "";

  const lower = text.toLowerCase();

  const junk = [
    "minimum",
    "equivalent",
    "experience",
    "proficiency",
    "knowledge",
    "degree",
    "bachelor",
    "master",
    "years",
    "including"
  ];

  return junk.some(word => lower.includes(word))
    ? ""
    : text;
}


function computeMarketStats(twin) {

  const jobs = twin.job_opportunities || [];

  const companyCounts = new Map();

  const locationCounts = new Map();

  const skillCounts = new Map();

  let skillSum = 0;

  let skillSamples = 0;

  let salaryJobs = 0;

  for (const job of jobs) {

    const company =
      String(job.company || "").trim();

    if (company && company !== "?") {
      companyCounts.set(
        company,
        (companyCounts.get(company) || 0) + 1
      );
    }

    const location =
      String(job.location || "").trim();

    if (location) {
      locationCounts.set(
        location,
        (locationCounts.get(location) || 0) + 1
      );
    }

    for (const raw of [
      ...(job.matched_skills || []),
      ...(job.required_skills || [])
    ]) {

      const skill = cleanSkillToken(raw);

      if (!skill) continue;

      const key = skill.toLowerCase();

      skillCounts.set(
        key,
        (skillCounts.get(key) || 0) + 1
      );
    }

    const matchPct = Number(job.skill_match_pct);

    if (isFinite(matchPct)) {
      skillSum += matchPct;
      skillSamples += 1;
    }

    if (job.salary_min && job.salary_max) {
      salaryJobs += 1;
    }
  }

  const top = map =>
    Array.from(map.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8);

  return {
    jobCount: jobs.length,
    companies: top(companyCounts),
    companyCount: companyCounts.size,
    locations: top(locationCounts),
    skills: top(skillCounts).map(
      ([key, count]) => {
        const original = jobs
          .flatMap(job =>
            [...(job.matched_skills || []), ...(job.required_skills || [])]
          )
          .find(
            skill =>
              String(skill || "").trim().toLowerCase() === key
          );

        return {
          skill: original ? String(original).trim() : key,
          count
        };
      }
    ),
    avgSkillMatch:
      skillSamples
        ? skillSum / skillSamples
        : null,
    salaryJobs,
    sources: Array.from(
      new Set(
        jobs.map(job => job.source).filter(Boolean)
      )
    )
  };
}


function rankListHtml(items, unit) {

  if (!items || !items.length) {
    return `<p class="empty-line">Not enough data yet.</p>`;
  }

  const max = Math.max(
    ...items.map(item => Number(item.count) || 0),
    1
  );

  return `
    <ul class="rank-list">
      ${items.map(item => `
        <li>
          <span class="rank-position">
            ${esc(item.count)}
          </span>
          <span class="rank-name">${esc(item.skill || item.company || item.location)}</span>
          <span class="rank-bar">
            <span style="width:${Math.round((item.count / max) * 100)}%"></span>
          </span>
          <span class="rank-count">
            ${unit ? unit : ""}
          </span>
        </li>
      `).join("")}
    </ul>
  `;
}


function marketTemplate() {

  return `
    <div class="page-header">
      <div>
        <div class="eyebrow">MARKET TRENDS</div>
        <h1>Market Intelligence</h1>
        <p>
          How your target role is moving, measured against the
          real postings your Job Agent collected for you.
        </p>
      </div>
    </div>

    <div id="marketContent" class="learning-loading">
      <div class="loading-note">
        Reading your market signals…
      </div>
    </div>
  `;
}


async function loadMarketIntelligence() {

  const container =
    document.getElementById("marketContent");

  if (!container) return;

  const twin = await loadTwinData();

  if (!twin) {

    container.className = "";

    container.innerHTML = `
      <div class="panel learning-empty">
        <h3>No Career Twin yet</h3>
        <p>Upload your resume on the
           <a href="#career-twin">Career Twin</a> page.
           Market signals are computed from your profile
           and the postings your agents collect.</p>
      </div>
    `;
    return;
  }

  const state = twin.career_state || {};

  const articles = computeMarketStats(twin);

  const breakdown =
    state.market_alignment_breakdown || {};

  const explanation =
    state.market_alignment_explanation || "";

  const alignment = state.market_alignment;

  const gaugeDegrees = (() => {
    const value = Number(alignment);

    if (!isFinite(value)) return 0;

    return Math.round(
      Math.max(0, Math.min(100, value)) / 100 * 360
    );
  })();

  const firstGap = extractGaps(state)[0];

  container.className = "";

  container.innerHTML = `

    <div class="panel">

      <div class="panel-header">
        <div>
          <h2>Market Alignment</h2>
          <p>Profile fit against the live postings
             collected for your target role.</p>
        </div>
      </div>

      <div class="market-gauge-grid">

        <div class="market-gauge"
             style="background:conic-gradient(#2e86fa 0deg ${gaugeDegrees}deg, #e9eef7 ${gaugeDegrees}deg 360deg)">

          <div class="market-gauge-center">

            <strong>
              ${typeof alignment === "number" ? alignment.toFixed(0) + "%" : "—"}
            </strong>

            <span>Aligned</span>

          </div>

        </div>

        <div>

          ${Object.keys(MARKET_LABELS).length ? `
            ${barRow(
              MARKET_LABELS.role_demand,
              breakdown.role_demand,
              MARKET_COLORS.role_demand
            )}
            ${barRow(
              MARKET_LABELS.skill_demand,
              breakdown.skill_demand,
              MARKET_COLORS.skill_demand
            )}
            ${barRow(
              MARKET_LABELS.profile_market_match,
              breakdown.profile_market_match,
              MARKET_COLORS.profile_market_match
            )}
            ${barRow(
              MARKET_LABELS.location_market_fit,
              breakdown.location_market_fit,
              MARKET_COLORS.location_market_fit
            )}
          ` : ""}

          ${
            explanation
              ? `<p class="market-explanation">${esc(explanation)}</p>`
              : ""
          }

        </div>

      </div>

    </div>

    <div class="mk-stats">

      <div class="mk-stat">

        <div class="mk-stat-value">${articles.jobCount}</div>

        <div class="mk-stat-label">Postings collected</div>

      </div>

      <div class="mk-stat">

        <div class="mk-stat-value">${articles.companyCount}</div>

        <div class="mk-stat-label">Companies hiring</div>

      </div>

      <div class="mk-stat">

        <div class="mk-stat-value">
          ${articles.avgSkillMatch == null ? "—" : articles.avgSkillMatch.toFixed(0) + "%"}
        </div>

        <div class="mk-stat-label">Avg skill match</div>

      </div>

      <div class="mk-stat">

        <div class="mk-stat-value">${articles.sources.length || "—"}</div>

        <div class="mk-stat-label">Job sources live</div>

      </div>

    </div>

    <div class="mk-two-col">

      <section class="panel">

        <div class="panel-header">
          <div>
            <h2>Most Demanded Skills</h2>
            <p>Counted across every posting your agents
               gathered for ${esc((twin.profile || {}).target_role || "your role")}.</p>
          </div>
        </div>

        ${rankListHtml(articles.skills.map(s => ({ skill: s.skill, count: s.count })), "postings")}

        ${
          articles.jobCount
            ? `<p class="sim-disclaimer">Demand here is measured on the postings this account
               collected, so treat it as a sample of the local market - not a census.</p>`
            : ""
        }

      </section>

      <div>

        <section class="panel" style="margin-bottom:16px">

          <div class="panel-header">
            <div>
              <h2>Companies Hiring You</h2>
            </div>
          </div>

          ${rankListHtml(
            articles.companies.map(item => ({
              company: item[0],
              count: item[1]
            })),
            "postings"
          )}

        </section>

        <section class="panel">

          <div class="panel-header">
            <div>
              <h2>Where the Roles Are</h2>
            </div>
          </div>

          ${rankListHtml(
            articles.locations.map(item => ({
              location: item[0],
              count: item[1]
            })),
            "postings"
          )}

        </section>

      </div>

    </div>

    ${
      firstGap
        ? `
          <div class="panel">

            <div class="panel-header">
              <div>
                <h2>Your Biggest Market Lever</h2>
                <p>Closing your top gap moves both
                   skill demand and profile fit.</p>
              </div>
              <a class="small-btn" href="#simulation">
                Run What-If&nbsp; →
              </a>
            </div>

            <p class="market-explanation">
              Learning <strong>${esc(firstGap.skill)}</strong>
              (${esc(firstGap.priority)} priority) is the single
              highest-impact change for your fit against
              these postings.
            </p>

          </div>
        `
        : ""
    }
  `;
}


/* =========================================================
    5. FUTURE SIMULATION PAGE
   =========================================================
   What-if projections, computed in the browser from the
   user's stored readiness breakdown + its weights. Nothing
   is invented: the arithmetic mirrors the backend formula
   readiness = skill_coverage*W + project_evidence*W +
   experience*W + fundamentals*W + education*W.
   ========================================================= */

const FALLBACK_WEIGHTS = {
  skill_coverage: 0.5,
  project_evidence: 0.2,
  experience: 0.1,
  fundamentals: 0.1,
  education: 0.1
};


function projectedReadiness(state, planSkills) {

  const breakdown = state.readiness_breakdown || {};

  const weights = (breakdown && breakdown.weights)
    ? { ...FALLBACK_WEIGHTS, ...breakdown.weights }
    : { ...FALLBACK_WEIGHTS };

  const component = key => {
    const value = Number(breakdown[key]);

    return isFinite(value) ? value : 0;
  };

  const required =
    Number(state.total_required) || 0;

  const matched =
    Number(state.total_matched) || 0;

  let base = 0;

  for (const key of [
    "skill_coverage",
    "project_evidence",
    "experience",
    "fundamentals",
    "education"
  ]) {
    base += component(key) * (Number(weights[key]) || 0);
  }

  base = Math.max(0, Math.min(100, base));

  if (!required) return base;

  const coverageNow = matched / required;

  const coverageAfter = Math.min(
    1,
    (matched + planSkills) / required
  );

  const delta =
    (coverageAfter - coverageNow) *
    100 *
    (Number(weights.skill_coverage) || 0);

  return Math.max(0, Math.min(100, base + delta));
}


function simulationTemplate() {

  return `
    <div class="page-header">
      <div>
        <div class="eyebrow">CAREER PLANNING</div>
        <h1>Future Simulation</h1>
        <p>
          What-if projections built from your actual readiness
          breakdown - see how fast your score moves when you
          close each gap.
        </p>
      </div>
    </div>

    <div id="simulationContent" class="learning-loading">
      <div class="loading-note">
        Projecting your pathway…
      </div>
    </div>
  `;
}


async function loadFutureSimulation() {

  const container = document.getElementById(
    "simulationContent"
  );

  if (!container) return;

  const twin = await loadTwinData();

  if (!twin) {

    container.className = "";

    container.innerHTML = `
      <div class="panel learning-empty">
        <h3>No Career Twin yet</h3>
        <p>Generate your Career Twin first - simulations
           need your readiness breakdown as the starting
           point.</p>
      </div>
    `;
    return;
  }

  const state = twin.career_state || {};

  const required = Number(state.total_required) || 0;

  const gaps = extractGaps(state);

  if (!required || !gaps.length) {

    container.className = "";

    container.innerHTML = `
      <div class="panel learning-empty">
        <h3>Nothing to simulate yet</h3>
        <p>Your twin has no open skill gaps for this role.
           Regenerate it after changing your target role to
           explore a new pathway.</p>
      </div>
    `;
    return;
  }

  const readiness = Number(state.readiness_score);

  const nowScore = isFinite(readiness) ? readiness : projectedReadiness(state, 0);

  const topGap = gaps[0].skill;

  const planTop1 = gaps.slice(0, 1);

  const planTop3 = gaps.slice(0, Math.min(3, gaps.length));

  const planAll = gaps;

  const plans = [
    {
      name: "Close your #1 gap",
      skills: planTop1,
      plan: planTop1.length
    },
    {
      name: "Close the top 3 gaps",
      skills: planTop3,
      plan: planTop3.length
    },
    {
      name: "Close every gap",
      skills: planAll,
      plan: planAll.length
    }
  ];

  const nowPct = nowScore.toFixed(0);

  container.className = "";

  container.innerHTML = `

    <div class="panel">

      <div class="panel-header">
        <div>
          <h2>Where You Stand Now</h2>
          <p>Base readiness: ${nowPct}% ·
             ${Number(state.total_matched) || 0}/${required} required
             skills matched · ${gaps.length} gaps open.</p>
        </div>
      </div>

      <div class="sim-now-comparison">

        <div>

          <div class="sim-tile-label">Readiness now</div>

          <div class="sim-tile-value">${nowPct}%</div>

          <div class="sim-tile-total">
            ${esc((twin.profile || {}).target_role || "your target role")}
          </div>

        </div>

        <div class="sim-arrow">→</div>

        <div>

          <div class="sim-tile-label">After all gaps</div>

          <div class="sim-tile-value">
            ${projectedReadiness(state, planAll.length).toFixed(0)}%
          </div>

          <div class="sim-tile-total">
            full coverage of ${required} required skills
          </div>

        </div>

      </div>

    </div>

    <div class="sim-plan-grid">

      ${plans.map(plan => {

        const projected = projectedReadiness(
          state,
          plan.plan
        );

        const gain = projected - nowScore;

        return `
          <article class="sim-plan">

            <div class="sim-plan-head">
              <h3>${esc(plan.name)}</h3>
            </div>

            <p class="sim-plan-total">
              ${plan.plan} skill${plan.plan === 1 ? "" : "s"} to close
            </p>

            <div class="sim-track">
              <span class="sim-track-base"
                    style="width:${nowScore.toFixed(2)}%"></span>
              <span class="sim-track-fill"
                    style="width:${projected.toFixed(2)}%"></span>
            </div>

            <div class="sim-gain${gain <= 0 ? " flat" : ""}">
              ${
                gain > 0.05
                  ? `+${gain.toFixed(0)} → ${projected.toFixed(0)}% readiness`
                  : `Readiness stays ~${projected.toFixed(0)}% - these gaps sit outside the scoring weights`
              }
            </div>

            <ul class="sim-skills">
              ${plan.skills.map(skill =>
                `<li>${esc(skill.skill)}
                      <small style="color:#8999b3"> · ${esc(skill.priority)}</small>
                </li>`
              ).join("")}
            </ul>

          </article>
        `;
      }).join("")}

    </div>

    <div class="panel">

      <div class="panel-header">
        <div>
          <h2>Turn a Plan Into a Schedule</h2>
          <p>Your learning roadmap orders these skills into
             phases with real courses.</p>
        </div>
        <a class="small-btn" href="#learning">
          Open Roadmap&nbsp; →
        </a>
      </div>

      <p class="sim-disclaimer">
        Projections reuse your stored readiness weights
        (${esc(
          Object.entries(
            ((state.readiness_breakdown || {}).weights || {})
          )
            .filter(([key]) => key !== "weights")
            .map(
              ([key, value]) => `${key.replace(/_/g, " ")} ${Math.round(Number(value) * 100)}%`
            )
            .join(" · ") || "default weights"
        )}).
        They estimate the scoring formula's response to new
        skills - study pace, interviews and market shifts
        aren't modelled.
      </p>

    </div>
  `;
}


/* =========================================================
    6. RECRUITER FEEDBACK PAGE
   =========================================================
   A recruiter's-eye view, built from the twin's strengths,
   weaknesses and readiness breakdown. No backend endpoint
   exists for human recruiter comments yet - this page
   says so instead of faking reviews.
   ========================================================= */

function feedbackTemplate() {

  return `
    <div class="page-header">
      <div>
        <div class="eyebrow">EXTERNAL PERSPECTIVE</div>
        <h1>Recruiter Feedback</h1>
        <p>
          How your profile reads to a recruiter today, and the
          fastest ways to make it stronger.
        </p>
      </div>
    </div>

    <div id="feedbackContent" class="learning-loading">
      <div class="loading-note">
        Reviewing your profile from a recruiter's lens…
      </div>
    </div>
  `;
}


function lowestComponent(breakdown) {

  const names = {
    skill_coverage: "role-required skills",
    project_evidence: "project evidence",
    experience: "work experience",
    fundamentals: "CS fundamentals",
    education: "formal education"
  };

  let worst = null;

  for (const [key, label] of Object.entries(names)) {

    const value = Number(breakdown[key]);

    if (!isFinite(value)) continue;

    if (!worst || value < worst.value) {
      worst = { key, label, value };
    }
  }

  return worst;
}


async function loadRecruiterFeedback() {

  const container = document.getElementById(
    "feedbackContent"
  );

  if (!container) return;

  const twin = await loadTwinData();

  if (!twin) {

    container.className = "";

    container.innerHTML = `
      <div class="panel learning-empty">
        <h3>No Career Twin yet</h3>
        <p>Recruiter feedback is generated from your
           profile - upload your resume first.</p>
      </div>
    `;
    return;
  }

  const state = twin.career_state || {};

  const profile = twin.profile || {};

  const readiness = state.readiness_score;

  const market = state.market_alignment;

  const strengths = (state.strengths || []).slice(0, 5);

  const weaknesses =
    (state.weaknesses && state.weaknesses.length
      ? state.weaknesses
      : extractGaps(state)
          .filter(gap => gap.priority === "High")
          .map(gap => gap.skill)
    ).slice(0, 5);

  const worst = lowestComponent(
    state.readiness_breakdown || {}
  );

  const projects = twin.projects || [];

  const insights = [];

  for (const skill of strengths) {
    insights.push({
      className: "good",
      tag: "Strength",
      title: `${skill} matches your target role`,
      body: `A recruiter scanning for
             ${profile.target_role || "this role"}-specific
             skills will notice ${skill} immediately. Keep it
             visible at the top of your resume.`
    });
  }

  if (worst && worst.value < 50) {
    insights.push({
      className: "warn",
      tag: "Watch out",
      title: `${worst.label} is your weakest readiness signal`,
      body: `This component scores ${worst.value.toFixed(0)}%.
             Recruiters weight exactly this area when they
             shortlist - a concrete, shipped project or a
             certificate closes it fastest.`
    });
  }

  for (const skill of weaknesses) {
    insights.push({
      className: "warn",
      tag: "Gap",
      title: `${skill} is absent from your profile`,
      body: `It appears in role requirements for
             ${profile.target_role || "your target role"}.
             Recruiters filter hard on it - either learn it
             or show adjacent proof in your projects.`
    });
  }

  if (projects.length) {
    insights.push({
      className: "good",
      tag: "Asset",
      title: `${projects.length} project${projects.length === 1 ? "" : "s"} show you build, not just study`,
      body: `Lead with "${(String(projects[0]).split(":")[0] || "your project").trim()}"`
        + ` - specific, working systems are how you pass`
        + ` the first human glance.`
    });
  }

  container.className = "";

  container.innerHTML = `

    <div class="panel">

      <div class="panel-header">
        <div>
          <h2>The 10-Second Glance</h2>
          <p>What a recruiter's first pass sees for
             ${esc(profile.target_role || "your profile")}.</p>
        </div>
      </div>

      <div class="twin-scores">

        <div class="twin-score-card">
          <div class="twin-score-num">
            ${typeof readiness === "number" ? readiness.toFixed(0) + "%" : "—"}
          </div>
          <div class="twin-score-cap">Readiness signal</div>
        </div>

        <div class="twin-score-card">
          <div class="twin-score-num">
            ${typeof market === "number" ? market.toFixed(0) + "%" : "—"}
          </div>
          <div class="twin-score-cap">Market fit signal</div>
        </div>

        <div class="twin-score-card">
          <div class="twin-score-num">
            ${(state.total_matched == null) ? "—" : state.total_matched}
          </div>
          <div class="twin-score-cap">Role skills proven</div>
        </div>

        <div class="twin-score-card">
          <div class="twin-score-num">
            ${(state.total_missing == null) ? "—" : state.total_missing}
          </div>
          <div class="twin-score-cap">Requirements unmet</div>
        </div>

      </div>

    </div>

    <div class="panel">

      <div class="panel-header">
        <div>
          <h2>What a Recruiter Would Flag</h2>
          <p>Generated from your stored strengths, gaps and
             readiness breakdown.</p>
        </div>
      </div>

      ${
        insights.length
          ? `<div class="fb-list">
              ${insights.map(item => `
                <div class="fb-item ${item.className}">
                  <div class="fb-icon">
                    ${item.className === "good" ? "✓" : "!"}
                  </div>
                  <div class="fb-body">
                    <h4>${esc(item.title)}
                        <span class="fb-tag ${item.className === "good" ? "pos" : "risk"}">
                          ${esc(item.tag)}
                        </span>
                    </h4>
                    <p>${esc(item.body)}</p>
                  </div>
                </div>
              `).join("")}
             </div>`
          : `<p class="empty-line">
               Not enough profile data to critique yet.
             </p>`
      }

    </div>

    <div class="panel learning-note">

      <strong>About human recruiter comments</strong>

      <p>
        Direct recruiter reviews aren't connected yet, so
        nothing here is invented - each point above is
        derived from the skill gap agent's scoring of your
        actual resume.
      </p>

    </div>
  `;
}


/* =========================================================
    7. SETTINGS PAGE
   =========================================================
   Account + career preferences (persisted to MongoDB via
   POST /preferences) + browser-only toggles.
   ========================================================= */

const SETTINGS_STORE_KEY = "cdt_app_settings";


function defaultSettings() {

  return {
    notifications: true,
    profileVisible: true,
    compactMode: false
  };
}


function readSettings() {

  try {

    const saved = JSON.parse(
      localStorage.getItem(SETTINGS_STORE_KEY)
    );

    return {
      ...defaultSettings(),
      ...(saved || {})
    };

  } catch (e) {

    return defaultSettings();
  }
}


function writeSettings(settings) {

  localStorage.setItem(
    SETTINGS_STORE_KEY,
    JSON.stringify(settings)
  );
}


function settingsTemplate() {

  return `
    <div class="page-header">
      <div>
        <div class="eyebrow">PREFERENCES</div>
        <h1>Settings</h1>
        <p>
          Manage your account, career preferences, and how
          the app behaves in this browser.
        </p>
      </div>
    </div>

    <div class="panel">

      <div class="panel-header">
        <div>
          <h2>Account</h2>
        </div>
      </div>

      <div class="settings-account">

        <div class="settings-avatar" id="settingsAvatar">
          A
        </div>

        <div class="settings-account-info">
          <h3 id="settingsName">Account</h3>
          <p id="settingsEmail">email</p>
        </div>

        <div class="settings-account-actions">
          <a class="small-btn" href="#career-twin">Profile & Twin →</a>
          <button class="secondary-btn" data-action="logout">
            Sign out
          </button>
        </div>

      </div>

    </div>

    <div class="panel">

      <div class="panel-header">
        <div>
          <h2>Career Preferences</h2>
          <p>Used by the Job Agent and Market Alignment
             whenever your Career Twin is regenerated.</p>
        </div>
      </div>

      <div class="form-grid">

        <div class="form-group">
          <label for="pref-target-role">Target Role</label>
          <input id="preference-target-role" type="text" placeholder="AI Engineer">
        </div>

        <div class="form-group">
          <label for="pref-location">Preferred Location</label>
          <input id="preference-location" type="text" placeholder="Hyderabad">
        </div>

        <div class="form-group">
          <label for="pref-work-mode">Work Mode</label>
          <select id="workMode">
            <option value="">Select Work Mode</option>
            <option value="Remote">Remote</option>
            <option value="Hybrid">Hybrid</option>
            <option value="On-site">On-site</option>
          </select>
        </div>

        <div class="form-group">
          <label for="pref-employment">Employment Type</label>
          <select id="preference-employment-type">
            <option value="">Select Employment Type</option>
            <option value="Full-time">Full-time</option>
            <option value="Part-time">Part-time</option>
            <option value="Contract">Contract</option>
          </select>
        </div>

        <div class="form-group">
          <label for="pref-salary">Expected Salary</label>
          <input id="preference-salary" type="text" placeholder="10-15 LPA">
        </div>

        <div class="form-group">
          <label for="pref-industry">Preferred Industry</label>
          <input id="preference-industry" type="text" placeholder="Artificial Intelligence">
        </div>

        <div class="form-group">
          <label for="pref-experience">Experience Level</label>
          <select id="preference-experience">
            <option value="">Select Experience Level</option>
            <option value="Entry Level">Entry Level</option>
            <option value="Mid Level">Mid Level</option>
            <option value="Senior Level">Senior Level</option>
          </select>
        </div>

        <div class="form-group">
          <label>
            <input id="preference-relocation" type="checkbox">
            Willing to relocate
          </label>
        </div>

      </div>

      <p class="settings-note">
        Preferences are saved to MongoDB and applied the next
        time your Career Twin is regenerated - re-upload your
        resume on the <a href="#career-twin">Career Twin page</a>
        to re-run the agents with them.
      </p>

      <button id="save-preferences" class="primary-btn" style="margin-top:16px">
        Save Preferences
      </button>

    </div>

    <div class="panel">

      <div class="panel-header">
        <div>
          <h2>App Preferences</h2>
          <p>Stored only in this browser - not sent to the
             backend.</p>
        </div>
      </div>

      <div class="toggles">

        <div class="toggle-row">

          <div class="toggle-row-text">
            <h4>Progress notifications</h4>
            <p>Toast updates when a twin or roadmap refreshes.</p>
          </div>

          <label class="toggle">
            <input type="checkbox" id="setting-notifications" data-setting="notifications">
            <span class="toggle-track"></span>
          </label>

        </div>

        <div class="toggle-row">

          <div class="toggle-row-text">
            <h4>Compact cards</h4>
            <p>Fit more rows of the job and roadmap lists on screen.</p>
          </div>

          <label class="toggle">
            <input type="checkbox" id="setting-compactMode" data-setting="compactMode">
            <span class="toggle-track"></span>
          </label>

        </div>

      </div>

    </div>
  `;
}


async function loadSettings() {

  const user = getAuthUser();

  const nameEl = document.getElementById("settingsName");

  const emailEl = document.getElementById("settingsEmail");

  const avatarEl = document.getElementById(
    "settingsAvatar"
  );

  if (nameEl) {
    nameEl.textContent =
      (user && (user.name || user.email)) || "Account";
  }

  if (emailEl) {
    emailEl.textContent = (user && user.email) || "";
  }

  if (avatarEl) {
    avatarEl.textContent = user && user.name
      ? user.name.trim().charAt(0).toUpperCase()
      : "A";
  }

  /* Prefill saved career preferences from the twin. */

  const twin = await loadTwinData();

  const preferences =
    (twin && twin.preferences) ||
    getCareerProfile();

  const fields = {
    "preference-target-role":
      preferences.target_role,
    "preference-location":
      preferences.location,
    "preference-salary":
      preferences.salary_expectation,
    "preference-industry":
      preferences.preferred_industry,
    "preference-experience":
      preferences.experience_level,
    "workMode":
      preferences.work_mode,
    "preference-employment-type":
      preferences.employment_type
  };

  for (const [id, value] of Object.entries(fields)) {

    const element = document.getElementById(id);

    if (!element) continue;

    if (typeof value === "string" && value) {
      element.value = value;
    }
  }

  const relocation =
    document.getElementById("preference-relocation");

  if (relocation) {
    relocation.checked = Boolean(
      preferences.relocation
    );
  }

  /* Browser-only toggles. */

  const settings = readSettings();

  document
    .querySelectorAll("[data-setting]")
    .forEach(toggle => {

      const key = toggle.dataset.setting;

      toggle.checked = Boolean(settings[key]);

      toggle.addEventListener("change", () => {

        settings[key] = toggle.checked;

        writeSettings(settings);

        document.body.classList.toggle(
          "compact-mode",
          Boolean(settings.compactMode)
        );
      });
    });
}

function renderRoute() {

  /* -----------------------------------------
     AUTH GATE - do nothing until logged in
     ----------------------------------------- */

  if (!getAuthToken()) {

    showAuthScreen();

    return;
  }

  hideAuthScreen();

  const routeName =
    currentRoute();


  page.innerHTML =
    routeName === "dashboard"

      ? dashboardTemplate()

      : routeName === "career-twin"

        ? careerTwinTemplate()

        : routeName === "skills"

          ? skillsTemplate()

          : routeName === "jobs"

            ? jobsTemplate()

            : routeName === "learning" ||
              routeName === "roadmap"

              ? learningTemplate()

              : routeName === "market"

                ? marketTemplate()

                : routeName === "simulation"

                  ? simulationTemplate()

                  : routeName === "feedback"

                    ? feedbackTemplate()

                    : routeName === "settings"

                      ? settingsTemplate()

                      : placeholderTemplate(
                          routeName
                        );


  /* -----------------------------------------
     ACTIVE SIDEBAR ITEM
     ----------------------------------------- */

  document
    .querySelectorAll(".nav-item")
    .forEach(item => {

      item.classList.toggle(
        "active",
        item.dataset.route === routeName
      );

    });


  /* -----------------------------------------
     BIND PAGE EVENTS
     ----------------------------------------- */

  bindDynamicActions();


  /* -----------------------------------------
     PAGE DATA LOADERS (FastAPI-backed)
     ----------------------------------------- */

  if (routeName === "dashboard") {

    loadDashboard();
  }


  /* -----------------------------------------
     AGENT 5 - LOAD ROADMAP
     ----------------------------------------- */

  if (
    routeName === "learning" ||
    routeName === "roadmap"
  ) {

    loadLearningRoadmap();
  }


  /* -----------------------------------------
     CAREER TWIN - RESUME UPLOAD + STATUS
     ----------------------------------------- */

  if (routeName === "career-twin") {

    bindResumeUpload();

    refreshTwinStatus();

    loadTwinDetails();
  }


  /* -----------------------------------------
     SKILL GAP ANALYSIS - REAL DATA
     ----------------------------------------- */

  if (routeName === "skills") {

    loadSkillAnalysis();
  }


  /* -----------------------------------------
     JOB OPPORTUNITIES - REAL DATA
     ----------------------------------------- */

  if (routeName === "jobs") {

    loadJobOpportunities();
  }


  /* -----------------------------------------
     MARKET / SIMULATION / FEEDBACK / SETTINGS
     ----------------------------------------- */

  if (routeName === "market") {

    loadMarketIntelligence();
  }

  if (routeName === "simulation") {

    loadFutureSimulation();
  }

  if (routeName === "feedback") {

    loadRecruiterFeedback();
  }

  if (routeName === "settings") {

    loadSettings();
  }


  /* -----------------------------------------
     CLOSE MOBILE SIDEBAR
     ----------------------------------------- */

  closeMobileSidebar();

}


/* =========================================================
   NAVIGATION
   ========================================================= */

window.addEventListener(
  "hashchange",
  renderRoute
);


/* =========================================================
   MOBILE MENU
   ========================================================= */

if (mobileMenuBtn) {

  mobileMenuBtn.addEventListener(
    "click",
    () => {

      sidebar.classList.add("open");

      mobileBackdrop.classList.add(
        "open"
      );

    }
  );

}


if (mobileBackdrop) {

  mobileBackdrop.addEventListener(
    "click",
    closeMobileSidebar
  );

}


/* =========================================================
   PROFILE MENU
   ========================================================= */

if (profileTrigger) {

  profileTrigger.addEventListener(
    "click",
    event => {

      event.stopPropagation();

      profileMenu.classList.toggle(
        "open"
      );

    }
  );

}


document.addEventListener(
  "click",
  event => {

    if (
      profileMenu &&
      !profileMenu.contains(event.target) &&
      !profileTrigger.contains(event.target)
    ) {

      profileMenu.classList.remove(
        "open"
      );

    }

  }
);


/* =========================================================
   COPILOT
   ========================================================= */

document
  .querySelectorAll(
    '[data-action="open-copilot"]'
  )
  .forEach(button => {

    button.addEventListener(
      "click",
      openCopilot
    );

  });


if (closeCopilot) {

  closeCopilot.addEventListener(
    "click",
    closeCopilotDialog
  );

}


if (copilotOverlay) {

  copilotOverlay.addEventListener(
    "click",
    event => {

      if (
        event.target === copilotOverlay
      ) {

        closeCopilotDialog();

      }

    }
  );

}


/* =========================================================
   COPILOT CHAT
   ========================================================= */

if (chatForm) {

  chatForm.addEventListener(
    "submit",
    event => {

      event.preventDefault();


      const question =
        chatInput.value.trim();


      if (!question) {
        return;
      }


      /* User message */

      const userMessage =
        document.createElement(
          "div"
        );

      userMessage.className =
        "message user";

      userMessage.textContent =
        question;


      chatMessages.appendChild(
        userMessage
      );


      chatInput.value = "";


      /* Temporary AI response */

      setTimeout(() => {

        const aiMessage =
          document.createElement(
            "div"
          );

        aiMessage.className =
          "message";

        aiMessage.textContent =
          "I can help you analyze your career profile, skills, learning path, jobs, and future career decisions.";

        chatMessages.appendChild(
          aiMessage
        );


        chatMessages.scrollTop =
          chatMessages.scrollHeight;

      }, 500);

    }
  );

}


/* =========================================================
   GLOBAL SEARCH
   ========================================================= */

const searchForm =
  document.getElementById(
    "searchForm"
  );

const globalSearch =
  document.getElementById(
    "globalSearch"
  );


if (searchForm) {

  searchForm.addEventListener(
    "submit",
    event => {

      event.preventDefault();


      const query =
        globalSearch.value.trim();


      if (!query) {

        showToast(
          "Type something to search."
        );

        return;

      }


      showToast(
        `Searching for "${query}"...`
      );

    }
  );

}


/* =========================================================
   NOTIFICATIONS
   ========================================================= */

const notificationBtn =
  document.getElementById(
    "notificationBtn"
  );


if (notificationBtn) {

  notificationBtn.addEventListener(
    "click",
    () => {

      showToast(
        "You have no new notifications."
      );

    }
  );

}


/* =========================================================
   SIGN OUT
   ========================================================= */

document.addEventListener(
  "click",
  event => {

    const logoutButton =
      event.target.closest('[data-action="logout"]');

    if (logoutButton) {

      event.preventDefault();

      logout();

      if (profileMenu) {
        profileMenu.classList.remove("open");
      }

      return;
    }

  }
);


/* =========================================================
   PROFILE NAME (show the logged-in user in the top bar)
   ========================================================= */

function updateProfileChrome() {

  const nameEl = document.getElementById("profileName");

  const avatarEl = document.getElementById("profileAvatar");

  const user = getAuthUser();

  if (nameEl) {

    nameEl.textContent =
      (user && (user.name || user.email)) || "Account";
  }

  if (avatarEl && user && user.name) {

    avatarEl.textContent =
      user.name.trim().charAt(0).toUpperCase() || "👤";
  }
}

// ========================================
// EXISTING CODE
// ========================================

// routes
// dashboardTemplate()
// careerTwinTemplate()
// placeholderTemplate()
// renderRoute()
// etc.


// ========================================
// SAVE PREFERENCES
// ========================================

async function savePreferences() {

    try {

        const preferences = {

            location:
                document.getElementById("preference-location").value,

            work_mode:
                document.getElementById("preference-work-mode").value,

            employment_type:
                document.getElementById("preference-employment-type").value,

            salary_expectation:
                document.getElementById("preference-salary").value,

            relocation:
                document.getElementById("preference-relocation").checked,

            preferred_industry:
                document.getElementById("preference-industry").value,

            experience_level:
                document.getElementById("preference-experience").value
        };


        const response = await apiFetch(
            "/preferences",
            {
                method: "POST",

                body: JSON.stringify(preferences)
            }
        );


        if (!response.ok) {
            throw new Error("Failed to save preferences");
        }


        const data = await response.json();


        console.log(data);


        alert("Preferences saved successfully!");


    } catch (error) {

        console.error(error);

        alert("Failed to save preferences.");

    }
}


// ========================================
// EXISTING CODE CONTINUES
// ========================================


/* =========================================================
   INITIAL PAGE LOAD
   =========================================================
   1. Wire up the login/register form.
   2. If a token is already stored, verify it is still valid.
   3. Render the app only once a session is confirmed.
   ========================================================= */

initAuthScreen();


(async function startApp() {

  const token = getAuthToken();

  if (!token) {

    showAuthScreen();

    return;
  }

  // Confirm the stored token is still valid.
  try {

    const response = await fetch(`${API_BASE}/auth/me`, {

      headers: { Authorization: `Bearer ${token}` }
    });

    if (response.ok) {

      const user = await response.json();

      // Refresh the cached user details.
      setAuthSession(token, user);

      hideAuthScreen();

      renderRoute();

      return;
    }

  } catch (e) {

    // Backend unreachable - fall through to login.
  }

  clearAuthSession();

  showAuthScreen();

})();
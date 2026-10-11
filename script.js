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
              Good Morning, Priya!
            </h1>

            <p>
              Here's your personalized career intelligence dashboard.
            </p>

          </div>

        </div>

        <div class="date">
          Today, 9 Sep 2026
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

            <div class="metric-value">
              B.Tech Computer Science
            </div>

            <div class="metric-subtitle">
              Final Year Student
            </div>

            <span class="status-pill blue">
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

            <div class="metric-value">
              ${profile.target_role}
            </div>

            <div class="metric-subtitle">
              Target Career
            </div>

            <span class="status-pill">
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

            <div class="metric-value">
              68%
            </div>

            <div class="progress">
              <span></span>
            </div>

            <div class="metric-note">
              +12% since last month
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

            <div class="metric-value">
              AWS
            </div>

            <div class="metric-subtitle">
              High Demand&nbsp; • &nbsp;92% growth
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

                <div class="large-avatar">
                  👩🏻
                </div>

                <div>

                  <h3>
                    Priya Sharma
                  </h3>

                  <p>
                    B.Tech Computer Science
                  </p>

                  <p>
                    Final Year Student
                  </p>

                </div>

              </div>


              <div class="profile-facts">

                <div class="fact-card">

                  <div class="fact-title">
                    <span>♧</span>
                    Current Skills
                  </div>

                  <div class="fact-value">
                    12
                  </div>

                  <div class="fact-note">
                    e.g. Python, Java, SQL...
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

                <div class="donut">

                  <div class="donut-center">

                    <strong>
                      68%
                    </strong>

                    <span>
                      Match Score
                    </span>

                  </div>

                </div>


                <div class="skill-columns">

                  <div class="skill-column">

                    <h4>
                      Your Skills
                    </h4>

                    <ul class="skill-list">

                      <li>
                        <span class="check">
                          ✓
                        </span>
                        Python
                      </li>

                      <li>
                        <span class="check">
                          ✓
                        </span>
                        Machine Learning
                      </li>

                      <li>
                        <span class="check">
                          ✓
                        </span>
                        SQL
                      </li>

                      <li>
                        <span class="check">
                          ✓
                        </span>
                        Java
                      </li>

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

                    <ul class="skill-list">

                      <li>
                        <span class="missing-icon">
                          !
                        </span>
                        AWS
                      </li>

                      <li>
                        <span class="missing-icon">
                          !
                        </span>
                        Docker
                      </li>

                      <li>
                        <span class="missing-icon">
                          !
                        </span>
                        Kubernetes
                      </li>

                      <li>
                        <span class="missing-icon">
                          !
                        </span>
                        MLOps
                      </li>

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

                <article
                  class="job-card"
                  data-search="ai engineer google bangalore remote"
                >

                  <div class="company-logo">
                    G
                  </div>

                  <div>

                    <div class="job-title">
                      AI Engineer
                    </div>

                    <div class="job-company">
                      Google
                    </div>

                  </div>

                </article>


                <article
                  class="job-card"
                  data-search="machine learning engineer microsoft"
                >

                  <div class="company-logo">
                    M
                  </div>

                  <div>

                    <div class="job-title">
                      Machine Learning Engineer
                    </div>

                    <div class="job-company">
                      Microsoft
                    </div>

                  </div>

                </article>


              </div>

            </section>

          </div>

        </div>

      </section>

    </div>

  `;
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
                    Build your personalized career profile and define
                    your career preferences.
                </p>
            </div>
        </div>

        <div class="card">

            <h2>Career Preferences</h2>

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
    `;
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
     JOB CARDS
     ----------------------------------------- */

  document
    .querySelectorAll(".job-card")
    .forEach(card => {

      card.addEventListener("click", () => {

        showToast(
          "Job details are ready to connect to your job API."
        );

      });

    });


  /* -----------------------------------------
     SAVE CAREER PREFERENCES
     ----------------------------------------- */

  const savePreferencesButton =
    document.getElementById("save-preferences");


  console.log(
    "Save button found:",
    savePreferencesButton
  );


  if (!savePreferencesButton) {
    console.error(
      "ERROR: savePreferences button not found!"
    );

    return;
  }


  savePreferencesButton.addEventListener(
    "click",
    async function () {

      console.log(
        "Save Preferences button clicked"
      );


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


      console.log(
        "Collected preferences:",
        preferences
      );


      /* -----------------------------------------
         SAVE TO LOCAL STORAGE
         ----------------------------------------- */

      localStorage.setItem(
        "careerPreferences",
        JSON.stringify(preferences)
      );


      console.log(
        "Saved to localStorage:",
        localStorage.getItem(
          "careerPreferences"
        )
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
          await fetch(
            "http://127.0.0.1:8000/preferences",
            {
              method: "POST",

              headers: {
                "Content-Type":
                  "application/json"
              },

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


        console.log(
          "Backend response:",
          data
        );


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
   RENDER ROUTE
   ========================================================= */

function renderRoute() {

  const routeName =
    currentRoute();


  page.innerHTML =
    routeName === "dashboard"

      ? dashboardTemplate()

      : routeName === "career-twin"

        ? careerTwinTemplate()

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
   SIGN OUT / OTHER ACTIONS
   ========================================================= */

document.addEventListener(
  "click",
  event => {

    const actionElement =
      event.target.closest(
        '[data-action="show-toast"]'
      );


    if (!actionElement) {
      return;
    }


    showToast(
      "Sign out functionality will be connected to your authentication API."
    );

  }
);

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


        const response = await fetch(
            "http://127.0.0.1:8000/preferences",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

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
   ========================================================= */

renderRoute();
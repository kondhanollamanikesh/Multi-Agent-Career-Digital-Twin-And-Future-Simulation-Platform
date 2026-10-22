/* Headless smoke test for script.js.
 *
 * Runs the real frontend code against a stub DOM and a stub
 * fetch that answers with data in the EXACT shape MongoDB was
 * observed to hold, then invokes every page loader.
 */

"use strict";

const fs = require("fs");

const path = require("path");

/* -----------------------------------------
   Real-shaped fixtures (from live MongoDB)
   ----------------------------------------- */

const REAL_TWIN = {
  user_id: "6acb557019d5b4d6a00fae69",

  profile: {
    target_role: "Software Engineer",
    experience_level: "Entry Level",
    location: ""
  },

  education: [
    "B.Tech – Computer Science and Engineering | TKR College of Engineering and Technology, Hyderabad | 2023 – Present | Pursuing",
    "Intermediate – MPC | Sri Chaitanya Junior College, Hyderabad | 2021 – 2023 | 94.4%"
  ],

  skills: [
    "Python", "Java", "SQL", "Machine Learning",
    "Deep Learning", "Natural Language Processing",
    "LLMs", "LangChain", "LangGraph", "RAG",
    "Git", "Docker", "FastAPI", "MongoDB",
    "Problem Solving"
  ],

  projects: [
    "Multi-Agent Career Digital Twin & Future Simulation Platform: Developing an AI-powered career platform.",
    "AI Technical Chatbot: Built an AI-powered technical chatbot using LLMs."
  ],

  experience: [],

  certifications: [
    "Completed Introduction to Generative AI (MDL-388) completion certificate on 27 August 2025."
  ],

  achievements: [
    "Solved 180+ Data Structures and Algorithms problems across LeetCode and GeeksforGeeks."
  ],

  target_roles: ["AI Engineer", "Software Engineer"],

  preferences: {
    target_role: "Software Engineer",
    location: "Hyderabad",
    work_mode: "Hybrid",
    employment_type: "Full-time",
    salary_expectation: "10-15 LPA",
    relocation: true,
    preferred_industry: "Artificial Intelligence",
    experience_level: "Entry Level"
  },

  career_state: {
    readiness_score: 63.28,

    readiness_breakdown: {
      skill_coverage: 55.56,
      project_evidence: 100.0,
      experience: 55.0,
      fundamentals: 0.0,
      education: 100.0,
      weights: {
        skill_coverage: 0.5,
        project_evidence: 0.2,
        experience: 0.1,
        fundamentals: 0.1,
        education: 0.1
      }
    },

    market_alignment: 44.33,

    market_alignment_breakdown: {
      role_demand: 100.0,
      skill_demand: 12.0,
      profile_market_match: 30.27,
      location_market_fit: null,
      weights: {
        role_demand: 0.25,
        skill_demand: 0.3,
        profile_market_match: 0.3,
        location_market_fit: 0.15
      }
    },

    market_alignment_explanation:
      "Role demand is strong for Software Engineer postings, but your skill demand signals are limited because few postings list skills you already have.",

    strengths: ["Python", "Git", "Problem Solving"],

    weaknesses: [],

    skill_gaps: [
      "Strong understanding of data structures",
      "Ability to write clean, testable code",
      "Familiarity with agile methodologies"
    ],

    prioritized_gaps: [
      {
        skill: "Data Structures and Algorithms",
        priority: "High",
        importance: "Core requirement for the role",
        learning_suggestion: "Grind 150 LeetCode problems"
      },
      {
        skill: "Unit Testing",
        priority: "Medium",
        importance: "Nice-to-have for the role",
        learning_suggestion: "Learn pytest basics"
      },
      {
        skill: "Agile Methodology",
        priority: "Low",
        importance: "Optional",
        learning_suggestion: "Read the Scrum guide"
      }
    ],

    total_required: 9,
    total_matched: 5,
    total_missing: 3,
    total_partial: 1,
    strict_coverage: 55.56
  },

  job_opportunities: [
    {
      title: "Software Developer",
      company: "Babcock Power APAC Pvt. Ltd.",
      location: "India",
      work_mode: "Unknown",
      salary_min: null,
      salary_max: null,
      source: "Adzuna",
      url: "https://www.adzuna.in/details/5855383520",
      matched_skills: ["SQL", "Python"],
      missing_skills: ["Django"],
      skill_match_pct: 66.7,
      job_score: 81.2
    },
    {
      title: "Full Stack Engineer (AI Tools)",
      company: "Zoho Corporation",
      location: "Chennai, Tamil Nadu",
      work_mode: "Hybrid",
      salary_min: 600000,
      salary_max: 1200000,
      source: "Jooble",
      url: "https://www.jooble.org/jdp/123",
      matched_skills: ["Python", "JavaScript", "Git"],
      missing_skills: [],
      skill_match_pct: 88.1,
      job_score: 87.5
    },
    {
      title: "Junior Software Engineer",
      company: "Babcock Power APAC Pvt. Ltd.",
      location: "Hyderabad",
      work_mode: "On-site",
      salary_min: null,
      salary_max: null,
      source: "Jobicy",
      url: "https://example.com/3",
      matched_skills: ["Python"],
      missing_skills: ["React"],
      skill_match_pct: 44.0,
      job_score: 70.1
    }
  ],

  learning_history: [],

  twin_version: 2
};

const REAL_ROADMAP = {
  success: true,
  target_role: "Software Engineer",
  roadmap: {
    summary: {
      target_role: "Software Engineer",
      total_phases: 2,
      total_skills: 3,
      estimated_weeks: 12,
      high_priority: 1,
      medium_priority: 1,
      low_priority: 1,
      total_estimated_hours: 140,
      completed_skills: 0,
      progress_percent: 0
    },
    phases: [
      {
        title: "Phase 1 – Core foundations",
        suggested_duration: "6-8 weeks",
        priority: "High",
        skills: [
          {
            skill: "Data Structures and Algorithms",
            importance: "Core requirement for the role",
            status: "not_started",
            practical_task: "Solve 20 array problems",
            status_score: null,
            resources: {
              youtube_resources: [
                {
                  title: "DSA Full Course",
                  channel: "CodeHelp",
                  duration_text: "9:59:41",
                  relevance_score: "94.2%",
                  url: "https://youtube.com/xyz",
                  thumbnail: "https://i.ytimg.com/vi/xyz/hqdefault.jpg"
                }
              ],
              documentation: {
                url: "https://wiki.python.org",
                description: "Official Python docs",
                verified: true
              },
              platform_links: [
                { platform: "Coursera", url: "https://coursera.org/search?query=dsa" },
                { platform: "edX", url: "https://edx.org/search?q=dsa" }
              ]
            }
          }
        ]
      },
      {
        title: "Phase 2 – Supporting skills",
        suggested_duration: "4-6 weeks",
        priority: "Medium",
        skills: [
          {
            skill: "Unit Testing",
            importance: "Nice-to-have",
            status: "in_progress",
            practical_task: "Write pytest suite",
            resources: {
              youtube_resources: [],
              documentation: null,
              platform_links: [
                { platform: "Udemy", url: "https://udemy.com/search/?q=pytest" }
              ]
            }
          }
        ]
      }
    ]
  }
};

/* -----------------------------------------
   Stub DOM
   ----------------------------------------- */

function makeElement(tag) {

  const element = {
    tagName: tag || "div",
    textContent: "",
    innerHTML: "",
    value: "",
    checked: false,
    hidden: false,
    disabled: false,
    dataset: {},
    style: {},
    classList: {
      add() {},
      remove() {},
      toggle() {},
      contains() { return false; }
    },
    addEventListener() {},
    removeEventListener() {},
    appendChild() {},
    querySelector() { return null; },
    querySelectorAll() { return []; },
    closest() { return null; },
    getAttribute() { return ""; },
    focus() {},
    scrollTop: 0,
    scrollHeight: 0
  };

  return element;
}

const elements = new Map();

const originalGetElementById = () => null;

global.document = {
  getElementById(id) {

    if (!elements.has(id)) {
      elements.set(id, makeElement());
    }

    return elements.get(id);
  },

  querySelectorAll() { return []; },

  querySelector() { return null; },

  addEventListener() {},

  createElement(tag) { return makeElement(tag); },

  body: makeElement("body"),

  forms: []
};

global.window = {
  addEventListener() {},
  location: {
    hash: "#dashboard",

    replace(value) {
      this.hash = value;
    }
  },

  confirm() { return true; },
  prompt() { return "75"; }
};

global.location = global.window.location;

const storage = new Map();

global.localStorage = {
  getItem(key) { return storage.get(key) || null; },

  setItem(key, value) { storage.set(key, String(value)); },

  removeItem(key) { storage.delete(key); }
};

global.fetch = async (url, options) => {

  const response = spec => ({
    ok: spec.ok !== false,
    status: spec.status || 200,
    json: async () => spec.body,
    text: async () => JSON.stringify(spec.body)
  });

  if (String(url).includes("/auth/me")) {
    return response({
      body: {
        user_id: "6acb557019d5b4d6a00fae69",
        email: "kondhanollamanikesh@gmail.com",
        name: "Manikesh"
      }
    });
  }

  if (String(url).includes("/career-twin/status")) {
    return response({

      body: {
        has_twin: true,
        target_role: "Software Engineer",
        skill_count: REAL_TWIN.skills.length,
        readiness_score: 63.28,
        market_alignment: 44.33,
        message: "Career Twin is ready."
      }
    });
  }

  if (String(url).includes("/career-twin")) {
    return response({
      body: {
        has_twin: true,
        career_twin: REAL_TWIN
      }
    });
  }

  if (String(url).includes("/learning-roadmap")) {
    return response({ body: REAL_ROADMAP });
  }

  return response({
    ok: false,
    status: 404,
    body: { detail: "stub 404" }
  });
};

/* Values the loaders read from localStorage. */

storage.set(
  "cdt_token",
  "stub-token"
);

storage.set(
  "cdt_user",
  JSON.stringify({
    name: "Manikesh",
    email: "kondhanollamanikesh@gmail.com"
  })
);

storage.set(
  "careerPreferences",
  JSON.stringify({
    target_role: "Software Engineer",
    location: "Hyderabad",
    employment_type: "Full-time",
    preferred_industry: "Artificial Intelligence",
    relocation: true,
    work_mode: "Hybrid"
  })
);

/* -----------------------------------------
   Load the real frontend code
   ----------------------------------------- */

const source = fs.readFileSync(
  path.join(__dirname, "..", "script.js"),
  "utf8"
);

/* script.js references document inside the IIFE startApp in a
   try-tolerant way; declarations are top level so evaluating in
   this scope is enough. Use an indirect eval to expose its
   function declarations. */

const api = require("vm");

const context = api.createContext({
  document: global.document,
  window: global.window,
  location: global.window.location,
  localStorage: global.localStorage,
  fetch: global.fetch,
  console,
  setTimeout,

  FormData: class FormData {
    append() {}
  },

  JSON,
  Object,
  Array,
  Number,
  Math,
  Date,
  String,
  Boolean,
  Map,
  Set,
  Promise,
  Error
});

api.runInContext(source, context);

async function testPageLoader(id, loaderKey) {

  const container = global.document.getElementById(id);

  await context[loaderKey]();

  const html = container.innerHTML || "";

  const problems = [];

  if (!html.trim()) {
    problems.push("empty");
  }

  if (html.includes("Loading your") && !html.includes("panel")) {
    problems.push("stuck on loading panel");
  }

  if (html.includes("undefined")) {
    const match = html.match(/[^ >]{0,40}undefined[^ <]{0,40}/);

    problems.push(`undefined leaked: ${match ? match[0] : "?"}`);
  }

  if (html.includes("[object Object]")) {
    problems.push("[object Object] leaked");
  }

  console.log(
    `${problems.length ? "FAIL" : "PASS"}  ${loaderKey}` +
    (problems.length ? "  -> " + problems.join("; ") : "") +
    `  (${html.length} chars)`
  );

  return problems.length === 0;
}

(async () => {

  const checks = [
    ["skillsContent", "loadSkillAnalysis"],
    ["jobsContent", "loadJobOpportunities"],
    ["marketContent", "loadMarketIntelligence"],
    ["simulationContent", "loadFutureSimulation"],
    ["feedbackContent", "loadRecruiterFeedback"],
    ["twinDetails", "loadTwinDetails"],
    ["learningContent", "loadLearningRoadmap"]
  ];

  let failures = 0;

  /* Dashboard needs its containers registered first. */

  for (const id of [
    "dashRole", "dashRoleSub", "dashRolePill", "dashGoal",
    "dashGoalPill", "dashReadiness", "dashReadinessBar",
    "dashReadinessNote", "dashTopSkill", "dashTopSkillSub",
    "dashSkillCount", "dashSkillNote", "dashCoverage",
    "dashDonut", "dashStrengths", "dashGaps", "dashboardJobs",
    "dashRoleLine", "dashLevelLine", "dashName", "dashGreeting",
    "dashGreetingName", "dashAvatar", "dashDate"
  ]) {

    global.document.getElementById(id);
  }

  const dashboardOk = await testPageLoader(
    "dashboardJobs",
    "loadDashboard"
  );

  if (!dashboardOk) failures += 1;

  for (const [id, loader] of checks) {

    const ok = await testPageLoader(id, loader);

    if (!ok) failures += 1;
  }

  /* Debug: dump generated pages' HTML for eyeball verification. */

  if (process.argv.includes("--dump")) {

    for (const id of [
      "dashName", "dashGreetingName", "dashDate", "dashRole",
      "dashRoleSub", "dashRolePill", "dashRoleLine", "dashLevelLine",
      "dashGoal", "dashGoalPill", "dashReadiness", "dashReadinessBar",
      "dashReadinessNote", "dashTopSkill", "dashTopSkillSub",
      "dashSkillCount", "dashSkillNote", "dashCoverage", "dashDonut",
      "dashStrengths", "dashGaps", "dashboardJobs",
      "skillsContent", "marketContent",
      "simulationContent", "feedbackContent", "twinDetails",
      "learningContent"
    ]) {

      const el = global.document.getElementById(id);

      console.log(`\n===== ${id} =====\n${el.textContent || el.innerHTML}`);
    }

    return;
  }

  /* Settings loader writes into different element types. */

  await context.loadSettings();

  const settingsName =
    global.document.getElementById("settingsName");

  console.log(
    `${settingsName.textContent.includes("Manikesh") ? "PASS" : "FAIL"}`
    + `  loadSettings (prefills account + preferences)`
  );

  if (!settingsName.textContent.includes("Manikesh")) {
    failures += 1;
  }

  const targetRoleInput =
    global.document.getElementById("preference-target-role");

  console.log(
    `${targetRoleInput.value === "Software Engineer" ? "PASS" : "FAIL"}`
    + `  loadSettings prefills target role from twin`
  );

  if (targetRoleInput.value !== "Software Engineer") {
    failures += 1;
  }

  console.log(
    failures
      ? `\n${failures} FAILURES`
      : "\nALL FRONTEND PAGE LOADERS PASS"
  );

  if (failures) process.exitCode = 1;

})().catch(error => {

  console.error("HARNESS CRASH:", error);

  process.exitCode = 1;
});

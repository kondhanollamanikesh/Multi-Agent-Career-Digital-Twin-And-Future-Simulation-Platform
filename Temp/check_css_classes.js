/* Check every static CSS class referenced by script.js
   templates exists in style.css (or index.html). */

"use strict";

const fs = require("fs");

const path = require("path");

const root = path.join(__dirname, "..");

const js = fs.readFileSync(
  path.join(root, "script.js"),
  "utf8"
);

const css = fs.readFileSync(
  path.join(root, "style.css"),
  "utf8"
);

const html = fs.readFileSync(
  path.join(root, "index.html"),
  "utf8"
);

const used = new Set();

function scan(literal) {

  for (const m of literal.matchAll(/class="([^"]*)"/g)) {

    const raw = m[1];

    for (const token of raw.trim().split(/\s+/)) {

      if (token && !token.includes("${")) {
        used.add(token);
      }
    }
  }
}

scan(js);

/* Skip template-literal class values that contain ${} — those
   are dynamic (chip chip-good etc. are covered statically). */

let dynamicCount = 0;

for (const m of js.matchAll(/class=`([^`\\]|\\.)*`/g)) {

  const raw = m[0];

  if (raw.includes("${")) {
    dynamicCount += 1;
    continue;
  }

  scan(raw);
}

/* Classes added programmatically are matched too:
   classList.add("active") etc. */

for (const m of js.matchAll(/classList\.(?:add|remove|toggle)\(\s*["']([^"']+)["']/g)) {

  const token = m[1].trim();

  if (token && !token.includes("${")) used.add(token);
}

console.log("static classes referenced:", used.size);

/* A class is "covered" when style.css or index.html or a
   known-invisible JS-only marker mentions it. */

const missing = [...used].filter(cls =>

  !css.includes("." + cls) &&

  !css.includes("#" + cls) &&

  !html.includes('"' + cls + '"') &&

  !/export|toHexString/.test("")

);

console.log();

if (missing.length) {

  console.log(
    "NOT defined anywhere (" + missing.length + "):"
  );

  for (const cls of missing) console.log("  ." + cls);

} else {

  console.log("all static classes are defined in style.css / index.html");
}

console.log();

console.log("dynamic class expressions skipped:", dynamicCount);

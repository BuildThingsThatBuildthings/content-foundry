#!/usr/bin/env node
import { copyFile, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const engineDir = dirname(fileURLToPath(import.meta.url));
const enginesDir = dirname(engineDir);
const skillDir = dirname(enginesDir);

function parseArgs(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith("--") || value === undefined) {
      throw new Error(`Invalid argument sequence near ${key || "(end)"}`);
    }
    values[key.slice(2)] = value;
  }
  return values;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

const args = parseArgs(process.argv.slice(2));
if (!args["run-dir"] || !args.output) {
  throw new Error(
    "Usage: build_composition.mjs --run-dir <run> --output <directory>",
  );
}
const runDir = resolve(args["run-dir"]);
const outputDir = resolve(args.output);
const outputRelative = relative(runDir, outputDir);
if (
  !outputRelative ||
  outputRelative.startsWith("..") ||
  isAbsolute(outputRelative)
) {
  throw new Error("Output must be a child directory of the Content Foundry run.");
}
const job = JSON.parse(await readFile(join(runDir, "job.json"), "utf8"));
const creative = JSON.parse(
  await readFile(join(runDir, "creative-system.json"), "utf8"),
);
const approval = JSON.parse(await readFile(join(runDir, "approval.json"), "utf8"));
const direction = creative.directions.find(
  (item) => item.id === approval.direction,
);
if (!direction) throw new Error(`Approved direction not found: ${approval.direction}`);
const deliverable = job.deliverables.find(
  (item) => Number(item.duration_seconds) > 0,
);
const duration = Number(deliverable?.duration_seconds || 12);
const width = Number(deliverable?.width || 1080);
const height = Number(deliverable?.height || 1920);
const beat = duration / 3;
const title = escapeHtml(direction.name);
const promise = escapeHtml(creative.emotional_promise);
const cta = escapeHtml(job.conversion_action);

await rm(outputDir, { recursive: true, force: true });
await mkdir(join(outputDir, "vendor"), { recursive: true });
await copyFile(
  join(skillDir, "assets", "fonts", "SourceSans3.ttf"),
  join(outputDir, "vendor", "SourceSans3.ttf"),
);

const project = {
  schema_version: "1.0",
  name: "content-foundry-master",
  entry: "index.html",
  direction: direction.id,
  duration_seconds: duration,
  dimensions: { width, height },
  storyboard: [
    { id: "hook", start: 0, duration: beat },
    { id: "promise", start: beat, duration: beat },
    { id: "cta", start: beat * 2, duration: beat },
  ],
  dependencies: { font: "Source Sans 3 (SIL OFL 1.1)" },
  animation_runtime: "css",
  deterministic: true,
};
await writeFile(
  join(outputDir, "hyperframes.json"),
  `${JSON.stringify(project, null, 2)}\n`,
);
await writeFile(
  join(outputDir, "BRIEF.md"),
  `# ${job.objective}\n\nDirection: ${direction.name}\n\nMetaphor: ${direction.metaphor}\n\nPacing: ${direction.pacing}\n`,
);

const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=${width}, height=${height}">
  <title>${title}</title>
  <style>
    @font-face { font-family: "Source Sans 3"; src: url("./vendor/SourceSans3.ttf") format("truetype"); font-display: block; }
    * { box-sizing: border-box; }
    html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; background: #06111f; color: #fff; font-family: "Source Sans 3", sans-serif; }
    #root { position: relative; width: ${width}px; height: ${height}px; overflow: hidden; isolation: isolate; background: radial-gradient(circle at 72% 24%, #123b61 0, #06111f 46%, #020812 100%); }
    #root::before { content: ""; position: absolute; inset: -20%; background: repeating-linear-gradient(118deg, transparent 0 48px, rgba(83,183,255,.055) 49px 50px); transform: rotate(-4deg); }
    .clip { position: absolute; inset: 0; display: grid; align-content: center; padding: 10%; }
    .content { opacity: 0; }
    #hook .content { animation: hook-beat ${duration}s linear both; }
    #promise .content { animation: promise-beat ${duration}s linear both; }
    #cta .content { animation: cta-beat ${duration}s linear both; }
    .eyebrow { color: #f5a623; font-size: ${Math.round(width * 0.035)}px; letter-spacing: .18em; text-transform: uppercase; font-weight: 800; }
    h1, h2 { max-width: 90%; margin: .25em 0 0; font-size: ${Math.round(width * 0.1)}px; line-height: .91; letter-spacing: -.05em; text-wrap: balance; }
    p { max-width: 78%; color: #a9dafc; font-size: ${Math.round(width * 0.038)}px; line-height: 1.2; text-wrap: balance; }
    .orb { position: absolute; right: -8%; bottom: 9%; width: 54%; aspect-ratio: 1; border: 2px solid rgba(83,183,255,.48); border-radius: 50%; box-shadow: inset 0 0 90px rgba(18,139,228,.25), 0 0 80px rgba(18,139,228,.16); animation: orb-beat ${duration}s linear both; }
    .cta-pill { display: inline-flex; width: fit-content; margin-top: .6em; padding: .55em .85em; border: 2px solid #f5a623; border-radius: 999px; color: #f5a623; font-size: ${Math.round(width * 0.038)}px; font-weight: 800; letter-spacing: .05em; text-transform: uppercase; }
    @keyframes hook-beat {
      0% { opacity: 0; transform: translateY(64px); }
      6%, 26% { opacity: 1; transform: translateY(0); }
      33.333%, 100% { opacity: 0; transform: translateY(-28px); }
    }
    @keyframes promise-beat {
      0%, 33.333% { opacity: 0; transform: scale(.88); }
      40%, 59% { opacity: 1; transform: scale(1); }
      66.666%, 100% { opacity: 0; transform: scale(1.04); }
    }
    @keyframes cta-beat {
      0%, 66.666% { opacity: 0; transform: translateY(46px) scale(.96); }
      75%, 100% { opacity: 1; transform: translateY(0) scale(1); }
    }
    @keyframes orb-beat {
      0%, 33.333% { transform: scale(.72) rotate(-20deg); }
      66.666%, 100% { transform: scale(1.08) rotate(22deg); }
    }
  </style>
</head>
<body>
  <main id="root" data-composition-id="content-foundry-master" data-no-timeline data-start="0" data-width="${width}" data-height="${height}" data-duration="${duration}">
    <section id="hook" class="clip" data-start="0" data-duration="${beat}" data-track-index="0">
      <div class="content"><span class="eyebrow">The friction</span><h1>${title}</h1></div>
    </section>
    <section id="promise" class="clip" data-start="${beat}" data-duration="${beat}" data-track-index="0">
      <div class="content"><span class="eyebrow">The shift</span><h2>${promise}</h2><div class="orb" data-layout-allow-overflow aria-hidden="true"></div></div>
    </section>
    <section id="cta" class="clip" data-start="${beat * 2}" data-duration="${beat}" data-track-index="0">
      <div class="content"><span class="eyebrow">Your next move</span><h2>${cta}</h2><div class="cta-pill">${cta}</div></div>
    </section>
  </main>
</body>
</html>
`;
await writeFile(join(outputDir, "index.html"), html);
console.log(JSON.stringify({ ok: true, output: outputDir, duration, width, height }));

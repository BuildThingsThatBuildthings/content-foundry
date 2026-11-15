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
  throw new Error("Usage: build_world.mjs --run-dir <run> --output <directory>");
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
const title = escapeHtml(direction.name);
const promise = escapeHtml(creative.emotional_promise);

await rm(outputDir, { recursive: true, force: true });
await mkdir(join(outputDir, "vendor"), { recursive: true });
await copyFile(
  join(enginesDir, "node_modules", "three", "build", "three.module.min.js"),
  join(outputDir, "vendor", "three.module.min.js"),
);
await copyFile(
  join(enginesDir, "node_modules", "three", "build", "three.core.min.js"),
  join(outputDir, "vendor", "three.core.min.js"),
);
await copyFile(
  join(skillDir, "assets", "fonts", "SourceSans3.ttf"),
  join(outputDir, "vendor", "SourceSans3.ttf"),
);

const world = {
  schema_version: "1.0",
  engine: "three",
  three_version: "0.181.2",
  composition_id: "world3d",
  direction: direction.id,
  duration_seconds: duration,
  dimensions: { width, height },
  deterministic: true,
  time_driver: "hf-seek",
  camera: {
    grammar: direction.camera_behavior,
    start: [0, 0.2, 8.4],
    end: [0.35, -0.05, 6.4],
  },
  scene: {
    metaphor: direction.metaphor,
    materials: creative.color_texture_material,
    lighting: creative.lighting,
    seed: 1709,
  },
};
await writeFile(join(outputDir, "world.json"), `${JSON.stringify(world, null, 2)}\n`);

const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=${width}, height=${height}">
  <title>${title} — Content Foundry 3D World</title>
  <style>
    @font-face { font-family: "Source Sans 3"; src: url("./vendor/SourceSans3.ttf") format("truetype"); font-display: block; }
    :root { color-scheme: dark; }
    * { box-sizing: border-box; }
    html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; background: #06111f; }
    #world3d { position: relative; width: ${width}px; height: ${height}px; overflow: hidden; isolation: isolate; }
    #three-layer { position: absolute; inset: 0; width: 100%; height: 100%; }
    .vignette { position: absolute; inset: 0; background: radial-gradient(circle at 50% 38%, transparent 18%, rgba(0,7,16,.74) 100%); transform-origin: center; animation: world-pulse ${duration}s linear both; }
    .copy { position: absolute; inset: 8% 7% auto; z-index: 2; color: #f8fbff; font-family: "Source Sans 3", sans-serif; text-wrap: balance; }
    .copy strong { display: block; color: #f5a623; font-size: ${Math.round(width * 0.035)}px; letter-spacing: .14em; text-transform: uppercase; }
    .copy h1 { max-width: 90%; margin: .3em 0 .25em; font-size: ${Math.round(width * 0.08)}px; line-height: .92; letter-spacing: -.045em; }
    .copy p { max-width: 72%; margin: 0; color: #9fd7ff; font-size: ${Math.round(width * 0.027)}px; line-height: 1.25; }
    @keyframes world-pulse {
      0% { opacity: .78; transform: scale(1); }
      45% { opacity: .96; transform: scale(1.025); }
      100% { opacity: .82; transform: scale(1.01); }
    }
  </style>
</head>
<body>
  <main id="world3d" data-composition-id="world3d" data-no-timeline data-start="0" data-width="${width}" data-height="${height}" data-duration="${duration}">
    <canvas id="three-layer" aria-label="Deterministic abstract three-dimensional portal"></canvas>
    <section class="copy" aria-label="Campaign message">
      <strong>Content Foundry world</strong>
      <h1>${title}</h1>
      <p>${promise}</p>
    </section>
    <div class="vignette" aria-hidden="true"></div>
  </main>
  <script type="module">
    import * as THREE from "./vendor/three.module.min.js";
    const width = ${width};
    const height = ${height};
    const duration = ${duration};
    const canvas = document.getElementById("three-layer");
    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setSize(width, height, false);
    renderer.setPixelRatio(1);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x06111f, 0.075);
    const camera = new THREE.PerspectiveCamera(35, width / height, 0.1, 100);
    const group = new THREE.Group();
    scene.add(group);
    group.position.set(0.35, -1.55, 0);
    const portal = new THREE.Mesh(
      new THREE.TorusGeometry(1.58, 0.065, 24, 160),
      new THREE.MeshStandardMaterial({ color: 0x2aa8ff, emissive: 0x0d4f87, metalness: 0.75, roughness: 0.22 }),
    );
    portal.rotation.x = 0.12;
    portal.rotation.y = -0.18;
    group.add(portal);
    const portalEcho = new THREE.Mesh(
      new THREE.TorusGeometry(1.82, 0.018, 16, 160),
      new THREE.MeshBasicMaterial({ color: 0x72d2ff, transparent: true, opacity: 0.52 }),
    );
    portalEcho.rotation.copy(portal.rotation);
    group.add(portalEcho);
    const core = new THREE.Mesh(
      new THREE.IcosahedronGeometry(0.82, 2),
      new THREE.MeshPhysicalMaterial({ color: 0xf5a623, emissive: 0x5b2700, roughness: 0.3, metalness: 0.64, clearcoat: 0.9 }),
    );
    group.add(core);
    const starGeometry = new THREE.BufferGeometry();
    const starCount = 360;
    const positions = new Float32Array(starCount * 3);
    for (let index = 0; index < starCount; index += 1) {
      const u = ((index * 73) % starCount) / starCount;
      const v = ((index * 193) % starCount) / starCount;
      const radius = 3.2 + (((index * 37) % 101) / 101) * 7.4;
      const theta = u * Math.PI * 2;
      const phi = Math.acos(2 * v - 1);
      positions[index * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[index * 3 + 1] = radius * Math.cos(phi);
      positions[index * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);
    }
    starGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    scene.add(new THREE.Points(starGeometry, new THREE.PointsMaterial({ color: 0x8ed8ff, size: 0.035 })));
    scene.add(new THREE.HemisphereLight(0x9bdcff, 0x06111f, 2.4));
    const key = new THREE.PointLight(0xf5a623, 48, 18);
    key.position.set(2.5, 3, 4);
    scene.add(key);
    function smooth(value) { return value * value * (3 - 2 * value); }
    function renderAt(time) {
      const progress = smooth(Math.min(1, Math.max(0, time / duration)));
      camera.position.set(0.35 * progress, 0.2 - 0.25 * progress, 8.4 - 2 * progress);
      camera.lookAt(0.35, -1.55, 0);
      group.rotation.y = time * 0.32;
      group.rotation.x = Math.sin(time * 0.48) * 0.11;
      core.scale.setScalar(0.92 + progress * 0.12);
      renderer.render(scene, camera);
    }
    window.addEventListener("hf-seek", (event) => renderAt(event.detail.time));
    renderAt(window.__hfThreeTime || 0);
  </script>
</body>
</html>
`;
await writeFile(join(outputDir, "index.html"), html);
console.log(JSON.stringify({ ok: true, output: outputDir, duration, width, height }));

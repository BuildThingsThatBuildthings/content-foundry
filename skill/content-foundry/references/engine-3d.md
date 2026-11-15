# Bundled Three.js world builder

The portable builder is `engines/world3d/build_world.mjs`. It pins Three.js, copies the local module
into each project, writes `world.json`, and emits a HyperFrames-compatible `index.html`.

Determinism rules:

- root `data-duration` is mandatory;
- render only from `hf-seek` event time (`event.detail.time`);
- no `requestAnimationFrame`, `setAnimationLoop`, `Date.now`, `performance.now`, unseeded random,
  remote render-critical models, textures, fonts, or HDRIs;
- pin canvas size and pixel ratio;
- derive camera, transforms, mixer time, shader uniforms, and particles from absolute time;
- preload local assets before critical seeking.

The default rights-clean world is an abstract portal/control-room foundation. A domain pack may
replace geometry and materials, but exact logos, copy, facts, and compliance remain deterministic
HTML/Remotion/Pillow layers.

If WebGL or Three.js is unavailable, route to a disclosed 2.5D parallax treatment using the same
camera path and creative system.

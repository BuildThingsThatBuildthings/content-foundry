# Dependency and license inventory

Content Foundry source is MIT-licensed. Runtime adapters preserve provider and dependency license
boundaries; optional services are not relicensed by this repository.

| Dependency or service | Version/pin | License or terms | Required | Role |
|---|---:|---|---|---|
| Python | 3.10+ | PSF | Yes | Portable runtime and deterministic pipeline |
| Pillow | 10+ | HPND | Core stills | Raster composite and QC |
| Three.js | 0.181.2 | MIT | 3D tier | Bundled local world renderer |
| Source Sans 3 | bundled | SIL OFL 1.1 | Yes | Deterministic typography |
| Playfair Display | bundled | SIL OFL 1.1 | Yes | Deterministic display typography |
| FFmpeg/ffprobe | system | LGPL/GPL build-dependent | Media tier | Conform, encode, inspect, loudness |
| Remotion | lockfile | Remotion license | Optional | Deterministic video composition |
| HyperFrames CLI | user/CI tool | Upstream terms | Optional | Check, preview, render, finishing |
| OpenAI, Gemini, HeyGen | configured provider | Provider terms | Optional | Image, voice, or avatar generation |
| Netlify, Vercel, PostBridge | configured provider | Provider terms | Optional | Deploy and scheduled-draft adapters |

The MIT release package excludes `node_modules`, generated media, credentials, and provider
outputs. `engines/package-lock.json` pins the MIT Three.js dependency. Review optional service
terms before commercial use.

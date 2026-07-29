import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  continueRender,
  delayRender,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {z} from 'zod';

export const FPS = 30;

// IG story/reel safe zones from channel-specs.md.
export const SAFE = {top: 108, bottom: 320, left: 60, right: 120};

// Brand display font: the bundled OFL serif staged by video_props.py
// (public/job/font-display.ttf). Loaded via FontFace so renders are identical
// on every OS; the stack degrades to system serifs when the file is absent.
export const serif = '"CF Serif", Didot, "Hoefler Text", Georgia, serif';
export const sans = 'Helvetica Neue, Helvetica, Arial, sans-serif';

let fontLoaded = false;

/** Load the bundled brand font once per render. Call at the top of each
 * composition component — delayRender must run inside a render context. */
export const useBrandFont = () => {
  const [handle] = React.useState(() =>
    fontLoaded ? null : delayRender('load brand font'));
  React.useEffect(() => {
    if (handle === null) return;
    const done = () => continueRender(handle);
    try {
      const face = new FontFace('CF Serif',
        `url(${staticFile('job/font-display.ttf')})`);
      face.load().then((f) => {
        (document as any).fonts.add(f);
        fontLoaded = true;
        done();
      }).catch(done);
    } catch {
      done();
    }
  }, [handle]);
};

export const sceneSchema = z.object({
  photo: z.string(),
  width: z.number(),
  height: z.number(),
  aspect: z.number(),
  room: z.string(),
  feature: z.string(),
  vo: z.string().nullable(),
  voDurationS: z.number(),
  frames: z.number(),
});

export const propsSchema = z.object({
  brand: z.object({
    primary: z.string(),
    secondary: z.string(),
    accent: z.string(),
    textOnDark: z.string(),
    logoDark: z.string(),
    name: z.string(),
  }),
  headline: z.string(),
  subline: z.string(),
  hook: z.string(),
  community: z.string(),
  scenes: z.array(sceneSchema),
  briefCards: z.array(z.object({
    photo: z.string(), width: z.number(), height: z.number(),
    aspect: z.number(), line: z.string(),
  })),
  endcard: z.object({
    vo: z.string().nullable(), voDurationS: z.number(), frames: z.number(),
  }),
  audio: z.object({
    bed: z.string().nullable(), bedVolume: z.number(), bedVolumeSolo: z.number(),
  }),
  compliance: z.object({
    license: z.string(), disclosure: z.string(), fairHousing: z.string(),
  }),
  warnings: z.array(z.string()),
});
export type VideoProps = z.infer<typeof propsSchema>;
export type Scene = z.infer<typeof sceneSchema>;

/**
 * Music bed for a whole composition. Loops, holds a base volume, fades out
 * over the final 1.5s. Volume is a per-frame function so ducking is
 * deterministic, not a mix guess.
 */
export const Bed: React.FC<{
  src: string | null;
  volume: number;
  totalFrames: number;
}> = ({src, volume, totalFrames}) => {
  if (!src) return null;
  return (
    <Audio
      loop
      src={staticFile(src)}
      volume={(f) =>
        interpolate(f, [0, 20, totalFrames - 45, totalFrames - 5], [0, volume, volume, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      }
    />
  );
};

/**
 * Aspect-aware photo treatment. The fix for "images don't fit the screen":
 *
 * - Landscape photo on a portrait canvas → the photo is FITTED to full width
 *   (never cropped beyond the traversal margin, ~5% per side) and placed in an
 *   editorial band; the surrounding brand field carries the typography. Motion
 *   is a slow lateral traversal INSIDE the fitted frame — it reveals the
 *   photograph instead of amputating it.
 * - Portrait/near-square photo → full-bleed cover with a slow push.
 */
export const FittedPhoto: React.FC<{
  scene: {photo: string; aspect: number};
  frames: number;
  centerY: number;
  index?: number;
}> = ({scene, frames, centerY, index = 0}) => {
  const frame = useCurrentFrame();
  const {width: W, height: H} = useVideoConfig();
  const isLandscape = scene.aspect > 1.05;
  const settle = interpolate(frame, [0, Math.min(24, frames / 3)], [0, 1], {
    extrapolateRight: 'clamp',
  });

  if (!isLandscape) {
    const zoom = interpolate(frame, [0, frames], [1.04, 1.1]);
    return (
      <AbsoluteFill>
        <Img
          src={staticFile(scene.photo)}
          style={{width: '100%', height: '100%', objectFit: 'cover',
                  transform: `scale(${zoom})`}}
        />
      </AbsoluteFill>
    );
  }

  const fitH = Math.round(W / scene.aspect);
  const top = Math.round(centerY - fitH / 2);
  // Traversal: image rendered 10% wider than the window, panning across it.
  const overscan = 1.1;
  const maxPan = (W * overscan - W) / 2;
  const dir = index % 2 === 0 ? 1 : -1;
  const pan = interpolate(frame, [0, frames], [-maxPan * dir, maxPan * dir]);
  return (
    <div
      style={{
        position: 'absolute', left: 0, top, width: W, height: fitH,
        overflow: 'hidden', opacity: settle,
      }}
    >
      <Img
        src={staticFile(scene.photo)}
        style={{
          position: 'absolute',
          left: -(W * overscan - W) / 2 + pan,
          width: W * overscan,
          height: fitH * overscan,
          top: -(fitH * overscan - fitH) / 2,
          objectFit: 'cover',
        }}
      />
    </div>
  );
};

/** Room callout: index + title above the photo band, feature line below. */
export const RoomCallout: React.FC<{
  room: string;
  feature: string;
  indexLabel: string;
  brand: VideoProps['brand'];
  photoTop: number;
  photoBottom: number;
}> = ({room, feature, indexLabel, brand, photoTop, photoBottom}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const rise = spring({frame, fps, config: {damping: 200}, durationInFrames: 26});
  const featureIn = interpolate(frame, [14, 34], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  return (
    <>
      <div
        style={{
          position: 'absolute', left: SAFE.left, right: SAFE.right,
          top: photoTop - 190,
          transform: `translateY(${(1 - rise) * 34}px)`, opacity: rise,
        }}
      >
        <div style={{fontFamily: serif, fontSize: 30, letterSpacing: 8,
                     color: brand.accent}}>
          {indexLabel}
        </div>
        <div style={{fontFamily: serif, fontSize: 84, color: brand.textOnDark,
                     lineHeight: 1.05, marginTop: 10, whiteSpace: 'nowrap'}}>
          {room}
        </div>
      </div>
      <div style={{position: 'absolute', left: SAFE.left, right: SAFE.right,
                   top: photoBottom + 46, opacity: featureIn}}>
        <div style={{height: 4, width: 96, backgroundColor: brand.accent}} />
        <div style={{fontFamily: sans, fontSize: 34, lineHeight: 1.4,
                     color: brand.textOnDark, opacity: 0.94, marginTop: 22}}>
          {feature}
        </div>
      </div>
    </>
  );
};

/** Shared compliance endcard. Optionally narrated. */
export const Endcard: React.FC<{
  brand: VideoProps['brand'];
  subline: string;
  compliance: VideoProps['compliance'];
  vo?: string | null;
}> = ({brand, subline, compliance, vo}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const rise = spring({frame, fps, config: {damping: 200}, durationInFrames: 30});
  return (
    <AbsoluteFill style={{backgroundColor: brand.primary}}>
      {vo ? <Audio src={staticFile(vo)} /> : null}
      <div
        style={{
          position: 'absolute', left: SAFE.left, right: SAFE.right, top: 690,
          textAlign: 'center',
          transform: `translateY(${(1 - rise) * 50}px)`, opacity: rise,
        }}
      >
        <Img src={staticFile(brand.logoDark)} style={{width: 620}} />
        <div style={{fontFamily: serif, fontSize: 36, letterSpacing: 5,
                     color: brand.accent, marginTop: 56,
                     textTransform: 'uppercase'}}>
          Now Showing
        </div>
        <div style={{fontFamily: serif, fontSize: 32, color: brand.textOnDark,
                     marginTop: 18, opacity: 0.92}}>
          {subline}
        </div>
      </div>
      <div
        style={{
          position: 'absolute', left: SAFE.left, right: SAFE.right,
          bottom: SAFE.bottom + 24, fontFamily: sans, fontSize: 26,
          lineHeight: 1.5, color: brand.textOnDark,
        }}
      >
        <div>{compliance.license}</div>
        <div>{compliance.disclosure}</div>
        <div>{compliance.fairHousing}</div>
      </div>
    </AbsoluteFill>
  );
};

/** Brand intro card shared by Walkthrough and Teaser. */
export const IntroCard: React.FC<{
  brand: VideoProps['brand'];
  title: string;
  subline: string;
  frames: number;
}> = ({brand, title, subline, frames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const rise = spring({frame, fps, config: {damping: 200}, durationInFrames: 28});
  const ruleW = interpolate(frame, [6, 30], [0, 240], {extrapolateRight: 'clamp'});
  const fade = interpolate(frame, [frames - 12, frames], [1, 0], {
    extrapolateLeft: 'clamp',
  });
  return (
    <AbsoluteFill style={{backgroundColor: brand.primary, opacity: fade}}>
      <div
        style={{
          position: 'absolute', left: SAFE.left, right: SAFE.right, top: 660,
          transform: `translateY(${(1 - rise) * 60}px)`, opacity: rise,
        }}
      >
        <div style={{height: 6, width: ruleW, backgroundColor: brand.accent}} />
        <div style={{fontFamily: serif, fontSize: 92, lineHeight: 1.12,
                     color: brand.textOnDark, marginTop: 44}}>
          {title}
        </div>
        <div style={{fontFamily: serif, fontSize: 34, letterSpacing: 5,
                     color: brand.accent, marginTop: 38,
                     textTransform: 'uppercase'}}>
          {subline}
        </div>
      </div>
    </AbsoluteFill>
  );
};

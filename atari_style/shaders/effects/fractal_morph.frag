#version 330 core
/*
 * Fractal Morph Composite Fragment Shader
 *
 * An honest, flat-2D demo whose star is the TRANSFORMATION itself:
 * the Mandelbrot set continuously morphing into a Julia set and back,
 * with a different Julia target each cycle.
 *
 * (Reborn from fractal_flight: the pseudo-3D relief lighting is gone —
 * 3D ambitions live in fractal_terrain.frag now. This shader keeps the
 * good bones: the morph iteration, the cardioid parameter path, and the
 * boundary-locked camera.)
 *
 * 1. MORPH — iterate z' = z^2 + mix(pixel, c_julia, morph) with z0 = pixel.
 *    morph = 0 renders the Mandelbrot set, morph = 1 renders the Julia set
 *    of c_julia, and intermediate values blend the two continuously.
 *    The morph wave is an eased triangle (~18 s cycle) that is visibly in
 *    transit ~90% of the time, with brief holds at both pure sets.
 *
 * 2. MULTI-ORBIT JULIA TARGETS — c_julia alternates each cycle between the
 *    main-cardioid boundary c(a) = e^{ia}/2 - e^{2ia}/4 (edge-of-connectivity
 *    seahorse/spiral Julias) and the period-2 disk boundary c = -1 + e^{ib}/4
 *    (basilica-family Julias), so successive Julia phases look different.
 *    The swap happens while morph == 0, where c_julia has no influence.
 *
 * 3. FULL-FRAME INTEREST — the camera drifts along the cardioid coast on the
 *    Mandelbrot side (biased slightly outside, into the filament zone) and
 *    settles to the origin as morph -> 1; zoom eases in log space between a
 *    coastline close-up and the full Julia silhouette. A derivative is
 *    carried through the iteration for distance estimation: DE contour
 *    bands texture the far exterior and a warm glow hugs the boundary.
 *    Interior pixels use orbit traps + contour bands (never flat black).
 *
 * Motion design: all terms are bounded, C1-continuous functions of time —
 * no speed*time products. The per-cycle orbit step is the only discrete
 * change and it occurs exactly while the morph is clamped to 0.
 *
 * Uniforms:
 *   iTime       - Animation time
 *   iResolution - Viewport resolution (width, height)
 *   iParams     - (drift_speed, morph_speed, texture_amt, zoom_amp)
 *   iColorMode  - Color palette selector (0-3)
 */

uniform float iTime;
uniform vec2 iResolution;
uniform vec4 iParams;
uniform int iColorMode;

in vec2 fragCoord;
out vec4 fragColor;

const float TAU = 6.28318530717958647692;
const int MAX_ITER = 200;

vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(TAU * (c * t + d));
}

vec3 getColor(float t, int mode) {
    if (mode == 0) {
        // Sunrise: deep blue to gold
        return palette(t, vec3(0.5, 0.4, 0.4), vec3(0.5, 0.4, 0.5),
                          vec3(1.0, 0.9, 0.8), vec3(0.05, 0.25, 0.55));
    } else if (mode == 1) {
        // Lava canyon
        return palette(t, vec3(0.55, 0.3, 0.2), vec3(0.45, 0.4, 0.3),
                          vec3(1.0, 1.0, 0.9), vec3(0.0, 0.12, 0.35));
    } else if (mode == 2) {
        // Electric storm
        return palette(t, vec3(0.4, 0.35, 0.6), vec3(0.45, 0.45, 0.4),
                          vec3(1.0, 1.0, 0.7), vec3(0.6, 0.3, 0.8));
    } else {
        // Pearl
        return palette(t, vec3(0.6), vec3(0.35), vec3(1.0), vec3(0.0, 0.1, 0.2));
    }
}

// Each pulse advances a phase by 1.0 over pulseLen seconds, then rests
// until the next period. C1-continuous (smoothstep has zero slope at both
// ends), monotonic — "occasional quick movement" without any jump.
float pulsedPhase(float t, float period, float pulseLen) {
    float n = floor(t / period);
    float f = t - n * period;
    return n + smoothstep(0.0, pulseLen, f);
}

void main() {
    float driftSpeed = iParams.x;   // camera drift along the coast (~0.5)
    float morphSpeed = iParams.y;   // morph cycle rate (~0.5 -> 18 s cycle)
    float textureAmt = iParams.z;   // DE micro-texture + trap contrast (~0.5)
    float zoomAmp    = iParams.w;   // zoom breathing depth (~0.5)

    float t = iTime;

    // --- Morph schedule -----------------------------------------------------
    // Eased triangle wave: in visible transit ~90% of the cycle, with brief
    // holds at pure Mandelbrot (tri ~ 0) and pure Julia (tri ~ 1). smoothstep
    // has zero slope at both clamp edges, so motion stays C1 through holds.
    float period = 24.0 - 12.0 * morphSpeed;          // 18 s at default 0.5
    float ph = fract(t / period);
    float tri = 1.0 - abs(2.0 * ph - 1.0);
    float morph = smoothstep(0.05, 0.95, tri);

    // --- Julia parameter path ------------------------------------------------
    // Slow drift with occasional eased pulses (every ~13 s).
    float a = t * 0.09 * driftSpeed
            + 0.35 * pulsedPhase(t, 13.0, 1.8)
            + 2.1;
    // Orbit A: main cardioid boundary (edge of connectivity, max complexity)
    vec2 cA = vec2(0.5 * cos(a) - 0.25 * cos(2.0 * a),
                   0.5 * sin(a) - 0.25 * sin(2.0 * a));
    // Orbit B: period-2 disk boundary (basilica family) — scaled/offset orbit
    float b = a * 1.37 + 0.8;
    vec2 cB = vec2(-1.0, 0.0) + 0.25 * vec2(cos(b), sin(b));
    // Alternate per cycle; floor(t/period) steps at ph = 0, the middle of the
    // pure-Mandelbrot hold, where c_julia has zero influence on the image.
    float orbitSel = mod(floor(t / period), 2.0);
    vec2 cJulia = mix(cA, cB, orbitSel);

    // --- Camera ----------------------------------------------------------------
    // Mandelbrot phase: hug the cardioid coast, biased slightly OUTSIDE the
    // boundary (into the filament zone) so the frame shows coastline detail.
    // Julia phase: settle to the origin, where Julia structure lives.
    vec2 outward = cA * 1.18 + vec2(0.025, 0.0);
    vec2 center = mix(outward, vec2(0.0), morph);

    // Zoom (log space): coastline close-up at the Mandelbrot end, full
    // dendrite silhouette at the Julia end. Gentle breathing, damped during
    // the Julia phase so the silhouette stays framed.
    float lz = mix(-0.35, 1.45, morph)
             + zoomAmp * 0.55 * sin(t * 0.075 + 0.7) * (1.0 - 0.6 * morph);
    float viewScale = exp2(lz);    // frame height on the complex plane

    // Slow continuous plane rotation keeps the 2D frame alive
    float rot = 0.10 * sin(t * 0.05) + t * 0.012;

    // --- Screen to fractal plane -------------------------------------------------
    vec2 uv = fragCoord - 0.5;
    uv.x *= iResolution.x / iResolution.y;
    float cr = cos(rot), sr = sin(rot);
    uv = vec2(uv.x * cr - uv.y * sr, uv.x * sr + uv.y * cr);
    vec2 p = center + uv * viewScale;

    // --- Morphing iteration with derivative + orbit traps -------------------------
    // z0 = p, c = mix(p, cJulia, morph)  =>  dz/dp obeys dz' = 2 z dz + (1-morph)
    // with dz0 = 1, valid across the whole morph for distance estimation.
    vec2 z = p;
    vec2 dz = vec2(1.0, 0.0);
    float dcdp = 1.0 - morph;
    vec2 c = mix(p, cJulia, morph);
    float trapCirc = 1e9;          // min | |z| - 0.25 |  (circle trap)
    float trapPt = 1e9;            // min |z|  (point trap at origin)
    float m2 = 0.0;
    float iter = 0.0;
    bool escaped = false;

    for (int i = 0; i < MAX_ITER; i++) {
        dz = 2.0 * vec2(z.x * dz.x - z.y * dz.y,
                        z.x * dz.y + z.y * dz.x) + vec2(dcdp, 0.0);
        z = vec2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y) + c;

        m2 = dot(z, z);
        float r = sqrt(m2);
        trapCirc = min(trapCirc, abs(r - 0.25));
        trapPt = min(trapPt, r);

        if (m2 > 256.0) {
            escaped = true;
            iter = float(i);
            break;
        }
        iter = float(i);
    }

    float paletteShift = t * 0.02;
    vec3 color;

    if (!escaped) {
        // --- Interior: orbit-trapped texture, dark but never flat ---------------
        float k = 3.5 + 11.0 * textureAmt;
        float s1 = exp(-trapCirc * k);          // luminous currents
        float s2 = exp(-trapPt * k * 0.6);      // soft radial structure
        // Trap-field contour bands keep even far-from-trap pixels textured;
        // frequency scales with zoom so several bands always cross the frame.
        float bandFreq = 30.0 / clamp(viewScale * 0.5, 0.004, 2.0);
        float b1 = sin(trapCirc * bandFreq * 5.0 - paletteShift * TAU);
        float b2 = sin(trapPt * bandFreq * 2.2 + paletteShift * TAU * 0.5);
        float bands = 0.5 + 0.3 * b1 + 0.2 * b2;
        bands *= bands;   // sharpen into ridges
        vec3 deep = getColor(fract(0.55 + paletteShift), iColorMode);
        vec3 vein = getColor(fract(0.28 + paletteShift), iColorMode);
        vein = max(vein, vec3(0.28, 0.30, 0.36));   // luminance floor
        color = deep * (0.09 + 0.24 * s1 + 0.12 * s2)
              + vein * (s1 * s1 * 0.22
                        + 0.38 * bands * (0.3 + 0.7 * textureAmt));
    } else {
        // --- Exterior: smooth iteration + DE glow + DE contour texture ----------
        float log_zn = 0.5 * log(m2);                       // ln|z|
        float nu = log(log_zn / log(2.0)) / log(2.0);
        float smoothIter = iter + 1.0 - nu;

        // Log-scaled color index; band count grows as the view tightens so
        // close-ups keep full palette variation.
        float bandCycles = 4.0 + 0.55 * max(0.0, -log2(viewScale * 0.5));
        float tc = log(smoothIter + 1.0) / log(float(MAX_ITER) + 1.0);
        tc = tc * bandCycles + paletteShift;
        color = getColor(fract(tc), iColorMode);

        // Distance estimate: d = |z| ln|z| / |dz|
        float d = sqrt(m2) * log_zn / max(length(dz), 1e-20);
        float px = viewScale / iResolution.y;               // pixel size

        // Micro-texture: two families of log-spaced DE contour bands fill
        // the far field so wide views never collapse to a smooth gradient.
        float ld = log2(max(d, 1e-14));
        float band = 0.5 + 0.5 * sin(ld * 4.2 - t * 0.15);
        float band2 = 0.5 + 0.5 * sin(ld * 19.0 + t * 0.1);
        color *= mix(1.0, 0.55 + 0.62 * band + 0.28 * band2, textureAmt);
        color += vec3(0.06, 0.10, 0.16) * band * textureAmt;

        // Warm glow hugging the boundary filaments
        float glow = exp2(-d / (px * 30.0));
        color += getColor(fract(0.1 + paletteShift), iColorMode) * glow * 0.4;
    }

    // Gentle vignette to focus the frame
    float r = length(fragCoord - 0.5);
    color *= 1.0 - smoothstep(0.55, 1.0, r) * 0.30;

    fragColor = vec4(color, 1.0);
}

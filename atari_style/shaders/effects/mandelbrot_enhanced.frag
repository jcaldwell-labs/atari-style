#version 330 core
/*
 * Mandelbrot Enhanced - Boundary Tour Fragment Shader
 *
 * A keyframed cinematic tour of the Mandelbrot set boundary, ported from
 * the proven TOUR_LOCATIONS path in terminal_arcade's mandelbrot_demo.py
 * (seahorse valley, elephant valley, spiral region), fixing the two
 * failure modes of the plain mandelbrot.frag demos:
 *
 * 1. NO FLAT REGIONS - interior pixels use an orbit trap (min distance of
 *    the orbit to a circle and a point) for dark-but-textured shading,
 *    so bulbs read as luminous structure instead of dead black fill.
 *
 * 2. EXTERIOR RICHNESS - smooth iteration coloring is combined with a
 *    distance-estimation (DE) field: a warm glow hugs the boundary and
 *    log-spaced DE contour bands give the low-iteration far field visible
 *    texture. The palette cycles slowly over time.
 *
 * 3. BOUNDARY TOUR - waypoints sit ON the boundary filaments (never inside
 *    bulbs), with constant-zoom edge pans before each deeper dive, exactly
 *    like the original terminal demo. Camera center and log2(zoom) are
 *    interpolated with smoothstep easing (C1-continuous: zero velocity at
 *    every waypoint, no time*speed products). Zoom interpolation happens
 *    in LOG space. The loop is ~110 s, then wraps seamlessly.
 *
 * 4. EXPLORE AT DEPTH - each deep destination is a 3-waypoint cluster:
 *    arrive, dwell, then TRAVERSE the local boundary structure at depth
 *    (seahorse: down the narrowing valley; elephant: march the herd into
 *    the cusp tip; spiral: pan northwest through neighboring double
 *    spirals) before leaving. Between destinations the camera pulls back
 *    only part way (lz ~ -1.7, never overview scale) and arcs over the
 *    NORTHERN boundary of the set, so transit frames keep the glowing
 *    edge in frame instead of crossing the flat interior. The only full
 *    overview is the loop start/end wrap.
 *
 * Precision: deepest scale is 0.006 (~270x magnification) - comfortably
 * inside float32 precision at 1080p (pixel size ~1e-5 vs eps ~1e-7).
 *
 * Uniforms:
 *   iTime       - Animation time
 *   iResolution - Viewport resolution (width, height)
 *   iParams     - (tour_speed, palette_speed, trap_strength, detail_mix)
 *   iColorMode  - Color palette selector (0-3)
 */

uniform float iTime;
uniform vec2 iResolution;
uniform vec4 iParams;
uniform int iColorMode;

in vec2 fragCoord;
out vec4 fragColor;

const float TAU = 6.28318530717958647692;
const int MAX_ITER = 350;

// ---------------------------------------------------------------------------
// Tour waypoints (ported from terminal_arcade TOUR_LOCATIONS, then extended
// with 3-waypoint exploration clusters at each deep destination).
// WP_C  = camera center on the complex plane
// WP_LZ = log2(view scale); view height = 2 * scale
// WP_T  = arrival time (seconds); WP_D = dwell (hold) time at the waypoint
// Entry 18 duplicates entry 0 so the loop wraps without a jump.
// ---------------------------------------------------------------------------
const int NUM_WP = 19;

const vec2 WP_C[NUM_WP] = vec2[NUM_WP](
    vec2(-0.5000,  0.0000),   //  0 overview of the whole set
    vec2(-0.7450,  0.1860),   //  1 approach seahorse valley along the edge
    vec2(-0.7450,  0.1860),   //  2 dive (zoom only)
    vec2(-0.7453,  0.1127),   //  3 EDGE PAN at constant zoom down the valley
    vec2(-0.7453,  0.1127),   //  4 deep seahorse: arrive + dwell
    vec2(-0.7483,  0.0890),   //  5 TRAVERSE down the valley between the walls
    vec2(-0.7515,  0.0480),   //  6 valley narrows: seahorse beads both sides
    vec2(-0.1800,  0.5400),   //  7 transit: arc over the NORTHERN boundary
    vec2( 0.2850,  0.0000),   //  8 approach elephant valley (east cusp)
    vec2( 0.2855,  0.0120),   //  9 EDGE PAN at constant zoom along the trunks
    vec2( 0.2855,  0.0120),   // 10 deep elephant: arrive + dwell
    vec2( 0.2770,  0.0075),   // 11 TRAVERSE: march with the herd toward cusp
    vec2( 0.2651,  0.0027),   // 12 cusp tip: elephants converge on the point
    vec2(-0.1000,  0.5800),   // 13 transit: back over the top, heading NW
    vec2(-0.7269,  0.1889),   // 14 approach the spiral region
    vec2(-0.7269,  0.1889),   // 15 deep spiral: arrive + dwell
    vec2(-0.7310,  0.1910),   // 16 TRAVERSE northwest along the spiral arms
    vec2(-0.7350,  0.1940),   // 17 neighboring double-spiral cluster
    vec2(-0.5000,  0.0000)    // 18 = waypoint 0 (wrap: the ONE full overview)
);

const float WP_LZ[NUM_WP] = float[NUM_WP](
    0.678,    //  0 scale 1.600
    -1.322,   //  1 scale 0.400
    -2.943,   //  2 scale 0.130
    -2.943,   //  3 scale 0.130 (constant-zoom pan)
    -6.059,   //  4 scale 0.015
    -6.300,   //  5 scale 0.0127 (traverse, slight deepen as valley narrows)
    -6.600,   //  6 scale 0.0103
    -1.800,   //  7 scale 0.287 (PARTIAL pullback, not overview)
    -3.059,   //  8 scale 0.120
    -3.059,   //  9 scale 0.120 (constant-zoom pan)
    -6.381,   // 10 scale 0.012
    -6.550,   // 11 scale 0.0107 (traverse, elephants shrink toward cusp)
    -6.850,   // 12 scale 0.0087
    -1.700,   // 13 scale 0.308 (PARTIAL pullback, not overview)
    -4.059,   // 14 scale 0.060
    -7.381,   // 15 scale 0.006 (deepest point of the tour)
    -7.050,   // 16 scale 0.0075 (ease out a touch to show adjacent arms)
    -7.300,   // 17 scale 0.0063 (re-deepen onto the neighbor spiral)
    0.678     // 18 scale 1.600 (wrap)
);

const float WP_T[NUM_WP] = float[NUM_WP](
    0.0,     //  0
    5.5,     //  1
    9.0,     //  2
    12.5,    //  3
    17.0,    //  4 seahorse cluster: 17.0 - 36.0 at depth
    24.5,    //  5
    32.0,    //  6
    41.0,    //  7
    45.5,    //  8
    49.0,    //  9
    53.5,    // 10 elephant cluster: 53.5 - 72.5 at depth
    61.0,    // 11
    68.5,    // 12
    77.5,    // 13
    82.0,    // 14
    87.0,    // 15 spiral cluster: 87.0 - 104.5 at depth
    94.0,    // 16
    100.5,   // 17
    110.0    // 18 (= total loop length)
);

const float WP_D[NUM_WP] = float[NUM_WP](
    2.0,   //  0 hold the overview
    0.3,   //  1
    0.3,   //  2
    0.3,   //  3
    2.5,   //  4 dwell at deep seahorse before the traverse begins
    2.0,   //  5 pause mid-valley
    4.0,   //  6 long look at the narrowing valley before leaving
    0.0,   //  7 crest the transit arc without stopping
    0.3,   //  8
    0.3,   //  9
    2.5,   // 10 dwell at deep elephant before the traverse begins
    2.0,   // 11 pause along the herd
    4.0,   // 12 long look into the cusp tip before leaving
    0.0,   // 13 crest the transit arc without stopping
    0.5,   // 14
    2.5,   // 15 dwell at the deep spiral before the traverse begins
    2.0,   // 16 pause among the arms
    4.0,   // 17 long look at the neighbor double-spiral
    0.0    // 18 (unused)
);

const float TOUR_TOTAL = 110.0;

// Cosine-based color palette (Inigo Quilez)
vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(TAU * (c * t + d));
}

vec3 getColor(float t, int mode) {
    if (mode == 0) {
        // Electric ocean: deep blue through cyan to warm gold
        return palette(t, vec3(0.30, 0.34, 0.45), vec3(0.45, 0.40, 0.42),
                          vec3(1.00, 1.00, 1.00), vec3(0.62, 0.78, 0.95));
    } else if (mode == 1) {
        // Ember: smoldering red-orange-cream
        return palette(t, vec3(0.50, 0.25, 0.15), vec3(0.50, 0.40, 0.30),
                          vec3(1.00, 1.00, 0.80), vec3(0.00, 0.15, 0.40));
    } else if (mode == 2) {
        // Psychedelic rainbow
        return palette(t, vec3(0.5), vec3(0.5), vec3(1.0),
                          vec3(0.00, 0.33, 0.67));
    } else {
        // Silver engraving
        return palette(t, vec3(0.55), vec3(0.40), vec3(1.0),
                          vec3(0.00, 0.05, 0.10));
    }
}

// Camera state along the tour: hold at each waypoint for its dwell, then
// smoothstep-travel to the next. Zero velocity at both segment ends keeps
// the motion C1-continuous everywhere, including the loop wrap.
void tourCamera(float t, out vec2 center, out float lz) {
    center = WP_C[0];
    lz = WP_LZ[0];
    for (int i = 0; i < NUM_WP - 1; i++) {
        if (t >= WP_T[i] && t < WP_T[i + 1]) {
            float travelStart = WP_T[i] + WP_D[i];
            float travelLen = max(WP_T[i + 1] - travelStart, 1e-4);
            float f = clamp((t - travelStart) / travelLen, 0.0, 1.0);
            center = mix(WP_C[i], WP_C[i + 1], smoothstep(0.0, 1.0, f));
            // LOG-space zoom lerp with asymmetric easing: zoom OUT early and
            // zoom IN late, so cross-set traversals happen at a wide view
            // (never pans across interior while still deep). Both easings are
            // C1: zero slope at segment ends.
            float fz = (WP_LZ[i + 1] > WP_LZ[i])
                ? smoothstep(0.0, 0.52, f)
                : smoothstep(0.42, 1.0, f);
            lz = mix(WP_LZ[i], WP_LZ[i + 1], fz);
        }
    }
}

void main() {
    // --- Parameters (all defaults tuned for 0.5) ---------------------------
    float tourSpeed    = mix(0.5, 1.5, iParams.x);    // playback rate
    float paletteSpeed = mix(0.0, 0.16, iParams.y);   // palette cycle rate
    float trapStrength = iParams.z;                   // interior trap contrast
    float detailMix    = iParams.w;                   // DE micro-texture amount

    // --- Camera -------------------------------------------------------------
    float t = mod(iTime * tourSpeed, TOUR_TOTAL);
    vec2 center;
    float lz;
    tourCamera(t, center, lz);
    float scale = exp2(lz);

    vec2 uv = fragCoord - 0.5;
    uv.x *= iResolution.x / iResolution.y;
    vec2 c = center + uv * (2.0 * scale);

    // Iteration budget grows with zoom depth so deep frames stay crisp
    float maxIter = clamp(90.0 + 34.0 * (0.7 - lz), 90.0, float(MAX_ITER));

    // --- Mandelbrot iteration with derivative + orbit traps ------------------
    vec2 z = vec2(0.0);
    vec2 dz = vec2(0.0);          // dz/dc for distance estimation
    float trapCirc = 1e9;         // min |  |z| - 0.25 |  (circle trap)
    float trapPt = 1e9;           // min |z| (point trap at origin)
    float m2 = 0.0;
    float iter = 0.0;
    bool escaped = false;

    for (int i = 0; i < MAX_ITER; i++) {
        if (float(i) >= maxIter) break;

        // dz = 2*z*dz + 1
        dz = 2.0 * vec2(z.x * dz.x - z.y * dz.y,
                        z.x * dz.y + z.y * dz.x) + vec2(1.0, 0.0);
        // z = z^2 + c
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

    float paletteShift = iTime * paletteSpeed;
    vec3 color;

    if (!escaped) {
        // --- Interior: orbit-trapped texture, dark but never flat ------------
        float k = 2.5 + 9.0 * trapStrength;
        float s1 = exp(-trapCirc * k);          // luminous currents
        float s2 = exp(-trapPt * k * 0.6);      // soft radial structure
        // Contour bands of the trap fields: these vary smoothly across every
        // bulb, so even pixels far from the traps keep visible texture.
        // Band frequency scales inversely with view scale so several bands
        // always cross the frame, even deep in slowly-varying bulb regions.
        float bandFreq = 30.0 / clamp(scale, 0.004, 2.0);
        float b1 = sin(trapCirc * bandFreq * 2.3 - paletteShift * TAU);
        float b2 = sin(trapPt * bandFreq + paletteShift * TAU * 0.5);
        float bands = 0.5 + 0.3 * b1 + 0.2 * b2;   // two crossing families
        bands *= bands;   // sharpen into ridges
        vec3 deep = getColor(fract(0.55 + paletteShift), iColorMode);
        vec3 vein = getColor(fract(0.28 + paletteShift), iColorMode);
        // Luminance floor: interior veins stay visible in every palette phase
        vein = max(vein, vec3(0.28, 0.30, 0.36));
        color = deep * (0.06 + 0.22 * s1 + 0.10 * s2)
              + vein * (s1 * s1 * 0.20
                        + 0.22 * bands * (0.3 + 0.7 * trapStrength));
    } else {
        // --- Exterior: smooth iteration + DE glow + DE contour texture -------
        float log_zn = 0.5 * log(m2);                       // ln|z|
        float nu = log(log_zn / log(2.0)) / log(2.0);
        float smoothIter = iter + 1.0 - nu;

        // Log-scaled color index (even band distribution at all depths).
        // Band count grows with zoom depth so deep frames - where the
        // smooth-iteration range across the frame shrinks - keep full
        // palette variation instead of washing out to one hue.
        float bandCycles = 3.0 + 0.55 * max(0.0, -lz);
        float tc = log(smoothIter + 1.0) / log(maxIter + 1.0);
        tc = tc * bandCycles + paletteShift;
        color = getColor(fract(tc), iColorMode);

        // Distance estimate: d = |z| * ln|z| / |dz|
        float d = sqrt(m2) * log_zn / max(length(dz), 1e-20);
        float px = 2.0 * scale / iResolution.y;             // pixel size

        // Micro-texture: log-spaced DE contour bands fill the far field
        float band = 0.5 + 0.5 * sin(log2(max(d, 1e-14)) * 3.2 - iTime * 0.15);
        color *= mix(1.0, 0.62 + 0.72 * band, detailMix);
        // Additive floor so the bands stay visible inside dark palette zones
        color += vec3(0.06, 0.10, 0.16) * band * detailMix;

        // Warm glow hugging the boundary filaments
        float glow = exp2(-d / (px * 30.0));
        color += getColor(fract(0.1 + paletteShift), iColorMode) * glow * 0.4;
    }

    // Gentle vignette to focus the frame
    float r = length(fragCoord - 0.5);
    color *= 1.0 - smoothstep(0.55, 1.0, r) * 0.30;

    fragColor = vec4(color, 1.0);
}

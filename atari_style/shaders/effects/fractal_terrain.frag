#version 330 core
/*
 * Fractal Terrain Composite Fragment Shader
 *
 * Low-altitude flight THROUGH raymarched Mandelbrot/Julia structure.
 *
 * v2: the escape dynamics ARE the landscape. Instead of smoothing the
 * escape time into dune-like mountains, the height field exposes the
 * raw structure of the iteration:
 *   - iteration level-sets become stepped TERRACES with sharp risers,
 *   - the set boundary filaments rise into tall SPINE WALLS,
 *   - orbit-trap pinches ridge the filament dendrites,
 *   - the non-escaping interior drops to a sunken, trap-ribbed floor.
 *
 * Construction:
 *   - fractalField() iterates z' = z^2 + mix(p, c_julia, morph) and
 *     returns (height, normalized smooth-iteration, orbit-trap dist).
 *   - Each pixel marches its ray with distance-growing steps until it
 *     dips below the terrain, then bisects for a crisp hit.
 *   - Surface color comes from the MATH, not altitude: the palette
 *     cycles with the smooth iteration count so escape contours stripe
 *     the terrain like strata, orbit trap modulates the detail, and
 *     thin bright contour lines mark each iteration band edge.
 *   - Near-boundary ground glows emissively (strongest on steep walls
 *     and in crevasses) — skimming a living fractal circuit — while a
 *     dark moody sky and distance fog keep the depth reading.
 *   - The camera flies the main cardioid boundary, heading aligned to
 *     the path tangent, banking into the periodic quick turns.
 *
 * Motion stays C1-continuous (no time*varyingSpeed products — see the
 * flux_spiral jerkiness fix).
 *
 * Performance: tuned for llvmpipe (software GL). MAX_ITER is low (the
 * mountain SHAPE doesn't need deep iteration), march steps grow with
 * distance, and sky rays exit after a few steps once above peak height.
 *
 * Uniforms:
 *   iTime       - Animation time
 *   iResolution - Viewport resolution (width, height)
 *   iParams     - (flight_speed, altitude, morph_speed, fog)
 *   iColorMode  - Color palette selector (0-3)
 */

uniform float iTime;
uniform vec2 iResolution;
uniform vec4 iParams;
uniform int iColorMode;

in vec2 fragCoord;
out vec4 fragColor;

const float TAU = 6.28318530717958647692;
const int MAX_ITER = 36;       // shape detail; low keeps marching affordable
const int MARCH_STEPS = 32;
const float T_MAX = 4.5;       // far clip in fractal-plane units
const float H_AMP = 0.28;      // world height of the tallest peaks

vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(TAU * (c * t + d));
}

vec3 getColor(float t, int mode) {
    if (mode == 0) {
        // Sunrise flight: deep blue to gold
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

// Monotonic smoothstep phase pulses: occasional quick turns, C1-continuous
float pulsedPhase(float t, float period, float pulseLen) {
    float n = floor(t / period);
    float f = t - n * period;
    return n + smoothstep(0.0, pulseLen, f);
}

// Bell-shaped window over each pulse: couples banking to the turn
float pulseWindow(float t, float period, float pulseLen) {
    float f = t - floor(t / period) * period;
    return smoothstep(0.0, pulseLen * 0.45, f)
         * (1.0 - smoothstep(pulseLen * 0.55, pulseLen * 1.2, f));
}

// Main cardioid boundary point and its tangent
vec2 cardioid(float a) {
    return vec2(0.5 * cos(a) - 0.25 * cos(2.0 * a),
                0.5 * sin(a) - 0.25 * sin(2.0 * a));
}

vec2 cardioidTangent(float a) {
    return normalize(vec2(-0.5 * sin(a) + 0.5 * sin(2.0 * a),
                           0.5 * cos(a) - 0.5 * cos(2.0 * a)));
}

// The fractal field that drives EVERYTHING:
//   .x  height in [0,1]   — terraces + boundary spines + sunken interior
//   .y  normalized smooth iteration in [0,1] (1.0 = interior / boundary)
//   .z  orbit-trap distance (filament proximity)
vec3 fractalField(vec2 p, vec2 cJulia, float morph) {
    vec2 z = p;
    vec2 c = mix(p, cJulia, morph);
    float m2 = 0.0;
    float trap = 1e9;
    int i;
    for (i = 0; i < MAX_ITER; i++) {
        z = vec2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y) + c;
        m2 = dot(z, z);
        trap = min(trap, m2);
        if (m2 > 64.0) break;
    }
    float trapD = sqrt(trap);
    if (i >= MAX_ITER) {
        // Interior: sunken basin floor ribbed by CONCENTRIC orbit-trap
        // contour ridges (a plain exp() here swells like smooth dunes —
        // the cosine snaps it into circuit-board rings)
        float ribs = exp(-trapD * 2.0) * (0.5 + 0.5 * cos(TAU * trapD * 5.0));
        return vec3(0.05 + 0.11 * ribs, 1.0, trapD);
    }
    // Clamped smooth iteration (first-iteration escapes go negative ->
    // sqrt(NaN) -> black artifacts; clamp reads as sea level far out)
    float si = max(0.0, float(i) + 1.0 - log2(log(m2) * 0.5));
    float n = si / float(MAX_ITER);
    // Stepped terraces: plateaus on iteration level-sets, sharp risers
    float sStep = floor(si) + smoothstep(0.55, 0.95, fract(si));
    float terrace = sStep / float(MAX_ITER);
    // Boundary spine walls: filaments shoot up hard near the set — driven
    // by the STEPPED iteration so they climb as discrete ziggurat cliffs,
    // and the ramp is a pure cubic (NOT smoothstep: its saturating top
    // rounds the summits into dunes — exactly what we're killing). The
    // cliff size per iteration band GROWS toward the boundary.
    float wall = pow(max(terrace - 0.30, 0.0) / 0.70, 3.0);
    // Dendrite ridges: orbit-trap pinches trace the filament arms
    float dendrite = exp(-trapD * 4.0) * smoothstep(0.35, 0.75, n);
    float h = terrace * 0.40 + wall * 0.50 + dendrite * 0.22;
    // Alternating-parity ridges: every OTHER iteration band rides higher,
    // so each escape level-set is a real cliff edge. The per-band steps of
    // the ramp alone are ~0.005 world units — invisible; this corduroy is
    // what makes the slopes read as contour terraces instead of dunes.
    float parity = mod(floor(si), 2.0) * 2.0 - 1.0;
    h += parity * (0.035 + 0.09 * smoothstep(0.30, 0.85, n))
       * smoothstep(0.08, 0.35, n);
    return vec3(clamp(h, 0.0, 1.0), n, trapD);
}

// Geometry height in world units: full range, no soft-cap — spines tower
// above eye level and break the horizon (the camera's terrain-following
// clearance band keeps it out of the rock)
float worldH(vec2 p, vec2 cJulia, float morph) {
    return fractalField(p, cJulia, morph).x * H_AMP;
}

void main() {
    float flightSpeed = iParams.x;   // journey speed (default ~0.4)
    float altitude    = iParams.y;   // camera height (~0.35)
    float morphSpeed  = iParams.z;   // Mandelbrot<->Julia morph rate (~0.25)
    float fogAmt      = iParams.w;   // fog density (~0.5)

    float t = iTime;

    // --- Flight path along the cardioid boundary ---------------------------
    float a = t * 0.05 * flightSpeed * 2.5
            + 0.4 * pulsedPhase(t, 12.0, 2.0)
            + 2.1;
    vec2 pathPos = cardioid(a) * 1.18;          // ride the filament zone
    vec2 tangent = cardioidTangent(a);

    vec2 cJulia = cardioid(a - 0.35);
    float mraw = 0.5 + 0.5 * sin(t * morphSpeed * 0.6 - 1.2);
    float morph = smoothstep(0.1, 0.9, mraw);

    // --- Camera -------------------------------------------------------------
    float heading = atan(tangent.y, tangent.x);

    // Terrain-following flight: hold a clearance band above the ground at
    // the camera, with a look-ahead sample so we climb before cliff walls
    // instead of into them. Ridges beside and ahead can still rise above
    // eye level — that's the "through the mountains" drama.
    // (v2 terrain is spikier — a mid look-ahead sample catches the thin
    // spine walls the two endpoint samples used to straddle)
    float gHere  = worldH(pathPos, cJulia, morph);
    float gMid   = worldH(pathPos + tangent * 0.05, cJulia, morph);
    float gAhead = worldH(pathPos + tangent * 0.10, cJulia, morph);
    float camH = max(gHere, max(gMid, gAhead))
               + 0.045 + altitude * 0.15
               + 0.012 * sin(t * 0.4)
               + 0.03 * pulseWindow(t, 12.0, 2.0);

    // Dynamic pitch: deeper base with slow dive/climb cycles (two slow
    // incommensurate sines, C1-continuous) — dives near -0.30 rad, eases
    // up to about -0.08 rad on climbs so the horizon visibly travels
    float pitch = -0.19 + 0.08 * sin(t * 0.11) + 0.03 * sin(t * 0.23 + 1.0);

    float bank = 0.50 * pulseWindow(t, 12.0, 2.0) + 0.05 * sin(t * 0.31);

    float ch = cos(heading), sh = sin(heading);
    float cp = cos(pitch),   sp = sin(pitch);
    vec3 fwd = vec3(ch * cp, sh * cp, sp);
    vec3 right0 = normalize(cross(fwd, vec3(0.0, 0.0, 1.0)));
    vec3 up0 = cross(right0, fwd);
    float cb = cos(bank), sb = sin(bank);
    vec3 right = right0 * cb + up0 * sb;
    vec3 up = -right0 * sb + up0 * cb;

    vec2 uv = fragCoord - 0.5;
    uv.x *= iResolution.x / iResolution.y;
    vec3 ray = normalize(fwd + uv.x * right * 1.15 + uv.y * up * 1.15);

    vec3 camPos = vec3(pathPos, camH);

    // Sun low ahead-left
    vec3 sunDir = normalize(vec3(ch * 0.7 - sh * 0.4, sh * 0.7 + ch * 0.4, 0.30));

    // Sky (also the fog tint): dark and moody so the glowing structure
    // carries the frame — a dim band of palette color at the horizon
    // fading to near-black overhead
    float horizon = smoothstep(-0.10, 0.45, ray.z);
    vec3 skyLow  = getColor(0.78, iColorMode) * 0.28;
    vec3 skyHigh = vec3(0.012, 0.014, 0.035);
    vec3 sky = mix(skyLow, skyHigh, horizon);
    float sunDot = max(dot(ray, sunDir), 0.0);
    sky += vec3(1.0, 0.85, 0.6) * (pow(sunDot, 64.0) * 0.30 + pow(sunDot, 12.0) * 0.03);

    // --- Raymarch the height field ------------------------------------------
    float tRay = 0.035;
    float tHit = -1.0;
    float tPrev = tRay;
    for (int s = 0; s < MARCH_STEPS; s++) {
        vec3 pos = camPos + ray * tRay;
        // Climbing rays that clear the peaks can never hit again
        if (pos.z > H_AMP + 0.01 && ray.z >= 0.0) break;
        if (pos.z < worldH(pos.xy, cJulia, morph)) {
            tHit = tRay;
            break;
        }
        tPrev = tRay;
        tRay += 0.014 + tRay * 0.085;     // steps grow with distance
        if (tRay > T_MAX) break;
    }

    vec3 color;
    if (tHit < 0.0) {
        color = sky;
    } else {
        // Bisect [tPrev, tHit] for a crisp surface
        float lo = tPrev, hi = tHit;
        for (int b = 0; b < 8; b++) {
            float mid = 0.5 * (lo + hi);
            vec3 pos = camPos + ray * mid;
            if (pos.z < worldH(pos.xy, cJulia, morph)) hi = mid;
            else lo = mid;
        }
        float dist = 0.5 * (lo + hi);
        vec3 hitPos = camPos + ray * dist;
        vec3 fld = fractalField(hitPos.xy, cJulia, morph);
        float h = fld.x;
        float n = fld.y;                       // boundary proximity
        float si = n * float(MAX_ITER);        // smooth iteration count
        float trapD = fld.z;

        // Finite-difference normal; eps widens with distance (anti-shimmer)
        float eps = max(0.0025, dist * 0.006);
        float hW = h * H_AMP;
        float hx = worldH(hitPos.xy + vec2(eps, 0.0), cJulia, morph);
        float hy = worldH(hitPos.xy + vec2(0.0, eps), cJulia, morph);
        vec3 normal = normalize(vec3((hW - hx) / eps, (hW - hy) / eps, 1.0));

        float diffuse = max(dot(normal, sunDir), 0.0);
        float spec = pow(max(dot(reflect(-sunDir, normal), -ray), 0.0), 18.0);

        // --- Color from the MATH, not the altitude --------------------------
        // Each iteration band gets ONE palette color (quantized on floor(si))
        // so the terrain is striped by discrete escape-contour strata, not a
        // smooth rainbow. Orbit trap shifts the hue along the dendrites.
        float band = floor(si);
        float colorT = fract(band * 0.17 + exp(-trapD * 2.0) * 0.15);
        vec3 base = getColor(colorT, iColorMode);
        // Alternate-band brightness striping survives even where distant
        // bands get narrower than the march sampling can resolve
        base *= 0.74 + 0.26 * mod(band, 2.0);
        // Brightness ramps across each terrace, snapping at the riser, and a
        // thin bright contour line marks every iteration level-set
        base *= 0.75 + 0.25 * fract(si);
        float bandEdge = smoothstep(0.44, 0.5, abs(fract(si) - 0.5));
        base += getColor(fract(colorT + 0.5), iColorMode) * bandEdge * 0.30;
        // Fine sub-band contour ripple: even the wide low-iteration strata
        // stay visibly wrapped by level-sets of the escape field (kills any
        // residual "smooth dune" reading on the lowland plateaus)
        base *= 0.87 + 0.13 * cos(TAU * si * 3.0);
        // Spine rock near the boundary darkens so the glow reads as edges
        base *= mix(1.0, 0.40, smoothstep(0.70, 0.95, n));
        // Dark riser faces between terraces give the steps definition
        float facet = mix(0.45, 1.0, smoothstep(0.2, 0.9, normal.z));
        color = base * (0.14 + 0.62 * diffuse) * facet
              + vec3(1.0, 0.95, 0.85) * spec * 0.10;
        // Far-exterior lowlands fall to a dark abyssal floor
        color = mix(sky * 0.35, color, smoothstep(0.015, 0.05, h));

        // --- Emissive boundary glow ------------------------------------------
        // Ground hugging the set boundary (highest iterations / interior) and
        // the tightest orbit-trap filaments runs hot — strongest on steep
        // walls and crevasse edges, like circuitry under the rock
        float boundary = smoothstep(0.86, 0.995, n);
        float filament = exp(-trapD * 5.0) * smoothstep(0.50, 0.90, n);
        float crevasse = 0.4 + 0.9 * (1.0 - normal.z);
        vec3 glowC = getColor(0.92, iColorMode) * 1.25;
        vec3 emissive = glowC * (boundary * 0.55 + filament * 0.40) * crevasse;
        // Interior basin floors (n==1 everywhere) must NOT wash out into a
        // uniform glow-dune: gate their glow to THIN orbit-trap veins so the
        // floor stays dark with bright circuitry running through it
        emissive *= mix(1.0, exp(-trapD * 10.0), step(0.9995, n));

        // Distance fog into the dark sky; basins hold a touch more haze.
        // The glow is added after fog (attenuated, not erased) so distant
        // boundary walls still smoulder through the murk.
        float fog = 1.0 - exp(-dist * dist * (0.30 + fogAmt * 0.70));
        fog = clamp(fog + (1.0 - h) * 0.08 * fogAmt, 0.0, 1.0);
        color = mix(color, sky, fog);
        color += emissive * (1.0 - fog * 0.65);
    }

    // Gentle vignette
    float r = length(fragCoord - 0.5);
    color *= 1.0 - smoothstep(0.6, 1.05, r) * 0.30;

    fragColor = vec4(color, 1.0);
}

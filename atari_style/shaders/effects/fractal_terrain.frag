#version 330 core
/*
 * Fractal Terrain Composite Fragment Shader
 *
 * Low-altitude flight THROUGH raymarched Mandelbrot/Julia mountains.
 *
 * Unlike a flat-plane projection with relief shading (which reads as
 * "flat mountains"), this raymarches the escape-time height field as
 * REAL displaced geometry: peaks rise, ridges occlude one another and
 * layer into the fog, and summits can break the horizon.
 *
 * Construction:
 *   - terrainH() maps the smooth escape-time of the morphing fractal
 *     z' = z^2 + mix(p, c_julia, morph) to a height in [0, H_AMP].
 *   - Each pixel marches its ray with distance-growing steps until it
 *     dips below the terrain, then bisects for a crisp hit.
 *   - Hit points get finite-difference normals, sun diffuse + specular,
 *     height-banded palette color with snow caps, and water below the
 *     shoreline. Distance fog blends everything into the sky.
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

// Terrain height in [0,1] from smooth escape time of the morphing fractal
float terrainH(vec2 p, vec2 cJulia, float morph) {
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
    if (i >= MAX_ITER) {
        // Interior: not a flat mesa — carve it with the orbit trap so the
        // high plateaus read as ridged highlands, not blank snowfields
        return 0.80 + 0.20 * exp(-sqrt(trap) * 1.5);
    }
    // Clamped smooth iteration (first-iteration escapes go negative ->
    // sqrt(NaN) -> black artifacts; clamp reads as sea level far out)
    float si = max(0.0, float(i) + 1.0 - log2(log(m2) * 0.5));
    return sqrt(si / float(MAX_ITER));
}

// Geometry height in world units: full range, no soft-cap — summits tower
// above eye level and break the horizon (the camera's terrain-following
// clearance band keeps it out of the rock)
float worldH(vec2 p, vec2 cJulia, float morph) {
    return terrainH(p, cJulia, morph) * H_AMP;
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
    float gHere  = worldH(pathPos, cJulia, morph);
    float gAhead = worldH(pathPos + tangent * 0.10, cJulia, morph);
    float camH = max(gHere, gAhead)
               + 0.035 + altitude * 0.15
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

    // Sky (also the fog tint)
    float horizon = smoothstep(-0.10, 0.45, ray.z);
    vec3 skyLow  = getColor(0.78, iColorMode) * 0.95;
    vec3 skyHigh = getColor(0.55, iColorMode) * 0.40;
    vec3 sky = mix(skyLow, skyHigh, horizon);
    float sunDot = max(dot(ray, sunDir), 0.0);
    sky += vec3(1.0, 0.9, 0.7) * (pow(sunDot, 48.0) * 0.9 + pow(sunDot, 6.0) * 0.18);

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
        float h = terrainH(hitPos.xy, cJulia, morph);

        // Finite-difference normal; eps widens with distance (anti-shimmer)
        float eps = max(0.0025, dist * 0.006);
        float hW  = worldH(hitPos.xy, cJulia, morph);
        float hx = worldH(hitPos.xy + vec2(eps, 0.0), cJulia, morph);
        float hy = worldH(hitPos.xy + vec2(0.0, eps), cJulia, morph);
        vec3 normal = normalize(vec3((hW - hx) / eps, (hW - hy) / eps, 1.0));

        float diffuse = max(dot(normal, sunDir), 0.0);
        float spec = pow(max(dot(reflect(-sunDir, normal), -ray), 0.0), 18.0);

        if (h < 0.04) {
            // Water: mirror of the sky with sun glints
            color = sky * 0.45 + getColor(0.12, iColorMode) * 0.15
                  + vec3(1.0, 0.9, 0.7) * spec * 0.8;
        } else {
            // Height-banded terrain color, brighter and snowier up high
            float colorT = fract(h * 1.7 + 0.05);
            vec3 base = getColor(colorT, iColorMode);
            color = base * (0.22 + 0.85 * diffuse)
                  + vec3(1.0, 0.95, 0.85) * spec * 0.30;
            // Snow caps only on the genuinely high, gentle ridges
            float snow = smoothstep(0.88, 0.985, h) * smoothstep(0.55, 0.85, normal.z);
            color = mix(color, vec3(0.92, 0.94, 0.98) * (0.45 + 0.6 * diffuse), snow);
            // Glowing shoreline
            color += getColor(0.9, iColorMode) * smoothstep(0.10, 0.04, h) * 0.25;
        }

        // Distance fog into the sky; valleys hold a touch more haze
        float fog = 1.0 - exp(-dist * dist * (0.30 + fogAmt * 0.70));
        fog = clamp(fog + (1.0 - h) * 0.08 * fogAmt, 0.0, 1.0);
        color = mix(color, sky, fog);
    }

    // Gentle vignette
    float r = length(fragCoord - 0.5);
    color *= 1.0 - smoothstep(0.6, 1.05, r) * 0.30;

    fragColor = vec4(color, 1.0);
}

#version 330 core
/*
 * Fractal Terrain Composite Fragment Shader
 *
 * Low-altitude flight THROUGH a Mandelbrot/Julia mountain landscape —
 * the perspective sibling of fractal_flight (which looks straight down).
 *
 * Construction (classic demoscene terrain flyover):
 *   - A camera flies above the fractal plane along the main cardioid
 *     boundary, heading aligned with the path tangent (windshield view,
 *     not map view).
 *   - Each pixel casts a ray; rays pointing below the horizon intersect
 *     the ground plane and sample the fractal escape-time height field
 *     there. Rays above the horizon render sky + sun.
 *   - Relief lighting from screen-space finite differences, distance fog
 *     blending terrain into the sky at the horizon.
 *   - Banking is COUPLED to the turns: each pulsedPhase quick-turn rolls
 *     the camera into the curve like a coordinated banked turn.
 *
 * Motion stays C1-continuous throughout (no time*varyingSpeed products —
 * see flux_spiral jerkiness fix).
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
const int MAX_ITER = 80;
const float T_MAX = 6.0;   // far clip in fractal-plane units

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

// Bell-shaped window over each pulse, used to couple banking to the turn
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

// Smooth escape-time height for the morphing fractal (0 = interior sea)
float fractalHeight(vec2 p, vec2 cJulia, float morph) {
    vec2 z = p;
    vec2 c = mix(p, cJulia, morph);
    float m2 = 0.0;
    int i;
    for (i = 0; i < MAX_ITER; i++) {
        z = vec2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y) + c;
        m2 = dot(z, z);
        if (m2 > 64.0) break;
    }
    if (i >= MAX_ITER) return 0.0;
    // Clamp: points that escape on the first iteration with large |z|^2
    // make the smooth-iteration term negative -> sqrt(NaN) -> black ring
    // at the horizon. Clamping to 0 reads as sea level in the far field.
    float si = max(0.0, float(i) + 1.0 - log2(log(m2) * 0.5));
    return sqrt(si / float(MAX_ITER));
}

void main() {
    float flightSpeed = iParams.x;   // journey speed (default ~0.4)
    float altitude    = iParams.y;   // camera height above plane (~0.35)
    float morphSpeed  = iParams.z;   // Mandelbrot<->Julia morph rate (~0.25)
    float fogAmt      = iParams.w;   // fog density (~0.5)

    float t = iTime;

    // --- Flight path along the cardioid boundary ---------------------------
    float a = t * 0.05 * flightSpeed * 2.5
            + 0.4 * pulsedPhase(t, 12.0, 2.0)
            + 2.1;
    vec2 pathPos = cardioid(a) * 1.10;          // skim the filament zone
    vec2 tangent = cardioidTangent(a);

    // Julia parameter rides the same boundary, slightly behind the camera
    vec2 cJulia = cardioid(a - 0.35);
    float mraw = 0.5 + 0.5 * sin(t * morphSpeed * 0.6 - 1.2);
    float morph = smoothstep(0.1, 0.9, mraw);

    // --- Camera basis -------------------------------------------------------
    // World: x/y = fractal plane, z = up. Heading follows the path tangent.
    float heading = atan(tangent.y, tangent.x);
    float camH = 0.12 + altitude * 0.5;

    // Gentle altitude bob + slight extra climb during turns
    camH += 0.02 * sin(t * 0.4) + 0.05 * pulseWindow(t, 12.0, 2.0);

    // Pitch: looking ahead and down toward the terrain
    float pitch = -0.30 - 0.10 * sin(t * 0.13);

    // Bank coupled to the quick turns (roll into the curve), plus tiny sway
    float bank = 0.55 * pulseWindow(t, 12.0, 2.0) + 0.06 * sin(t * 0.31);

    float ch = cos(heading), sh = sin(heading);
    float cp = cos(pitch),   sp = sin(pitch);
    vec3 fwd = vec3(ch * cp, sh * cp, sp);
    vec3 right0 = normalize(cross(fwd, vec3(0.0, 0.0, 1.0)));
    vec3 up0 = cross(right0, fwd);
    float cb = cos(bank), sb = sin(bank);
    vec3 right = right0 * cb + up0 * sb;
    vec3 up = -right0 * sb + up0 * cb;

    // --- Ray for this pixel -------------------------------------------------
    vec2 uv = fragCoord - 0.5;
    uv.x *= iResolution.x / iResolution.y;
    vec3 ray = normalize(fwd + uv.x * right * 1.2 + uv.y * up * 1.2);

    vec3 camPos = vec3(pathPos, camH);

    // Sun direction: low ahead-left of the flight path
    vec3 sunDir = normalize(vec3(ch * 0.7 - sh * 0.4, sh * 0.7 + ch * 0.4, 0.35));

    // Sky (also the fog tint)
    float horizon = smoothstep(-0.12, 0.45, ray.z);
    vec3 skyLow  = getColor(0.78, iColorMode) * 0.9;
    vec3 skyHigh = getColor(0.55, iColorMode) * 0.45;
    vec3 sky = mix(skyLow, skyHigh, horizon);
    float sunDot = max(dot(ray, sunDir), 0.0);
    sky += vec3(1.0, 0.9, 0.7) * (pow(sunDot, 48.0) * 0.9 + pow(sunDot, 6.0) * 0.18);

    vec3 color;
    if (ray.z > -0.015) {
        // Above (or skimming) the horizon: pure sky
        color = sky;
    } else {
        // Intersect the ground plane z = 0
        float dist = camH / -ray.z;
        if (dist > T_MAX) {
            color = sky;
        } else {
            vec2 ground = camPos.xy + ray.xy * dist;

            // Height + screen-space normal; widen eps with distance to
            // soften far-field shimmer
            float eps = max(0.0015, dist * 2.2 / iResolution.y);
            float h  = fractalHeight(ground, cJulia, morph);
            float hx = fractalHeight(ground + vec2(eps, 0.0), cJulia, morph);
            float hy = fractalHeight(ground + vec2(0.0, eps), cJulia, morph);

            float hscale = 22.0;
            vec3 normal = normalize(vec3((h - hx) * hscale, (h - hy) * hscale, 1.0));

            float diffuse = max(dot(normal, sunDir), 0.0);
            float spec = pow(max(dot(reflect(-sunDir, normal), -ray), 0.0), 20.0);

            float colorT = fract(h * 2.8 + t * 0.02);
            vec3 base = getColor(colorT, iColorMode);

            if (h <= 0.0) {
                // Interior "sea": dark mirror picking up sky + sun glints
                color = getColor(0.12, iColorMode) * 0.10 + sky * 0.25
                      + vec3(1.0, 0.9, 0.7) * spec * 0.45;
            } else {
                color = base * (0.30 + 0.80 * diffuse)
                      + vec3(1.0, 0.95, 0.85) * spec * 0.35;
                // Glowing surf line where terrain meets the sea
                color += getColor(0.9, iColorMode) * smoothstep(0.22, 0.0, h) * 0.30;
            }

            // Distance fog into the sky color
            float fog = 1.0 - exp(-dist * dist * (0.25 + fogAmt * 0.55));
            color = mix(color, sky, clamp(fog, 0.0, 1.0));
        }
    }

    // Gentle vignette
    float r = length(fragCoord - 0.5);
    color *= 1.0 - smoothstep(0.6, 1.05, r) * 0.30;

    fragColor = vec4(color, 1.0);
}

#version 330 core
/*
 * Fractal Flight Composite Fragment Shader
 *
 * A continuous "aerial" journey over a Mandelbrot/Julia hybrid landscape.
 *
 * Three ideas combine:
 *
 * 1. MORPH — iterate z' = z^2 + mix(pixel, c_julia, morph) with z0 = pixel.
 *    morph = 0 renders the Mandelbrot set, morph = 1 renders the Julia set
 *    of c_julia, and intermediate values blend the two continuously.
 *
 * 2. ALWAYS-INTERESTING PARAMETER PATH — c_julia travels along the main
 *    cardioid boundary c(a) = e^{ia}/2 - e^{2ia}/4. Boundary points produce
 *    Julia sets at the edge of connectivity (maximum visual complexity),
 *    and the camera flies along the same boundary on the Mandelbrot side,
 *    so the frame is never empty at either end of the morph.
 *
 * 3. PSEUDO-3D RELIEF — the smooth escape-time field is treated as a height
 *    map; screen-space finite differences give a surface normal used for
 *    diffuse + specular lighting, turning the fractal into terrain.
 *
 * Motion design: all camera terms (pan, zoom breathing, bank) are bounded,
 * C1-continuous functions of time — no speed*time products (see flux_spiral
 * jerkiness fix). Occasional "quick moves" are smoothstep ramps that each
 * permanently advance a phase by a fixed amount: fast but never discontinuous.
 *
 * Uniforms:
 *   iTime       - Animation time
 *   iResolution - Viewport resolution (width, height)
 *   iParams     - (flight_speed, morph_speed, relief, zoom_amp)
 *   iColorMode  - Color palette selector (0-3)
 */

uniform float iTime;
uniform vec2 iResolution;
uniform vec4 iParams;
uniform int iColorMode;

in vec2 fragCoord;
out vec4 fragColor;

const float TAU = 6.28318530717958647692;
const int MAX_ITER = 96;

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

// Each pulse advances a phase by 1.0 over PULSE_LEN seconds, then rests
// until the next period. C1-continuous (smoothstep has zero slope at both
// ends), monotonic — "occasional quick movement" without any jump.
float pulsedPhase(float t, float period, float pulseLen) {
    float n = floor(t / period);
    float f = t - n * period;
    return n + smoothstep(0.0, pulseLen, f);
}

// Smooth escape-time height for the morphing fractal.
// Returns (height, orbitTrap): height is 0 for interior points, and
// orbitTrap (min distance of the orbit to a unit circle) gives the
// interior "sea" luminous structure instead of dead black.
vec2 fractalHeight(vec2 p, vec2 cJulia, float morph) {
    vec2 z = p;
    vec2 c = mix(p, cJulia, morph);
    float m2 = 0.0;
    float trap = 1e9;
    int i;
    for (i = 0; i < MAX_ITER; i++) {
        z = vec2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y) + c;
        m2 = dot(z, z);
        trap = min(trap, abs(sqrt(m2) - 0.25));
        if (m2 > 64.0) break;
    }
    if (i >= MAX_ITER) return vec2(0.0, trap);  // interior: sea level
    // Smooth iteration count, normalized and eased for terrain-like slopes
    float si = float(i) + 1.0 - log2(log(m2) * 0.5);
    return vec2(sqrt(si / float(MAX_ITER)), trap);
}

void main() {
    float flightSpeed = iParams.x;   // overall journey speed (default ~0.4)
    float morphSpeed  = iParams.y;   // Mandelbrot<->Julia morph rate (~0.3)
    float relief      = iParams.z;   // lighting strength (~0.7)
    float zoomAmp     = iParams.w;   // zoom breathing depth (~0.5)

    float t = iTime;

    // --- Flight path ------------------------------------------------------
    // Cardioid parameter drifts slowly; quick pulses add occasional banked
    // "turns" (every ~11s) on top of the steady cruise.
    float a = t * 0.045 * flightSpeed * 2.5
            + 0.35 * pulsedPhase(t, 11.0, 1.6)
            + 2.1;
    vec2 cJulia = vec2(0.5 * cos(a) - 0.25 * cos(2.0 * a),
                       0.5 * sin(a) - 0.25 * sin(2.0 * a));

    // Morph: eased oscillation, lingering near the pure sets at both ends
    float mraw = 0.5 + 0.5 * sin(t * morphSpeed * 0.6 - 1.2);
    float morph = smoothstep(0.08, 0.92, mraw);

    // Camera target: fly along the cardioid boundary on the Mandelbrot side,
    // settle toward the origin (where Julia structure lives) as morph -> 1.
    // Bias the Mandelbrot-phase camera slightly OUTSIDE the boundary (into
    // the filament zone) so the frame shows coastline detail, not flat
    // interior.
    vec2 outward = cJulia * 1.22 + vec2(0.03, 0.0);
    vec2 center = mix(outward, vec2(0.0), morph);

    // Zoom breathes slowly; a gentle surge accompanies each pulse turn.
    // Pull back during the Julia phase so the whole dendrite silhouette is
    // in frame (recognizable shape), dive closer along the Mandelbrot coast.
    float zoomPhase = sin(t * 0.11 * flightSpeed * 2.5 + 0.7);
    float zoom = exp2(1.1 + zoomAmp * 1.4 * zoomPhase
                      + 0.25 * sin(pulsedPhase(t, 11.0, 1.6) * TAU)
                      - 0.8 * morph);

    // Slow continuous bank (roll), like a long coordinated turn
    float bank = 0.12 * sin(t * 0.07) + t * 0.015;

    // --- Screen to fractal plane -------------------------------------------
    vec2 uv = fragCoord - 0.5;
    uv.x *= iResolution.x / iResolution.y;
    float cb = cos(bank), sb = sin(bank);
    uv = vec2(uv.x * cb - uv.y * sb, uv.x * sb + uv.y * cb);
    float scale = 2.6 / zoom;
    vec2 p = center + uv * scale;

    // --- Height field + screen-space normal --------------------------------
    float eps = scale * 1.5 / iResolution.y;
    vec2 ht = fractalHeight(p, cJulia, morph);
    float h = ht.x;
    float trap = ht.y;
    float hx = fractalHeight(p + vec2(eps, 0.0), cJulia, morph).x;
    float hy = fractalHeight(p + vec2(0.0, eps), cJulia, morph).x;

    float hscale = 18.0 * relief;
    vec3 normal = normalize(vec3((h - hx) * hscale, (h - hy) * hscale, 1.0));

    // Sun low over the terrain, slowly circling
    vec3 lightDir = normalize(vec3(cos(t * 0.05) * 0.6, sin(t * 0.05) * 0.6, 0.55));
    float diffuse = max(dot(normal, lightDir), 0.0);
    vec3 viewDir = vec3(0.0, 0.0, 1.0);
    float spec = pow(max(dot(reflect(-lightDir, normal), viewDir), 0.0), 24.0);

    // --- Color --------------------------------------------------------------
    float colorT = fract(h * 2.8 + t * 0.02);
    vec3 base = getColor(colorT, iColorMode);

    vec3 color;
    if (h <= 0.0) {
        // Interior "sea": dark water with luminous orbit-trap currents.
        // Must stay clearly darker than the terrain so the coastline reads.
        float seaT = exp(-trap * 3.0);
        color = getColor(0.12, iColorMode) * (0.05 + seaT * 0.35)
              + getColor(0.9, iColorMode) * seaT * seaT * 0.30;
    } else {
        color = base * (0.35 + 0.75 * diffuse) + vec3(1.0, 0.95, 0.85) * spec * 0.6;
        // Atmospheric glow near the coastline (low heights)
        color += getColor(0.9, iColorMode) * smoothstep(0.25, 0.0, h) * 0.25;
    }

    // Gentle vignette to focus the frame
    float r = length(fragCoord - 0.5);
    color *= 1.0 - smoothstep(0.55, 1.0, r) * 0.35;

    fragColor = vec4(color, 1.0);
}

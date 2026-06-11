#version 330 core
/*
 * Quaternion Julia Composite Fragment Shader
 *
 * True 3D fractal flight: a raymarched quaternion Julia set
 * q -> q^2 + c (w = 0 slice of the 4D set) that continuously MORPHS
 * while a choreographed camera flies AROUND it, swoops OVER its
 * surface, and passes THROUGH the gaps between its limbs.
 *
 * Construction:
 *   - julDE() iterates the quaternion map with the scalar derivative
 *     recurrence |dq'| = 2|q||dq|, giving the standard distance
 *     estimate DE = 0.5 |q| ln|q| / |dq|. Quaternion squaring is pure
 *     multiply/add (no trig) - friendly to llvmpipe software GL.
 *   - c(t) wanders quaternion space on four slow incommensurate sines
 *     with |c| held in roughly [0.45, 0.85]: the set stays connected-ish
 *     and visibly grows, splits and twists limbs over ~15-25 s spans.
 *   - The camera rides spherical coordinates whose radius breathes on a
 *     ~45 s cycle between far orbit (~2.5 set-radii) and sub-radius
 *     passes; elevation cycles on an incommensurate period for the
 *     over-the-pole swoops. All terms are bounded C1 sines. A small
 *     DE-based push keeps the camera from ever sitting inside rock.
 *   - Shading: tetrahedron-technique DE-gradient normals, key + sky
 *     fill lighting, 5-tap DE ambient occlusion, orbit-trap surface
 *     coloring through palette(), boundary glow from the closest-
 *     approach of marched rays, and distance fog into a dark sky.
 *
 * Performance: tuned for llvmpipe. 72 march steps with DE-proportional
 * stepping and bounding-sphere clip, 9 fractal iterations, escape
 * radius^2 = 16, normals = 4 extra DE evals, AO = 5.
 *
 * Uniforms:
 *   iTime       - Animation time
 *   iResolution - Viewport resolution (width, height)
 *   iParams     - (flight_speed, morph_speed, detail, fog_glow)
 *   iColorMode  - Color palette selector (0-3)
 */

uniform float iTime;
uniform vec2 iResolution;
uniform vec4 iParams;
uniform int iColorMode;

in vec2 fragCoord;
out vec4 fragColor;

const float TAU = 6.28318530717958647692;
const int FRACTAL_ITER = 13;
const int MARCH_STEPS = 72;
const float ESCAPE2 = 16.0;
const float BOUND_R = 1.45;     // bounding sphere of the visible set
const float T_MAX = 9.0;

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

// Main cardioid boundary of the Mandelbrot set
vec2 cardioid(float a) {
    return vec2(0.5 * cos(a) - 0.25 * cos(2.0 * a),
                0.5 * sin(a) - 0.25 * sin(2.0 * a));
}

// Quaternion square: q = (x, yzw) -> (x^2 - |yzw|^2, 2 x yzw). No trig.
vec4 qsqr(vec4 q) {
    return vec4(q.x * q.x - dot(q.yzw, q.yzw), 2.0 * q.x * q.yzw);
}

// Distance estimate to the w=0 slice of the quaternion Julia set of c.
// Scalar derivative recurrence dr' = 2 r dr (quaternion norm is
// multiplicative), DE = 0.5 r ln(r) / dr. Also returns orbit traps:
//   trap.x = min |q|        (radial trap - shells around the body)
//   trap.y = min |q.y|      (planar trap - stripes along limbs)
//   trap.z = normalized escape iteration (fractal banding)
float julDE(vec3 p, vec4 c, out vec3 trap) {
    vec4 q = vec4(p, 0.0);
    float dr = 1.0;
    float r2 = dot(q, q);
    float trapR = 1e9;
    float trapY = 1e9;
    float it = float(FRACTAL_ITER);
    for (int i = 0; i < FRACTAL_ITER; i++) {
        dr = 2.0 * sqrt(r2) * dr;
        q = qsqr(q) + c;
        r2 = dot(q, q);
        trapR = min(trapR, r2);
        trapY = min(trapY, abs(q.y));
        if (r2 > ESCAPE2) { it = float(i); break; }
    }
    trap = vec3(sqrt(trapR), trapY, it / float(FRACTAL_ITER));
    float r = sqrt(r2);
    return 0.5 * r * log(max(r, 1e-12)) / max(dr, 1e-12);
}

// DE without trap output (for marching / normals / AO)
float julDEfast(vec3 p, vec4 c) {
    vec3 dummy;
    return julDE(p, c, dummy);
}

// --- Camera choreography ----------------------------------------------------
// Spherical path around the set, every term a bounded C1 sine:
//   radius breathes on a ~45 s cycle between far orbit (~3.3) and
//   sub-bounding-radius passes (~0.7) -> AROUND / THROUGH;
//   elevation cycles on an incommensurate ~30 s period -> OVER the poles.
vec3 camPath(float tc) {
    float az = tc * 0.16 + 0.35 * sin(tc * 0.043);
    float el = 0.55 * sin(tc * 0.209) + 0.25 * sin(tc * 0.111 + 2.0);
    float R = 1.85 + 0.95 * sin(tc * 0.1396 - 1.65)
                   + 0.15 * sin(tc * 0.071 + 0.8);
    return R * vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az));
}

void main() {
    float flightSpeed = iParams.x;   // choreography rate (~0.5 -> 45 s loop)
    float morphSpeed  = iParams.y;   // c-path rate through quaternion space
    float detail      = iParams.z;   // surface crispness (hit epsilon)
    float fogGlow     = iParams.w;   // fog density + boundary glow strength

    float t = iTime;

    // --- Morphing Julia parameter ------------------------------------------
    // A quaternion Julia set looks limb-rich exactly when the 2D point
    // (c.x, |c.yzw|) sits near the Mandelbrot boundary (edge of
    // connectivity). So ride the main cardioid: aa wanders the upper
    // coast on slow incommensurate sines (avoiding the cusp and the
    // period-2 pinch where the imaginary part vanishes), breathing
    // slightly in/out of the set, while the vector part's DIRECTION
    // precesses slowly in 3D. Limbs visibly grow, split and twist over
    // ~15-25 s spans; everything is bounded C1 sines.
    float tm = t * (0.4 + 1.2 * morphSpeed);
    float aa = 1.55 + 0.95 * sin(tm * 0.031) + 0.30 * sin(tm * 0.017 + 2.0);
    vec2 m2d = cardioid(aa) * (1.01 + 0.05 * sin(tm * 0.043 + 1.0));
    float th = tm * 0.023 + 1.0;                  // yz precession
    float ph = 0.55 * sin(tm * 0.029 + 0.6);      // w tilt
    vec3 cdir = vec3(cos(th) * cos(ph), sin(th) * cos(ph), sin(ph));
    vec4 c = vec4(m2d.x, m2d.y * cdir);

    // --- Camera --------------------------------------------------------------
    float tc = t * (0.4 + 1.2 * flightSpeed);
    vec3 cam = camPath(tc);
    vec3 camAhead = camPath(tc + 0.35);

    // Where to look: a slow wander near the structure's heart; on close
    // passes blend toward the flight direction so through-passages read
    // as flying along the corridor, not staring at a wall.
    float closeness = smoothstep(1.8, 0.95, length(cam));
    vec3 flightDir = normalize(camAhead - cam + vec3(1e-5));
    vec3 wander = 0.22 * vec3(sin(tc * 0.083),
                              0.6 * sin(tc * 0.067 + 1.0),
                              sin(tc * 0.091 + 3.0));
    vec3 target = mix(wander, cam + flightDir * 1.4, closeness * 0.30);

    // Safety: nudge the camera radially outward if it would sit inside
    // rock (DE below clearance). Keeps through-passes threading the gaps.
    for (int k = 0; k < 3; k++) {
        float dcam = julDEfast(cam, c);
        if (dcam >= 0.16) break;
        cam += normalize(cam) * (0.16 - dcam);
    }

    vec3 fwd = normalize(target - cam);
    float roll = 0.16 * sin(tc * 0.13 + 1.2) * (0.4 + 0.6 * closeness);
    vec3 upRef = vec3(sin(roll), cos(roll), 0.0);
    vec3 right = normalize(cross(fwd, upRef));
    vec3 up = cross(right, fwd);

    // FOV: tight when orbiting far (structure fills the frame), wide on
    // close passes (peripheral limbs sweep past). C1 via closeness.
    float fovK = mix(0.85, 1.55, closeness);
    vec2 uv = fragCoord - 0.5;
    uv.x *= iResolution.x / iResolution.y;
    vec3 ray = normalize(fwd + fovK * (uv.x * right + uv.y * up));

    // --- Sky (also the fog tint) ----------------------------------------------
    float horizon = 0.5 + 0.5 * ray.y;
    vec3 sky = mix(getColor(0.62, iColorMode) * 0.22,
                   getColor(0.50, iColorMode) * 0.07,
                   horizon);
    // faint nebular wash so "empty" never means pure black
    sky += getColor(0.85, iColorMode)
         * 0.06 * (0.5 + 0.5 * sin(ray.x * 3.0 + ray.y * 5.0 + t * 0.03));

    // --- Raymarch ---------------------------------------------------------------
    // Skip ahead to the bounding sphere when outside it.
    float tray = 0.0;
    float b = dot(cam, cam) - BOUND_R * BOUND_R;
    if (b > 0.0) {
        float pc = -dot(cam, ray);
        float h = pc * pc - b;
        if (h < 0.0) { tray = T_MAX + 1.0; }       // misses the set entirely
        else tray = max(pc - sqrt(h), 0.0);
    }

    // Hit threshold: pixel-cone scale (angular pixel size times distance)
    // with a small floor; detail tightens it for crisper fine limbs.
    float pxAngle = fovK / iResolution.y;
    float epsScale = mix(1.5, 0.6, detail);
    float hitT = -1.0;
    vec3 trap = vec3(0.0);
    float glowMin = 1e9;                            // closest approach / dist
    for (int s = 0; s < MARCH_STEPS; s++) {
        if (tray > T_MAX) break;
        vec3 pos = cam + ray * tray;
        // Outside the bounding sphere and heading away: done
        float rr = dot(pos, pos);
        if (rr > BOUND_R * BOUND_R + 0.4 && dot(pos, ray) > 0.0) break;
        vec3 tr;
        float d = julDE(pos, c, tr);
        glowMin = min(glowMin, d / (tray + 0.12));
        if (d < max(3e-4, tray * pxAngle * epsScale)) {
            hitT = tray;
            trap = tr;
            break;
        }
        tray += d * 0.8;
    }

    vec3 color;
    float paletteShift = t * 0.015;

    if (hitT < 0.0) {
        color = sky;
        // Boundary glow: rays that grazed the structure pick up a halo.
        // Feather it toward the bounding sphere so the clip never shows
        // as a hard disk edge behind the set.
        float pc2 = -dot(cam, ray);
        vec3 closestP = cam + ray * max(pc2, 0.0);
        float feather = smoothstep(BOUND_R, BOUND_R * 0.55, length(closestP));
        float glow = exp(-glowMin * 26.0) * feather;
        color += getColor(fract(0.12 + paletteShift), iColorMode)
               * glow * (0.35 + 0.8 * fogGlow);
    } else {
        vec3 pos = cam + ray * hitT;

        // Tetrahedron-technique normal: 4 extra DE evals
        float epsN = max(7e-4, hitT * 2.2e-3);
        vec2 e = vec2(1.0, -1.0) * 0.57735 * epsN;
        vec3 n = normalize(e.xyy * julDEfast(pos + e.xyy, c)
                         + e.yyx * julDEfast(pos + e.yyx, c)
                         + e.yxy * julDEfast(pos + e.yxy, c)
                         + e.xxx * julDEfast(pos + e.xxx, c));

        // 5-tap DE ambient occlusion along the normal
        float occ = 0.0, sca = 1.0;
        for (int i = 1; i <= 5; i++) {
            float hh = 0.012 + 0.11 * float(i) / 5.0;
            occ += (hh - julDEfast(pos + n * hh, c)) * sca;
            sca *= 0.72;
        }
        float ao = clamp(1.0 - 2.6 * occ, 0.0, 1.0);

        // Orbit-trap surface coloring: shells (trap.x), limb stripes
        // (trap.y) and escape-iteration bands give fractal detail.
        float ci = 0.55 * trap.x + 1.15 * trap.y
                 + 0.35 * trap.z + paletteShift;
        vec3 base = getColor(fract(ci), iColorMode);
        // deepen crevices (low trap.x = orbit dove near the core)
        base *= 0.55 + 0.45 * smoothstep(0.0, 0.9, trap.x);

        // Key + fill + rim lighting. The key tracks the camera side
        // (offset up-left) so the visible face is always sculpted by
        // light no matter where the orbit has taken us.
        vec3 key = normalize(normalize(cam) + vec3(0.35, 0.75, 0.15));
        float diff = max(dot(n, key), 0.0);
        float fill = 0.5 + 0.5 * n.y;                       // sky fill
        float rim = pow(1.0 - max(dot(n, -ray), 0.0), 3.0);
        float spec = pow(max(dot(reflect(-key, n), -ray), 0.0), 14.0);

        color = base * (0.16 + 1.05 * diff * (0.35 + 0.65 * ao))
              + getColor(0.62, iColorMode) * 0.20 * fill * ao
              + vec3(1.0, 0.95, 0.85) * spec * 0.35 * ao;
        color += getColor(fract(0.12 + paletteShift), iColorMode)
               * rim * 0.18 * (0.5 + 0.5 * ao);

        // Distance fog into the sky
        float fog = 1.0 - exp(-hitT * hitT * (0.008 + 0.04 * fogGlow));
        color = mix(color, sky, clamp(fog, 0.0, 1.0));
    }

    // Gentle vignette
    float r = length(fragCoord - 0.5);
    color *= 1.0 - smoothstep(0.6, 1.05, r) * 0.30;

    fragColor = vec4(color, 1.0);
}

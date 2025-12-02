#version 330 core
/*
 * Lissajous Curve Fragment Shader
 *
 * Renders parametric Lissajous curves using SDF (Signed Distance Field) approach.
 * The curve is defined by: x = sin(a*t + delta), y = sin(b*t)
 *
 * Uniforms:
 *   iTime       - Animation time (affects phase)
 *   iResolution - Viewport resolution (width, height)
 *   iParams     - (freqA, freqB, phase_offset, trail_intensity)
 *   iColorMode  - Color palette selector (0-3)
 */

uniform float iTime;
uniform vec2 iResolution;
uniform vec4 iParams;
uniform int iColorMode;

in vec2 fragCoord;
out vec4 fragColor;

const float PI = 3.14159265358979323846;
const float TAU = 6.28318530717958647692;

// Cosine-based color palette
vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(TAU * (c * t + d));
}

vec3 getColor(float t, int mode) {
    if (mode == 0) {
        // Electric blue-white
        vec3 a = vec3(0.1, 0.3, 0.6);
        vec3 b = vec3(0.4, 0.4, 0.4);
        vec3 c = vec3(1.0, 1.0, 1.0);
        vec3 d = vec3(0.0, 0.1, 0.2);
        return palette(t, a, b, c, d);
    } else if (mode == 1) {
        // Neon pink-cyan
        vec3 a = vec3(0.5, 0.2, 0.5);
        vec3 b = vec3(0.5, 0.3, 0.4);
        vec3 c = vec3(1.0, 1.0, 0.5);
        vec3 d = vec3(0.8, 0.2, 0.5);
        return palette(t, a, b, c, d);
    } else if (mode == 2) {
        // Rainbow trail
        vec3 a = vec3(0.5);
        vec3 b = vec3(0.5);
        vec3 c = vec3(1.0);
        vec3 d = vec3(0.0, 0.33, 0.67);
        return palette(t, a, b, c, d);
    } else {
        // Golden glow
        vec3 a = vec3(0.4, 0.3, 0.1);
        vec3 b = vec3(0.4, 0.3, 0.2);
        vec3 c = vec3(1.0, 0.8, 0.4);
        vec3 d = vec3(0.0, 0.1, 0.2);
        return palette(t, a, b, c, d);
    }
}

// Calculate minimum distance to Lissajous curve
// Using sampling approach since analytical SDF is complex for Lissajous
float distToLissajous(vec2 p, float a, float b, float delta, float phase) {
    float minDist = 1000.0;
    float minT = 0.0;

    // Sample the curve at multiple points
    const int SAMPLES = 128;
    for (int i = 0; i < SAMPLES; i++) {
        float t = float(i) / float(SAMPLES) * TAU;

        // Lissajous equations
        vec2 curvePoint = vec2(
            sin(a * t + delta + phase),
            sin(b * t + phase * 0.7)
        );

        float d = length(p - curvePoint);
        if (d < minDist) {
            minDist = d;
            minT = t;
        }
    }

    return minDist;
}

void main() {
    // Extract parameters
    float freqA = max(1.0, iParams.x * 10.0);   // Frequency A (default ~3)
    float freqB = max(1.0, iParams.y * 10.0);   // Frequency B (default ~4)
    float phaseOffset = iParams.z * TAU;        // Phase offset (0 to 2*PI)
    float trailIntensity = iParams.w;           // Trail/glow intensity

    // Center coordinate system and scale to [-1, 1]
    vec2 uv = fragCoord * 2.0 - 1.0;

    // Aspect ratio correction
    uv.x *= iResolution.x / iResolution.y;

    // Scale down slightly to fit curve
    uv *= 1.2;

    // Animate phase over time
    float animatedPhase = phaseOffset + iTime * 0.5;

    // Calculate distance to curve
    float dist = distToLissajous(uv, freqA, freqB, animatedPhase, 0.0);

    // Create glow effect based on distance
    // Closer = brighter
    float lineWidth = 0.03;
    float glowWidth = 0.15 * (0.5 + trailIntensity * 0.5);

    // Sharp line
    float line = smoothstep(lineWidth, 0.0, dist);

    // Soft glow
    float glow = exp(-dist * (3.0 + (1.0 - trailIntensity) * 5.0));

    // Combine line and glow
    float intensity = line + glow * 0.5 * trailIntensity;

    // Color based on position along curve (use distance for variation)
    float colorT = fract(dist * 5.0 + iTime * 0.2);

    // Get base color
    vec3 color = getColor(colorT, iColorMode);

    // Apply intensity
    color *= intensity;

    // Add subtle background
    vec3 bgColor = vec3(0.02, 0.02, 0.05);
    color = max(color, bgColor * (1.0 - intensity * 0.5));

    fragColor = vec4(color, 1.0);
}

#version 330 core
/*
 * Plasma-Lissajous Composite Fragment Shader
 *
 * Combines plasma and Lissajous effects where the plasma field
 * modulates the Lissajous curve's frequencies, creating organic
 * morphing patterns.
 *
 * Uniforms:
 *   iTime       - Animation time
 *   iResolution - Viewport resolution (width, height)
 *   iParams     - (plasma_freq, liss_base_freq, modulation_strength, trail_intensity)
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
        // Electric plasma-curve blend
        vec3 a = vec3(0.3, 0.2, 0.5);
        vec3 b = vec3(0.4, 0.4, 0.4);
        vec3 c = vec3(1.0, 1.0, 1.0);
        vec3 d = vec3(0.0, 0.1, 0.2);
        return palette(t, a, b, c, d);
    } else if (mode == 1) {
        // Neon fusion
        vec3 a = vec3(0.5, 0.2, 0.3);
        vec3 b = vec3(0.5, 0.4, 0.4);
        vec3 c = vec3(1.0, 1.0, 0.5);
        vec3 d = vec3(0.8, 0.2, 0.5);
        return palette(t, a, b, c, d);
    } else if (mode == 2) {
        // Ocean depths
        vec3 a = vec3(0.0, 0.3, 0.5);
        vec3 b = vec3(0.2, 0.4, 0.4);
        vec3 c = vec3(1.0, 1.0, 0.5);
        vec3 d = vec3(0.0, 0.1, 0.2);
        return palette(t, a, b, c, d);
    } else {
        // Fire and gold
        vec3 a = vec3(0.5, 0.3, 0.1);
        vec3 b = vec3(0.5, 0.3, 0.2);
        vec3 c = vec3(1.0, 0.8, 0.4);
        vec3 d = vec3(0.0, 0.1, 0.2);
        return palette(t, a, b, c, d);
    }
}

// Compute plasma value at a point
float computePlasma(vec2 uv, float freq, float t) {
    vec2 p = uv * freq * 10.0;
    float value = 0.0;
    value += sin(p.x + t);
    value += sin(p.y + t * 1.2);
    value += sin((p.x + p.y) * 0.8 + t * 0.8);
    value += sin(length(p) + t * 1.5);
    return value / 4.0;  // Normalized to [-1, 1]
}

// Compute global plasma modulation value
float getPlasmaModulation(float freq, float t) {
    // Sample plasma at center (0.5, 0.5) for global modulation
    return computePlasma(vec2(0.5, 0.5), freq, t);
}

// Calculate minimum distance to Lissajous curve
float distToLissajous(vec2 p, float a, float b, float delta) {
    float minDist = 1000.0;
    const int SAMPLES = 100;

    for (int i = 0; i < SAMPLES; i++) {
        float t = float(i) / float(SAMPLES) * TAU;
        vec2 curvePoint = vec2(sin(a * t + delta), sin(b * t));
        minDist = min(minDist, length(p - curvePoint));
    }

    return minDist;
}

void main() {
    // Extract parameters
    float plasmaFreq = iParams.x;             // Plasma frequency (default ~0.1)
    float lissBaseFreq = iParams.y * 10.0;    // Base Lissajous frequency (default ~3)
    float modStrength = iParams.z;            // How much plasma affects Lissajous
    float trailIntensity = iParams.w;         // Glow intensity

    // Get plasma modulation value (global)
    float plasmaVal = getPlasmaModulation(plasmaFreq, iTime);

    // Modulate Lissajous frequencies based on plasma
    float freqA = lissBaseFreq + plasmaVal * modStrength * 4.0;
    float freqB = lissBaseFreq - plasmaVal * modStrength * 4.0;  // Inverse for contrast

    // Ensure frequencies stay positive
    freqA = max(1.0, freqA);
    freqB = max(1.0, freqB);

    // Center coordinate system
    vec2 uv = fragCoord * 2.0 - 1.0;
    uv.x *= iResolution.x / iResolution.y;
    uv *= 1.2;  // Scale to fit

    // Animate phase
    float phase = iTime * 0.5;

    // Calculate distance to modulated Lissajous curve
    float dist = distToLissajous(uv, freqA, freqB, phase);

    // Create glow effect
    float lineWidth = 0.03;
    float glowWidth = 0.15 * (0.5 + trailIntensity * 0.5);
    float line = smoothstep(lineWidth, 0.0, dist);
    float glow = exp(-dist * (3.0 + (1.0 - trailIntensity) * 5.0));
    float intensity = line + glow * 0.5 * trailIntensity;

    // Add subtle plasma background
    float bgPlasma = computePlasma(fragCoord, plasmaFreq * 0.5, iTime * 0.5);
    bgPlasma = bgPlasma * 0.5 + 0.5;  // Normalize to [0, 1]

    // Color based on position and plasma
    float colorT = fract(dist * 5.0 + bgPlasma * 0.3 + iTime * 0.2);

    // Get color
    vec3 color = getColor(colorT, iColorMode);

    // Apply Lissajous intensity
    color *= intensity;

    // Add subtle plasma-colored background
    vec3 bgColor = getColor(bgPlasma, iColorMode) * 0.1;
    color = max(color, bgColor * (1.0 - intensity * 0.5));

    fragColor = vec4(color, 1.0);
}

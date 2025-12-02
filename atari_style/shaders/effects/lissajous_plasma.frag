#version 330 core
/*
 * Lissajous-Plasma Composite Fragment Shader
 *
 * Combines Lissajous curves with plasma where the curve's position
 * and dynamics modulate the plasma field's frequencies and colors,
 * creating a reactive plasma that follows the curve.
 *
 * Uniforms:
 *   iTime       - Animation time
 *   iResolution - Viewport resolution (width, height)
 *   iParams     - (liss_speed, plasma_intensity, curve_influence, color_shift)
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
        // Aurora borealis
        vec3 a = vec3(0.2, 0.4, 0.3);
        vec3 b = vec3(0.3, 0.4, 0.4);
        vec3 c = vec3(1.0, 1.0, 0.5);
        vec3 d = vec3(0.0, 0.2, 0.4);
        return palette(t, a, b, c, d);
    } else if (mode == 1) {
        // Sunset plasma
        vec3 a = vec3(0.5, 0.3, 0.2);
        vec3 b = vec3(0.5, 0.3, 0.3);
        vec3 c = vec3(1.0, 0.8, 0.5);
        vec3 d = vec3(0.0, 0.15, 0.3);
        return palette(t, a, b, c, d);
    } else if (mode == 2) {
        // Electric storm
        vec3 a = vec3(0.1, 0.1, 0.3);
        vec3 b = vec3(0.4, 0.4, 0.5);
        vec3 c = vec3(1.0, 1.0, 1.0);
        vec3 d = vec3(0.6, 0.2, 0.8);
        return palette(t, a, b, c, d);
    } else {
        // Grayscale ethereal
        float v = t * 0.8 + 0.2;
        return vec3(v * 0.9, v, v * 1.1);
    }
}

// Get current Lissajous curve point
vec2 getLissajousPoint(float t, float freqA, float freqB, float phase) {
    return vec2(sin(freqA * t + phase), sin(freqB * t));
}

// Get Lissajous velocity (derivative)
vec2 getLissajousVelocity(float t, float freqA, float freqB, float phase) {
    return vec2(
        freqA * cos(freqA * t + phase),
        freqB * cos(freqB * t)
    );
}

// Compute plasma with modulated frequencies
float computePlasma(vec2 uv, float freqMod, float t) {
    vec2 p = uv * 10.0;
    float value = 0.0;

    // Base plasma waves with frequency modulation
    value += sin(p.x * (1.0 + freqMod * 0.5) + t);
    value += sin(p.y * (1.0 - freqMod * 0.3) + t * 1.2);
    value += sin((p.x + p.y) * (0.8 + freqMod * 0.4) + t * 0.8);
    value += sin(length(p) * (1.0 + freqMod * 0.2) + t * 1.5);

    return value / 4.0;  // Normalized to [-1, 1]
}

// Calculate distance to Lissajous curve (simplified)
float distToLissajous(vec2 p, float freqA, float freqB, float phase) {
    float minDist = 1000.0;
    const int SAMPLES = 64;

    for (int i = 0; i < SAMPLES; i++) {
        float t = float(i) / float(SAMPLES) * TAU;
        vec2 curvePoint = getLissajousPoint(t, freqA, freqB, phase);
        minDist = min(minDist, length(p - curvePoint));
    }

    return minDist;
}

void main() {
    // Extract parameters
    float lissSpeed = iParams.x * 2.0;        // Lissajous animation speed
    float plasmaIntensity = iParams.y;        // How visible the plasma is
    float curveInfluence = iParams.z;         // How much curve affects plasma
    float colorShift = iParams.w;             // Color cycling speed

    // Lissajous frequencies (classic 3:2 ratio creates figure-8 pattern)
    float freqA = 3.0;
    float freqB = 2.0;
    float phase = iTime * lissSpeed;

    // Get current curve position and velocity
    vec2 curvePos = getLissajousPoint(phase, freqA, freqB, 0.0);
    vec2 curveVel = getLissajousVelocity(phase, freqA, freqB, 0.0);

    // Velocity magnitude influences plasma frequency
    float speed = length(curveVel) / (freqA + freqB);  // Normalized

    // Center coordinate system
    vec2 uv = fragCoord * 2.0 - 1.0;
    uv.x *= iResolution.x / iResolution.y;

    // Distance from current pixel to curve point
    float distToCurve = length(uv - curvePos);

    // Distance to the curve itself (for glow effect)
    float distToPath = distToLissajous(uv, freqA, freqB, phase);

    // Frequency modulation based on distance to curve and curve velocity
    float freqMod = (1.0 - smoothstep(0.0, 1.5, distToCurve)) * curveInfluence;
    freqMod += speed * curveInfluence * 0.5;

    // Compute modulated plasma
    float plasmaVal = computePlasma(uv, freqMod, iTime);
    plasmaVal = plasmaVal * 0.5 + 0.5;  // Normalize to [0, 1]

    // Create curve glow effect
    float lineWidth = 0.02;
    float glowWidth = 0.3;
    float curveGlow = exp(-distToPath * 5.0);
    float curveLine = smoothstep(lineWidth, 0.0, distToPath);

    // Blend plasma intensity with distance to curve
    float plasmaStrength = plasmaIntensity * (0.3 + 0.7 * (1.0 - smoothstep(0.0, 2.0, distToCurve)));

    // Color cycling based on plasma, position, and time
    float colorT = fract(plasmaVal + distToPath * 0.5 + iTime * colorShift * 0.1);

    // Get base colors
    vec3 plasmaColor = getColor(colorT, iColorMode);
    vec3 curveColor = getColor(fract(colorT + 0.5), iColorMode);

    // Combine plasma and curve
    vec3 color = plasmaColor * plasmaStrength * plasmaVal;

    // Add curve glow
    color += curveColor * curveGlow * 0.6;
    color += curveColor * curveLine * 1.5;

    // Add reactive highlight near curve position
    float highlight = exp(-distToCurve * 3.0) * speed;
    color += vec3(highlight * 0.3) * getColor(0.5, iColorMode);

    // Subtle vignette
    float vignette = 1.0 - smoothstep(0.8, 1.5, length(uv));
    color *= vignette;

    fragColor = vec4(color, 1.0);
}

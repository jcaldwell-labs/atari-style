#version 330 core
/*
 * Plasma Effect Fragment Shader
 *
 * Classic demoscene plasma effect using summed sine waves.
 * Creates colorful, organic-looking patterns that flow and morph.
 *
 * Uniforms:
 *   iTime       - Animation time
 *   iResolution - Viewport resolution (width, height)
 *   iParams     - (freq_x, freq_y, freq_diag, freq_radial)
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

// Cosine-based color palette (Inigo Quilez)
vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(TAU * (c * t + d));
}

// Different color schemes
vec3 getColor(float t, int mode) {
    if (mode == 0) {
        // Classic plasma (blue-cyan-green-yellow-red-magenta)
        vec3 a = vec3(0.5, 0.5, 0.5);
        vec3 b = vec3(0.5, 0.5, 0.5);
        vec3 c = vec3(1.0, 1.0, 1.0);
        vec3 d = vec3(0.0, 0.33, 0.67);
        return palette(t, a, b, c, d);
    } else if (mode == 1) {
        // Fire plasma
        vec3 a = vec3(0.5, 0.2, 0.0);
        vec3 b = vec3(0.5, 0.3, 0.1);
        vec3 c = vec3(1.0, 0.8, 0.4);
        vec3 d = vec3(0.0, 0.15, 0.3);
        return palette(t, a, b, c, d);
    } else if (mode == 2) {
        // Ocean plasma
        vec3 a = vec3(0.0, 0.3, 0.5);
        vec3 b = vec3(0.2, 0.4, 0.4);
        vec3 c = vec3(1.0, 1.0, 0.5);
        vec3 d = vec3(0.0, 0.1, 0.2);
        return palette(t, a, b, c, d);
    } else {
        // Grayscale
        return vec3(t);
    }
}

void main() {
    // Extract parameters (scale them for shader space)
    float freqX = iParams.x * 10.0;      // Default 0.1 -> 1.0
    float freqY = iParams.y * 10.0;      // Default 0.1 -> 1.0
    float freqDiag = iParams.z * 10.0;   // Default 0.08 -> 0.8
    float freqRadial = iParams.w * 10.0; // Default 0.1 -> 1.0

    // Get pixel position in screen space
    vec2 uv = fragCoord * iResolution;

    // Calculate plasma value from multiple sine waves
    float value = 0.0;

    // Horizontal wave
    value += sin(uv.x * freqX * 0.01 + iTime);

    // Vertical wave (slightly different speed)
    value += sin(uv.y * freqY * 0.01 + iTime * 1.2);

    // Diagonal wave
    value += sin((uv.x + uv.y) * freqDiag * 0.01 + iTime * 0.8);

    // Radial wave from center
    vec2 center = iResolution * 0.5;
    float dist = length(uv - center);
    value += sin(dist * freqRadial * 0.01 + iTime * 1.5);

    // Normalize to [-1, 1] then to [0, 1]
    value = value / 4.0;
    value = value * 0.5 + 0.5;

    // Add slow color cycling
    value = fract(value + iTime * 0.05);

    // Get final color
    vec3 color = getColor(value, iColorMode);

    fragColor = vec4(color, 1.0);
}

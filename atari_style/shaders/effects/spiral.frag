#version 330 core
/*
 * Spiral Animation Fragment Shader
 *
 * Rotating spiral pattern using polar coordinates.
 * Creates hypnotic spiral arms that rotate around the center.
 *
 * Uniforms:
 *   iTime       - Animation time
 *   iResolution - Viewport resolution (width, height)
 *   iParams     - (num_spirals, rotation_speed, tightness, scale)
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
        // Psychedelic rainbow
        vec3 a = vec3(0.5);
        vec3 b = vec3(0.5);
        vec3 c = vec3(1.0);
        vec3 d = vec3(0.0, 0.33, 0.67);
        return palette(t, a, b, c, d);
    } else if (mode == 1) {
        // Neon green-purple
        vec3 a = vec3(0.2, 0.5, 0.3);
        vec3 b = vec3(0.4, 0.3, 0.5);
        vec3 c = vec3(1.0, 1.0, 1.0);
        vec3 d = vec3(0.0, 0.5, 0.3);
        return palette(t, a, b, c, d);
    } else if (mode == 2) {
        // Black and white spiral
        return vec3(smoothstep(0.4, 0.6, t));
    } else {
        // Sunset
        vec3 a = vec3(0.5, 0.3, 0.2);
        vec3 b = vec3(0.5, 0.3, 0.3);
        vec3 c = vec3(1.0, 0.7, 0.4);
        vec3 d = vec3(0.0, 0.15, 0.2);
        return palette(t, a, b, c, d);
    }
}

void main() {
    // Extract parameters
    float numSpirals = max(1.0, iParams.x * 10.0);   // Number of spiral arms (default ~3)
    float rotSpeed = iParams.y;                       // Rotation speed (default ~1.0)
    float tightness = iParams.z * 5.0;               // How tight the spiral is (default ~8)
    float scale = max(0.1, iParams.w);               // Overall scale

    // Center the coordinate system
    vec2 uv = fragCoord - 0.5;

    // Aspect ratio correction
    uv.x *= iResolution.x / iResolution.y;

    // Apply scale
    uv *= scale;

    // Convert to polar coordinates
    float r = length(uv);
    float theta = atan(uv.y, uv.x);

    // Rotation over time
    float rotation = iTime * rotSpeed;

    // Spiral function: combine angle with radius
    // The spiral pattern: sin(numSpirals * theta + r * tightness - rotation)
    float spiral = sin(theta * numSpirals + r * tightness - rotation);

    // Convert to [0, 1] range
    float t = spiral * 0.5 + 0.5;

    // Add subtle variation based on radius
    t = fract(t + r * 0.1);

    // Add color cycling
    t = fract(t + iTime * 0.1);

    // Get color
    vec3 color = getColor(t, iColorMode);

    // Optional: fade edges
    float vignette = 1.0 - smoothstep(0.8, 1.5, r / scale);
    color *= vignette;

    fragColor = vec4(color, 1.0);
}

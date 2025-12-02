#version 330 core
/*
 * Tunnel Vision Fragment Shader
 *
 * Classic raymarched tunnel effect using polar-to-cartesian mapping.
 * Creates the illusion of flying through an infinite tunnel.
 *
 * Uniforms:
 *   iTime       - Animation time
 *   iResolution - Viewport resolution (width, height)
 *   iParams     - (depth_speed, rotation_speed, tunnel_size, color_cycle_speed)
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
        // Cyberpunk (cyan-magenta)
        vec3 a = vec3(0.2, 0.4, 0.5);
        vec3 b = vec3(0.4, 0.3, 0.4);
        vec3 c = vec3(1.0, 1.0, 0.5);
        vec3 d = vec3(0.5, 0.2, 0.7);
        return palette(t, a, b, c, d);
    } else if (mode == 1) {
        // Matrix green
        vec3 a = vec3(0.0, 0.3, 0.0);
        vec3 b = vec3(0.0, 0.4, 0.1);
        vec3 c = vec3(0.5, 1.0, 0.5);
        vec3 d = vec3(0.0, 0.1, 0.0);
        return palette(t, a, b, c, d);
    } else if (mode == 2) {
        // Checkerboard contrast
        return vec3(step(0.5, t));
    } else {
        // Neon rainbow
        vec3 a = vec3(0.5);
        vec3 b = vec3(0.5);
        vec3 c = vec3(1.0);
        vec3 d = vec3(0.0, 0.33, 0.67);
        return palette(t, a, b, c, d);
    }
}

void main() {
    // Extract parameters
    float depthSpeed = iParams.x;          // Speed of flying through tunnel
    float rotSpeed = iParams.y;            // Tunnel rotation speed
    float tunnelSize = iParams.z;          // Affects depth perception
    float colorSpeed = iParams.w;          // Color cycling speed

    // Center the coordinate system
    vec2 uv = fragCoord - 0.5;

    // Aspect ratio correction
    uv.x *= iResolution.x / iResolution.y;

    // Convert to polar coordinates
    float dist = length(uv);
    float angle = atan(uv.y, uv.x);

    // Avoid division by zero at center
    dist = max(dist, 0.001);

    // Create tunnel depth (inverse of distance from center)
    // tunnelSize controls how "zoomed in" the tunnel appears
    float depth = (1.0 / dist) * tunnelSize * 0.5;

    // Animate depth (flying through tunnel)
    depth += iTime * depthSpeed;

    // Rotate the tunnel
    float rotatedAngle = angle + iTime * rotSpeed + depth * 0.05;

    // Create pattern
    // Checkerboard: based on depth rings and angle segments
    float rings = floor(depth * 0.5);              // Depth rings
    float segments = floor(rotatedAngle * 4.0 / PI); // Angular segments (8 total)

    // Checkerboard pattern
    float pattern = mod(rings + segments, 2.0);

    // Add some variation with continuous values
    float continuous = fract(depth * 0.1) + fract(rotatedAngle / TAU);
    continuous = fract(continuous + iTime * colorSpeed * 0.1);

    // Mix pattern with continuous for color
    float t;
    if (iColorMode == 2) {
        // Pure checkerboard for mode 2
        t = pattern;
    } else {
        // Colored version
        t = fract(continuous + pattern * 0.3);
    }

    // Get color
    vec3 color = getColor(t, iColorMode);

    // Add depth fog (darker at center/far away)
    float fog = 1.0 - exp(-dist * 3.0);
    color *= fog;

    // Add glow at edges
    float edgeGlow = smoothstep(0.0, 0.1, dist);
    color *= edgeGlow;

    fragColor = vec4(color, 1.0);
}

#version 330 core

// Uniforms provided by atari-style
uniform float u_time;
uniform vec2 u_resolution;
uniform vec4 u_params;  // param_a, param_b, param_c, param_d
uniform int u_color_mode;

out vec4 fragColor;

// Color palette function
vec3 palette(float t, int mode) {
    if (mode == 0) {
        // Rainbow
        return 0.5 + 0.5 * cos(6.28318 * (t + vec3(0.0, 0.33, 0.67)));
    } else if (mode == 1) {
        // Fire
        return vec3(t, t * 0.5, t * 0.2);
    } else if (mode == 2) {
        // Ocean
        return vec3(t * 0.2, t * 0.5, t);
    } else {
        // Grayscale
        return vec3(t);
    }
}

void main() {
    // Normalize coordinates to [-1, 1]
    vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution) / min(u_resolution.x, u_resolution.y);

    // Unpack parameters
    float param_a = u_params.x;
    float param_b = u_params.y;
    float param_c = u_params.z;
    float param_d = u_params.w;

    // Your shader code here
    float d = length(uv);
    float angle = atan(uv.y, uv.x);

    // Example effect: animated rings
    float rings = sin(d * 10.0 * param_a - u_time * param_b);
    float spiral = sin(angle * 5.0 + d * param_c * 10.0 - u_time * param_d);

    float intensity = rings * spiral * 0.5 + 0.5;

    // Apply color
    vec3 color = palette(intensity, u_color_mode);

    fragColor = vec4(color, 1.0);
}

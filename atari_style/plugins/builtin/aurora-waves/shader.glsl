#version 330 core

// Aurora Waves - Northern lights inspired effect
// Built-in example plugin for atari-style

uniform float u_time;
uniform vec2 u_resolution;
uniform vec4 u_params;  // wave_speed, color_shift, wave_height, glow_intensity
uniform int u_color_mode;

out vec4 fragColor;

// Simplex-like noise for smooth randomness
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);

    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

// Fractal Brownian Motion for layered noise
float fbm(vec2 p) {
    float value = 0.0;
    float amplitude = 0.5;
    float frequency = 1.0;

    for (int i = 0; i < 5; i++) {
        value += amplitude * noise(p * frequency);
        frequency *= 2.0;
        amplitude *= 0.5;
    }

    return value;
}

// Aurora color palette
vec3 aurora_color(float t, float shift) {
    // Green-cyan-magenta aurora colors
    vec3 c1 = vec3(0.1, 0.8, 0.3);  // Green
    vec3 c2 = vec3(0.2, 0.9, 0.8);  // Cyan
    vec3 c3 = vec3(0.8, 0.3, 0.9);  // Magenta
    vec3 c4 = vec3(0.3, 0.5, 0.9);  // Blue

    float phase = fract(t + shift);

    if (phase < 0.33) {
        return mix(c1, c2, phase * 3.0);
    } else if (phase < 0.66) {
        return mix(c2, c3, (phase - 0.33) * 3.0);
    } else {
        return mix(c3, c4, (phase - 0.66) * 3.0);
    }
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;

    // Unpack parameters
    float wave_speed = u_params.x;
    float color_shift = u_params.y;
    float wave_height = u_params.z;
    float glow_intensity = u_params.w;

    // Create flowing aurora bands
    float time = u_time * wave_speed;

    // Multiple wave layers
    float wave1 = sin(uv.x * 3.0 + time) * wave_height * 0.3;
    float wave2 = sin(uv.x * 5.0 - time * 1.3) * wave_height * 0.2;
    float wave3 = sin(uv.x * 7.0 + time * 0.7) * wave_height * 0.15;

    // Add noise-based distortion
    float noise_val = fbm(vec2(uv.x * 2.0 + time * 0.5, uv.y * 0.5));
    float wave_y = 0.5 + wave1 + wave2 + wave3 + noise_val * 0.1;

    // Distance from wave center
    float dist = abs(uv.y - wave_y);

    // Create soft glow falloff
    float glow = exp(-dist * 8.0 / glow_intensity);
    glow = smoothstep(0.0, 1.0, glow);

    // Add vertical ribbons
    float ribbon_noise = fbm(vec2(uv.x * 10.0, time * 0.2));
    float ribbons = pow(ribbon_noise, 3.0) * 0.5;

    // Combine effects
    float intensity = glow + ribbons * glow;

    // Apply color
    float color_phase = uv.x + noise_val * 0.3 + time * 0.1;
    vec3 color = aurora_color(color_phase, color_shift);

    // Apply intensity with some vertical fade
    float vert_fade = smoothstep(0.0, 0.3, uv.y) * smoothstep(1.0, 0.7, uv.y);
    color *= intensity * vert_fade;

    // Add subtle stars in background
    float stars = step(0.997, hash(floor(uv * u_resolution * 0.1)));
    color += vec3(stars) * 0.3 * (1.0 - intensity);

    // Dark sky background
    vec3 sky = vec3(0.02, 0.02, 0.05);
    color = mix(sky, color, clamp(intensity, 0.0, 1.0));

    fragColor = vec4(color, 1.0);
}

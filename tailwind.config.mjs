/** @type {import('tailwindcss').Config} */
export default {
    content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
    darkMode: 'class',
    theme: {
        extend: {
            animation: {
                "drift-line": "driftLine 18s linear infinite",
                "soft-pulse": "softPulse 7s ease-in-out infinite",
            },
            keyframes: {
                driftLine: {
                    "0%": { strokeDashoffset: "0" },
                    "100%": { strokeDashoffset: "-320" },
                },
                softPulse: {
                    "0%, 100%": { opacity: "0.28", transform: "scale(1)" },
                    "50%": { opacity: "0.5", transform: "scale(1.02)" },
                },
            },
        },
    },
    plugins: [],
}

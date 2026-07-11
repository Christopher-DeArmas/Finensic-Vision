/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Black / near-black surfaces.
        ink: {
          950: "#08080a",
          900: "#0c0c0f",
          850: "#111114",
          800: "#16161b",
          750: "#1c1c22",
          700: "#24242c",
          600: "#2f2f38",
        },
        // Gold accent scale.
        gold: {
          50: "#fbf6e5",
          100: "#f5e9bf",
          200: "#efd98c",
          300: "#e7c65a",
          400: "#d9b23c",
          500: "#d4af37",
          600: "#b18f22",
          700: "#8a6f1b",
          800: "#5f4c12",
          900: "#3a2f0b",
          DEFAULT: "#d4af37",
        },
        // Brand blue undertone.
        brand: {
          400: "#4d9bff",
          500: "#1f80ff",
          600: "#1666d6",
          700: "#1250a8",
          DEFAULT: "#1f80ff",
        },
        // Semantic risk colors.
        risk: {
          low: "#34d399",
          medium: "#eab308",
          high: "#f97316",
          critical: "#ef4444",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        gold: "0 0 0 1px rgba(212,175,55,0.15), 0 8px 30px -12px rgba(212,175,55,0.25)",
        card: "0 1px 0 0 rgba(255,255,255,0.03) inset, 0 10px 30px -18px rgba(0,0,0,0.9)",
      },
      keyframes: {
        flash: {
          "0%": { backgroundColor: "rgba(239,68,68,0.28)" },
          "100%": { backgroundColor: "rgba(239,68,68,0)" },
        },
        pulseDot: {
          "0%,100%": { opacity: "1" },
          "50%": { opacity: "0.35" },
        },
      },
      animation: {
        flash: "flash 1.6s ease-out",
        pulseDot: "pulseDot 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

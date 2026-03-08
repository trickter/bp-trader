/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        shell: "#041126",
        panel: "#081936",
        panelAlt: "#0c2246",
        line: "rgba(125, 170, 255, 0.12)",
        glow: "#40d5ff",
        profit: "#22e28b",
        loss: "#ff6f91",
        warning: "#ffbc42",
        text: "#e8efff",
        muted: "#88a0c7"
      },
      boxShadow: {
        panel: "0 20px 60px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.04)",
        neon: "0 0 0 1px rgba(64, 213, 255, 0.18), 0 0 24px rgba(64, 213, 255, 0.08)"
      },
      fontFamily: {
        display: ["Georgia", "Cambria", "\"Times New Roman\"", "serif"],
        body: ["\"IBM Plex Sans\"", "\"Segoe UI\"", "sans-serif"]
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(144, 182, 255, 0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(144, 182, 255, 0.07) 1px, transparent 1px)"
      }
    }
  },
  plugins: [],
};

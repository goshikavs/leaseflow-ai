import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          800: "#1e3a5f",
          900: "#152943",
        },
      },
    },
  },
  plugins: [],
};

export default config;

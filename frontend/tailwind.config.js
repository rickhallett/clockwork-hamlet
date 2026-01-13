/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#1a1b26',
        'bg-secondary': '#24283b',
        'bg-highlight': '#414868',
        'fg-primary': '#c0caf5',
        'fg-secondary': '#a9b1d6',
        'fg-dim': '#565f89',
        'accent-blue': '#7aa2f7',
        'accent-cyan': '#7dcfff',
        'accent-green': '#9ece6a',
        'accent-magenta': '#bb9af7',
        'accent-red': '#f7768e',
        'accent-yellow': '#e0af68',
        'accent-orange': '#ff9e64',
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}

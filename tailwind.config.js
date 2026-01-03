/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'teamwork-green': '#A4D65E',
        'teamwork-green-dark': '#8BC34A',
        'teamwork-charcoal': '#3A3A3A',
        'light-bg': '#FFFFFF',
        'light-surface': '#F8F9FA',
        'light-border': '#E5E7EB',
        'text-primary': '#1F2937',
        'text-secondary': '#6B7280',
        'text-muted': '#9CA3AF',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

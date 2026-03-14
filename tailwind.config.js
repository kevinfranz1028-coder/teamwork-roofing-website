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
        'teamwork-green': '#1A6B28',
        'teamwork-green-dark': '#144F1E',
        'teamwork-charcoal': '#2B2B2B',
        'teamwork-silver': '#8C8C8C',
        'teamwork-pale': '#E8F3EA',
        'light-bg': '#F2F2F2',
        'light-surface': '#F2F2F2',
        'light-border': '#E5E7EB',
        'text-primary': '#2B2B2B',
        'text-secondary': '#8C8C8C',
        'text-muted': '#8C8C8C',
      },
      fontFamily: {
        sans: ['Open Sans', 'Arial', 'Helvetica', 'sans-serif'],
        heading: ['Oswald', 'Arial', 'Helvetica', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

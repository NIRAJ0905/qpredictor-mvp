/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f0f4ff',
          100: '#e0e9ff',
          500: '#4f6ef7',
          600: '#3d5be0',
          700: '#2d47c9',
          900: '#1a2a7a',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    }
  },
  plugins: []
}

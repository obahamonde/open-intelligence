import { useDark } from '~/hooks'

export default function Footer() {
  const { isDark, toggleDark } = useDark()
  return (
    <footer className="bg-white dark:bg-[#1A1A2E] text-black dark:text-white py-8 border-t border-black/20 dark:border-white/20">
      <div className="container mx-auto px-4 text-center">
        <p>© 2024 OpenAI In a Box. All rights reserved.</p>
       <button className="icon-btn !outline-none" onClick={() => toggleDark()}>
        {isDark ? <div className="i-carbon-moon" /> : <div className="i-carbon-sun" />}
      </button>

      <a
        className="icon-btn i-carbon-logo-github"
        rel="noreferrer"
        href="https://github.com/obahamonde/open-intelligence"
        target="_blank"
        title="GitHub"
      />  
      <p className="mt-2">
          This project is licensed under the MIT License - see the{" "}
          <a href="#" className="text-blue-600 dark:text-blue-400 hover:underline">
            LICENSE
          </a>{" "}
          file for details.
        </p>
      </div>
    </footer>
  )
}

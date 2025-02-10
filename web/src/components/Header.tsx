import { MoonIcon, SunIcon } from 'lucide-react'
import { Button } from "~/components/ui/button"
import { Icon } from "@iconify/react"

interface HeaderProps {
  darkMode: boolean
  toggleDarkMode: () => void
}

export default function Header({ darkMode, toggleDarkMode }: HeaderProps) {
  return (
    <header className="fixed top-0 w-full z-50 bg-white/10 dark:bg-black/10 backdrop-blur-md border-b border-white/20">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-[#00F5FF] to-[#FF1493] text-transparent bg-clip-text">
          OpenAI In a Box
        </h1>
        <nav className="flex items-center space-x-4">
          <a href="https://github.com/obahamonde/open-intelligence" className="text-black dark:text-white hover:text-[#00F5FF] transition-colors">
            <Icon icon="mdi:github" width="24" height="24"></Icon>
            <span className="ml-2 hidden sm:inline">GitHub</span>
          </a>
          <a href="#" className="text-black dark:text-white hover:text-[#00F5FF] transition-colors">
            <Icon icon="simple-icons:kofi" width="24" height="24"></Icon>
            <span className="ml-2 hidden sm:inline">Ko-fi</span>
          </a>
          <a href="/docs" className="text-black dark:text-white hover:text-[#00F5FF] transition-colors">
            <Icon icon="mdi:file-document-outline" width="24" height="24"></Icon>
            <span className="ml-2 hidden sm:inline">Docs</span>
          </a>
          <Button variant="ghost" size="icon" onClick={toggleDarkMode}>
            {darkMode ? <SunIcon className="h-[1.2rem] w-[1.2rem]" /> : <MoonIcon className="h-[1.2rem] w-[1.2rem]" />}
          </Button>
        </nav>
      </div>
    </header>
  )
}


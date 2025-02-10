import { useState, useEffect } from "react"
import Header from "~/components/Header"
import Hero from "~/components/Hero"
import Models from "~/components/Models"
import Installation from "~/components/Installation"
import Usage from "~/components/Usage"
import Footer from "~/components/Footer"

export default function Home() {
  const [darkMode, setDarkMode] = useState(false)

  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
  }

  useEffect(() => {
    // Background image carousel
    const bgImages = [
      'https://source.unsplash.com/random/1920x1080?ai',
      'https://source.unsplash.com/random/1920x1080?technology',
      'https://source.unsplash.com/random/1920x1080?future'
    ]
    let currentBgIndex = 0
    const bgCarousel = document.getElementById('bgCarousel')

    function changeBgImage() {
      const nextIndex = (currentBgIndex + 1) % bgImages.length
      const nextImage = new Image()
      nextImage.src = bgImages[nextIndex]
      nextImage.onload = () => {
        if (bgCarousel) {
          bgCarousel.style.backgroundImage = `linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url(${bgImages[nextIndex]})`
          bgCarousel.style.backgroundSize = 'cover'
          bgCarousel.style.backgroundPosition = 'center'
        }
        currentBgIndex = nextIndex
      }
    }

    const interval = setInterval(changeBgImage, 5000)
    changeBgImage() // Initial load

    return () => clearInterval(interval)
  }, [])

  return (
    <div className={`min-h-screen ${darkMode ? "dark" : ""}`}>
      <Header darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
      <main>
        <Hero />
        <Models />
        <Installation />
        <Usage />
      </main>
      <Footer />
    </div>
  )
}
"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "~/components/ui/card"
import { Icon } from "@iconify/react"

const models = [
  { name: "Chat", model: "llama-3", icon: "mdi:chat" },
  { name: "Image", model: "flux-schnell", icon: "mdi:image" },
  { name: "TextToSpeech", model: "xtts", icon: "mdi:microphone" },
  { name: "SpeechToText", model: "Whisper-Large-v3", icon: "mdi:headphones" },
  { name: "VectorStores", model: "quipubase + PostgreSQL", icon: "mdi:database" },
  { name: "Search", model: "quipubase + faiss-cpu", icon: "mdi:magnify" },
  { name: "FineTuning", model: "S3 + PostgreSQL + Huggingface + vLLM", icon: "mdi:cog" },
]

export default function Models() {
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => (prevIndex + 1) % models.length)
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  return (
    <section className="py-16 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-white to-purple-50 dark:from-[#1A1A2E] dark:to-purple-900/20"></div>
      <div className="absolute inset-0 grid-background"></div>
      <div className="container mx-auto px-4 relative z-10">
        <h2 className="text-3xl font-bold mb-12 text-center text-black dark:text-white fade-in">Models Implemented</h2>
        <div className="flex overflow-hidden relative h-[400px]">
          <Card className="absolute w-full bg-white/10 dark:bg-white/5 backdrop-blur-xl border border-white/20 dark:border-white/10 rounded-lg p-8 flex flex-col items-center justify-center h-[400px] fade-in shadow-lg shadow-purple-500/5">
            <CardContent className="flex flex-col items-center justify-center">
              <div className="w-32 h-32 rounded-lg mb-6 flex items-center justify-center bg-gradient-to-br from-[#00F5FF]/20 to-[#FF1493]/20 backdrop-blur-3xl">
                <Icon
                  icon={models[currentIndex].icon}
                  className="w-16 h-16"
                  style={{ color: ["#00F5FF", "#FF1493", "#8A2BE2"][currentIndex % 3] }}
                />
              </div>
              <h3 className="text-2xl font-bold mb-2 text-black dark:text-white">{models[currentIndex].name}</h3>
              <p className="text-lg text-black/70 dark:text-white/70 mb-6">{models[currentIndex].model}</p>
            </CardContent>
          </Card>
        </div>
        <div className="flex justify-center mt-8 gap-2">
          {models.map((_, index) => (
            <button
              key={index}
              className={`w-3 h-3 rounded-full transition-all duration-300 ${
                index === currentIndex
                  ? "bg-gradient-to-r from-[#00F5FF] to-[#FF1493] scale-125"
                  : "bg-black/30 dark:bg-white/30"
              }`}
              onClick={() => setCurrentIndex(index)}
            ></button>
          ))}
        </div>
      </div>
    </section>
  )
}


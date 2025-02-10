import { Button } from "~/components/ui/button"

export default function Hero() {
  return (
    <section className="min-h-screen relative flex items-center justify-center overflow-hidden">
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat transition-opacity duration-1000"
        style={{
          backgroundImage:
            "url(https://hebbkx1anhila5yf.public.blob.vercel-storage.com/8B510D1C-C187-4681-96B4-96E7E92F2244-DKZBJFz7SRsgA8b6T6uiQqP1k7ToHS.png)",
          backgroundPosition: "50% 30%",
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/50 to-[#1A1A2E]/90"></div>
      <div className="absolute inset-0 grid-background"></div>
      <div className="container mx-auto px-4 text-center relative z-10 mt-16">
        <h2 className="text-6xl font-bold mb-4 text-white title-glow fade-in">OpenAI In a Box</h2>
        <p className="text-2xl mb-8 text-white/80 max-w-2xl mx-auto fade-in fade-in-delay-1">
          Unleash the Power of AI: Your Complete OpenAI Solution
        </p>
        <Button
          size="lg"
          className="bg-white/10 backdrop-blur-md border border-white/20 hover:bg-white/20 text-white cta-glow fade-in fade-in-delay-2 px-8 py-6 text-lg"
        >
          Get Started
        </Button>
      </div>
    </section>
  )
}


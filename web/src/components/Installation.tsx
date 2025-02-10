import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card"

const installationSteps = [
  "git clone https://github.com/obahamonde/openai-in-a-box.git",
  "cd openai-in-a-box",
  "docker build -t openai-in-a-box .",
  "docker run -d -p 8080:8080 openai-in-a-box",
]

export default function Installation() {
  return (
    <section className="py-16 relative overflow-hidden">
      <div className="absolute inset-0 bg-gray-100 dark:bg-[#1A1A2E]"></div>
      <div className="absolute inset-0 grid-background"></div>
      <div className="container mx-auto px-4 relative z-10">
        <h2 className="text-3xl font-bold mb-8 text-center text-black dark:text-white fade-in">Installation</h2>
        <Card className="bg-white/10 dark:bg-white/10 backdrop-blur-md border border-black/20 dark:border-white/20 fade-in fade-in-delay-1">
          <CardHeader>
            <CardTitle className="text-black dark:text-white">Follow these steps to install:</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="list-decimal list-inside space-y-2">
              {installationSteps.map((step, index) => (
                <li
                  key={index}
                  className="font-mono bg-black/5 dark:bg-black/30 p-2 rounded text-black dark:text-white"
                >
                  {step}
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      </div>
    </section>
  )
}


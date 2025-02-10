import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card"

export default function Usage() {
  return (
    <section className="py-16 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-white to-blue-50 dark:from-[#1A1A2E] dark:to-blue-900/20"></div>
      <div className="absolute inset-0 grid-background"></div>
      <div className="container mx-auto px-4 relative z-10">
        <h2 className="text-3xl font-bold mb-8 text-center text-black dark:text-white fade-in">Usage</h2>
        <Card className="bg-white/10 dark:bg-white/5 backdrop-blur-xl border border-white/20 dark:border-white/10 fade-in fade-in-delay-1 shadow-lg shadow-blue-500/5">
          <CardHeader>
            <CardTitle className="text-black dark:text-white">Example usage with Python:</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-black/5 dark:bg-black/50 p-6 rounded-lg overflow-x-auto text-sm font-mono">
              <code className="text-black dark:text-white">
                <span className="text-purple-600 dark:text-purple-400">from</span>{" "}
                <span className="text-blue-600 dark:text-blue-400">openai</span>{" "}
                <span className="text-purple-600 dark:text-purple-400">import</span>{" "}
                <span className="text-green-600 dark:text-green-400">OpenAI</span>
                {"\n\n"}
                <span className="text-blue-600 dark:text-blue-400">client</span>{" "}
                <span className="text-purple-600 dark:text-purple-400">=</span>{" "}
                <span className="text-green-600 dark:text-green-400">OpenAI</span>()
                {"\n\n"}
                <span className="text-blue-600 dark:text-blue-400">response</span>{" "}
                <span className="text-purple-600 dark:text-purple-400">=</span> client.chat.completion(
                {"\n    "}messages=[{"\n        "}
                {"{"}
                {"\n            "}"role": "system",
                {"\n            "}"content": "You are a chatbot."
                {"\n        "}
                {"}"}
                {"\n    "}]{"\n"}){"\n"}
                <span className="text-purple-600 dark:text-purple-400">print</span>(response.choices[0].message.content)
              </code>
            </pre>
          </CardContent>
        </Card>
      </div>
    </section>
  )
}


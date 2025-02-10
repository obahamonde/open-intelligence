import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card"
import { CheckCircle } from "lucide-react"

const features = [
  "REST API: Fully documented REST API complying with OpenAI API Specification.",
  "OpenAI SDKs: Supports all OpenAI SDKs out of the box.",
  "Docker: Production ready Docker image.",
  "GPU: Supports H100 and x4 A40 GPUs.",
  "Caching: RocksDB based caching for faster responses.",
  "Monitoring: Prometheus and Grafana for monitoring.",
  "Security: API Key based authentication.",
  "Rate Limiting: Rate limiting based on OpenAI API Specification.",
  "Custom Models: Custom models can be added easily with vLLM.",
]

export default function Features() {
  return (
    <section className="py-16 bg-white">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl font-bold mb-8 text-center">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <Card key={index}>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                  {feature.split(":")[0]}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p>{feature.split(":")[1]}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}


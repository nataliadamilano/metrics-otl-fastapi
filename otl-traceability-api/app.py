from opentelemetry.propagate import inject
from opentelemetry import trace
from fastapi import FastAPI
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.context import attach, detach
import httpx

resource = Resource.create({SERVICE_NAME: "traceability-api"})
provider = TracerProvider(resource=resource)
# Sets the global default tracer provider
trace.set_tracer_provider(provider)

jaeger_exporter = JaegerExporter(agent_host_name="localhost", agent_port=6831)
processor = BatchSpanProcessor(jaeger_exporter)
provider.add_span_processor(processor)


app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

# Middleware para inyectar encabezados de trazas
@app.middleware("http")
async def inject_trace_headers(request, call_next):
    # Comienza un span de trazas
    with trace.get_tracer_provider().get_tracer(__name__).start_as_current_span("parent_span"):
        # Inyecta los encabezados de trazas en la solicitud
        with attach(request.scope):
            response = await call_next(request)
        return response

# Ruta de ejemplo
@app.get("/")
async def read_root():
    # Obtiene el span actual y agrega atributos, eventos, etc.
    current_span = trace.get_current_span()
    current_span.set_attribute("custom_attribute", "custom_value")
    current_span.add_event("example_event", {"key": "value"})
    return {"message": "Hello, World!"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app=app, host="0.0.0.0", port=8001)
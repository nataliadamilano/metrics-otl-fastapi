# import requests
# from opentelemetry.baggage.propagation import W3CBaggagePropagator
# from opentelemetry.propagators.composite import CompositePropagator
# from fastapi import FastAPI, Request
# from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
# from opentelemetry.instrumentation.requests import RequestsInstrumentor
# from opentelemetry.propagate import set_global_textmap
# from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
# import uvicorn 

# set_global_textmap(CompositePropagator([TraceContextTextMapPropagator(), W3CBaggagePropagator()]))

# app = FastAPI()

# FastAPIInstrumentor.instrument_app(app)
# RequestsInstrumentor().instrument()

# @app.get("/")
# async def get_things():

#     return {
#         "Hello": "world",
#         "request": "algo"
#     }
from fastapi import FastAPI, Header, Request
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                            ConsoleSpanExporter)
from opentelemetry.trace.propagation.tracecontext import \
    TraceContextTextMapPropagator
import uvicorn

app = FastAPI()


trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

tracer = trace.get_tracer(__name__)

prop = TraceContextTextMapPropagator()
carrier = {}

@app.get("/ruta")
def mi_ruta(request: Request):
    prop = TraceContextTextMapPropagator()
    context = prop.extract(carrier=request.headers)
    return {"message": "Ruta procesada correctamente", "trace": context}

if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8081)
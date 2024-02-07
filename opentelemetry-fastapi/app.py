# from fastapi import FastAPI, Request
# import uvicorn
# from opentelemetry import trace, context, propagate
# from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor, SimpleSpanProcessor
# from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
# from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# # Configurar proveedor de trazas con un exportador de consola
# tracer_provider = TracerProvider()
# tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
# trace.set_tracer_provider(tracer_provider)

# # Configura el propagador de contexto para Trace Context
# propagate.set_global_textmap(TraceContextTextMapPropagator())

# app = FastAPI()

# # Instrumenta tu aplicación FastAPI
# FastAPIInstrumentor().instrument_app(app)

# # Middleware para propagar el contexto de trazas en las solicitudes HTTP
# @app.middleware("http")
# async def propagate_trace_context(request: Request, call_next):
#     # Extraer el contexto de trazas del encabezado HTTP
#     context = propagate.extract(request.headers)
#     with trace.use_span(span=context):
#         response = await call_next(request)
#         # Propagar el contexto de trazas en el encabezado de respuesta HTTP
#         propagate.inject(response.headers)
#     return response

# @app.get("/ruta")
# async def ruta(request: Request):
#     # Aquí puedes acceder al contexto de trazas usando trace.get_current_span()
#     current_span = trace.get_current_span()
#     print(current_span)
#     # Realiza las operaciones que necesites con el contexto de trazas
#     return {"message": "Ruta procesada correctamente"}
# from fastapi import FastAPI
# from opentelemetry import trace
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import ConsoleSpanExporter
# from opentelemetry.sdk.trace.export import SimpleSpanProcessor
# from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# app = FastAPI()

# # Configuración del proveedor de trazas
# tracer_provider = TracerProvider()

# # Exportador de trazas a la consola
# span_processor = SimpleSpanProcessor(ConsoleSpanExporter())
# tracer_provider.add_span_processor(span_processor)

# # Configurar el proveedor de trazas
# trace.set_tracer_provider(tracer_provider)
# tracer = trace.get_tracer(__name__)

# # Propagador de contexto de trazas
# propagator = TraceContextTextMapPropagator()

# @app.get("/")
# def mi_ruta():
#     # Iniciar un span de trazas para la ruta actual
#     with tracer.start_as_current_span("first-span") as span:
#         # Crear un diccionario "carrier" y realizar la inyección del contexto de trazas
#         carrier = {}
#         propagator.inject(carrier=carrier)

#         # Imprimir el diccionario "carrier" después de inyectar el contexto de trazas
#         print("Carrier after injecting span context", carrier)

#         # Extraer el contexto de trazas del diccionario "carrier"
#         ctx = propagator.extract(carrier=carrier)

#         # Iniciar un nuevo span de trazas usando el contexto extraído
#         with tracer.start_as_current_span("next-span", context=ctx):
#             # Aquí puedes realizar las operaciones adicionales de tu ruta
#             pass

#         # Devolver la respuesta a tu cliente (puede ser el contenido del span actual o cualquier otro dato)
#         return "Ruta procesada correctamente"

# @app.get("/baggage")
# def bagagge():
#     # Crear un diccionario "carrier" con el valor de traceparent
#     carrier = {"traceparent": "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"}

#     # Extraer el valor de traceparent del "carrier"
#     traceparent_header = carrier.get("traceparent")
#     print("el traceparent header: ", traceparent_header)
#     # Establecer el valor de traceparent como un "baggage" en el contexto de trazas
#     with tracer.start_as_current_span("first-span") as span:
#         span.set_attribute("traceparent", traceparent_header)
#         print("ESTO SERIA EL SPAN: ", span)
#         # Extraer el valor de traceparent del "baggage" en el contexto del siguiente span
#         baggage_value = span.__getattribute__("traceparent")
#         print("Traceparent value in next-span (baggage):", baggage_value)

#         # Aquí puedes realizar las operaciones adicionales de tu ruta
#         pass

#     # Devolver la respuesta a tu cliente (puede ser el contenido del span actual o cualquier otro dato)
#     return "Ruta procesada correctamente"
from fastapi import FastAPI
from opentelemetry import trace, propagate
import requests
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

app = FastAPI()

tracer = trace.get_tracer(__name__)
propagator = TraceContextTextMapPropagator()

@app.get("/")
def enviar_solicitud():
    with tracer.start_as_current_span("servicio-a"):
        # Obtener el `traceparent` del contexto actual de trazas
        carrier = {}
        propagator.inject(carrier=carrier)
        # Enviar la solicitud al servicio B incluyendo el `traceparent` en el encabezado
        response = requests.get("http://localhost:8081/ruta", headers=carrier)

        # Devolver la respuesta del servicio B al cliente del servicio A
        return response.text

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

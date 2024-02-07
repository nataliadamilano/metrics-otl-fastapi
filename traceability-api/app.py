from fastapi.datastructures import Headers
from fastapi.requests import HTTPConnection
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import Status, StatusCode
from opentelemetry.propagate import set_global_textmap, get_global_textmap
from opentelemetry.propagators.jaeger import JaegerPropagator
from opentelemetry.propagators.textmap import Getter, Setter, TextMapPropagator
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.context import Context
from starlette.types import Message, Receive, Scope, Send

resource = Resource.create({SERVICE_NAME: "traceability-api"})
provider = TracerProvider(resource=resource)
# Sets the global default tracer provider
trace.set_tracer_provider(provider)

jaeger_exporter = JaegerExporter(agent_host_name="localhost", agent_port=6831)
processor = BatchSpanProcessor(jaeger_exporter)
provider.add_span_processor(processor)


app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

class MyGetter(Getter):
    def get(self, carrier: Request, key: str):
        assert carrier != None
        return carrier.headers.get(key)

    def keys(self, carrier: Request):
        return carrier.headers


    
class RequestsHeaderMapper(HTTPConnection):
    @property
    def headers(self) -> Headers:
        if not hasattr(self, "_headers"):
            self._headers = Headers(scope=self.scope)
        return self._headers
    
    @headers.setter
    def headers(self, new_headers: Headers):
        self._headers = new_headers

class MySetter(Setter):
    def set(self, carrier: RequestsHeaderMapper, key: str, value: str):
        assert carrier != None
        return carrier.headers.get(key)
        
class MyTextMapPropagator(TextMapPropagator):
    def extract(self, carrier, context, getter):
        # Implementa la lógica para extraer datos del portador (carrier)
        pass

    def inject(self, carrier, context, setter):
        # Implementa la lógica para inyectar datos en el portador (carrier)
        pass

    def fields(self):
        # Implementa la lógica para obtener los campos del portador (carrier)
        pass
    
# Middleware para crear un span global para cada solicitud
class TraceMiddleware:
    def __init__(self, app):
        self.app = app
        self.tracer = trace.get_tracer(__name__)
    
    def create_span(self):
        with self.tracer.start_span("GET_http://localhost:8000/local") as span:
            span.set_attribute("prueba_create_span_1", "valor_1")
            span.set_attribute("prueba_create_span_2", "valor_2")
            
    async def __call__(self, scope, receive, send):
        
        # if trace.get_current_span() is None:
        #     with tracer.start_as_current_span("nombre_del_span") as span:
        #         # Aquí puedes establecer atributos en el span según sea necesario
        #         span.set_attribute("atributo_1", "valor_1")
        #         span.set_attribute("atributo_2", "valor_2")
        # else:
        #     with trace.get_current_span() as span:
        #         # Injectar el contexto de trazas en el encabezado HTTP usando el propagador Jaeger
        #         #headers = {}
        propagator = MyTextMapPropagator()
        getter = MyGetter()
        request = Request(scope, receive=receive)
        extracted_context = propagator.extract(getter= getter, carrier=request , context=None)
                
        if extracted_context != None:
            print("aloha")
            with self.tracer.start_as_current_span(context=extracted_context) as span:
                self.create_span()
        else:
            span = self.create_span()
                # Configurar el propagador (en este caso, B3 propagator)
            b3_propagator = get_global_textmap()

            # Obtener el contexto actual y el span actual (opcional)
            current_context = Context.current()
            # current_span = trace.get_current_span()

            # Crear un diccionario para almacenar los encabezados que se enviarán en la solicitud
            headers = {}

            # Inyectar el contexto de trazas en los encabezados
            b3_propagator.inject(current_context, headers)

            # headers ahora contiene el uber-trace-id y otros encabezados de trazas
            print(headers)
            # for header, value in request.headers.items():
            #     print(f"{header}: {value}")
                
            # textmap_propagator = get_global_textmap()
            # setter = MySetter()
            # requestHeaders = RequestsHeaderMapper(scope)
            # textmap_propagator.inject(span, requestHeaders, setter)
        await self.app(scope, receive, send)

# Aplicar el middleware de trazas
app.add_middleware(TraceMiddleware)

@app.get("/local")
def get(request: Request):
    # # Obtiene el tracer actual
    # tracer = trace.get_tracer(__name__)

    # # Inicia un nuevo span (opcional)
    # with tracer.start_as_current_span(f"{request.method}_{request.url}") as span:
    #     # Agrega atributos al span actual
    #     span.set_attribute("nombre-del-atributo", "valor-del-atributo")
        
    #     # Realiza operaciones adicionales en tu aplicación aquí

    #     # Devuelve una respuesta
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app=app, host="0.0.0.0", port=8000)
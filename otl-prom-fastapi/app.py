from fastapi import FastAPI, HTTPException, Response
import random
import uvicorn
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.resources import Resource
import prometheus_client

app = FastAPI()

# Crear un recurso con metadatos
app_resource = Resource.create(
    {
        "service.name": "fastapi-metrics",
        "service.version": "1.0.0",
        "environment": "development",
        "language": "python",
    }
)

metric_reader = PrometheusMetricReader("fastapi")
provider = MeterProvider(resource=app_resource, metric_readers=[metric_reader])

# Sets the global default meter provider
metrics.set_meter_provider(provider)

# Creates a meter from the global meter provider
meter = metrics.get_meter("nati.meter.test")

heads_counter = meter.create_counter(
    name="heads_count", unit="events", description="Number of heads"
)

requests_counter = meter.create_counter(
    name="http_request_count", unit="requests", description="Cantidad de requests recibidos."
)

messages_processed_counter = meter.create_counter(
    name="messages_processed_count", unit="messages", description="Cantidad de mensajes procesados."
)

errors_counter = meter.create_counter(
    name="errors_count", unit="errors", description="Cantidad de errores arrojados."
)

@app.get("/metrics")
def get_metrics():
    return Response(
        media_type="text/plain",
        content=prometheus_client.generate_latest()
    )

@app.get("/flip-coins")
async def flip_coins(times=None):    
    try:    
        if times is None or not times.isdigit():
            raise HTTPException(
                status_code=400,
                detail="time must be set in request and an integer"
            )
        times_as_int = int(times)
        
        heads = 0
        for _ in range(times_as_int):
            if random.randint(0, 1):
                heads += 1
        tails = times_as_int - heads
        
        heads_counter.add(heads)
        # heads_count.inc(heads)
        # tails_count.inc(tails)
        # flip_count.inc(times_as_int)
        
        messages_processed_counter.add(1)
        return {
            "heads": heads,
            "tails": tails,
        }
    except HTTPException as ex:
        errors_counter.add(1, {"status_code": str(ex.status_code)})
        raise ex
    
@app.get("/internal-error")
async def internal_error():
    requests_counter.add(1)
    
    try:
        raise HTTPException(status_code=500)
    except HTTPException as ex:
        errors_counter.add(1, {"status_code": str(ex.status_code)})
        raise ex
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6060)
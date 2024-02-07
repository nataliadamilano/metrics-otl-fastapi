from fastapi import FastAPI, HTTPException
import random
import uvicorn
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)

app = FastAPI()

metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
provider = MeterProvider(metric_readers=[metric_reader])

# Sets the global default meter provider
metrics.set_meter_provider(provider)

# Creates a meter from the global meter provider
meter = metrics.get_meter("nati.meter.test")

heads_counter = meter.create_counter(
    name="heads_count", unit="events", description="Number of heads"
)

@app.get("/flip-coins")
async def flip_coins(times=None):
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
    
    return {
        "heads": heads,
        "tails": tails,
    }
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5050)
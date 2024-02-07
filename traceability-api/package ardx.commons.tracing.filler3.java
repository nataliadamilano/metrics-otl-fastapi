package ardx.commons.tracing.filler.filter.configuration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.info.BuildProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.propagation.ContextPropagators;
import io.opentelemetry.exporter.jaeger.thrift.JaegerThriftSpanExporter;
import io.opentelemetry.exporter.logging.LoggingSpanExporter;
import io.opentelemetry.extension.trace.propagation.JaegerPropagator;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import io.opentelemetry.sdk.trace.samplers.Sampler;
import io.opentelemetry.semconv.resource.attributes.ResourceAttributes;

@Configuration
public class OpenTelemetryConfiguration {
	
	private static final Logger LOGGER = LoggerFactory.getLogger(OpenTelemetryConfiguration.class);
	
	private String traceparent;
	
	@Autowired
	BuildProperties buildProperties;
	
	@Value("${jaeger.collector.host:localhost}")
	private String jaegerCollectorHost;
	
	@Value("${jaeger.collector.port:14268}")
	private String jaegerCollectorPort;

	@Bean
    public OpenTelemetrySdk getOpenTelemetry (){
		try {
	        Resource serviceNameResource =
	                Resource.create(Attributes.of(ResourceAttributes.SERVICE_NAME, buildProperties.getArtifact()));
	        return OpenTelemetrySdk.builder()
	                .setTracerProvider(
	                        SdkTracerProvider.builder()
	                                .addSpanProcessor(SimpleSpanProcessor.create(getJaegerExporter()))
	                                .addSpanProcessor(SimpleSpanProcessor.create(LoggingSpanExporter.create()))
	                                .setSampler(Sampler.alwaysOn())
	                                .setResource(Resource.getDefault().merge(serviceNameResource))
	                                .build())
//	                .setPropagators(ContextPropagators.create(W3CTraceContextPropagator.getInstance(), jaegerPropagator))
	                .setPropagators(ContextPropagators.create(JaegerPropagator.getInstance()))
	                .buildAndRegisterGlobal();
		} catch(Exception ex) {
			LOGGER.error("Ha ocurrido un error al configurar Opentelemetry: " + ex.getMessage());
			return null;
		} finally {
			LOGGER.info("Configuracion de Opentelemetry realizada exitosamente");
		}
    }

    @Bean
    public JaegerThriftSpanExporter getJaegerExporter(){
    	String host = getJaegerCollectorHost();
    	String port = getJaegerCollectorPort();
        String jaegerUrl= "http://" + host + ":" + port + "/api/traces";
        LOGGER.info("Jaeger URL: " + jaegerUrl);
        return JaegerThriftSpanExporter.builder()
		            .setEndpoint(jaegerUrl)
		            .build();
    }

    @Bean
    public Tracer getTracer(){
        return getOpenTelemetry().getTracer(buildProperties.getArtifact());
    }
    
    public String getTraceparent() {
		return traceparent;
	}

	public void setTraceparent(String traceparent) {
		this.traceparent = traceparent;
	}

	public String getJaegerCollectorHost() {
		return jaegerCollectorHost;
	}

	public void setJaegerCollectorHost(String jaegerCollectorHost) {
		this.jaegerCollectorHost = jaegerCollectorHost;
	}

	public String getJaegerCollectorPort() {
		return jaegerCollectorPort;
	}

	public void setJaegerCollectorPort(String jaegerCollectorPort) {
		this.jaegerCollectorPort = jaegerCollectorPort;
	}

}
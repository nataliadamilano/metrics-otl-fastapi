import java.io.IOException;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.info.BuildProperties;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import ardx.commons.tracing.filler.filter.configuration.HeaderMapRequestWrapper;
import ardx.commons.tracing.filler.filter.configuration.OpenTelemetryConfiguration;
import ardx.commons.tracing.filler.filter.configuration.TracingFillerProperties;
import ardx.commons.tracing.filler.filter.exceptions.RequiredAttributeNotProvidedException;
import ardx.commons.tracing.filler.filter.model.TracingFillerErrorContainer;
import ardx.commons.tracing.filler.filter.service.TracingFillerContextProvider;
import ardx.commons.tracing.filler.filter.service.TracingFillerErrorSerializer;
import ardx.commons.tracing.filler.filter.utils.Utils;
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.baggage.Baggage;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Context;
import io.opentelemetry.context.Scope;
import io.opentelemetry.context.propagation.TextMapGetter;
import io.opentelemetry.context.propagation.TextMapSetter;
import io.opentelemetry.semconv.trace.attributes.SemanticAttributes;

@Component
public class TracingFillerFilter extends OncePerRequestFilter {

    private static final Logger LOGGER = LoggerFactory.getLogger(TracingFillerFilter.class);

    final static String X_FORWARDED_FOR_KEY = "x-forwarded-for";

    TracingFillerErrorSerializer tracingFillerErrorSerializer;

    TracingFillerProperties tracingFillerProperties;

    TracingFillerContextProvider tracingFillerContextProvider;
    
    private final OpenTelemetry openTelemetry;
    
    @Autowired
	OpenTelemetryConfiguration configuration;
    
    @Autowired
	private Tracer tracer;
    
    @Autowired
	public TracingFillerFilter(OpenTelemetry openTelemetry, OpenTelemetryConfiguration configuration, BuildProperties buildProperties) {
    	this.configuration = configuration;
		this.openTelemetry = openTelemetry;
		this.tracer = openTelemetry.getTracerProvider().get(buildProperties.getArtifact());
	}
    
    TextMapGetter<HttpServletRequest> getter = new TextMapGetter<HttpServletRequest>() {
		@Override
        public Iterable<String> keys(HttpServletRequest httpServletRequest) {
            return Utils.iterable(httpServletRequest.getHeaderNames());
        }

        @Override
        public String get(HttpServletRequest httpServletRequest, String s) {
            assert httpServletRequest != null;
            return httpServletRequest.getHeader(s);
        }
    };
            
    TextMapSetter<HeaderMapRequestWrapper> setter =
            (carrier, key, value) -> {
            	assert carrier != null;
                carrier.addHeader(key, value);
            };
            
    private Span createSpan(HttpServletRequest request, HttpServletResponse response) {
    	String methodName = request.getMethod();
    	String requestURI = request.getRequestURI();
    	String protocol = request.getProtocol();
    	String serverName = request.getServerName();
    	int status = response.getStatus();
    	int port = request.getLocalPort();
    	
    	Span span = tracer.spanBuilder(methodName+"_"+requestURI).startSpan();
    	span.addEv…
[15:26, 31/10/2023] Nati⚡: protected void doFilterInternal(
        HttpServletRequest httpServletRequest,
        HttpServletResponse httpServletResponse,
        FilterChain filterChain
    ) throws ServletException, IOException {
        try{
        	HeaderMapRequestWrapper requestWrapper = new HeaderMapRequestWrapper(httpServletRequest);
        	
    		Context extractedContext = openTelemetry.getPropagators().getTextMapPropagator()
                    .extract(Context.current(), httpServletRequest, getter);

    		if(!extractedContext.toString().equals("{}")) {
    			try (Scope scope = extractedContext.makeCurrent()) {
    				createSpan(httpServletRequest, httpServletResponse);
    			}
    		} else {
    	    	Span span = createSpan(httpServletRequest, httpServletResponse);
    			
    			Enumeration<String> headerNames = httpServletRequest.getHeaderNames();
    		    headerNames.asIterator().forEachRemaining(header -> {
    		         if(header != null) {
    		        	 requestWrapper.addHeader(header, httpServletRequest.getHeader(header));
    		         }
    		    });
    			openTelemetry.getPropagators().getTextMapPropagator().inject(Context.current().with(span), requestWrapper, setter);
    			configuration.setTraceparent(requestWrapper.getHeader("uber-trace-id"));
    		}
        }
        catch(Exception exception){
            TracingFillerErrorContainer tracingFillerErrorContainer = tracingFillerErrorSerializer.serialize(exception);
            httpServletResponse.setStatus(tracingFillerErrorContainer.getHttpStatus().value());
            Map<String, String> headers = tracingFillerErrorContainer.getHeaders();
            for (Map.Entry<String,String> entry : headers.entrySet()){
                httpServletResponse.addHeader(entry.getKey(), entry.getValue());
            }
            String responseBody = tracingFillerErrorContainer.getContent();
            httpServletResponse.setContentLength(responseBody.length());
            httpServletResponse.getWriter().write(responseBody);
            return;
        }
        filterChain.doFilter(httpServletRequest, httpServletResponse);
    }
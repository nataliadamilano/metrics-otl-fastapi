package ardx.commons.tracing.filler.filter.interceptor;

import java.io.IOException;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpRequest;
import org.springframework.http.client.ClientHttpRequestExecution;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.http.client.ClientHttpResponse;
import org.springframework.stereotype.Component;

import ardx.commons.tracing.filler.filter.configuration.OpenTelemetryConfiguration;

@Component
public class TracingRestTemplateInterceptor implements ClientHttpRequestInterceptor {
	
	@Autowired
	OpenTelemetryConfiguration configuration;
	
	public TracingRestTemplateInterceptor(OpenTelemetryConfiguration configuration) {
		this.configuration = configuration;
	}

	@Override
	public ClientHttpResponse intercept(HttpRequest request, byte[] body, ClientHttpRequestExecution execution)
			throws IOException {
		
		request.getHeaders().add("uber-trace-id", configuration.getTraceparent());
        ClientHttpResponse response = execution.execute(request, body);
		return response;
	}

}
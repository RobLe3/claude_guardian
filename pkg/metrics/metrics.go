package metrics

import (
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// Collector holds Prometheus metrics collectors
type Collector struct {
	requestDuration prometheus.HistogramVec
	requestTotal    prometheus.CounterVec
	requestSize     prometheus.HistogramVec
	responseSize    prometheus.HistogramVec
	errorTotal      prometheus.CounterVec
}

// NewCollector creates a new metrics collector
func NewCollector(serviceName string) *Collector {
	c := &Collector{
		requestDuration: *prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "http_request_duration_seconds",
				Help:    "HTTP request latencies in seconds",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"service", "method", "endpoint", "status_code"},
		),
		requestTotal: *prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Name: "http_requests_total",
				Help: "Total number of HTTP requests",
			},
			[]string{"service", "method", "endpoint", "status_code"},
		),
		requestSize: *prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "http_request_size_bytes",
				Help:    "HTTP request sizes in bytes",
				Buckets: prometheus.ExponentialBuckets(1024, 2, 10),
			},
			[]string{"service", "method", "endpoint"},
		),
		responseSize: *prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "http_response_size_bytes",
				Help:    "HTTP response sizes in bytes",
				Buckets: prometheus.ExponentialBuckets(1024, 2, 10),
			},
			[]string{"service", "method", "endpoint", "status_code"},
		),
		errorTotal: *prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Name: "errors_total",
				Help: "Total number of errors by type",
			},
			[]string{"service", "type", "operation"},
		),
	}

	// Register metrics with Prometheus
	prometheus.MustRegister(&c.requestDuration)
	prometheus.MustRegister(&c.requestTotal)
	prometheus.MustRegister(&c.requestSize)
	prometheus.MustRegister(&c.responseSize)
	prometheus.MustRegister(&c.errorTotal)

	return c
}

// RecordHTTPRequest records metrics for an HTTP request
func (c *Collector) RecordHTTPRequest(serviceName, method, endpoint string, statusCode int, duration time.Duration, requestSize, responseSize int64) {
	statusCodeStr := strconv.Itoa(statusCode)
	
	c.requestDuration.WithLabelValues(serviceName, method, endpoint, statusCodeStr).Observe(duration.Seconds())
	c.requestTotal.WithLabelValues(serviceName, method, endpoint, statusCodeStr).Inc()
	c.requestSize.WithLabelValues(serviceName, method, endpoint).Observe(float64(requestSize))
	c.responseSize.WithLabelValues(serviceName, method, endpoint, statusCodeStr).Observe(float64(responseSize))
}

// RecordError records an error metric
func (c *Collector) RecordError(serviceName, errorType, operation string) {
	c.errorTotal.WithLabelValues(serviceName, errorType, operation).Inc()
}

// HandlerFunc returns a handler function for the /metrics endpoint
func HandlerFunc() gin.HandlerFunc {
	h := promhttp.Handler()
	return gin.WrapH(h)
}

// Middleware creates a Gin middleware for automatic metrics collection
func Middleware(serviceName string, collector *Collector) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		
		// Process request
		c.Next()
		
		// Record metrics
		duration := time.Since(start)
		requestSize := calculateRequestSize(c.Request)
		responseSize := int64(c.Writer.Size())
		
		collector.RecordHTTPRequest(
			serviceName,
			c.Request.Method,
			c.FullPath(),
			c.Writer.Status(),
			duration,
			requestSize,
			responseSize,
		)
	}
}

// calculateRequestSize calculates the size of an HTTP request
func calculateRequestSize(r *http.Request) int64 {
	size := int64(0)
	if r.URL != nil {
		size += int64(len(r.URL.String()))
	}
	
	size += int64(len(r.Method))
	size += int64(len(r.Proto))
	
	for name, values := range r.Header {
		size += int64(len(name))
		for _, value := range values {
			size += int64(len(value))
		}
	}
	
	if r.ContentLength > 0 {
		size += r.ContentLength
	}
	
	return size
}
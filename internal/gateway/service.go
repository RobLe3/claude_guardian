package gateway

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/iff-guardian/platform/pkg/config"
	"github.com/iff-guardian/platform/pkg/logger"
	"github.com/iff-guardian/platform/pkg/metrics"
)

// Service represents the gateway service
type Service struct {
	config  *config.Config
	logger  logger.Logger
	metrics *metrics.Collector
}

// New creates a new gateway service
func New(cfg *config.Config, log logger.Logger, metrics *metrics.Collector) *Service {
	return &Service{
		config:  cfg,
		logger:  log,
		metrics: metrics,
	}
}

// RegisterRoutes registers HTTP routes
func (s *Service) RegisterRoutes(router *gin.RouterGroup) {
	router.GET("/status", s.getStatus)
	router.GET("/version", s.getVersion)
	
	// Authentication routes (proxy to auth service)
	auth := router.Group("/auth")
	{
		auth.POST("/login", s.proxyToAuthService)
		auth.POST("/logout", s.proxyToAuthService)
		auth.POST("/refresh", s.proxyToAuthService)
		auth.GET("/profile", s.proxyToAuthService)
	}
	
	// Detection routes (proxy to detection engine)
	detection := router.Group("/detection")
	{
		detection.POST("/scan", s.proxyToDetectionEngine)
		detection.GET("/threats", s.proxyToDetectionEngine)
		detection.GET("/status", s.proxyToDetectionEngine)
	}
	
	// Configuration routes (proxy to config service)
	cfg := router.Group("/config")
	{
		cfg.GET("/", s.proxyToConfigService)
		cfg.PUT("/", s.proxyToConfigService)
		cfg.GET("/:key", s.proxyToConfigService)
		cfg.PUT("/:key", s.proxyToConfigService)
	}
	
	// Monitoring routes (proxy to monitoring service)
	monitoring := router.Group("/monitoring")
	{
		monitoring.GET("/metrics", s.proxyToMonitoringService)
		monitoring.GET("/health", s.proxyToMonitoringService)
		monitoring.GET("/alerts", s.proxyToMonitoringService)
	}
}

// getStatus returns the service status
func (s *Service) getStatus(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"service": "gateway",
		"status":  "healthy",
		"timestamp": time.Now(),
	})
}

// getVersion returns the service version
func (s *Service) getVersion(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"service": "gateway",
		"version": "1.0.0",
		"environment": s.config.Environment,
	})
}

// proxyToAuthService proxies requests to the auth service
func (s *Service) proxyToAuthService(c *gin.Context) {
	s.logger.Info("Proxying request to auth service", "path", c.Request.URL.Path)
	// TODO: Implement actual proxy logic
	c.JSON(http.StatusNotImplemented, gin.H{
		"error": "Auth service proxy not implemented yet",
	})
}

// proxyToDetectionEngine proxies requests to the detection engine
func (s *Service) proxyToDetectionEngine(c *gin.Context) {
	s.logger.Info("Proxying request to detection engine", "path", c.Request.URL.Path)
	// TODO: Implement actual proxy logic
	c.JSON(http.StatusNotImplemented, gin.H{
		"error": "Detection engine proxy not implemented yet",
	})
}

// proxyToConfigService proxies requests to the config service
func (s *Service) proxyToConfigService(c *gin.Context) {
	s.logger.Info("Proxying request to config service", "path", c.Request.URL.Path)
	// TODO: Implement actual proxy logic
	c.JSON(http.StatusNotImplemented, gin.H{
		"error": "Config service proxy not implemented yet",
	})
}

// proxyToMonitoringService proxies requests to the monitoring service
func (s *Service) proxyToMonitoringService(c *gin.Context) {
	s.logger.Info("Proxying request to monitoring service", "path", c.Request.URL.Path)
	// TODO: Implement actual proxy logic
	c.JSON(http.StatusNotImplemented, gin.H{
		"error": "Monitoring service proxy not implemented yet",
	})
}

// LoggingMiddleware creates a logging middleware
func LoggingMiddleware(log logger.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		raw := c.Request.URL.RawQuery
		
		c.Next()
		
		latency := time.Since(start)
		clientIP := c.ClientIP()
		method := c.Request.Method
		statusCode := c.Writer.Status()
		
		if raw != "" {
			path = path + "?" + raw
		}
		
		log.Info("HTTP request",
			"method", method,
			"path", path,
			"status", statusCode,
			"latency", latency.String(),
			"client_ip", clientIP,
		)
	}
}

// MetricsMiddleware creates a metrics middleware
func MetricsMiddleware(metrics *metrics.Collector) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		
		c.Next()
		
		duration := time.Since(start)
		requestSize := int64(0) // TODO: Calculate actual request size
		responseSize := int64(c.Writer.Size())
		
		metrics.RecordHTTPRequest(
			"gateway",
			c.Request.Method,
			c.FullPath(),
			c.Writer.Status(),
			duration,
			requestSize,
			responseSize,
		)
	}
}
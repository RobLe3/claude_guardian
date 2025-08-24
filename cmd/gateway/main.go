package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/iff-guardian/platform/internal/gateway"
	"github.com/iff-guardian/platform/pkg/config"
	"github.com/iff-guardian/platform/pkg/logger"
	"github.com/iff-guardian/platform/pkg/metrics"
	"github.com/iff-guardian/platform/pkg/health"
)

func main() {
	// Load configuration
	cfg, err := config.Load("gateway")
	if err != nil {
		log.Fatal("Failed to load configuration:", err)
	}

	// Initialize logger
	logger := logger.New(cfg.LogLevel, cfg.ServiceName)
	
	// Initialize metrics
	metricsCollector := metrics.NewCollector("gateway")
	
	// Initialize health checker
	healthChecker := health.New()
	
	// Create gateway service
	gatewayService := gateway.New(cfg, logger, metricsCollector)
	
	// Setup Gin router
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}
	
	router := gin.New()
	router.Use(gin.Recovery())
	router.Use(gateway.LoggingMiddleware(logger))
	router.Use(gateway.MetricsMiddleware(metricsCollector))
	
	// Health check endpoint
	router.GET("/health", health.HandlerFunc(healthChecker))
	router.GET("/ready", health.ReadinessHandlerFunc(healthChecker))
	
	// Metrics endpoint
	router.GET("/metrics", metrics.HandlerFunc())
	
	// API routes
	api := router.Group("/api/v1")
	gatewayService.RegisterRoutes(api)
	
	// Create HTTP server
	server := &http.Server{
		Addr:    fmt.Sprintf(":%d", cfg.Port),
		Handler: router,
	}
	
	// Start server in goroutine
	go func() {
		logger.Info("Starting gateway service", "port", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Error("Failed to start server", "error", err)
			os.Exit(1)
		}
	}()
	
	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	
	logger.Info("Shutting down gateway service...")
	
	// Graceful shutdown with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	
	if err := server.Shutdown(ctx); err != nil {
		logger.Error("Server forced to shutdown", "error", err)
	}
	
	logger.Info("Gateway service stopped")
}
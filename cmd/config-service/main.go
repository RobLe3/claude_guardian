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
	"github.com/iff-guardian/platform/internal/config_service"
	"github.com/iff-guardian/platform/pkg/config"
	"github.com/iff-guardian/platform/pkg/logger"
	"github.com/iff-guardian/platform/pkg/metrics"
	"github.com/iff-guardian/platform/pkg/health"
	"github.com/iff-guardian/platform/pkg/database"
)

func main() {
	// Load configuration
	cfg, err := config.Load("config-service")
	if err != nil {
		log.Fatal("Failed to load configuration:", err)
	}

	// Initialize logger
	logger := logger.New(cfg.LogLevel, cfg.ServiceName)
	
	// Initialize metrics
	metricsCollector := metrics.NewCollector("config_service")
	
	// Initialize database
	db, err := database.NewPostgres(cfg.Database.URL)
	if err != nil {
		logger.Error("Failed to connect to database", "error", err)
		os.Exit(1)
	}
	defer db.Close()
	
	// Initialize health checker
	healthChecker := health.New()
	healthChecker.AddCheck("database", database.HealthCheck(db))
	
	// Create config service
	configService := config_service.New(cfg, logger, metricsCollector, db)
	
	// Setup Gin router
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}
	
	router := gin.New()
	router.Use(gin.Recovery())
	router.Use(config_service.LoggingMiddleware(logger))
	router.Use(config_service.MetricsMiddleware(metricsCollector))
	
	// Health check endpoints
	router.GET("/health", health.HandlerFunc(healthChecker))
	router.GET("/ready", health.ReadinessHandlerFunc(healthChecker))
	
	// Metrics endpoint
	router.GET("/metrics", metrics.HandlerFunc())
	
	// API routes
	api := router.Group("/api/v1")
	configService.RegisterRoutes(api)
	
	// Create HTTP server
	server := &http.Server{
		Addr:    fmt.Sprintf(":%d", cfg.Port),
		Handler: router,
	}
	
	// Start server in goroutine
	go func() {
		logger.Info("Starting config service", "port", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Error("Failed to start server", "error", err)
			os.Exit(1)
		}
	}()
	
	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	
	logger.Info("Shutting down config service...")
	
	// Graceful shutdown with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	
	if err := server.Shutdown(ctx); err != nil {
		logger.Error("Server forced to shutdown", "error", err)
	}
	
	logger.Info("Config service stopped")
}
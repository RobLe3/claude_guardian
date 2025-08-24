package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/iff-guardian/detection-engine/internal/config"
	"github.com/iff-guardian/detection-engine/internal/handlers"
	"github.com/iff-guardian/detection-engine/internal/middleware"
	"github.com/iff-guardian/detection-engine/internal/services"
)

// Detection Engine Service - Real-time threat detection and analysis
// Uses ML models and behavioral analysis to identify security threats
func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize threat detection services
	vectorService := services.NewVectorService(cfg.VectorDB)
	graphService := services.NewGraphService(cfg.GraphDB)
	mlService := services.NewMLService(cfg.ML)
	threatDetector := services.NewThreatDetector(vectorService, graphService, mlService)

	// Setup Gin router
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}
	
	router := gin.New()
	
	// Global middleware
	router.Use(gin.Recovery())
	router.Use(middleware.Logger())
	router.Use(middleware.CORS())
	router.Use(middleware.SecurityHeaders())

	// Health check endpoints
	router.GET("/health", handlers.HealthCheck)
	router.GET("/health/ready", func(c *gin.Context) {
		// Check if all dependencies are ready
		status := map[string]string{
			"status": "ready",
			"vector_db": "connected",
			"graph_db": "connected",
			"ml_models": "loaded",
		}
		c.JSON(http.StatusOK, status)
	})

	// API versioning
	v1 := router.Group("/api/v1")
	{
		// Threat detection endpoints
		detection := v1.Group("/detection")
		{
			detection.POST("/analyze", handlers.AnalyzeThreat(threatDetector))
			detection.POST("/batch-analyze", handlers.BatchAnalyze(threatDetector))
			detection.GET("/patterns", handlers.GetThreatPatterns(threatDetector))
			detection.POST("/learn", handlers.LearnFromFeedback(threatDetector))
		}

		// Real-time threat monitoring
		monitoring := v1.Group("/monitoring")
		{
			monitoring.GET("/threats/live", handlers.LiveThreats(threatDetector))
			monitoring.GET("/metrics", handlers.DetectionMetrics(threatDetector))
			monitoring.POST("/alerts", handlers.CreateAlert(threatDetector))
		}

		// Model management
		models := v1.Group("/models")
		{
			models.GET("/", handlers.ListModels(mlService))
			models.POST("/retrain", handlers.RetrainModel(mlService))
			models.GET("/:id/performance", handlers.ModelPerformance(mlService))
		}
	}

	// Metrics endpoint for Prometheus
	router.GET("/metrics", handlers.PrometheusMetrics)

	// Create HTTP server
	server := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.Port),
		Handler:      router,
		ReadTimeout:  cfg.Server.ReadTimeout,
		WriteTimeout: cfg.Server.WriteTimeout,
		IdleTimeout:  cfg.Server.IdleTimeout,
	}

	// Start background threat processing
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go threatDetector.StartBackgroundProcessing(ctx)

	// Start server in goroutine
	go func() {
		log.Printf("Starting Detection Engine Service on port %d", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down Detection Engine Service...")

	// Cancel background processing
	cancel()

	// Graceful shutdown with timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("Detection Engine Service forced to shutdown: %v", err)
	}

	log.Println("Detection Engine Service shutdown completed")
}

// ThreatAnalysisRequest represents a request for threat analysis
type ThreatAnalysisRequest struct {
	Action     string                 `json:"action" binding:"required"`
	Context    map[string]interface{} `json:"context"`
	UserID     string                 `json:"user_id" binding:"required"`
	Timestamp  time.Time              `json:"timestamp"`
}

// ThreatAnalysisResponse represents the result of threat analysis
type ThreatAnalysisResponse struct {
	ThreatLevel   string                 `json:"threat_level"`
	RiskScore     float64                `json:"risk_score"`
	Confidence    float64                `json:"confidence"`
	Reasons       []string               `json:"reasons"`
	Recommendations []string             `json:"recommendations"`
	SimilarThreats []SimilarThreat       `json:"similar_threats"`
	Action        string                 `json:"action"` // allow, block, warn
	Metadata      map[string]interface{} `json:"metadata"`
}

// SimilarThreat represents a similar threat pattern found
type SimilarThreat struct {
	ID         string  `json:"id"`
	Similarity float64 `json:"similarity"`
	Pattern    string  `json:"pattern"`
	Outcome    string  `json:"outcome"`
}
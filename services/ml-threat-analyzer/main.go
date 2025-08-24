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
	"github.com/iff-guardian/ml-threat-analyzer/internal/config"
	"github.com/iff-guardian/ml-threat-analyzer/internal/handlers"
	"github.com/iff-guardian/ml-threat-analyzer/internal/ml"
	"github.com/iff-guardian/ml-threat-analyzer/internal/models"
	"github.com/iff-guardian/ml-threat-analyzer/internal/services"
)

// ML Threat Analyzer Service - Advanced ML-based threat detection
// Uses multiple ML models for threat classification, behavioral analysis, and attack correlation
func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize ML model manager
	modelManager := ml.NewModelManager(cfg.ML)
	
	// Load pre-trained models
	if err := modelManager.LoadModels(); err != nil {
		log.Fatalf("Failed to load ML models: %v", err)
	}

	// Initialize services
	vectorService := services.NewVectorService(cfg.VectorDB)
	featureExtractor := services.NewFeatureExtractor(cfg.Features)
	behaviorAnalyzer := services.NewBehaviorAnalyzer(cfg.Behavior)
	threatClassifier := services.NewThreatClassifier(modelManager, vectorService)
	attackCorrelator := services.NewAttackCorrelator(cfg.Graph, behaviorAnalyzer)

	// Setup Gin router
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}
	
	router := gin.New()
	
	// Global middleware
	router.Use(gin.Recovery())
	router.Use(handlers.Logger())
	router.Use(handlers.CORS())
	router.Use(handlers.SecurityHeaders())
	router.Use(handlers.RateLimiter(cfg.RateLimit))

	// Health check endpoints
	router.GET("/health", handlers.HealthCheck)
	router.GET("/health/ready", func(c *gin.Context) {
		status := map[string]interface{}{
			"status": "ready",
			"models_loaded": modelManager.GetLoadedModels(),
			"vector_db": vectorService.HealthCheck(),
			"feature_extractor": featureExtractor.Status(),
			"behavior_analyzer": behaviorAnalyzer.Status(),
		}
		c.JSON(http.StatusOK, status)
	})

	// API versioning
	v1 := router.Group("/api/v1")
	{
		// Threat analysis endpoints
		analysis := v1.Group("/analysis")
		{
			analysis.POST("/classify", handlers.ClassifyThreat(threatClassifier))
			analysis.POST("/behavioral", handlers.AnalyzeBehavior(behaviorAnalyzer))
			analysis.POST("/correlate", handlers.CorrelateAttacks(attackCorrelator))
			analysis.POST("/batch", handlers.BatchAnalyze(threatClassifier))
		}

		// Feature extraction endpoints
		features := v1.Group("/features")
		{
			features.POST("/extract", handlers.ExtractFeatures(featureExtractor))
			features.GET("/schema", handlers.GetFeatureSchema(featureExtractor))
		}

		// Model management endpoints
		models := v1.Group("/models")
		{
			models.GET("/", handlers.ListModels(modelManager))
			models.GET("/:name", handlers.GetModel(modelManager))
			models.POST("/:name/predict", handlers.PredictWithModel(modelManager))
			models.POST("/:name/retrain", handlers.RetrainModel(modelManager))
			models.GET("/:name/metrics", handlers.GetModelMetrics(modelManager))
		}

		// Training and learning endpoints
		training := v1.Group("/training")
		{
			training.POST("/feedback", handlers.ProcessFeedback(threatClassifier))
			training.POST("/update", handlers.UpdateModels(modelManager))
			training.GET("/status", handlers.GetTrainingStatus(modelManager))
		}

		// Vector similarity endpoints
		similarity := v1.Group("/similarity")
		{
			similarity.POST("/search", handlers.SimilaritySearch(vectorService))
			similarity.POST("/embed", handlers.GenerateEmbeddings(vectorService))
			similarity.GET("/clusters", handlers.GetThreatClusters(vectorService))
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

	// Start background services
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go modelManager.StartModelMonitoring(ctx)
	go threatClassifier.StartContinuousLearning(ctx)
	go behaviorAnalyzer.StartBehaviorTracking(ctx)
	go attackCorrelator.StartAttackCorrelation(ctx)

	// Start server in goroutine
	go func() {
		log.Printf("Starting ML Threat Analyzer Service on port %d", cfg.Port)
		log.Printf("Loaded models: %v", modelManager.GetLoadedModels())
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down ML Threat Analyzer Service...")

	// Cancel background processing
	cancel()

	// Save model states before shutdown
	if err := modelManager.SaveModelStates(); err != nil {
		log.Printf("Warning: Failed to save model states: %v", err)
	}

	// Graceful shutdown with timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("ML Threat Analyzer Service forced to shutdown: %v", err)
	}

	log.Println("ML Threat Analyzer Service shutdown completed")
}

// ThreatAnalysisRequest represents a request for ML-based threat analysis
type ThreatAnalysisRequest struct {
	Action      string                 `json:"action" binding:"required"`
	Context     map[string]interface{} `json:"context"`
	UserID      string                 `json:"user_id" binding:"required"`
	ToolName    string                 `json:"tool_name,omitempty"`
	Parameters  map[string]interface{} `json:"parameters,omitempty"`
	Timestamp   time.Time              `json:"timestamp"`
	SessionData map[string]interface{} `json:"session_data,omitempty"`
}

// ThreatClassificationResult represents the result of ML threat classification
type ThreatClassificationResult struct {
	ThreatType        string                 `json:"threat_type"`
	ThreatCategory    string                 `json:"threat_category"`
	RiskScore         float64                `json:"risk_score"`
	Confidence        float64                `json:"confidence"`
	ModelUsed         string                 `json:"model_used"`
	Features          []string               `json:"features"`
	SimilarThreats    []SimilarThreat        `json:"similar_threats"`
	Recommendations   []string               `json:"recommendations"`
	ActionRequired    string                 `json:"action_required"`
	Reasoning         []string               `json:"reasoning"`
	Metadata          map[string]interface{} `json:"metadata"`
	ProcessingTimeMs  int64                  `json:"processing_time_ms"`
}

// BehavioralAnalysisResult represents behavioral pattern analysis
type BehavioralAnalysisResult struct {
	UserID            string                 `json:"user_id"`
	BehaviorProfile   map[string]interface{} `json:"behavior_profile"`
	AnomalyScore      float64                `json:"anomaly_score"`
	DeviationTypes    []string               `json:"deviation_types"`
	HistoricalPattern map[string]interface{} `json:"historical_pattern"`
	RiskFactors       []string               `json:"risk_factors"`
	Timeline          []BehaviorEvent        `json:"timeline"`
	Verdict           string                 `json:"verdict"`
}

// AttackCorrelationResult represents multi-stage attack correlation
type AttackCorrelationResult struct {
	AttackChainID     string        `json:"attack_chain_id"`
	Stages            []AttackStage `json:"stages"`
	Severity          string        `json:"severity"`
	Confidence        float64       `json:"confidence"`
	MITRE_Tactics     []string      `json:"mitre_tactics"`
	MITRE_Techniques  []string      `json:"mitre_techniques"`
	Timeline          []time.Time   `json:"timeline"`
	Indicators        []string      `json:"indicators"`
	Recommendations   []string      `json:"recommendations"`
}

// SimilarThreat represents a similar threat found through vector similarity
type SimilarThreat struct {
	ID            string                 `json:"id"`
	Similarity    float64                `json:"similarity"`
	ThreatType    string                 `json:"threat_type"`
	Description   string                 `json:"description"`
	Outcome       string                 `json:"outcome"`
	Metadata      map[string]interface{} `json:"metadata"`
	FirstSeen     time.Time              `json:"first_seen"`
}

// BehaviorEvent represents a behavioral event in the timeline
type BehaviorEvent struct {
	Timestamp   time.Time              `json:"timestamp"`
	EventType   string                 `json:"event_type"`
	Description string                 `json:"description"`
	RiskScore   float64                `json:"risk_score"`
	Context     map[string]interface{} `json:"context"`
}

// AttackStage represents a stage in a multi-stage attack
type AttackStage struct {
	StageNumber   int                    `json:"stage_number"`
	StageName     string                 `json:"stage_name"`
	Description   string                 `json:"description"`
	Timestamp     time.Time              `json:"timestamp"`
	Indicators    []string               `json:"indicators"`
	Confidence    float64                `json:"confidence"`
	Context       map[string]interface{} `json:"context"`
}
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
	
	"github.com/iff-guardian/ai-threat-hunter/internal/config"
	"github.com/iff-guardian/ai-threat-hunter/internal/handlers"
	"github.com/iff-guardian/ai-threat-hunter/internal/hunting"
	"github.com/iff-guardian/ai-threat-hunter/internal/intelligence"
	"github.com/iff-guardian/ai-threat-hunter/internal/middleware"
	"github.com/iff-guardian/ai-threat-hunter/internal/ml"
	"github.com/iff-guardian/ai-threat-hunter/internal/services"
)

// AI Threat Hunter Service - Autonomous threat hunting using advanced ML and graph neural networks
// Provides unsupervised anomaly detection, behavioral pattern analysis, and adaptive hunting algorithms
func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize ML services
	neuralNetworkService := ml.NewNeuralNetworkService(cfg.NeuralNetwork)
	anomalyDetector := ml.NewAnomalyDetector(cfg.AnomalyDetection)
	patternAnalyzer := ml.NewPatternAnalyzer(cfg.PatternAnalysis)
	threatIntelligence := intelligence.NewThreatIntelligenceService(cfg.ThreatIntel)

	// Initialize hunting engines
	huntingEngine := hunting.NewHuntingEngine(neuralNetworkService, anomalyDetector, patternAnalyzer)
	adaptiveHunter := hunting.NewAdaptiveHunter(cfg.AdaptiveHunting)
	behaviorAnalyzer := hunting.NewBehaviorAnalyzer(cfg.BehaviorAnalysis)

	// Initialize external service connections
	vectorDBService := services.NewVectorDBService(cfg.VectorDB)
	graphService := services.NewGraphService(cfg.GraphDB)
	timeseriesService := services.NewTimeSeriesService(cfg.TimeSeries)
	alertService := services.NewAlertService(cfg.Alerts)

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
	router.Use(middleware.RateLimiter(cfg.RateLimit))

	// Health check endpoints
	router.GET("/health", handlers.HealthCheck)
	router.GET("/health/ready", func(c *gin.Context) {
		status := map[string]interface{}{
			"status": "ready",
			"services": map[string]string{
				"neural_network":      neuralNetworkService.Status(),
				"anomaly_detector":    anomalyDetector.Status(),
				"pattern_analyzer":    patternAnalyzer.Status(),
				"hunting_engine":      huntingEngine.Status(),
				"adaptive_hunter":     adaptiveHunter.Status(),
				"behavior_analyzer":   behaviorAnalyzer.Status(),
				"threat_intelligence": threatIntelligence.Status(),
			},
			"ml_models": map[string]interface{}{
				"loaded_models":    neuralNetworkService.GetLoadedModels(),
				"model_accuracy":   neuralNetworkService.GetModelAccuracy(),
				"last_training":    neuralNetworkService.GetLastTrainingTime(),
				"active_hunts":     huntingEngine.GetActiveHuntCount(),
				"detection_rate":   huntingEngine.GetDetectionRate(),
			},
		}
		c.JSON(http.StatusOK, status)
	})

	// API versioning
	v1 := router.Group("/api/v1")
	v1.Use(middleware.RequireAuth(cfg.Auth))
	{
		// Autonomous threat hunting
		hunting := v1.Group("/hunting")
		{
			hunting.POST("/start", handlers.StartHuntingCampaign(huntingEngine))
			hunting.GET("/campaigns", handlers.GetHuntingCampaigns(huntingEngine))
			hunting.GET("/campaigns/:id", handlers.GetCampaignDetails(huntingEngine))
			hunting.POST("/campaigns/:id/stop", handlers.StopHuntingCampaign(huntingEngine))
			hunting.POST("/campaigns/:id/extend", handlers.ExtendHuntingCampaign(huntingEngine))
			hunting.GET("/results", handlers.GetHuntingResults(huntingEngine))
			hunting.POST("/adaptive", handlers.StartAdaptiveHunting(adaptiveHunter))
			hunting.GET("/adaptive/status", handlers.GetAdaptiveHuntingStatus(adaptiveHunter))
		}

		// AI-powered threat analysis
		analysis := v1.Group("/analysis")
		{
			analysis.POST("/anomalies", handlers.DetectAnomalies(anomalyDetector))
			analysis.POST("/patterns", handlers.AnalyzePatterns(patternAnalyzer))
			analysis.POST("/behavior", handlers.AnalyzeBehavior(behaviorAnalyzer))
			analysis.GET("/trends", handlers.GetThreatTrends(patternAnalyzer))
			analysis.POST("/predictions", handlers.GenerateThreatPredictions(neuralNetworkService))
			analysis.GET("/landscape", handlers.GetThreatLandscape(threatIntelligence))
		}

		// Neural network and ML model management
		ml := v1.Group("/ml")
		{
			ml.GET("/models", handlers.GetMLModels(neuralNetworkService))
			ml.POST("/models/train", handlers.TrainMLModel(neuralNetworkService))
			ml.POST("/models/:id/predict", handlers.PredictWithModel(neuralNetworkService))
			ml.GET("/models/:id/performance", handlers.GetModelPerformance(neuralNetworkService))
			ml.POST("/models/:id/retrain", handlers.RetrainModel(neuralNetworkService))
			ml.DELETE("/models/:id", handlers.DeleteModel(neuralNetworkService))
			ml.GET("/metrics", handlers.GetMLMetrics(neuralNetworkService))
		}

		// Threat intelligence integration
		intelligence := v1.Group("/intelligence")
		{
			intelligence.GET("/feeds", handlers.GetThreatFeeds(threatIntelligence))
			intelligence.POST("/feeds", handlers.CreateThreatFeed(threatIntelligence))
			intelligence.PUT("/feeds/:id", handlers.UpdateThreatFeed(threatIntelligence))
			intelligence.DELETE("/feeds/:id", handlers.DeleteThreatFeed(threatIntelligence))
			intelligence.POST("/enrich", handlers.EnrichThreatData(threatIntelligence))
			intelligence.GET("/indicators", handlers.GetThreatIndicators(threatIntelligence))
			intelligence.POST("/correlate", handlers.CorrelateThreatIntelligence(threatIntelligence))
		}

		// Advanced search and discovery
		discovery := v1.Group("/discovery")
		{
			discovery.POST("/search", handlers.SearchThreats(huntingEngine, vectorDBService))
			discovery.POST("/graph-query", handlers.ExecuteGraphQuery(graphService))
			discovery.GET("/entities", handlers.DiscoverEntities(huntingEngine))
			discovery.POST("/timeline", handlers.BuildThreatTimeline(timeseriesService))
			discovery.GET("/relationships", handlers.DiscoverRelationships(graphService))
		}

		// Automated response and actions
		response := v1.Group("/response")
		{
			response.POST("/alerts", handlers.CreateThreatAlert(alertService))
			response.POST("/block", handlers.BlockThreatIndicator(huntingEngine))
			response.POST("/isolate", handlers.IsolateAsset(huntingEngine))
			response.POST("/quarantine", handlers.QuarantineEntity(huntingEngine))
			response.GET("/actions", handlers.GetResponseActions(huntingEngine))
		}

		// Hunting rule management
		rules := v1.Group("/rules")
		{
			rules.GET("/", handlers.GetHuntingRules(huntingEngine))
			rules.POST("/", handlers.CreateHuntingRule(huntingEngine))
			rules.GET("/:id", handlers.GetHuntingRule(huntingEngine))
			rules.PUT("/:id", handlers.UpdateHuntingRule(huntingEngine))
			rules.DELETE("/:id", handlers.DeleteHuntingRule(huntingEngine))
			rules.POST("/:id/test", handlers.TestHuntingRule(huntingEngine))
			rules.POST("/:id/deploy", handlers.DeployHuntingRule(huntingEngine))
		}
	}

	// Real-time streaming endpoints
	streaming := router.Group("/stream")
	streaming.Use(middleware.RequireAuth(cfg.Auth))
	{
		streaming.GET("/threats", handlers.StreamThreats(huntingEngine))
		streaming.GET("/anomalies", handlers.StreamAnomalies(anomalyDetector))
		streaming.GET("/alerts", handlers.StreamAlerts(alertService))
		streaming.GET("/intelligence", handlers.StreamThreatIntelligence(threatIntelligence))
	}

	// Admin endpoints for system management
	admin := v1.Group("/admin")
	admin.Use(middleware.RequireRole("admin"))
	{
		admin.GET("/stats", handlers.GetSystemStats(huntingEngine, neuralNetworkService, anomalyDetector))
		admin.POST("/maintenance", handlers.EnableMaintenanceMode(huntingEngine))
		admin.DELETE("/maintenance", handlers.DisableMaintenanceMode(huntingEngine))
		admin.POST("/models/deploy", handlers.DeployNewModel(neuralNetworkService))
		admin.POST("/retrain-all", handlers.RetrainAllModels(neuralNetworkService))
		admin.GET("/performance", handlers.GetPerformanceMetrics(huntingEngine))
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

	go huntingEngine.StartContinuousHunting(ctx)
	go adaptiveHunter.StartAdaptiveLearning(ctx)
	go anomalyDetector.StartRealTimeDetection(ctx)
	go patternAnalyzer.StartPatternAnalysis(ctx)
	go threatIntelligence.StartIntelligenceProcessing(ctx)
	go neuralNetworkService.StartModelManagement(ctx)

	// Start server in goroutine
	go func() {
		log.Printf("Starting AI Threat Hunter Service on port %d", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down AI Threat Hunter Service...")

	// Cancel background processing
	cancel()

	// Graceful shutdown with timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("AI Threat Hunter Service forced to shutdown: %v", err)
	}

	log.Println("AI Threat Hunter Service shutdown completed")
}

// HuntingCampaign represents an autonomous threat hunting campaign
type HuntingCampaign struct {
	ID              string                 `json:"id"`
	Name            string                 `json:"name"`
	Description     string                 `json:"description"`
	Status          CampaignStatus         `json:"status"`
	Priority        string                 `json:"priority"`
	StartTime       time.Time              `json:"start_time"`
	EndTime         *time.Time             `json:"end_time,omitempty"`
	Duration        time.Duration          `json:"duration"`
	TargetAssets    []string               `json:"target_assets"`
	HuntingRules    []string               `json:"hunting_rules"`
	MLModels        []string               `json:"ml_models"`
	Progress        float64                `json:"progress"`
	ThreatsFound    int                    `json:"threats_found"`
	AnomaliesFound  int                    `json:"anomalies_found"`
	Confidence      float64                `json:"confidence"`
	AutoAdaptive    bool                   `json:"auto_adaptive"`
	CreatedBy       string                 `json:"created_by"`
	Metadata        map[string]interface{} `json:"metadata"`
	Results         []HuntingResult        `json:"results"`
}

// CampaignStatus represents the status of a hunting campaign
type CampaignStatus string

const (
	CampaignStatusPlanning   CampaignStatus = "planning"
	CampaignStatusActive     CampaignStatus = "active"
	CampaignStatusPaused     CampaignStatus = "paused"
	CampaignStatusCompleted  CampaignStatus = "completed"
	CampaignStatusFailed     CampaignStatus = "failed"
	CampaignStatusTerminated CampaignStatus = "terminated"
)

// HuntingResult represents a result from autonomous threat hunting
type HuntingResult struct {
	ID               string                 `json:"id"`
	CampaignID       string                 `json:"campaign_id"`
	ThreatType       string                 `json:"threat_type"`
	ThreatName       string                 `json:"threat_name"`
	Severity         string                 `json:"severity"`
	Confidence       float64                `json:"confidence"`
	RiskScore        float64                `json:"risk_score"`
	Description      string                 `json:"description"`
	AffectedAssets   []string               `json:"affected_assets"`
	Indicators       []ThreatIndicator      `json:"indicators"`
	AttackVector     string                 `json:"attack_vector"`
	MITRETechniques  []string               `json:"mitre_techniques"`
	Timeline         []TimelineEvent        `json:"timeline"`
	Evidence         []Evidence             `json:"evidence"`
	DetectionMethod  string                 `json:"detection_method"`
	DetectedAt       time.Time              `json:"detected_at"`
	FirstSeen        time.Time              `json:"first_seen"`
	LastSeen         time.Time              `json:"last_seen"`
	Status           string                 `json:"status"`
	AssignedAnalyst  *string                `json:"assigned_analyst,omitempty"`
	Metadata         map[string]interface{} `json:"metadata"`
	ActionsTaken     []ResponseAction       `json:"actions_taken"`
}

// ThreatIndicator represents an indicator of compromise discovered during hunting
type ThreatIndicator struct {
	Type         string                 `json:"type"`
	Value        string                 `json:"value"`
	Description  string                 `json:"description"`
	Confidence   float64                `json:"confidence"`
	Source       string                 `json:"source"`
	Tags         []string               `json:"tags"`
	FirstSeen    time.Time              `json:"first_seen"`
	LastSeen     time.Time              `json:"last_seen"`
	Context      map[string]interface{} `json:"context"`
	ThreatTypes  []string               `json:"threat_types"`
}

// TimelineEvent represents an event in the threat timeline
type TimelineEvent struct {
	Timestamp   time.Time              `json:"timestamp"`
	EventType   string                 `json:"event_type"`
	Description string                 `json:"description"`
	Source      string                 `json:"source"`
	Severity    string                 `json:"severity"`
	AssetID     string                 `json:"asset_id"`
	UserID      string                 `json:"user_id"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// Evidence represents digital evidence collected during hunting
type Evidence struct {
	ID           string                 `json:"id"`
	Type         string                 `json:"type"`
	Source       string                 `json:"source"`
	Description  string                 `json:"description"`
	Hash         string                 `json:"hash"`
	Size         int64                  `json:"size"`
	CollectedAt  time.Time              `json:"collected_at"`
	Chain        []string               `json:"chain_of_custody"`
	Metadata     map[string]interface{} `json:"metadata"`
	Location     string                 `json:"location"`
	Integrity    bool                   `json:"integrity_verified"`
}

// ResponseAction represents an automated response action
type ResponseAction struct {
	ID           string                 `json:"id"`
	Type         string                 `json:"type"`
	Description  string                 `json:"description"`
	Status       string                 `json:"status"`
	ExecutedAt   time.Time              `json:"executed_at"`
	ExecutedBy   string                 `json:"executed_by"`
	Parameters   map[string]interface{} `json:"parameters"`
	Result       string                 `json:"result"`
	Error        *string                `json:"error,omitempty"`
}

// MLModel represents a machine learning model used for threat hunting
type MLModel struct {
	ID              string                 `json:"id"`
	Name            string                 `json:"name"`
	Type            string                 `json:"type"`
	Version         string                 `json:"version"`
	Description     string                 `json:"description"`
	Algorithm       string                 `json:"algorithm"`
	Framework       string                 `json:"framework"`
	Status          string                 `json:"status"`
	Accuracy        float64                `json:"accuracy"`
	Precision       float64                `json:"precision"`
	Recall          float64                `json:"recall"`
	F1Score         float64                `json:"f1_score"`
	TrainingData    string                 `json:"training_data"`
	TrainedAt       time.Time              `json:"trained_at"`
	LastUsed        *time.Time             `json:"last_used,omitempty"`
	PredictionCount int64                  `json:"prediction_count"`
	ModelPath       string                 `json:"model_path"`
	Parameters      map[string]interface{} `json:"parameters"`
	Metadata        map[string]interface{} `json:"metadata"`
}

// HuntingRule represents a rule for autonomous threat hunting
type HuntingRule struct {
	ID              string                 `json:"id"`
	Name            string                 `json:"name"`
	Description     string                 `json:"description"`
	Category        string                 `json:"category"`
	Severity        string                 `json:"severity"`
	Enabled         bool                   `json:"enabled"`
	Logic           map[string]interface{} `json:"logic"`
	Conditions      []RuleCondition        `json:"conditions"`
	Actions         []RuleAction           `json:"actions"`
	MLModels        []string               `json:"ml_models"`
	TargetAssets    []string               `json:"target_assets"`
	Schedule        *RuleSchedule          `json:"schedule,omitempty"`
	Confidence      float64                `json:"confidence_threshold"`
	FalsePositives  int                    `json:"false_positives"`
	TruePositives   int                    `json:"true_positives"`
	LastTriggered   *time.Time             `json:"last_triggered,omitempty"`
	CreatedAt       time.Time              `json:"created_at"`
	UpdatedAt       time.Time              `json:"updated_at"`
	CreatedBy       string                 `json:"created_by"`
	Version         int                    `json:"version"`
	Tags            []string               `json:"tags"`
}

// RuleCondition represents a condition in a hunting rule
type RuleCondition struct {
	Field          string      `json:"field"`
	Operator       string      `json:"operator"`
	Value          interface{} `json:"value"`
	LogicalOperator string     `json:"logical_operator,omitempty"`
	Weight         float64     `json:"weight"`
}

// RuleAction represents an action to take when a hunting rule matches
type RuleAction struct {
	Type        string                 `json:"type"`
	Parameters  map[string]interface{} `json:"parameters"`
	Conditions  []string               `json:"conditions,omitempty"`
	Delay       *time.Duration         `json:"delay,omitempty"`
}

// RuleSchedule represents when a hunting rule should be active
type RuleSchedule struct {
	StartTime    *time.Time `json:"start_time,omitempty"`
	EndTime      *time.Time `json:"end_time,omitempty"`
	DaysOfWeek   []int      `json:"days_of_week,omitempty"`
	HoursOfDay   []int      `json:"hours_of_day,omitempty"`
	Timezone     string     `json:"timezone,omitempty"`
	Recurring    bool       `json:"recurring"`
}

// AnomalyDetection represents an anomaly detected by AI analysis
type AnomalyDetection struct {
	ID               string                 `json:"id"`
	Type             string                 `json:"type"`
	Description      string                 `json:"description"`
	Severity         string                 `json:"severity"`
	AnomalyScore     float64                `json:"anomaly_score"`
	Confidence       float64                `json:"confidence"`
	Baseline         map[string]interface{} `json:"baseline"`
	ActualValue      map[string]interface{} `json:"actual_value"`
	Deviation        float64                `json:"deviation"`
	DetectionMethod  string                 `json:"detection_method"`
	MLModel          string                 `json:"ml_model"`
	AffectedAssets   []string               `json:"affected_assets"`
	TimeWindow       string                 `json:"time_window"`
	DetectedAt       time.Time              `json:"detected_at"`
	Context          map[string]interface{} `json:"context"`
	RelatedAnomalies []string               `json:"related_anomalies"`
	Status           string                 `json:"status"`
	InvestigationID  *string                `json:"investigation_id,omitempty"`
}

// ThreatLandscape represents the current threat landscape analysis
type ThreatLandscape struct {
	GeneratedAt     time.Time              `json:"generated_at"`
	TimeRange       string                 `json:"time_range"`
	TotalThreats    int                    `json:"total_threats"`
	ActiveThreats   int                    `json:"active_threats"`
	CriticalThreats int                    `json:"critical_threats"`
	ThreatsByType   map[string]int         `json:"threats_by_type"`
	ThreatsBySector map[string]int         `json:"threats_by_sector"`
	EmergingThreats []EmergingThreat       `json:"emerging_threats"`
	ThreatActors    []ThreatActor          `json:"threat_actors"`
	AttackVectors   map[string]int         `json:"attack_vectors"`
	Predictions     []ThreatPrediction     `json:"predictions"`
	Recommendations []string               `json:"recommendations"`
	Metadata        map[string]interface{} `json:"metadata"`
}

// EmergingThreat represents a newly identified threat
type EmergingThreat struct {
	ID           string    `json:"id"`
	Name         string    `json:"name"`
	Description  string    `json:"description"`
	Severity     string    `json:"severity"`
	FirstSeen    time.Time `json:"first_seen"`
	Frequency    int       `json:"frequency"`
	Confidence   float64   `json:"confidence"`
	Indicators   []string  `json:"indicators"`
	AttackVector string    `json:"attack_vector"`
	Mitigation   []string  `json:"mitigation"`
}

// ThreatActor represents a threat actor profile
type ThreatActor struct {
	ID           string   `json:"id"`
	Name         string   `json:"name"`
	Aliases      []string `json:"aliases"`
	Type         string   `json:"type"`
	Motivation   string   `json:"motivation"`
	Capabilities []string `json:"capabilities"`
	Targets      []string `json:"targets"`
	TTPs         []string `json:"ttps"`
	LastActive   time.Time `json:"last_active"`
	Confidence   float64  `json:"confidence"`
}

// ThreatPrediction represents a prediction about future threats
type ThreatPrediction struct {
	ID           string                 `json:"id"`
	ThreatType   string                 `json:"threat_type"`
	Prediction   string                 `json:"prediction"`
	Probability  float64                `json:"probability"`
	TimeFrame    string                 `json:"time_frame"`
	Confidence   float64                `json:"confidence"`
	Factors      []string               `json:"factors"`
	Mitigation   []string               `json:"mitigation"`
	GeneratedAt  time.Time              `json:"generated_at"`
	Model        string                 `json:"model"`
	Metadata     map[string]interface{} `json:"metadata"`
}
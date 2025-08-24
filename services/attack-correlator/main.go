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
	"github.com/neo4j/neo4j-go-driver/v5/neo4j"
	
	"github.com/iff-guardian/attack-correlator/internal/config"
	"github.com/iff-guardian/attack-correlator/internal/correlation"
	"github.com/iff-guardian/attack-correlator/internal/handlers"
	"github.com/iff-guardian/attack-correlator/internal/middleware"
	"github.com/iff-guardian/attack-correlator/internal/mitre"
	"github.com/iff-guardian/attack-correlator/internal/services"
)

// Attack Correlator Service - Multi-stage attack detection and correlation
// Uses graph analysis and MITRE ATT&CK framework to identify attack chains
func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize Neo4j driver
	driver, err := neo4j.NewDriverWithContext(cfg.Neo4j.URI, neo4j.BasicAuth(cfg.Neo4j.Username, cfg.Neo4j.Password))
	if err != nil {
		log.Fatalf("Failed to create Neo4j driver: %v", err)
	}
	defer driver.Close(context.Background())

	// Initialize services
	graphService := services.NewGraphService(driver)
	mitreService := mitre.NewMITREService(cfg.MITRE)
	correlationEngine := correlation.NewCorrelationEngine(graphService, mitreService, cfg.Correlation)
	alertService := services.NewAlertService(cfg.Alerts)
	timelineService := services.NewTimelineService(graphService)

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
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		
		// Test Neo4j connection
		session := driver.NewSession(ctx, neo4j.SessionConfig{})
		defer session.Close(ctx)
		
		_, err := session.Run(ctx, "RETURN 1", nil)
		status := map[string]interface{}{
			"status":            "ready",
			"neo4j_connection": map[string]string{
				"status": func() string {
					if err != nil {
						return "error"
					}
					return "connected"
				}(),
			},
			"correlation_engine": correlationEngine.Status(),
			"mitre_service":      mitreService.Status(),
			"alert_service":      alertService.Status(),
		}
		c.JSON(http.StatusOK, status)
	})

	// API versioning
	v1 := router.Group("/api/v1")
	v1.Use(middleware.RequireAuth(cfg.Auth))
	{
		// Attack correlation endpoints
		correlation := v1.Group("/correlation")
		{
			correlation.POST("/analyze", handlers.AnalyzeAttackChain(correlationEngine))
			correlation.POST("/events", handlers.ProcessSecurityEvents(correlationEngine))
			correlation.GET("/chains", handlers.GetAttackChains(correlationEngine))
			correlation.GET("/chains/:id", handlers.GetAttackChainDetails(correlationEngine))
			correlation.POST("/chains/:id/resolve", handlers.ResolveAttackChain(correlationEngine))
		}

		// MITRE ATT&CK integration
		mitre := v1.Group("/mitre")
		{
			mitre.GET("/tactics", handlers.GetMITRETactics(mitreService))
			mitre.GET("/techniques", handlers.GetMITRETechniques(mitreService))
			mitre.GET("/techniques/:id", handlers.GetTechniqueDetails(mitreService))
			mitre.POST("/map", handlers.MapToMITRE(mitreService))
			mitre.GET("/coverage", handlers.GetMITRECoverage(mitreService))
		}

		// Graph analysis endpoints
		graph := v1.Group("/graph")
		{
			graph.GET("/nodes", handlers.GetGraphNodes(graphService))
			graph.GET("/relationships", handlers.GetRelationships(graphService))
			graph.POST("/query", handlers.ExecuteGraphQuery(graphService))
			graph.GET("/paths", handlers.FindAttackPaths(graphService))
			graph.GET("/centrality", handlers.GetCentralityMetrics(graphService))
		}

		// Timeline analysis
		timeline := v1.Group("/timeline")
		{
			timeline.GET("/events", handlers.GetTimelineEvents(timelineService))
			timeline.POST("/reconstruct", handlers.ReconstructAttack(timelineService))
			timeline.GET("/patterns", handlers.GetTimelinePatterns(timelineService))
		}

		// Alert integration
		alerts := v1.Group("/alerts")
		{
			alerts.POST("/create", handlers.CreateCorrelationAlert(alertService))
			alerts.GET("/correlation", handlers.GetCorrelationAlerts(alertService))
			alerts.POST("/:id/enrich", handlers.EnrichAlert(correlationEngine, mitreService))
		}
	}

	// Admin endpoints for advanced correlation management
	admin := v1.Group("/admin")
	admin.Use(middleware.RequireRole("admin"))
	{
		admin.POST("/rules", handlers.CreateCorrelationRule(correlationEngine))
		admin.GET("/rules", handlers.GetCorrelationRules(correlationEngine))
		admin.PUT("/rules/:id", handlers.UpdateCorrelationRule(correlationEngine))
		admin.DELETE("/rules/:id", handlers.DeleteCorrelationRule(correlationEngine))
		admin.POST("/retrain", handlers.RetrainCorrelationModel(correlationEngine))
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

	// Initialize graph schema
	if err := initializeGraphSchema(driver); err != nil {
		log.Printf("Warning: Failed to initialize graph schema: %v", err)
	}

	// Start background services
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go correlationEngine.StartRealTimeCorrelation(ctx)
	go mitreService.StartTechniqueUpdates(ctx)
	go timelineService.StartTimelineAnalysis(ctx)

	// Start server in goroutine
	go func() {
		log.Printf("Starting Attack Correlator Service on port %d", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down Attack Correlator Service...")

	// Cancel background processing
	cancel()

	// Graceful shutdown with timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("Attack Correlator Service forced to shutdown: %v", err)
	}

	log.Println("Attack Correlator Service shutdown completed")
}

// initializeGraphSchema creates the necessary graph schema for attack correlation
func initializeGraphSchema(driver neo4j.DriverWithContext) error {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	session := driver.NewSession(ctx, neo4j.SessionConfig{})
	defer session.Close(ctx)

	// Create constraints and indexes for better performance
	constraints := []string{
		"CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
		"CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
		"CREATE CONSTRAINT technique_id IF NOT EXISTS FOR (t:Technique) REQUIRE t.mitre_id IS UNIQUE",
		"CREATE CONSTRAINT tactic_id IF NOT EXISTS FOR (tac:Tactic) REQUIRE tac.mitre_id IS UNIQUE",
		"CREATE CONSTRAINT asset_id IF NOT EXISTS FOR (a:Asset) REQUIRE a.id IS UNIQUE",
		"CREATE INDEX event_timestamp IF NOT EXISTS FOR (e:Event) ON (e.timestamp)",
		"CREATE INDEX event_type IF NOT EXISTS FOR (e:Event) ON (e.event_type)",
		"CREATE INDEX user_risk IF NOT EXISTS FOR (u:User) ON (u.risk_score)",
	}

	for _, constraint := range constraints {
		_, err := session.Run(ctx, constraint, nil)
		if err != nil {
			log.Printf("Warning: Failed to create constraint/index: %s - %v", constraint, err)
		}
	}

	return nil
}

// AttackChain represents a correlated multi-stage attack
type AttackChain struct {
	ID              string                 `json:"id"`
	Name            string                 `json:"name"`
	Description     string                 `json:"description"`
	Severity        string                 `json:"severity"`
	Confidence      float64                `json:"confidence"`
	Status          string                 `json:"status"`
	StartTime       time.Time              `json:"start_time"`
	EndTime         *time.Time             `json:"end_time,omitempty"`
	Duration        *time.Duration         `json:"duration,omitempty"`
	Stages          []AttackStage          `json:"stages"`
	MITRETactics    []string               `json:"mitre_tactics"`
	MITRETechniques []string               `json:"mitre_techniques"`
	Indicators      []ThreatIndicator      `json:"indicators"`
	AffectedAssets  []string               `json:"affected_assets"`
	UserIDs         []string               `json:"user_ids"`
	Metadata        map[string]interface{} `json:"metadata"`
	CreatedAt       time.Time              `json:"created_at"`
	UpdatedAt       time.Time              `json:"updated_at"`
}

// AttackStage represents a single stage in an attack chain
type AttackStage struct {
	StageNumber     int                    `json:"stage_number"`
	StageName       string                 `json:"stage_name"`
	Description     string                 `json:"description"`
	MITRETactic     string                 `json:"mitre_tactic"`
	MITRETechniques []string               `json:"mitre_techniques"`
	Events          []SecurityEvent        `json:"events"`
	Timestamp       time.Time              `json:"timestamp"`
	Duration        time.Duration          `json:"duration"`
	Confidence      float64                `json:"confidence"`
	Indicators      []ThreatIndicator      `json:"indicators"`
	Context         map[string]interface{} `json:"context"`
}

// SecurityEvent represents a security event in the attack timeline
type SecurityEvent struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"`
	Source      string                 `json:"source"`
	UserID      string                 `json:"user_id"`
	AssetID     string                 `json:"asset_id"`
	Timestamp   time.Time              `json:"timestamp"`
	Severity    string                 `json:"severity"`
	Description string                 `json:"description"`
	Indicators  []ThreatIndicator      `json:"indicators"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// ThreatIndicator represents an indicator of compromise
type ThreatIndicator struct {
	Type        string                 `json:"type"`
	Value       string                 `json:"value"`
	Confidence  float64                `json:"confidence"`
	Source      string                 `json:"source"`
	Description string                 `json:"description"`
	FirstSeen   time.Time              `json:"first_seen"`
	LastSeen    time.Time              `json:"last_seen"`
	Context     map[string]interface{} `json:"context"`
}

// MITRETechnique represents a MITRE ATT&CK technique
type MITRETechnique struct {
	ID          string   `json:"id"`
	Name        string   `json:"name"`
	Description string   `json:"description"`
	Tactics     []string `json:"tactics"`
	Platforms   []string `json:"platforms"`
	DataSources []string `json:"data_sources"`
	Detection   string   `json:"detection"`
	Mitigation  string   `json:"mitigation"`
	URL         string   `json:"url"`
}

// CorrelationResult represents the result of attack correlation analysis
type CorrelationResult struct {
	AttackChains    []AttackChain          `json:"attack_chains"`
	Confidence      float64                `json:"confidence"`
	ProcessingTime  time.Duration          `json:"processing_time"`
	EventsAnalyzed  int                    `json:"events_analyzed"`
	ChainsDetected  int                    `json:"chains_detected"`
	Recommendations []string               `json:"recommendations"`
	Metadata        map[string]interface{} `json:"metadata"`
}
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
	"github.com/confluentinc/confluent-kafka-go/kafka"
	
	"github.com/iff-guardian/siem-integration-gateway/internal/config"
	"github.com/iff-guardian/siem-integration-gateway/internal/connectors"
	"github.com/iff-guardian/siem-integration-gateway/internal/handlers"
	"github.com/iff-guardian/siem-integration-gateway/internal/middleware"
	"github.com/iff-guardian/siem-integration-gateway/internal/normalization"
	"github.com/iff-guardian/siem-integration-gateway/internal/services"
)

// SIEM Integration Gateway - Universal integration platform for external security tools
// Provides multi-protocol support, real-time data synchronization, and bidirectional threat intelligence sharing
func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize Kafka producer and consumer
	kafkaProducer, err := kafka.NewProducer(&kafka.ConfigMap{
		"bootstrap.servers": cfg.Kafka.Brokers,
		"client.id":         "iff-siem-gateway",
		"acks":              "all",
	})
	if err != nil {
		log.Fatalf("Failed to create Kafka producer: %v", err)
	}
	defer kafkaProducer.Close()

	kafkaConsumer, err := kafka.NewConsumer(&kafka.ConfigMap{
		"bootstrap.servers": cfg.Kafka.Brokers,
		"group.id":          "iff-siem-gateway-group",
		"auto.offset.reset": "latest",
	})
	if err != nil {
		log.Fatalf("Failed to create Kafka consumer: %v", err)
	}
	defer kafkaConsumer.Close()

	// Initialize SIEM connectors
	splunkConnector := connectors.NewSplunkConnector(cfg.Splunk)
	qradarConnector := connectors.NewQRadarConnector(cfg.QRadar)
	sentinelConnector := connectors.NewSentinelConnector(cfg.Sentinel)
	elasticConnector := connectors.NewElasticConnector(cfg.ElasticSIEM)
	arcsightConnector := connectors.NewArcSightConnector(cfg.ArcSight)

	// Initialize services
	dataTransformService := services.NewDataTransformService(cfg.DataTransform)
	routingService := services.NewRoutingService(cfg.Routing)
	enrichmentService := services.NewEnrichmentService(cfg.Enrichment)
	threatIntelService := services.NewThreatIntelligenceService(cfg.ThreatIntel)

	// Initialize normalization engines
	cefNormalizer := normalization.NewCEFNormalizer()
	leefNormalizer := normalization.NewLEEFNormalizer()
	stixNormalizer := normalization.NewSTIXNormalizer()
	jsonNormalizer := normalization.NewJSONNormalizer()

	// Register SIEM connectors
	connectorRegistry := connectors.NewRegistry()
	connectorRegistry.Register("splunk", splunkConnector)
	connectorRegistry.Register("qradar", qradarConnector)
	connectorRegistry.Register("sentinel", sentinelConnector)
	connectorRegistry.Register("elastic", elasticConnector)
	connectorRegistry.Register("arcsight", arcsightConnector)

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
			"connectors": map[string]string{
				"splunk":   splunkConnector.Status(),
				"qradar":   qradarConnector.Status(),
				"sentinel": sentinelConnector.Status(),
				"elastic":  elasticConnector.Status(),
				"arcsight": arcsightConnector.Status(),
			},
			"services": map[string]string{
				"data_transform": dataTransformService.Status(),
				"routing":        routingService.Status(),
				"enrichment":     enrichmentService.Status(),
				"threat_intel":   threatIntelService.Status(),
			},
			"kafka": map[string]interface{}{
				"producer_status": "connected",
				"consumer_status": "connected",
				"topics":          cfg.Kafka.Topics,
			},
			"active_connections": connectorRegistry.GetActiveConnectionCount(),
			"data_throughput":    routingService.GetThroughputMetrics(),
		}
		c.JSON(http.StatusOK, status)
	})

	// API versioning
	v1 := router.Group("/api/v1")
	v1.Use(middleware.RequireAuth(cfg.Auth))
	{
		// SIEM connector management
		connectors := v1.Group("/connectors")
		{
			connectors.GET("/", handlers.GetConnectors(connectorRegistry))
			connectors.POST("/", handlers.CreateConnector(connectorRegistry))
			connectors.GET("/:id", handlers.GetConnector(connectorRegistry))
			connectors.PUT("/:id", handlers.UpdateConnector(connectorRegistry))
			connectors.DELETE("/:id", handlers.DeleteConnector(connectorRegistry))
			connectors.POST("/:id/test", handlers.TestConnector(connectorRegistry))
			connectors.POST("/:id/sync", handlers.SyncConnector(connectorRegistry))
			connectors.GET("/:id/status", handlers.GetConnectorStatus(connectorRegistry))
		}

		// Data ingestion and forwarding
		data := v1.Group("/data")
		{
			data.POST("/ingest", handlers.IngestData(dataTransformService, routingService))
			data.POST("/forward", handlers.ForwardData(routingService, connectorRegistry))
			data.POST("/transform", handlers.TransformData(dataTransformService))
			data.POST("/enrich", handlers.EnrichData(enrichmentService))
			data.GET("/flow", handlers.GetDataFlow(routingService))
			data.GET("/metrics", handlers.GetDataMetrics(routingService))
		}

		// Protocol-specific endpoints
		protocols := v1.Group("/protocols")
		{
			// CEF (Common Event Format)
			protocols.POST("/cef/ingest", handlers.IngestCEF(cefNormalizer, routingService))
			protocols.POST("/cef/convert", handlers.ConvertToCEF(cefNormalizer))
			
			// LEEF (Log Event Extended Format)
			protocols.POST("/leef/ingest", handlers.IngestLEEF(leefNormalizer, routingService))
			protocols.POST("/leef/convert", handlers.ConvertToLEEF(leefNormalizer))
			
			// STIX/TAXII (Structured Threat Information eXpression)
			protocols.POST("/stix/ingest", handlers.IngestSTIX(stixNormalizer, routingService))
			protocols.POST("/stix/convert", handlers.ConvertToSTIX(stixNormalizer))
			protocols.GET("/taxii/collections", handlers.GetTAXIICollections(stixNormalizer))
			protocols.POST("/taxii/poll", handlers.PollTAXIIFeed(stixNormalizer))
			
			// JSON normalization
			protocols.POST("/json/normalize", handlers.NormalizeJSON(jsonNormalizer))
			protocols.POST("/json/schema/validate", handlers.ValidateJSONSchema(jsonNormalizer))
		}

		// Threat intelligence sharing
		threatIntel := v1.Group("/threat-intel")
		{
			threatIntel.GET("/feeds", handlers.GetThreatIntelFeeds(threatIntelService))
			threatIntel.POST("/feeds", handlers.CreateThreatIntelFeed(threatIntelService))
			threatIntel.PUT("/feeds/:id", handlers.UpdateThreatIntelFeed(threatIntelService))
			threatIntel.DELETE("/feeds/:id", handlers.DeleteThreatIntelFeed(threatIntelService))
			threatIntel.POST("/share", handlers.ShareThreatIntelligence(threatIntelService, connectorRegistry))
			threatIntel.POST("/correlate", handlers.CorrelateThreatIntel(threatIntelService))
			threatIntel.GET("/indicators", handlers.GetThreatIndicators(threatIntelService))
			threatIntel.POST("/iocs/submit", handlers.SubmitIOCs(threatIntelService))
		}

		// Bidirectional synchronization
		sync := v1.Group("/sync")
		{
			sync.POST("/start", handlers.StartBidirectionalSync(connectorRegistry))
			sync.POST("/stop", handlers.StopBidirectionalSync(connectorRegistry))
			sync.GET("/status", handlers.GetSyncStatus(connectorRegistry))
			sync.POST("/configure", handlers.ConfigureSync(connectorRegistry))
			sync.GET("/conflicts", handlers.GetSyncConflicts(connectorRegistry))
			sync.POST("/resolve", handlers.ResolveSyncConflicts(connectorRegistry))
		}

		// Data routing and transformation rules
		rules := v1.Group("/rules")
		{
			rules.GET("/routing", handlers.GetRoutingRules(routingService))
			rules.POST("/routing", handlers.CreateRoutingRule(routingService))
			rules.PUT("/routing/:id", handlers.UpdateRoutingRule(routingService))
			rules.DELETE("/routing/:id", handlers.DeleteRoutingRule(routingService))
			rules.GET("/transform", handlers.GetTransformRules(dataTransformService))
			rules.POST("/transform", handlers.CreateTransformRule(dataTransformService))
			rules.PUT("/transform/:id", handlers.UpdateTransformRule(dataTransformService))
			rules.DELETE("/transform/:id", handlers.DeleteTransformRule(dataTransformService))
		}

		// Integration monitoring and analytics
		monitoring := v1.Group("/monitoring")
		{
			monitoring.GET("/connections", handlers.GetConnectionStatus(connectorRegistry))
			monitoring.GET("/throughput", handlers.GetThroughputMetrics(routingService))
			monitoring.GET("/errors", handlers.GetIntegrationErrors(connectorRegistry))
			monitoring.GET("/latency", handlers.GetLatencyMetrics(routingService))
			monitoring.GET("/health-dashboard", handlers.GetHealthDashboard(connectorRegistry, routingService))
		}
	}

	// Webhook endpoints for SIEM systems
	webhooks := router.Group("/webhooks")
	{
		webhooks.POST("/splunk", handlers.HandleSplunkWebhook(splunkConnector, routingService))
		webhooks.POST("/qradar", handlers.HandleQRadarWebhook(qradarConnector, routingService))
		webhooks.POST("/sentinel", handlers.HandleSentinelWebhook(sentinelConnector, routingService))
		webhooks.POST("/elastic", handlers.HandleElasticWebhook(elasticConnector, routingService))
		webhooks.POST("/arcsight", handlers.HandleArcSightWebhook(arcsightConnector, routingService))
		webhooks.POST("/generic", handlers.HandleGenericWebhook(routingService))
	}

	// Real-time streaming endpoints
	streaming := router.Group("/stream")
	streaming.Use(middleware.RequireAuth(cfg.Auth))
	{
		streaming.GET("/events", handlers.StreamEvents(routingService))
		streaming.GET("/threat-intel", handlers.StreamThreatIntelligence(threatIntelService))
		streaming.GET("/alerts", handlers.StreamAlerts(routingService))
		streaming.GET("/metrics", handlers.StreamMetrics(routingService))
	}

	// Admin endpoints for system management
	admin := v1.Group("/admin")
	admin.Use(middleware.RequireRole("admin"))
	{
		admin.GET("/stats", handlers.GetIntegrationStats(connectorRegistry, routingService))
		admin.POST("/maintenance", handlers.EnableMaintenanceMode(connectorRegistry))
		admin.DELETE("/maintenance", handlers.DisableMaintenanceMode(connectorRegistry))
		admin.POST("/connectors/bulk-sync", handlers.BulkSyncConnectors(connectorRegistry))
		admin.POST("/data/replay", handlers.ReplayData(routingService))
		admin.GET("/audit", handlers.GetAuditLog(routingService))
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

	go dataTransformService.StartDataProcessing(ctx, kafkaConsumer)
	go routingService.StartRouting(ctx, kafkaProducer)
	go enrichmentService.StartEnrichment(ctx)
	go threatIntelService.StartThreatIntelProcessing(ctx)
	go connectorRegistry.StartHealthChecking(ctx)
	go startKafkaMessageProcessing(ctx, kafkaConsumer, routingService)

	// Start server in goroutine
	go func() {
		log.Printf("Starting SIEM Integration Gateway on port %d", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down SIEM Integration Gateway...")

	// Cancel background processing
	cancel()

	// Graceful shutdown with timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("SIEM Integration Gateway forced to shutdown: %v", err)
	}

	log.Println("SIEM Integration Gateway shutdown completed")
}

// startKafkaMessageProcessing handles Kafka message processing
func startKafkaMessageProcessing(ctx context.Context, consumer *kafka.Consumer, routingService *services.RoutingService) {
	consumer.SubscribeTopics([]string{"iff-events", "iff-threats", "iff-intel"}, nil)
	
	for {
		select {
		case <-ctx.Done():
			return
		default:
			msg, err := consumer.ReadMessage(100 * time.Millisecond)
			if err != nil {
				continue
			}
			
			// Process the message through routing service
			if err := routingService.ProcessKafkaMessage(msg); err != nil {
				log.Printf("Failed to process Kafka message: %v", err)
			}
		}
	}
}

// SIEMConnector represents a SIEM system connector
type SIEMConnector struct {
	ID               string                 `json:"id"`
	Name             string                 `json:"name"`
	Type             SIEMType               `json:"type"`
	Description      string                 `json:"description"`
	Version          string                 `json:"version"`
	Status           ConnectorStatus        `json:"status"`
	Endpoint         string                 `json:"endpoint"`
	Credentials      map[string]interface{} `json:"credentials,omitempty"`
	Configuration    ConnectorConfig        `json:"configuration"`
	SupportedFormats []string               `json:"supported_formats"`
	Capabilities     []string               `json:"capabilities"`
	LastConnected    *time.Time             `json:"last_connected,omitempty"`
	LastError        *string                `json:"last_error,omitempty"`
	DataIngested     int64                  `json:"data_ingested"`
	DataForwarded    int64                  `json:"data_forwarded"`
	Latency          time.Duration          `json:"latency"`
	CreatedAt        time.Time              `json:"created_at"`
	UpdatedAt        time.Time              `json:"updated_at"`
	Metadata         map[string]interface{} `json:"metadata"`
}

// SIEMType represents different types of SIEM systems
type SIEMType string

const (
	SIEMTypeSplunk     SIEMType = "splunk"
	SIEMTypeQRadar     SIEMType = "qradar"
	SIEMTypeSentinel   SIEMType = "sentinel"
	SIEMTypeElastic    SIEMType = "elastic"
	SIEMTypeArcSight   SIEMType = "arcsight"
	SIEMTypeGeneric    SIEMType = "generic"
)

// ConnectorStatus represents the status of a SIEM connector
type ConnectorStatus string

const (
	ConnectorStatusConnected    ConnectorStatus = "connected"
	ConnectorStatusDisconnected ConnectorStatus = "disconnected"
	ConnectorStatusError        ConnectorStatus = "error"
	ConnectorStatusMaintenance  ConnectorStatus = "maintenance"
)

// ConnectorConfig represents configuration for a SIEM connector
type ConnectorConfig struct {
	BatchSize           int           `json:"batch_size"`
	RetryAttempts       int           `json:"retry_attempts"`
	RetryDelay          time.Duration `json:"retry_delay"`
	TimeoutDuration     time.Duration `json:"timeout_duration"`
	CompressionEnabled  bool          `json:"compression_enabled"`
	EncryptionEnabled   bool          `json:"encryption_enabled"`
	BidirectionalSync   bool          `json:"bidirectional_sync"`
	SyncInterval        time.Duration `json:"sync_interval"`
	DataFilters         []DataFilter  `json:"data_filters"`
	FieldMappings       []FieldMapping `json:"field_mappings"`
	CustomHeaders       map[string]string `json:"custom_headers,omitempty"`
}

// DataFilter represents a filter for data processing
type DataFilter struct {
	Field     string      `json:"field"`
	Operator  string      `json:"operator"`
	Value     interface{} `json:"value"`
	Include   bool        `json:"include"`
}

// FieldMapping represents field mapping between systems
type FieldMapping struct {
	SourceField string `json:"source_field"`
	TargetField string `json:"target_field"`
	Transform   string `json:"transform,omitempty"`
	Default     interface{} `json:"default,omitempty"`
}

// DataEvent represents a normalized data event
type DataEvent struct {
	ID             string                 `json:"id"`
	Source         string                 `json:"source"`
	EventType      string                 `json:"event_type"`
	Timestamp      time.Time              `json:"timestamp"`
	Severity       string                 `json:"severity"`
	Category       string                 `json:"category"`
	Message        string                 `json:"message"`
	RawData        string                 `json:"raw_data"`
	NormalizedData map[string]interface{} `json:"normalized_data"`
	Enrichment     map[string]interface{} `json:"enrichment,omitempty"`
	Tags           []string               `json:"tags"`
	Indicators     []IOC                  `json:"indicators,omitempty"`
	ProcessedAt    time.Time              `json:"processed_at"`
	Destinations   []string               `json:"destinations"`
	Metadata       map[string]interface{} `json:"metadata"`
}

// IOC represents an Indicator of Compromise
type IOC struct {
	Type        string                 `json:"type"`
	Value       string                 `json:"value"`
	Description string                 `json:"description"`
	Confidence  float64                `json:"confidence"`
	Source      string                 `json:"source"`
	Tags        []string               `json:"tags"`
	FirstSeen   time.Time              `json:"first_seen"`
	LastSeen    time.Time              `json:"last_seen"`
	Context     map[string]interface{} `json:"context"`
}

// RoutingRule represents a rule for routing data
type RoutingRule struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Enabled     bool                   `json:"enabled"`
	Priority    int                    `json:"priority"`
	Conditions  []RuleCondition        `json:"conditions"`
	Actions     []RoutingAction        `json:"actions"`
	Destinations []string              `json:"destinations"`
	Transform   *TransformConfig       `json:"transform,omitempty"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	MatchCount  int64                  `json:"match_count"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// RuleCondition represents a condition in a routing rule
type RuleCondition struct {
	Field    string      `json:"field"`
	Operator string      `json:"operator"`
	Value    interface{} `json:"value"`
	Logic    string      `json:"logic,omitempty"`
}

// RoutingAction represents an action to take when routing
type RoutingAction struct {
	Type       string                 `json:"type"`
	Target     string                 `json:"target"`
	Parameters map[string]interface{} `json:"parameters,omitempty"`
}

// TransformConfig represents transformation configuration
type TransformConfig struct {
	FieldMappings    []FieldMapping         `json:"field_mappings"`
	CustomScript     string                 `json:"custom_script,omitempty"`
	OutputFormat     string                 `json:"output_format"`
	Parameters       map[string]interface{} `json:"parameters,omitempty"`
}

// ThreatIntelligenceFeed represents a threat intelligence feed
type ThreatIntelligenceFeed struct {
	ID              string                 `json:"id"`
	Name            string                 `json:"name"`
	Description     string                 `json:"description"`
	Type            string                 `json:"type"`
	URL             string                 `json:"url"`
	Format          string                 `json:"format"`
	UpdateInterval  time.Duration          `json:"update_interval"`
	LastUpdated     *time.Time             `json:"last_updated,omitempty"`
	Status          string                 `json:"status"`
	RecordCount     int64                  `json:"record_count"`
	Quality         float64                `json:"quality"`
	Reliability     float64                `json:"reliability"`
	Categories      []string               `json:"categories"`
	Tags            []string               `json:"tags"`
	Authentication  map[string]interface{} `json:"authentication,omitempty"`
	Configuration   map[string]interface{} `json:"configuration"`
	CreatedAt       time.Time              `json:"created_at"`
	UpdatedAt       time.Time              `json:"updated_at"`
	Metadata        map[string]interface{} `json:"metadata"`
}

// SyncStatus represents bidirectional synchronization status
type SyncStatus struct {
	ConnectorID      string                 `json:"connector_id"`
	ConnectorName    string                 `json:"connector_name"`
	SyncEnabled      bool                   `json:"sync_enabled"`
	LastSyncTime     *time.Time             `json:"last_sync_time,omitempty"`
	NextSyncTime     *time.Time             `json:"next_sync_time,omitempty"`
	SyncInterval     time.Duration          `json:"sync_interval"`
	RecordsSynced    int64                  `json:"records_synced"`
	RecordsUpstream  int64                  `json:"records_upstream"`
	RecordsDownstream int64                 `json:"records_downstream"`
	Conflicts        int                    `json:"conflicts"`
	LastError        *string                `json:"last_error,omitempty"`
	Status           string                 `json:"status"`
	Metadata         map[string]interface{} `json:"metadata"`
}

// IntegrationMetrics represents metrics for SIEM integration
type IntegrationMetrics struct {
	Timestamp         time.Time              `json:"timestamp"`
	ConnectorID       string                 `json:"connector_id"`
	EventsIngested    int64                  `json:"events_ingested"`
	EventsForwarded   int64                  `json:"events_forwarded"`
	EventsFiltered    int64                  `json:"events_filtered"`
	EventsError       int64                  `json:"events_error"`
	AverageLatency    time.Duration          `json:"average_latency"`
	MaxLatency        time.Duration          `json:"max_latency"`
	MinLatency        time.Duration          `json:"min_latency"`
	Throughput        float64                `json:"throughput"`
	ErrorRate         float64                `json:"error_rate"`
	ConnectionUptime  float64                `json:"connection_uptime"`
	DataQuality       float64                `json:"data_quality"`
	Metadata          map[string]interface{} `json:"metadata"`
}

// NormalizationResult represents the result of data normalization
type NormalizationResult struct {
	OriginalFormat string                 `json:"original_format"`
	TargetFormat   string                 `json:"target_format"`
	Success        bool                   `json:"success"`
	NormalizedData map[string]interface{} `json:"normalized_data"`
	Warnings       []string               `json:"warnings,omitempty"`
	Errors         []string               `json:"errors,omitempty"`
	ProcessingTime time.Duration          `json:"processing_time"`
	Metadata       map[string]interface{} `json:"metadata"`
}

// EnrichmentResult represents the result of data enrichment
type EnrichmentResult struct {
	OriginalData   map[string]interface{} `json:"original_data"`
	EnrichedData   map[string]interface{} `json:"enriched_data"`
	EnrichmentSources []string            `json:"enrichment_sources"`
	Success        bool                   `json:"success"`
	Confidence     float64                `json:"confidence"`
	ProcessingTime time.Duration          `json:"processing_time"`
	Metadata       map[string]interface{} `json:"metadata"`
}
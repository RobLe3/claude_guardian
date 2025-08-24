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
	"github.com/gorilla/websocket"
	
	"github.com/iff-guardian/real-time-dashboard/internal/config"
	"github.com/iff-guardian/real-time-dashboard/internal/dashboard"
	"github.com/iff-guardian/real-time-dashboard/internal/handlers"
	"github.com/iff-guardian/real-time-dashboard/internal/middleware"
	"github.com/iff-guardian/real-time-dashboard/internal/services"
)

// Real-time Security Dashboard Service
// Provides real-time security monitoring, alerts, and visualization
func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize services
	authService := services.NewAuthService(cfg.Auth)
	metricsService := services.NewMetricsService(cfg.Metrics)
	alertService := services.NewAlertService(cfg.Alerts)
	threatService := services.NewThreatService(cfg.ThreatAPI)
	dashboardManager := dashboard.NewDashboardManager(cfg.Dashboard)

	// Initialize WebSocket manager for real-time updates
	wsManager := services.NewWebSocketManager()

	// Initialize data aggregators
	threatAggregator := services.NewThreatAggregator(threatService, metricsService)
	metricsAggregator := services.NewMetricsAggregator(metricsService)
	alertAggregator := services.NewAlertAggregator(alertService)

	// Setup Gin router
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}
	
	router := gin.New()
	
	// Global middleware
	router.Use(gin.Recovery())
	router.Use(middleware.Logger())
	router.Use(middleware.CORS(cfg.CORS))
	router.Use(middleware.SecurityHeaders())
	router.Use(middleware.RateLimiter(cfg.RateLimit))

	// Serve static files for dashboard frontend
	router.Static("/static", "./web/static")
	router.LoadHTMLGlob("web/templates/*")

	// Health check endpoints
	router.GET("/health", handlers.HealthCheck)
	router.GET("/health/ready", func(c *gin.Context) {
		status := map[string]interface{}{
			"status": "ready",
			"services": map[string]string{
				"auth":      authService.Status(),
				"metrics":   metricsService.Status(),
				"alerts":    alertService.Status(),
				"threats":   threatService.Status(),
				"websocket": wsManager.Status(),
			},
			"connected_clients": wsManager.GetConnectedCount(),
		}
		c.JSON(http.StatusOK, status)
	})

	// Dashboard main page
	router.GET("/", func(c *gin.Context) {
		c.HTML(http.StatusOK, "dashboard.html", gin.H{
			"title": "IFF-Guardian Security Dashboard",
			"user":  middleware.GetUser(c),
		})
	})

	// Authentication required for all dashboard APIs
	api := router.Group("/api/v1")
	api.Use(middleware.RequireAuth(authService))
	{
		// WebSocket endpoint for real-time updates
		api.GET("/ws", func(c *gin.Context) {
			handleWebSocketConnection(c, wsManager, authService)
		})

		// Dashboard data endpoints
		dashboard := api.Group("/dashboard")
		{
			dashboard.GET("/overview", handlers.GetDashboardOverview(threatAggregator, metricsAggregator))
			dashboard.GET("/threats", handlers.GetThreatData(threatAggregator))
			dashboard.GET("/metrics", handlers.GetMetricsData(metricsAggregator))
			dashboard.GET("/alerts", handlers.GetAlerts(alertAggregator))
			dashboard.GET("/timeline", handlers.GetSecurityTimeline(threatAggregator))
		}

		// Real-time threat monitoring
		threats := api.Group("/threats")
		{
			threats.GET("/live", handlers.GetLiveThreats(threatAggregator))
			threats.GET("/trends", handlers.GetThreatTrends(threatAggregator))
			threats.GET("/heatmap", handlers.GetThreatHeatmap(threatAggregator))
			threats.GET("/:id", handlers.GetThreatDetails(threatService))
			threats.POST("/:id/resolve", handlers.ResolveThreat(threatService))
		}

		// System metrics and performance
		metrics := api.Group("/metrics")
		{
			metrics.GET("/performance", handlers.GetPerformanceMetrics(metricsService))
			metrics.GET("/system", handlers.GetSystemMetrics(metricsService))
			metrics.GET("/security", handlers.GetSecurityMetrics(metricsService))
			metrics.GET("/export", handlers.ExportMetrics(metricsService))
		}

		// Alert management
		alerts := api.Group("/alerts")
		{
			alerts.GET("/", handlers.ListAlerts(alertService))
			alerts.GET("/:id", handlers.GetAlert(alertService))
			alerts.POST("/:id/acknowledge", handlers.AcknowledgeAlert(alertService))
			alerts.POST("/:id/resolve", handlers.ResolveAlert(alertService))
			alerts.POST("/bulk-action", handlers.BulkAlertAction(alertService))
		}

		// Dashboard configuration
		config := api.Group("/config")
		{
			config.GET("/dashboards", handlers.GetDashboardConfigs(dashboardManager))
			config.POST("/dashboards", handlers.CreateDashboard(dashboardManager))
			config.PUT("/dashboards/:id", handlers.UpdateDashboard(dashboardManager))
			config.DELETE("/dashboards/:id", handlers.DeleteDashboard(dashboardManager))
		}

		// User preferences
		preferences := api.Group("/preferences")
		{
			preferences.GET("/", handlers.GetUserPreferences(authService))
			preferences.PUT("/", handlers.UpdateUserPreferences(authService))
		}
	}

	// Admin endpoints
	admin := router.Group("/api/v1/admin")
	admin.Use(middleware.RequireAuth(authService))
	admin.Use(middleware.RequireRole("admin"))
	{
		admin.GET("/stats", handlers.GetAdminStats(metricsService, wsManager))
		admin.GET("/clients", handlers.GetConnectedClients(wsManager))
		admin.POST("/broadcast", handlers.BroadcastMessage(wsManager))
		admin.GET("/system-health", handlers.GetSystemHealth(metricsService))
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

	go threatAggregator.StartRealTimeAggregation(ctx, wsManager)
	go metricsAggregator.StartMetricsCollection(ctx, wsManager)
	go alertAggregator.StartAlertProcessing(ctx, wsManager)
	go wsManager.StartConnectionManager(ctx)

	// Start server in goroutine
	go func() {
		log.Printf("Starting Real-time Dashboard Service on port %d", cfg.Port)
		log.Printf("Dashboard available at http://localhost:%d/", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down Real-time Dashboard Service...")

	// Cancel background processing
	cancel()

	// Close all WebSocket connections
	wsManager.CloseAllConnections()

	// Graceful shutdown with timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("Real-time Dashboard Service forced to shutdown: %v", err)
	}

	log.Println("Real-time Dashboard Service shutdown completed")
}

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		// In production, implement proper origin checking
		return true
	},
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
}

// handleWebSocketConnection handles WebSocket connections for real-time updates
func handleWebSocketConnection(c *gin.Context, wsManager *services.WebSocketManager, authService *services.AuthService) {
	// Get user from context (already authenticated by middleware)
	user := middleware.GetUser(c)
	if user == nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Authentication required"})
		return
	}

	// Upgrade HTTP connection to WebSocket
	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		log.Printf("Failed to upgrade WebSocket connection: %v", err)
		return
	}

	// Create WebSocket client
	client := &services.WebSocketClient{
		ID:         generateClientID(),
		UserID:     user.ID,
		Username:   user.Username,
		Connection: conn,
		Send:       make(chan []byte, 256),
		JoinedAt:   time.Now(),
		LastSeen:   time.Now(),
		Subscriptions: make(map[string]bool),
	}

	log.Printf("WebSocket client connected: %s (%s)", client.Username, client.ID)

	// Register client with WebSocket manager
	wsManager.RegisterClient(client)

	// Start client goroutines
	go wsManager.HandleClientWriter(client)
	go wsManager.HandleClientReader(client)
}

// generateClientID generates a unique client ID
func generateClientID() string {
	return fmt.Sprintf("client_%d", time.Now().UnixNano())
}

// DashboardOverview represents the main dashboard overview data
type DashboardOverview struct {
	Summary struct {
		TotalThreats     int64   `json:"total_threats"`
		ActiveThreats    int64   `json:"active_threats"`
		ResolvedThreats  int64   `json:"resolved_threats"`
		FalsePositives   int64   `json:"false_positives"`
		ThreatTrend      float64 `json:"threat_trend"`
		DetectionRate    float64 `json:"detection_rate"`
		ResponseTime     float64 `json:"avg_response_time_ms"`
	} `json:"summary"`
	
	ThreatsByType []struct {
		Type  string `json:"type"`
		Count int64  `json:"count"`
	} `json:"threats_by_type"`
	
	ThreatsBySeverity []struct {
		Severity string `json:"severity"`
		Count    int64  `json:"count"`
	} `json:"threats_by_severity"`
	
	RecentThreats []struct {
		ID          string    `json:"id"`
		Type        string    `json:"type"`
		Severity    string    `json:"severity"`
		Description string    `json:"description"`
		Timestamp   time.Time `json:"timestamp"`
		Status      string    `json:"status"`
	} `json:"recent_threats"`
	
	SystemMetrics struct {
		CPUUsage       float64 `json:"cpu_usage"`
		MemoryUsage    float64 `json:"memory_usage"`
		NetworkTraffic int64   `json:"network_traffic"`
		ActiveSessions int64   `json:"active_sessions"`
	} `json:"system_metrics"`
	
	AlertSummary struct {
		TotalAlerts      int64 `json:"total_alerts"`
		CriticalAlerts   int64 `json:"critical_alerts"`
		Unacknowledged   int64 `json:"unacknowledged"`
		RecentAlerts     []Alert `json:"recent_alerts"`
	} `json:"alert_summary"`
}

// Alert represents a security alert
type Alert struct {
	ID          string                 `json:"id"`
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Severity    string                 `json:"severity"`
	Status      string                 `json:"status"`
	Source      string                 `json:"source"`
	Timestamp   time.Time              `json:"timestamp"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// ThreatHeatmapData represents threat heatmap visualization data
type ThreatHeatmapData struct {
	TimeSlots []time.Time `json:"time_slots"`
	ThreatTypes []string  `json:"threat_types"`
	HeatmapData [][]int64 `json:"heatmap_data"`
	MaxValue    int64     `json:"max_value"`
}
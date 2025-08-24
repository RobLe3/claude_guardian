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
	
	"github.com/iff-guardian/alert-system/internal/config"
	"github.com/iff-guardian/alert-system/internal/handlers"
	"github.com/iff-guardian/alert-system/internal/middleware"
	"github.com/iff-guardian/alert-system/internal/notifications"
	"github.com/iff-guardian/alert-system/internal/services"
)

// Alert System Service - Multi-channel alert management and notification system
// Handles alert creation, escalation, notification delivery, and resolution tracking
func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize services
	dbService := services.NewDatabaseService(cfg.Database)
	alertManager := services.NewAlertManager(dbService, cfg.Alerts)
	notificationService := notifications.NewNotificationService(cfg.Notifications)
	escalationEngine := services.NewEscalationEngine(cfg.Escalation)
	templateService := services.NewTemplateService(cfg.Templates)

	// Initialize notification channels
	emailNotifier := notifications.NewEmailNotifier(cfg.Email)
	slackNotifier := notifications.NewSlackNotifier(cfg.Slack)
	webhookNotifier := notifications.NewWebhookNotifier(cfg.Webhook)
	smsNotifier := notifications.NewSMSNotifier(cfg.SMS)

	// Register notification channels
	notificationService.RegisterChannel("email", emailNotifier)
	notificationService.RegisterChannel("slack", slackNotifier)
	notificationService.RegisterChannel("webhook", webhookNotifier)
	notificationService.RegisterChannel("sms", smsNotifier)

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
				"database":      dbService.HealthCheck(),
				"alert_manager": alertManager.Status(),
				"notifications": notificationService.Status(),
				"escalation":    escalationEngine.Status(),
			},
			"notification_channels": notificationService.GetChannelStatus(),
			"active_alerts":         alertManager.GetActiveAlertCount(),
		}
		c.JSON(http.StatusOK, status)
	})

	// API versioning
	v1 := router.Group("/api/v1")
	v1.Use(middleware.RequireAuth(cfg.Auth))
	{
		// Alert management endpoints
		alerts := v1.Group("/alerts")
		{
			alerts.POST("/", handlers.CreateAlert(alertManager, notificationService))
			alerts.GET("/", handlers.ListAlerts(alertManager))
			alerts.GET("/:id", handlers.GetAlert(alertManager))
			alerts.PUT("/:id", handlers.UpdateAlert(alertManager))
			alerts.DELETE("/:id", handlers.DeleteAlert(alertManager))
			
			// Alert actions
			alerts.POST("/:id/acknowledge", handlers.AcknowledgeAlert(alertManager, notificationService))
			alerts.POST("/:id/resolve", handlers.ResolveAlert(alertManager, notificationService))
			alerts.POST("/:id/escalate", handlers.EscalateAlert(alertManager, escalationEngine))
			alerts.POST("/:id/snooze", handlers.SnoozeAlert(alertManager))
			alerts.POST("/:id/comment", handlers.AddAlertComment(alertManager))
			
			// Bulk operations
			alerts.POST("/bulk/acknowledge", handlers.BulkAcknowledgeAlerts(alertManager))
			alerts.POST("/bulk/resolve", handlers.BulkResolveAlerts(alertManager))
			alerts.POST("/bulk/assign", handlers.BulkAssignAlerts(alertManager))
		}

		// Alert rules and policies
		rules := v1.Group("/rules")
		{
			rules.GET("/", handlers.ListAlertRules(alertManager))
			rules.POST("/", handlers.CreateAlertRule(alertManager))
			rules.GET("/:id", handlers.GetAlertRule(alertManager))
			rules.PUT("/:id", handlers.UpdateAlertRule(alertManager))
			rules.DELETE("/:id", handlers.DeleteAlertRule(alertManager))
			rules.POST("/:id/test", handlers.TestAlertRule(alertManager))
		}

		// Notification management
		notifications := v1.Group("/notifications")
		{
			notifications.GET("/channels", handlers.GetNotificationChannels(notificationService))
			notifications.POST("/channels", handlers.CreateNotificationChannel(notificationService))
			notifications.PUT("/channels/:id", handlers.UpdateNotificationChannel(notificationService))
			notifications.DELETE("/channels/:id", handlers.DeleteNotificationChannel(notificationService))
			notifications.POST("/test", handlers.TestNotification(notificationService))
			notifications.GET("/history", handlers.GetNotificationHistory(notificationService))
		}

		// Escalation management
		escalation := v1.Group("/escalation")
		{
			escalation.GET("/policies", handlers.GetEscalationPolicies(escalationEngine))
			escalation.POST("/policies", handlers.CreateEscalationPolicy(escalationEngine))
			escalation.PUT("/policies/:id", handlers.UpdateEscalationPolicy(escalationEngine))
			escalation.DELETE("/policies/:id", handlers.DeleteEscalationPolicy(escalationEngine))
			escalation.GET("/schedules", handlers.GetOnCallSchedules(escalationEngine))
			escalation.POST("/schedules", handlers.CreateOnCallSchedule(escalationEngine))
		}

		// Alert analytics and reporting
		analytics := v1.Group("/analytics")
		{
			analytics.GET("/summary", handlers.GetAlertSummary(alertManager))
			analytics.GET("/trends", handlers.GetAlertTrends(alertManager))
			analytics.GET("/mttr", handlers.GetMTTRMetrics(alertManager))
			analytics.GET("/volume", handlers.GetAlertVolume(alertManager))
			analytics.GET("/false-positives", handlers.GetFalsePositiveRate(alertManager))
			analytics.GET("/response-times", handlers.GetResponseTimeMetrics(alertManager))
		}

		// Template management
		templates := v1.Group("/templates")
		{
			templates.GET("/", handlers.ListAlertTemplates(templateService))
			templates.POST("/", handlers.CreateAlertTemplate(templateService))
			templates.GET("/:id", handlers.GetAlertTemplate(templateService))
			templates.PUT("/:id", handlers.UpdateAlertTemplate(templateService))
			templates.DELETE("/:id", handlers.DeleteAlertTemplate(templateService))
			templates.POST("/:id/preview", handlers.PreviewTemplate(templateService))
		}
	}

	// Webhook endpoints for external integrations
	webhooks := router.Group("/webhooks")
	{
		webhooks.POST("/generic", handlers.HandleGenericWebhook(alertManager))
		webhooks.POST("/prometheus", handlers.HandlePrometheusWebhook(alertManager))
		webhooks.POST("/grafana", handlers.HandleGrafanaWebhook(alertManager))
		webhooks.POST("/security-tools", handlers.HandleSecurityToolWebhook(alertManager))
	}

	// Admin endpoints
	admin := v1.Group("/admin")
	admin.Use(middleware.RequireRole("admin"))
	{
		admin.GET("/stats", handlers.GetSystemStats(alertManager, notificationService))
		admin.POST("/maintenance", handlers.EnableMaintenanceMode(alertManager))
		admin.DELETE("/maintenance", handlers.DisableMaintenanceMode(alertManager))
		admin.POST("/purge", handlers.PurgeOldAlerts(alertManager))
		admin.GET("/audit", handlers.GetAuditLog(alertManager))
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

	go alertManager.StartAlertProcessing(ctx)
	go notificationService.StartNotificationDelivery(ctx)
	go escalationEngine.StartEscalationProcessing(ctx)
	go alertManager.StartAlertCleanup(ctx)

	// Start server in goroutine
	go func() {
		log.Printf("Starting Alert System Service on port %d", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down Alert System Service...")

	// Cancel background processing
	cancel()

	// Graceful shutdown with timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("Alert System Service forced to shutdown: %v", err)
	}

	log.Println("Alert System Service shutdown completed")
}

// Alert represents a security alert in the system
type Alert struct {
	ID          string                 `json:"id" db:"id"`
	Title       string                 `json:"title" db:"title"`
	Description string                 `json:"description" db:"description"`
	Severity    AlertSeverity          `json:"severity" db:"severity"`
	Status      AlertStatus            `json:"status" db:"status"`
	Source      string                 `json:"source" db:"source"`
	SourceID    string                 `json:"source_id" db:"source_id"`
	Category    string                 `json:"category" db:"category"`
	Tags        []string               `json:"tags" db:"tags"`
	
	// Threat information
	ThreatType    string                 `json:"threat_type" db:"threat_type"`
	RiskScore     float64                `json:"risk_score" db:"risk_score"`
	Confidence    float64                `json:"confidence" db:"confidence"`
	MITRE_TacticID   *string             `json:"mitre_tactic_id" db:"mitre_tactic_id"`
	MITRE_TechniqueID *string            `json:"mitre_technique_id" db:"mitre_technique_id"`
	
	// Assignment and tracking
	AssignedTo    *string                `json:"assigned_to" db:"assigned_to"`
	AssignedBy    *string                `json:"assigned_by" db:"assigned_by"`
	AssignedAt    *time.Time             `json:"assigned_at" db:"assigned_at"`
	
	// Timing information
	CreatedAt     time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt     time.Time              `json:"updated_at" db:"updated_at"`
	AcknowledgedAt *time.Time            `json:"acknowledged_at" db:"acknowledged_at"`
	ResolvedAt    *time.Time             `json:"resolved_at" db:"resolved_at"`
	FirstSeen     time.Time              `json:"first_seen" db:"first_seen"`
	LastSeen      time.Time              `json:"last_seen" db:"last_seen"`
	
	// Escalation
	EscalationLevel int                  `json:"escalation_level" db:"escalation_level"`
	EscalatedAt    *time.Time            `json:"escalated_at" db:"escalated_at"`
	
	// Metadata and context
	Metadata      map[string]interface{} `json:"metadata" db:"metadata"`
	Context       map[string]interface{} `json:"context" db:"context"`
	
	// Related entities
	AffectedAssets []string              `json:"affected_assets" db:"affected_assets"`
	UserIDs       []string               `json:"user_ids" db:"user_ids"`
	RelatedAlerts []string               `json:"related_alerts" db:"related_alerts"`
	
	// Notification tracking
	NotificationsSent []NotificationRecord `json:"notifications_sent" db:"-"`
	Comments         []AlertComment        `json:"comments" db:"-"`
}

// AlertSeverity represents the severity level of an alert
type AlertSeverity string

const (
	SeverityCritical AlertSeverity = "critical"
	SeverityHigh     AlertSeverity = "high" 
	SeverityMedium   AlertSeverity = "medium"
	SeverityLow      AlertSeverity = "low"
	SeverityInfo     AlertSeverity = "info"
)

// AlertStatus represents the current status of an alert
type AlertStatus string

const (
	StatusOpen         AlertStatus = "open"
	StatusAcknowledged AlertStatus = "acknowledged"
	StatusInProgress   AlertStatus = "in_progress"
	StatusResolved     AlertStatus = "resolved"
	StatusClosed       AlertStatus = "closed"
	StatusSnoozed      AlertStatus = "snoozed"
	StatusEscalated    AlertStatus = "escalated"
)

// AlertRule represents a rule for creating alerts
type AlertRule struct {
	ID          string                 `json:"id" db:"id"`
	Name        string                 `json:"name" db:"name"`
	Description string                 `json:"description" db:"description"`
	Enabled     bool                   `json:"enabled" db:"enabled"`
	Conditions  map[string]interface{} `json:"conditions" db:"conditions"`
	Actions     []AlertAction          `json:"actions" db:"actions"`
	Severity    AlertSeverity          `json:"severity" db:"severity"`
	Throttle    *time.Duration         `json:"throttle" db:"throttle"`
	CreatedAt   time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at" db:"updated_at"`
}

// AlertAction represents an action to take when an alert is triggered
type AlertAction struct {
	Type       string                 `json:"type"`
	Channel    string                 `json:"channel"`
	Recipients []string               `json:"recipients"`
	Template   string                 `json:"template"`
	Conditions map[string]interface{} `json:"conditions,omitempty"`
}

// NotificationRecord represents a notification that was sent for an alert
type NotificationRecord struct {
	ID        string                 `json:"id" db:"id"`
	AlertID   string                 `json:"alert_id" db:"alert_id"`
	Channel   string                 `json:"channel" db:"channel"`
	Recipient string                 `json:"recipient" db:"recipient"`
	Status    string                 `json:"status" db:"status"`
	SentAt    time.Time              `json:"sent_at" db:"sent_at"`
	Error     *string                `json:"error" db:"error"`
	Metadata  map[string]interface{} `json:"metadata" db:"metadata"`
}

// AlertComment represents a comment on an alert
type AlertComment struct {
	ID        string    `json:"id" db:"id"`
	AlertID   string    `json:"alert_id" db:"alert_id"`
	UserID    string    `json:"user_id" db:"user_id"`
	Username  string    `json:"username" db:"username"`
	Comment   string    `json:"comment" db:"comment"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
}

// EscalationPolicy represents an escalation policy for alerts
type EscalationPolicy struct {
	ID          string             `json:"id" db:"id"`
	Name        string             `json:"name" db:"name"`
	Description string             `json:"description" db:"description"`
	Enabled     bool               `json:"enabled" db:"enabled"`
	Steps       []EscalationStep   `json:"steps" db:"steps"`
	Conditions  []string           `json:"conditions" db:"conditions"`
	CreatedAt   time.Time          `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time          `json:"updated_at" db:"updated_at"`
}

// EscalationStep represents a single step in an escalation policy
type EscalationStep struct {
	StepNumber  int           `json:"step_number"`
	Delay       time.Duration `json:"delay"`
	Recipients  []string      `json:"recipients"`
	Channels    []string      `json:"channels"`
	Conditions  []string      `json:"conditions"`
}

// AlertSummary represents aggregated alert statistics
type AlertSummary struct {
	TotalAlerts        int64                    `json:"total_alerts"`
	OpenAlerts         int64                    `json:"open_alerts"`
	AcknowledgedAlerts int64                    `json:"acknowledged_alerts"`
	ResolvedAlerts     int64                    `json:"resolved_alerts"`
	CriticalAlerts     int64                    `json:"critical_alerts"`
	AlertsBySeverity   map[AlertSeverity]int64  `json:"alerts_by_severity"`
	AlertsByStatus     map[AlertStatus]int64    `json:"alerts_by_status"`
	AlertsByCategory   map[string]int64         `json:"alerts_by_category"`
	MTTR               time.Duration            `json:"mttr"`
	FalsePositiveRate  float64                  `json:"false_positive_rate"`
	Period             string                   `json:"period"`
	GeneratedAt        time.Time                `json:"generated_at"`
}
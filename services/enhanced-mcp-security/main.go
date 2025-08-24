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
	
	"github.com/iff-guardian/enhanced-mcp-security/internal/config"
	"github.com/iff-guardian/enhanced-mcp-security/internal/filtering"
	"github.com/iff-guardian/enhanced-mcp-security/internal/handlers"
	"github.com/iff-guardian/enhanced-mcp-security/internal/middleware"
	"github.com/iff-guardian/enhanced-mcp-security/internal/rbac"
	"github.com/iff-guardian/enhanced-mcp-security/internal/services"
)

// Enhanced MCP Security Service - Advanced security controls for MCP tool execution
// Provides ML-based tool filtering, risk-based access control, and dynamic policy enforcement
func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize services
	authService := services.NewAuthService(cfg.Auth)
	mlAnalyzer := services.NewMLAnalyzerClient(cfg.MLAnalyzer)
	behaviorService := services.NewBehaviorAnalysisService(cfg.Behavior)
	policyEngine := rbac.NewPolicyEngine(cfg.RBAC)
	toolFilterEngine := filtering.NewToolFilterEngine(mlAnalyzer, behaviorService, cfg.Filtering)
	riskAssessmentService := services.NewRiskAssessmentService(cfg.Risk)
	auditService := services.NewAuditService(cfg.Audit)

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
				"auth":             authService.Status(),
				"ml_analyzer":      mlAnalyzer.Status(),
				"behavior":         behaviorService.Status(),
				"policy_engine":    policyEngine.Status(),
				"tool_filter":      toolFilterEngine.Status(),
				"risk_assessment":  riskAssessmentService.Status(),
			},
			"active_policies":    policyEngine.GetActivePolicyCount(),
			"filtered_tools":     toolFilterEngine.GetFilteredToolCount(),
		}
		c.JSON(http.StatusOK, status)
	})

	// API versioning
	v1 := router.Group("/api/v1")
	v1.Use(middleware.RequireAuth(authService))
	{
		// Tool filtering endpoints
		filtering := v1.Group("/filtering")
		{
			filtering.POST("/analyze", handlers.AnalyzeToolRequest(toolFilterEngine))
			filtering.POST("/filter", handlers.FilterTool(toolFilterEngine))
			filtering.GET("/rules", handlers.GetFilteringRules(toolFilterEngine))
			filtering.POST("/rules", handlers.CreateFilteringRule(toolFilterEngine))
			filtering.PUT("/rules/:id", handlers.UpdateFilteringRule(toolFilterEngine))
			filtering.DELETE("/rules/:id", handlers.DeleteFilteringRule(toolFilterEngine))
			filtering.GET("/statistics", handlers.GetFilteringStatistics(toolFilterEngine))
		}

		// Risk-based access control
		rbac := v1.Group("/rbac")
		{
			rbac.POST("/evaluate", handlers.EvaluateAccess(policyEngine, riskAssessmentService))
			rbac.GET("/policies", handlers.GetAccessPolicies(policyEngine))
			rbac.POST("/policies", handlers.CreateAccessPolicy(policyEngine))
			rbac.PUT("/policies/:id", handlers.UpdateAccessPolicy(policyEngine))
			rbac.DELETE("/policies/:id", handlers.DeleteAccessPolicy(policyEngine))
			rbac.GET("/user-permissions", handlers.GetUserPermissions(policyEngine))
			rbac.POST("/dynamic-access", handlers.EvaluateDynamicAccess(policyEngine, riskAssessmentService))
		}

		// Risk assessment endpoints
		risk := v1.Group("/risk")
		{
			risk.POST("/assess", handlers.AssessRisk(riskAssessmentService))
			risk.GET("/user/:id/profile", handlers.GetUserRiskProfile(riskAssessmentService))
			risk.PUT("/user/:id/risk-score", handlers.UpdateUserRiskScore(riskAssessmentService))
			risk.GET("/tool/:name/risk", handlers.GetToolRiskProfile(riskAssessmentService))
			risk.GET("/trends", handlers.GetRiskTrends(riskAssessmentService))
		}

		// Behavior analysis integration
		behavior := v1.Group("/behavior")
		{
			behavior.POST("/analyze", handlers.AnalyzeBehavior(behaviorService))
			behavior.GET("/user/:id/patterns", handlers.GetUserBehaviorPatterns(behaviorService))
			behavior.POST("/baseline", handlers.UpdateBehaviorBaseline(behaviorService))
			behavior.GET("/anomalies", handlers.GetBehaviorAnomalies(behaviorService))
			behavior.POST("/feedback", handlers.ProvideBehaviorFeedback(behaviorService))
		}

		// Security policies management
		policies := v1.Group("/policies")
		{
			policies.GET("/", handlers.GetSecurityPolicies(policyEngine))
			policies.POST("/", handlers.CreateSecurityPolicy(policyEngine))
			policies.GET("/:id", handlers.GetSecurityPolicy(policyEngine))
			policies.PUT("/:id", handlers.UpdateSecurityPolicy(policyEngine))
			policies.DELETE("/:id", handlers.DeleteSecurityPolicy(policyEngine))
			policies.POST("/:id/test", handlers.TestSecurityPolicy(policyEngine))
		}

		// Audit and compliance
		audit := v1.Group("/audit")
		{
			audit.GET("/logs", handlers.GetAuditLogs(auditService))
			audit.GET("/compliance", handlers.GetComplianceReport(auditService, policyEngine))
			audit.POST("/export", handlers.ExportAuditData(auditService))
			audit.GET("/violations", handlers.GetPolicyViolations(auditService))
		}
	}

	// MCP integration endpoints (called by MCP service)
	mcp := router.Group("/mcp")
	mcp.Use(middleware.RequireServiceAuth(cfg.ServiceAuth))
	{
		mcp.POST("/evaluate-tool-call", handlers.EvaluateToolCall(toolFilterEngine, policyEngine, riskAssessmentService))
		mcp.POST("/check-permissions", handlers.CheckPermissions(policyEngine))
		mcp.POST("/log-tool-execution", handlers.LogToolExecution(auditService))
		mcp.GET("/user-context", handlers.GetUserSecurityContext(policyEngine, riskAssessmentService))
	}

	// Admin endpoints
	admin := v1.Group("/admin")
	admin.Use(middleware.RequireRole("admin"))
	{
		admin.GET("/stats", handlers.GetSecurityStats(toolFilterEngine, policyEngine, riskAssessmentService))
		admin.POST("/retrain", handlers.RetrainModels(toolFilterEngine, behaviorService))
		admin.POST("/policies/bulk-import", handlers.BulkImportPolicies(policyEngine))
		admin.POST("/maintenance", handlers.EnableMaintenanceMode(policyEngine))
		admin.DELETE("/maintenance", handlers.DisableMaintenanceMode(policyEngine))
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

	go toolFilterEngine.StartContinuousLearning(ctx)
	go behaviorService.StartBehaviorMonitoring(ctx)
	go policyEngine.StartPolicyEvaluation(ctx)
	go riskAssessmentService.StartRiskMonitoring(ctx)

	// Start server in goroutine
	go func() {
		log.Printf("Starting Enhanced MCP Security Service on port %d", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down Enhanced MCP Security Service...")

	// Cancel background processing
	cancel()

	// Graceful shutdown with timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("Enhanced MCP Security Service forced to shutdown: %v", err)
	}

	log.Println("Enhanced MCP Security Service shutdown completed")
}

// ToolCallEvaluationRequest represents a request to evaluate a tool call
type ToolCallEvaluationRequest struct {
	UserID      string                 `json:"user_id" binding:"required"`
	ToolName    string                 `json:"tool_name" binding:"required"`
	Parameters  map[string]interface{} `json:"parameters"`
	Context     map[string]interface{} `json:"context"`
	SessionData map[string]interface{} `json:"session_data"`
	Timestamp   time.Time              `json:"timestamp"`
}

// ToolCallEvaluationResponse represents the result of tool call evaluation
type ToolCallEvaluationResponse struct {
	Allowed        bool                   `json:"allowed"`
	RiskScore      float64                `json:"risk_score"`
	RiskLevel      string                 `json:"risk_level"`
	Confidence     float64                `json:"confidence"`
	Reasons        []string               `json:"reasons"`
	PolicyMatches  []PolicyMatch          `json:"policy_matches"`
	Recommendations []string              `json:"recommendations"`
	RequiredActions []string              `json:"required_actions"`
	Metadata       map[string]interface{} `json:"metadata"`
	ProcessingTime time.Duration          `json:"processing_time"`
}

// PolicyMatch represents a matched security policy
type PolicyMatch struct {
	PolicyID    string                 `json:"policy_id"`
	PolicyName  string                 `json:"policy_name"`
	Action      string                 `json:"action"`
	Condition   string                 `json:"condition"`
	Confidence  float64                `json:"confidence"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// UserRiskProfile represents a user's risk profile
type UserRiskProfile struct {
	UserID              string                 `json:"user_id"`
	BaseRiskScore       float64                `json:"base_risk_score"`
	CurrentRiskScore    float64                `json:"current_risk_score"`
	RiskLevel           string                 `json:"risk_level"`
	RiskFactors         []RiskFactor           `json:"risk_factors"`
	BehaviorProfile     map[string]interface{} `json:"behavior_profile"`
	RecentActivities    []ActivityRecord       `json:"recent_activities"`
	TrustScore          float64                `json:"trust_score"`
	LastAssessment      time.Time              `json:"last_assessment"`
	AssessmentHistory   []RiskAssessment       `json:"assessment_history"`
}

// RiskFactor represents a factor contributing to user risk
type RiskFactor struct {
	Factor      string                 `json:"factor"`
	Weight      float64                `json:"weight"`
	Value       float64                `json:"value"`
	Description string                 `json:"description"`
	Impact      string                 `json:"impact"`
	Source      string                 `json:"source"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// ActivityRecord represents a user activity record
type ActivityRecord struct {
	ID          string                 `json:"id"`
	UserID      string                 `json:"user_id"`
	Activity    string                 `json:"activity"`
	ToolName    string                 `json:"tool_name"`
	Timestamp   time.Time              `json:"timestamp"`
	RiskScore   float64                `json:"risk_score"`
	Outcome     string                 `json:"outcome"`
	Context     map[string]interface{} `json:"context"`
}

// RiskAssessment represents a historical risk assessment
type RiskAssessment struct {
	ID          string                 `json:"id"`
	UserID      string                 `json:"user_id"`
	RiskScore   float64                `json:"risk_score"`
	RiskLevel   string                 `json:"risk_level"`
	Factors     []RiskFactor           `json:"factors"`
	Timestamp   time.Time              `json:"timestamp"`
	Trigger     string                 `json:"trigger"`
	Assessor    string                 `json:"assessor"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// SecurityPolicy represents a dynamic security policy
type SecurityPolicy struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Enabled     bool                   `json:"enabled"`
	Priority    int                    `json:"priority"`
	Conditions  []PolicyCondition      `json:"conditions"`
	Actions     []PolicyAction         `json:"actions"`
	Scope       PolicyScope            `json:"scope"`
	Schedule    *PolicySchedule        `json:"schedule,omitempty"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	CreatedBy   string                 `json:"created_by"`
	Version     int                    `json:"version"`
}

// PolicyCondition represents a condition in a security policy
type PolicyCondition struct {
	Field    string      `json:"field"`
	Operator string      `json:"operator"`
	Value    interface{} `json:"value"`
	Logic    string      `json:"logic,omitempty"`
}

// PolicyAction represents an action to take when policy matches
type PolicyAction struct {
	Type       string                 `json:"type"`
	Parameters map[string]interface{} `json:"parameters"`
	OnSuccess  string                 `json:"on_success,omitempty"`
	OnFailure  string                 `json:"on_failure,omitempty"`
}

// PolicyScope defines the scope of a security policy
type PolicyScope struct {
	Users    []string `json:"users,omitempty"`
	Groups   []string `json:"groups,omitempty"`
	Tools    []string `json:"tools,omitempty"`
	Actions  []string `json:"actions,omitempty"`
	Global   bool     `json:"global,omitempty"`
}

// PolicySchedule defines when a policy is active
type PolicySchedule struct {
	StartTime    *time.Time `json:"start_time,omitempty"`
	EndTime      *time.Time `json:"end_time,omitempty"`
	DaysOfWeek   []int      `json:"days_of_week,omitempty"`
	HoursOfDay   []int      `json:"hours_of_day,omitempty"`
	Timezone     string     `json:"timezone,omitempty"`
	Recurring    bool       `json:"recurring,omitempty"`
}

// FilteringRule represents a tool filtering rule
type FilteringRule struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Enabled     bool                   `json:"enabled"`
	ToolPattern string                 `json:"tool_pattern"`
	Conditions  []FilterCondition      `json:"conditions"`
	Action      FilterAction           `json:"action"`
	Confidence  float64                `json:"confidence"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

// FilterCondition represents a condition in a filtering rule
type FilterCondition struct {
	Type      string      `json:"type"`
	Field     string      `json:"field"`
	Operator  string      `json:"operator"`
	Value     interface{} `json:"value"`
	Weight    float64     `json:"weight"`
}

// FilterAction represents the action to take when a filter rule matches
type FilterAction struct {
	Type        string                 `json:"type"`
	Severity    string                 `json:"severity"`
	Message     string                 `json:"message"`
	Parameters  map[string]interface{} `json:"parameters"`
	Escalate    bool                   `json:"escalate,omitempty"`
}
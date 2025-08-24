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
	"github.com/gorilla/websocket"
	
	"github.com/claude-guardian/mcp-service/internal/config"
	"github.com/claude-guardian/mcp-service/internal/handlers"
	"github.com/claude-guardian/mcp-service/internal/middleware"
	"github.com/claude-guardian/mcp-service/internal/mcp"
	"github.com/claude-guardian/mcp-service/internal/security"
	"github.com/claude-guardian/mcp-service/internal/services"
)

// MCP Service - Model Context Protocol integration for Claude Code
// Provides secure MCP server with threat analysis and tool management
func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize services
	authService := services.NewAuthService(cfg.Auth)
	threatAnalyzer := services.NewThreatAnalyzer(cfg.ThreatAnalysis)
	toolRegistry := services.NewToolRegistry(cfg.Tools)
	resourceManager := services.NewResourceManager(cfg.Resources)
	auditService := services.NewAuditService(cfg.Audit)
	securityGuard := security.NewSecurityGuard(threatAnalyzer, auditService)

	// Initialize MCP server
	mcpServer := mcp.NewServer(&mcp.ServerConfig{
		Name:        "claude-guardian",
		Version:     "1.0.0",
		Description: "Claude Guardian Security MCP Server",
		Capabilities: mcp.ServerCapabilities{
			Tools:         &mcp.ToolsCapability{ListChanged: true},
			Resources:     &mcp.ResourcesCapability{Subscribe: true, ListChanged: true},
			Prompts:       &mcp.PromptsCapability{ListChanged: true},
			Logging:       &mcp.LoggingCapability{},
		},
	})

	// Register MCP handlers
	registerMCPHandlers(mcpServer, toolRegistry, resourceManager, securityGuard, auditService)

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
	router.Use(middleware.Audit(auditService))

	// Health check endpoints
	router.GET("/health", handlers.HealthCheck)
	router.GET("/health/ready", func(c *gin.Context) {
		status := map[string]interface{}{
			"status": "ready",
			"mcp_server": "running",
			"threat_analyzer": threatAnalyzer.Status(),
			"tool_registry": len(toolRegistry.GetTools()),
			"resources": len(resourceManager.GetResources()),
		}
		c.JSON(http.StatusOK, status)
	})

	// MCP protocol endpoints
	v1 := router.Group("/api/v1")
	{
		// MCP WebSocket endpoint for Claude Code integration
		v1.GET("/mcp", func(c *gin.Context) {
			handleMCPWebSocket(c, mcpServer, authService, securityGuard)
		})

		// REST endpoints for MCP management
		mcp := v1.Group("/mcp")
		mcp.Use(middleware.RequireAuth(authService))
		{
			// Tool management
			mcp.GET("/tools", handlers.ListTools(toolRegistry))
			mcp.POST("/tools", handlers.RegisterTool(toolRegistry, securityGuard))
			mcp.PUT("/tools/:name", handlers.UpdateTool(toolRegistry, securityGuard))
			mcp.DELETE("/tools/:name", handlers.UnregisterTool(toolRegistry))
			mcp.POST("/tools/:name/execute", handlers.ExecuteTool(toolRegistry, securityGuard, auditService))

			// Resource management
			mcp.GET("/resources", handlers.ListResources(resourceManager))
			mcp.GET("/resources/read", handlers.ReadResource(resourceManager, securityGuard))
			mcp.POST("/resources/subscribe", handlers.SubscribeResource(resourceManager))

			// Security management
			mcp.GET("/security/policies", handlers.GetSecurityPolicies(securityGuard))
			mcp.PUT("/security/policies/:name", handlers.UpdateSecurityPolicy(securityGuard))
			mcp.GET("/security/threats", handlers.GetThreats(threatAnalyzer))
			mcp.POST("/security/analyze", handlers.AnalyzeThreat(threatAnalyzer))
		}

		// Administration endpoints
		admin := v1.Group("/admin")
		admin.Use(middleware.RequireAuth(authService))
		admin.Use(middleware.RequireRole("admin"))
		{
			admin.GET("/audit-logs", handlers.GetAuditLogs(auditService))
			admin.GET("/metrics", handlers.GetMetrics(mcpServer, threatAnalyzer))
			admin.POST("/tools/bulk-update", handlers.BulkUpdateTools(toolRegistry))
			admin.POST("/security/retrain", handlers.RetrainThreatModel(threatAnalyzer))
		}
	}

	// Prometheus metrics endpoint
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

	go threatAnalyzer.StartBackgroundAnalysis(ctx)
	go toolRegistry.StartToolMonitoring(ctx)
	go resourceManager.StartResourceWatching(ctx)

	// Start server in goroutine
	go func() {
		log.Printf("Starting MCP Service on port %d", cfg.Port)
		log.Printf("MCP WebSocket endpoint: ws://localhost:%d/api/v1/mcp", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down MCP Service...")

	// Cancel background processing
	cancel()

	// Graceful shutdown with timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("MCP Service forced to shutdown: %v", err)
	}

	log.Println("MCP Service shutdown completed")
}

// WebSocket upgrader for MCP connections
var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		// TODO: Implement proper origin checking in production
		return true
	},
}

// handleMCPWebSocket handles MCP protocol WebSocket connections
func handleMCPWebSocket(c *gin.Context, mcpServer *mcp.Server, authService *services.AuthService, securityGuard *security.SecurityGuard) {
	// Authenticate the connection
	token := c.Query("token")
	if token == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Authentication token required"})
		return
	}

	user, err := authService.ValidateToken(token)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid authentication token"})
		return
	}

	// Upgrade to WebSocket
	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		log.Printf("Failed to upgrade WebSocket connection: %v", err)
		return
	}
	defer conn.Close()

	log.Printf("MCP WebSocket connection established for user: %s", user.Username)

	// Create MCP session
	session := &mcp.Session{
		ID:            generateSessionID(),
		UserID:        user.ID,
		User:          user,
		Connection:    conn,
		SecurityGuard: securityGuard,
		CreatedAt:     time.Now(),
	}

	// Handle MCP protocol messages
	mcpServer.HandleSession(c.Request.Context(), session)
}

// registerMCPHandlers registers all MCP protocol message handlers
func registerMCPHandlers(mcpServer *mcp.Server, toolRegistry *services.ToolRegistry, resourceManager *services.ResourceManager, securityGuard *security.SecurityGuard, auditService *services.AuditService) {
	
	// Initialize handler
	mcpServer.HandleInitialize(func(ctx context.Context, session *mcp.Session, params *mcp.InitializeParams) (*mcp.InitializeResult, error) {
		log.Printf("MCP Initialize request from client: %s", params.ClientInfo.Name)
		
		return &mcp.InitializeResult{
			ProtocolVersion: "2024-11-05",
			ServerInfo: mcp.ServerInfo{
				Name:    "claude-guardian",
				Version: "1.0.0",
			},
			Capabilities: mcpServer.Config.Capabilities,
		}, nil
	})

	// Tools list handler
	mcpServer.HandleToolsList(func(ctx context.Context, session *mcp.Session, params *mcp.ToolsListParams) (*mcp.ToolsListResult, error) {
		tools := toolRegistry.GetToolsForUser(session.UserID)
		
		mcpTools := make([]mcp.Tool, len(tools))
		for i, tool := range tools {
			mcpTools[i] = mcp.Tool{
				Name:        tool.Name,
				Description: tool.Description,
				InputSchema: tool.InputSchema,
			}
		}

		return &mcp.ToolsListResult{
			Tools: mcpTools,
		}, nil
	})

	// Tool call handler with security analysis
	mcpServer.HandleToolCall(func(ctx context.Context, session *mcp.Session, params *mcp.ToolCallParams) (*mcp.ToolCallResult, error) {
		// Security analysis before execution
		threat, err := securityGuard.AnalyzeToolCall(session.UserID, params.Name, params.Arguments)
		if err != nil {
			return nil, fmt.Errorf("security analysis failed: %w", err)
		}

		// Block high-risk operations
		if threat.RiskLevel == "high" || threat.RiskLevel == "critical" {
			auditService.LogSecurityEvent(session.UserID, "tool_call_blocked", map[string]interface{}{
				"tool": params.Name,
				"risk_level": threat.RiskLevel,
				"reason": threat.Reason,
			})
			
			return &mcp.ToolCallResult{
				Content: []mcp.Content{{
					Type: "text",
					Text: fmt.Sprintf("Tool execution blocked due to security risk: %s", threat.Reason),
				}},
				IsError: true,
			}, nil
		}

		// Execute the tool
		tool, exists := toolRegistry.GetTool(params.Name)
		if !exists {
			return nil, fmt.Errorf("tool not found: %s", params.Name)
		}

		result, err := tool.Execute(ctx, session.UserID, params.Arguments)
		if err != nil {
			auditService.LogToolExecution(session.UserID, params.Name, params.Arguments, nil, err)
			return &mcp.ToolCallResult{
				Content: []mcp.Content{{
					Type: "text",
					Text: fmt.Sprintf("Tool execution failed: %v", err),
				}},
				IsError: true,
			}, nil
		}

		// Log successful execution
		auditService.LogToolExecution(session.UserID, params.Name, params.Arguments, result, nil)

		return &mcp.ToolCallResult{
			Content: []mcp.Content{{
				Type: "text",
				Text: fmt.Sprintf("Tool executed successfully: %v", result),
			}},
			IsError: false,
		}, nil
	})

	// Resources list handler
	mcpServer.HandleResourcesList(func(ctx context.Context, session *mcp.Session, params *mcp.ResourcesListParams) (*mcp.ResourcesListResult, error) {
		resources := resourceManager.GetResourcesForUser(session.UserID)
		
		mcpResources := make([]mcp.Resource, len(resources))
		for i, resource := range resources {
			mcpResources[i] = mcp.Resource{
				URI:         resource.URI,
				Name:        resource.Name,
				Description: resource.Description,
				MimeType:    resource.MimeType,
			}
		}

		return &mcp.ResourcesListResult{
			Resources: mcpResources,
		}, nil
	})

	// Resource read handler with security checks
	mcpServer.HandleResourceRead(func(ctx context.Context, session *mcp.Session, params *mcp.ResourceReadParams) (*mcp.ResourceReadResult, error) {
		// Security check for resource access
		allowed, err := securityGuard.CheckResourceAccess(session.UserID, params.URI)
		if err != nil {
			return nil, fmt.Errorf("security check failed: %w", err)
		}

		if !allowed {
			auditService.LogSecurityEvent(session.UserID, "resource_access_denied", map[string]interface{}{
				"resource": params.URI,
			})
			
			return nil, fmt.Errorf("access denied to resource: %s", params.URI)
		}

		// Read the resource
		content, err := resourceManager.ReadResource(params.URI)
		if err != nil {
			return nil, fmt.Errorf("failed to read resource: %w", err)
		}

		auditService.LogResourceAccess(session.UserID, params.URI, "read", true)

		return &mcp.ResourceReadResult{
			Contents: []mcp.ResourceContent{{
				URI:      params.URI,
				MimeType: content.MimeType,
				Text:     content.Text,
			}},
		}, nil
	})

	// Logging handler
	mcpServer.HandleLogging(func(ctx context.Context, session *mcp.Session, params *mcp.LoggingParams) error {
		auditService.LogMCPMessage(session.UserID, params.Level, params.Data)
		return nil
	})
}

// generateSessionID generates a unique session ID
func generateSessionID() string {
	return fmt.Sprintf("session_%d", time.Now().UnixNano())
}
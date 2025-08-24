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
	"github.com/iff-guardian/auth-service/internal/config"
	"github.com/iff-guardian/auth-service/internal/handlers"
	"github.com/iff-guardian/auth-service/internal/middleware"
	"github.com/iff-guardian/auth-service/internal/services"
)

// Authentication Service - JWT-based authentication with RBAC
// Handles user authentication, authorization, and session management
func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize services
	dbService := services.NewDatabaseService(cfg.Database)
	redisService := services.NewRedisService(cfg.Redis)
	authService := services.NewAuthService(cfg.Auth, dbService, redisService)
	rbacService := services.NewRBACService(dbService)
	auditService := services.NewAuditService(cfg.Audit, dbService)

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
	router.Use(middleware.AuditLog(auditService))

	// Health check endpoints
	router.GET("/health", handlers.HealthCheck)
	router.GET("/health/ready", func(c *gin.Context) {
		status := map[string]string{
			"status": "ready",
			"database": dbService.HealthCheck(),
			"redis": redisService.HealthCheck(),
		}
		c.JSON(http.StatusOK, status)
	})

	// API versioning
	v1 := router.Group("/api/v1")
	{
		// Authentication endpoints
		auth := v1.Group("/auth")
		{
			auth.POST("/register", handlers.Register(authService))
			auth.POST("/login", handlers.Login(authService))
			auth.POST("/refresh", handlers.RefreshToken(authService))
			auth.POST("/logout", middleware.RequireAuth(authService), handlers.Logout(authService))
			auth.POST("/forgot-password", handlers.ForgotPassword(authService))
			auth.POST("/reset-password", handlers.ResetPassword(authService))
			
			// MFA endpoints
			mfa := auth.Group("/mfa")
			mfa.POST("/setup", middleware.RequireAuth(authService), handlers.SetupMFA(authService))
			mfa.POST("/verify", handlers.VerifyMFA(authService))
			mfa.POST("/disable", middleware.RequireAuth(authService), handlers.DisableMFA(authService))
		}

		// User management endpoints
		users := v1.Group("/users")
		users.Use(middleware.RequireAuth(authService))
		{
			users.GET("/profile", handlers.GetProfile(authService))
			users.PUT("/profile", handlers.UpdateProfile(authService))
			users.POST("/change-password", handlers.ChangePassword(authService))
			users.GET("/sessions", handlers.GetActiveSessions(authService))
			users.DELETE("/sessions/:id", handlers.RevokeSession(authService))
		}

		// RBAC endpoints
		rbac := v1.Group("/rbac")
		rbac.Use(middleware.RequireAuth(authService))
		rbac.Use(middleware.RequirePermission(rbacService, "rbac:read"))
		{
			rbac.GET("/roles", handlers.GetRoles(rbacService))
			rbac.POST("/roles", middleware.RequirePermission(rbacService, "rbac:write"), handlers.CreateRole(rbacService))
			rbac.GET("/permissions", handlers.GetPermissions(rbacService))
			rbac.POST("/users/:id/roles", middleware.RequirePermission(rbacService, "rbac:write"), handlers.AssignRole(rbacService))
			rbac.DELETE("/users/:id/roles/:role", middleware.RequirePermission(rbacService, "rbac:write"), handlers.RevokeRole(rbacService))
		}

		// Admin endpoints
		admin := v1.Group("/admin")
		admin.Use(middleware.RequireAuth(authService))
		admin.Use(middleware.RequireRole(rbacService, "admin"))
		{
			admin.GET("/users", handlers.ListUsers(authService))
			admin.POST("/users/:id/activate", handlers.ActivateUser(authService))
			admin.POST("/users/:id/deactivate", handlers.DeactivateUser(authService))
			admin.GET("/audit-logs", handlers.GetAuditLogs(auditService))
			admin.GET("/security-events", handlers.GetSecurityEvents(auditService))
		}
	}

	// Token validation endpoint for other services
	router.POST("/validate", handlers.ValidateToken(authService))
	
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

	// Start background token cleanup
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go authService.StartTokenCleanup(ctx)

	// Start server in goroutine
	go func() {
		log.Printf("Starting Authentication Service on port %d", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down Authentication Service...")

	// Cancel background processing
	cancel()

	// Graceful shutdown with timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("Authentication Service forced to shutdown: %v", err)
	}

	log.Println("Authentication Service shutdown completed")
}
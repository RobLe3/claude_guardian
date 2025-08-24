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
	"github.com/iff-guardian/gateway/internal/config"
	"github.com/iff-guardian/gateway/internal/handlers"
	"github.com/iff-guardian/gateway/internal/middleware"
	"github.com/iff-guardian/gateway/internal/services"
)

// Gateway Service - Core API Gateway for IFF-Guardian
// Handles request routing, rate limiting, authentication, and load balancing
func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize services
	authService := services.NewAuthService(cfg.Auth)
	rateLimiter := middleware.NewRateLimiter(cfg.RateLimit)
	
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
	router.Use(rateLimiter.Middleware())

	// Health check endpoint
	router.GET("/health", handlers.HealthCheck)
	router.GET("/health/ready", handlers.ReadinessCheck)
	router.GET("/health/live", handlers.LivenessCheck)

	// API versioning
	v1 := router.Group("/api/v1")
	{
		// Authentication routes
		auth := v1.Group("/auth")
		auth.POST("/login", handlers.Login(authService))
		auth.POST("/refresh", handlers.RefreshToken(authService))
		auth.POST("/logout", middleware.RequireAuth(authService), handlers.Logout(authService))

		// Protected routes
		protected := v1.Group("/")
		protected.Use(middleware.RequireAuth(authService))
		{
			// MCP Protocol endpoints
			mcp := protected.Group("/mcp")
			mcp.POST("/tools/call", handlers.ToolCall)
			mcp.GET("/tools", handlers.ListTools)
			mcp.POST("/resources/read", handlers.ReadResource)

			// Security monitoring endpoints
			security := protected.Group("/security")
			security.GET("/threats", handlers.GetThreats)
			security.POST("/analyze", handlers.AnalyzeThreat)
			security.GET("/events", handlers.GetSecurityEvents)

			// Configuration endpoints
			config := protected.Group("/config")
			config.GET("/policies", handlers.GetPolicies)
			config.PUT("/policies/:id", handlers.UpdatePolicy)
		}
	}

	// GraphQL endpoint (delegated to GraphQL service)
	router.POST("/graphql", middleware.RequireAuth(authService), handlers.GraphQLProxy)
	router.GET("/graphql", handlers.GraphQLPlayground)

	// Create HTTP server
	server := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.Port),
		Handler:      router,
		ReadTimeout:  cfg.Server.ReadTimeout,
		WriteTimeout: cfg.Server.WriteTimeout,
		IdleTimeout:  cfg.Server.IdleTimeout,
	}

	// Start server in goroutine
	go func() {
		log.Printf("Starting Gateway Service on port %d", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down Gateway Service...")

	// Graceful shutdown with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("Gateway Service forced to shutdown: %v", err)
	}

	log.Println("Gateway Service shutdown completed")
}
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

	"github.com/99designs/gqlgen/graphql/handler"
	"github.com/99designs/gqlgen/graphql/handler/extension"
	"github.com/99designs/gqlgen/graphql/handler/lru"
	"github.com/99designs/gqlgen/graphql/handler/transport"
	"github.com/99designs/gqlgen/graphql/playground"
	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
	
	"github.com/iff-guardian/graphql-api/generated"
	"github.com/iff-guardian/graphql-api/internal/config"
	"github.com/iff-guardian/graphql-api/internal/middleware"
	"github.com/iff-guardian/graphql-api/internal/resolvers"
	"github.com/iff-guardian/graphql-api/internal/services"
)

// GraphQL API Service - Unified API for IFF-Guardian
// Provides GraphQL interface with real-time subscriptions
func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize services
	dbService := services.NewDatabaseService(cfg.Database)
	authService := services.NewAuthService(cfg.Auth, dbService)
	threatService := services.NewThreatService(cfg.ThreatDetection)
	mcpService := services.NewMCPService(cfg.MCP)
	metricsService := services.NewMetricsService(cfg.Metrics)

	// Initialize GraphQL resolver
	resolver := &resolvers.Resolver{
		AuthService:    authService,
		ThreatService:  threatService,
		MCPService:     mcpService,
		MetricsService: metricsService,
	}

	// Create GraphQL server
	srv := handler.New(generated.NewExecutableSchema(generated.Config{
		Resolvers: resolver,
	}))

	// Configure GraphQL server
	srv.AddTransport(transport.Websocket{
		KeepAlivePingInterval: 10 * time.Second,
		Upgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				// Configure CORS for WebSocket connections
				return cfg.CORS.AllowOrigin(r.Header.Get("Origin"))
			},
		},
	})
	srv.AddTransport(transport.Options{})
	srv.AddTransport(transport.GET{})
	srv.AddTransport(transport.POST{})
	srv.AddTransport(transport.MultipartForm{})

	// Add extensions
	srv.Use(extension.Introspection{})
	srv.Use(extension.AutomaticPersistedQuery{
		Cache: lru.New(100),
	})

	// Add complexity limiting
	srv.Use(extension.FixedComplexityLimit(300))

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

	// Health check endpoints
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy"})
	})
	
	router.GET("/health/ready", func(c *gin.Context) {
		status := gin.H{
			"status": "ready",
			"database": "connected", // TODO: Implement actual health checks
			"services": gin.H{
				"auth": "ready",
				"threat": "ready",
				"mcp": "ready",
				"metrics": "ready",
			},
		}
		c.JSON(http.StatusOK, status)
	})

	// GraphQL endpoints
	router.POST("/graphql", func(c *gin.Context) {
		// Add authentication context
		ctx := middleware.AddAuthContext(c.Request.Context(), c, authService)
		c.Request = c.Request.WithContext(ctx)
		
		// Add user context if authenticated
		if user := middleware.GetUserFromContext(ctx); user != nil {
			ctx = context.WithValue(ctx, "user", user)
			c.Request = c.Request.WithContext(ctx)
		}
		
		srv.ServeHTTP(c.Writer, c.Request)
	})

	// WebSocket endpoint for subscriptions
	router.GET("/graphql", func(c *gin.Context) {
		// Add authentication context for WebSocket
		ctx := middleware.AddAuthContext(c.Request.Context(), c, authService)
		c.Request = c.Request.WithContext(ctx)
		
		srv.ServeHTTP(c.Writer, c.Request)
	})

	// GraphQL Playground (development only)
	if cfg.Environment == "development" {
		router.GET("/playground", func(c *gin.Context) {
			playground.Handler("GraphQL playground", "/graphql")(c.Writer, c.Request)
		})
	}

	// Schema introspection endpoint
	router.GET("/schema", func(c *gin.Context) {
		schema := generated.NewExecutableSchema(generated.Config{Resolvers: resolver})
		c.Header("Content-Type", "application/graphql")
		c.String(http.StatusOK, schema.Schema().String())
	})

	// Metrics endpoint for Prometheus
	router.GET("/metrics", func(c *gin.Context) {
		// TODO: Implement Prometheus metrics
		c.JSON(http.StatusOK, gin.H{"metrics": "endpoint"})
	})

	// Create HTTP server
	server := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.Port),
		Handler:      router,
		ReadTimeout:  cfg.Server.ReadTimeout,
		WriteTimeout: cfg.Server.WriteTimeout,
		IdleTimeout:  cfg.Server.IdleTimeout,
	}

	// Start subscription manager for real-time updates
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go resolver.StartSubscriptionManager(ctx)

	// Start server in goroutine
	go func() {
		log.Printf("Starting GraphQL API Service on port %d", cfg.Port)
		if cfg.Environment == "development" {
			log.Printf("GraphQL Playground available at http://localhost:%d/playground", cfg.Port)
		}
		log.Printf("GraphQL endpoint available at http://localhost:%d/graphql", cfg.Port)
		
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down GraphQL API Service...")

	// Cancel background processing
	cancel()

	// Graceful shutdown with timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("GraphQL API Service forced to shutdown: %v", err)
	}

	log.Println("GraphQL API Service shutdown completed")
}
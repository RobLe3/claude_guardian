package health

import (
	"context"
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

// Status represents the health status of a component
type Status string

const (
	StatusHealthy   Status = "healthy"
	StatusUnhealthy Status = "unhealthy"
	StatusUnknown   Status = "unknown"
)

// Check represents a health check function
type Check func(ctx context.Context) error

// CheckResult represents the result of a health check
type CheckResult struct {
	Name      string    `json:"name"`
	Status    Status    `json:"status"`
	Error     string    `json:"error,omitempty"`
	Timestamp time.Time `json:"timestamp"`
	Duration  string    `json:"duration"`
}

// HealthResponse represents the overall health response
type HealthResponse struct {
	Status    Status                  `json:"status"`
	Timestamp time.Time               `json:"timestamp"`
	Checks    map[string]CheckResult  `json:"checks"`
	Uptime    string                  `json:"uptime"`
}

// Checker manages health checks
type Checker struct {
	checks   map[string]Check
	mutex    sync.RWMutex
	startTime time.Time
}

// New creates a new health checker
func New() *Checker {
	return &Checker{
		checks:    make(map[string]Check),
		startTime: time.Now(),
	}
}

// AddCheck adds a new health check
func (h *Checker) AddCheck(name string, check Check) {
	h.mutex.Lock()
	defer h.mutex.Unlock()
	h.checks[name] = check
}

// RemoveCheck removes a health check
func (h *Checker) RemoveCheck(name string) {
	h.mutex.Lock()
	defer h.mutex.Unlock()
	delete(h.checks, name)
}

// Check runs all health checks and returns the results
func (h *Checker) Check(ctx context.Context) HealthResponse {
	h.mutex.RLock()
	checks := make(map[string]Check)
	for name, check := range h.checks {
		checks[name] = check
	}
	h.mutex.RUnlock()

	results := make(map[string]CheckResult)
	overallStatus := StatusHealthy
	
	for name, check := range checks {
		result := h.runCheck(ctx, name, check)
		results[name] = result
		
		if result.Status != StatusHealthy {
			overallStatus = StatusUnhealthy
		}
	}

	return HealthResponse{
		Status:    overallStatus,
		Timestamp: time.Now(),
		Checks:    results,
		Uptime:    time.Since(h.startTime).String(),
	}
}

// runCheck runs a single health check
func (h *Checker) runCheck(ctx context.Context, name string, check Check) CheckResult {
	start := time.Now()
	
	// Set timeout for individual check
	checkCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	
	err := check(checkCtx)
	duration := time.Since(start)
	
	result := CheckResult{
		Name:      name,
		Timestamp: time.Now(),
		Duration:  duration.String(),
	}
	
	if err != nil {
		result.Status = StatusUnhealthy
		result.Error = err.Error()
	} else {
		result.Status = StatusHealthy
	}
	
	return result
}

// HandlerFunc returns a Gin handler for health checks
func HandlerFunc(checker *Checker) gin.HandlerFunc {
	return func(c *gin.Context) {
		ctx := c.Request.Context()
		result := checker.Check(ctx)
		
		status := http.StatusOK
		if result.Status != StatusHealthy {
			status = http.StatusServiceUnavailable
		}
		
		c.JSON(status, result)
	}
}

// ReadinessHandlerFunc returns a Gin handler for readiness checks
// This is similar to health but may have different logic
func ReadinessHandlerFunc(checker *Checker) gin.HandlerFunc {
	return func(c *gin.Context) {
		ctx := c.Request.Context()
		result := checker.Check(ctx)
		
		// For readiness, we might be more strict
		status := http.StatusOK
		if result.Status != StatusHealthy {
			status = http.StatusServiceUnavailable
		}
		
		c.JSON(status, map[string]interface{}{
			"status":    result.Status,
			"timestamp": result.Timestamp,
			"ready":     result.Status == StatusHealthy,
		})
	}
}
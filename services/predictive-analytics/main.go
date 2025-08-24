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
	
	"github.com/iff-guardian/predictive-analytics/internal/config"
	"github.com/iff-guardian/predictive-analytics/internal/forecasting"
	"github.com/iff-guardian/predictive-analytics/internal/handlers"
	"github.com/iff-guardian/predictive-analytics/internal/middleware"
	"github.com/iff-guardian/predictive-analytics/internal/models"
	"github.com/iff-guardian/predictive-analytics/internal/services"
)

// Predictive Analytics Engine - Time-series forecasting and threat prediction system
// Provides 24-48 hour threat forecasting, attack trend analysis, and risk score predictions
func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize forecasting services
	timeseriesAnalyzer := forecasting.NewTimeSeriesAnalyzer(cfg.TimeSeries)
	prophetForecaster := forecasting.NewProphetForecaster(cfg.Prophet)
	lstmPredictor := forecasting.NewLSTMPredictor(cfg.LSTM)
	trendAnalyzer := forecasting.NewTrendAnalyzer(cfg.TrendAnalysis)
	seasonalAnalyzer := forecasting.NewSeasonalAnalyzer(cfg.SeasonalAnalysis)

	// Initialize prediction models
	threatPredictor := models.NewThreatPredictor(cfg.ThreatPrediction)
	riskScorePredictor := models.NewRiskScorePredictor(cfg.RiskPrediction)
	attackVolumePredictor := models.NewAttackVolumePredictor(cfg.VolumePrediction)
	anomalyPredictor := models.NewAnomalyPredictor(cfg.AnomalyPrediction)

	// Initialize external services
	dataIngestionService := services.NewDataIngestionService(cfg.DataIngestion)
	historicalDataService := services.NewHistoricalDataService(cfg.HistoricalData)
	alertService := services.NewAlertService(cfg.Alerts)
	reportingService := services.NewReportingService(cfg.Reporting)

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
				"timeseries_analyzer":     timeseriesAnalyzer.Status(),
				"prophet_forecaster":      prophetForecaster.Status(),
				"lstm_predictor":          lstmPredictor.Status(),
				"trend_analyzer":          trendAnalyzer.Status(),
				"seasonal_analyzer":       seasonalAnalyzer.Status(),
				"threat_predictor":        threatPredictor.Status(),
				"risk_score_predictor":    riskScorePredictor.Status(),
				"attack_volume_predictor": attackVolumePredictor.Status(),
				"data_ingestion":          dataIngestionService.Status(),
			},
			"prediction_models": map[string]interface{}{
				"active_models":        threatPredictor.GetActiveModels(),
				"prediction_accuracy":  threatPredictor.GetAccuracyMetrics(),
				"last_training":        threatPredictor.GetLastTrainingTime(),
				"predictions_generated": threatPredictor.GetPredictionCount(),
			},
		}
		c.JSON(http.StatusOK, status)
	})

	// API versioning
	v1 := router.Group("/api/v1")
	v1.Use(middleware.RequireAuth(cfg.Auth))
	{
		// Threat prediction endpoints
		predictions := v1.Group("/predictions")
		{
			predictions.POST("/threats", handlers.PredictThreats(threatPredictor))
			predictions.POST("/risks", handlers.PredictRiskScores(riskScorePredictor))
			predictions.POST("/volume", handlers.PredictAttackVolume(attackVolumePredictor))
			predictions.POST("/anomalies", handlers.PredictAnomalies(anomalyPredictor))
			predictions.GET("/active", handlers.GetActivePredictions(threatPredictor))
			predictions.GET("/history", handlers.GetPredictionHistory(threatPredictor))
			predictions.POST("/validate", handlers.ValidatePredictions(threatPredictor))
		}

		// Time-series forecasting
		forecasting := v1.Group("/forecasting")
		{
			forecasting.POST("/timeseries", handlers.ForecastTimeSeries(timeseriesAnalyzer))
			forecasting.POST("/prophet", handlers.ForecastWithProphet(prophetForecaster))
			forecasting.POST("/lstm", handlers.ForecastWithLSTM(lstmPredictor))
			forecasting.GET("/models", handlers.GetForecastingModels(timeseriesAnalyzer))
			forecasting.POST("/models/retrain", handlers.RetrainForecastingModels(timeseriesAnalyzer))
			forecasting.GET("/accuracy", handlers.GetForecastingAccuracy(timeseriesAnalyzer))
		}

		// Trend analysis
		trends := v1.Group("/trends")
		{
			trends.POST("/analyze", handlers.AnalyzeTrends(trendAnalyzer))
			trends.GET("/threat-types", handlers.GetThreatTypeTrends(trendAnalyzer))
			trends.GET("/attack-vectors", handlers.GetAttackVectorTrends(trendAnalyzer))
			trends.GET("/geographical", handlers.GetGeographicalTrends(trendAnalyzer))
			trends.GET("/temporal", handlers.GetTemporalTrends(trendAnalyzer))
			trends.POST("/correlations", handlers.FindTrendCorrelations(trendAnalyzer))
		}

		// Seasonal analysis
		seasonal := v1.Group("/seasonal")
		{
			seasonal.POST("/analyze", handlers.AnalyzeSeasonalPatterns(seasonalAnalyzer))
			seasonal.GET("/patterns", handlers.GetSeasonalPatterns(seasonalAnalyzer))
			seasonal.POST("/predictions", handlers.PredictSeasonalThreats(seasonalAnalyzer))
			seasonal.GET("/calendar", handlers.GetThreatCalendar(seasonalAnalyzer))
		}

		// Data ingestion and processing
		data := v1.Group("/data")
		{
			data.POST("/ingest", handlers.IngestData(dataIngestionService))
			data.GET("/sources", handlers.GetDataSources(dataIngestionService))
			data.POST("/sources", handlers.CreateDataSource(dataIngestionService))
			data.PUT("/sources/:id", handlers.UpdateDataSource(dataIngestionService))
			data.DELETE("/sources/:id", handlers.DeleteDataSource(dataIngestionService))
			data.GET("/quality", handlers.GetDataQuality(dataIngestionService))
		}

		// Historical data analysis
		historical := v1.Group("/historical")
		{
			historical.GET("/threats", handlers.GetHistoricalThreats(historicalDataService))
			historical.GET("/patterns", handlers.GetHistoricalPatterns(historicalDataService))
			historical.POST("/compare", handlers.CompareHistoricalPeriods(historicalDataService))
			historical.GET("/baselines", handlers.GetHistoricalBaselines(historicalDataService))
			historical.POST("/analyze", handlers.AnalyzeHistoricalData(historicalDataService))
		}

		// Predictive alerts and notifications
		alerts := v1.Group("/alerts")
		{
			alerts.POST("/", handlers.CreatePredictiveAlert(alertService))
			alerts.GET("/", handlers.GetPredictiveAlerts(alertService))
			alerts.GET("/:id", handlers.GetPredictiveAlert(alertService))
			alerts.PUT("/:id", handlers.UpdatePredictiveAlert(alertService))
			alerts.DELETE("/:id", handlers.DeletePredictiveAlert(alertService))
			alerts.POST("/:id/acknowledge", handlers.AcknowledgePredictiveAlert(alertService))
		}

		// Reporting and dashboards
		reports := v1.Group("/reports")
		{
			reports.GET("/forecast", handlers.GenerateForecastReport(reportingService))
			reports.GET("/trends", handlers.GenerateTrendReport(reportingService))
			reports.GET("/accuracy", handlers.GenerateAccuracyReport(reportingService))
			reports.POST("/custom", handlers.GenerateCustomReport(reportingService))
			reports.GET("/scheduled", handlers.GetScheduledReports(reportingService))
			reports.POST("/schedule", handlers.ScheduleReport(reportingService))
		}

		// Model management and training
		models := v1.Group("/models")
		{
			models.GET("/", handlers.GetPredictionModels(threatPredictor))
			models.POST("/train", handlers.TrainPredictionModel(threatPredictor))
			models.POST("/:id/retrain", handlers.RetrainPredictionModel(threatPredictor))
			models.GET("/:id/performance", handlers.GetModelPerformance(threatPredictor))
			models.POST("/:id/deploy", handlers.DeployPredictionModel(threatPredictor))
			models.DELETE("/:id", handlers.DeletePredictionModel(threatPredictor))
			models.GET("/comparison", handlers.CompareModelPerformance(threatPredictor))
		}

		// Configuration and settings
		config := v1.Group("/config")
		{
			config.GET("/prediction-settings", handlers.GetPredictionSettings(threatPredictor))
			config.PUT("/prediction-settings", handlers.UpdatePredictionSettings(threatPredictor))
			config.GET("/thresholds", handlers.GetPredictionThresholds(threatPredictor))
			config.PUT("/thresholds", handlers.UpdatePredictionThresholds(threatPredictor))
		}
	}

	// Real-time streaming endpoints for predictions
	streaming := router.Group("/stream")
	streaming.Use(middleware.RequireAuth(cfg.Auth))
	{
		streaming.GET("/predictions", handlers.StreamPredictions(threatPredictor))
		streaming.GET("/forecasts", handlers.StreamForecasts(timeseriesAnalyzer))
		streaming.GET("/alerts", handlers.StreamPredictiveAlerts(alertService))
		streaming.GET("/trends", handlers.StreamTrendUpdates(trendAnalyzer))
	}

	// Admin endpoints for system management
	admin := v1.Group("/admin")
	admin.Use(middleware.RequireRole("admin"))
	{
		admin.GET("/stats", handlers.GetPredictiveAnalyticsStats(threatPredictor, timeseriesAnalyzer))
		admin.POST("/maintenance", handlers.EnableMaintenanceMode(threatPredictor))
		admin.DELETE("/maintenance", handlers.DisableMaintenanceMode(threatPredictor))
		admin.POST("/models/bulk-retrain", handlers.BulkRetrainModels(threatPredictor))
		admin.GET("/performance", handlers.GetSystemPerformanceMetrics(threatPredictor))
		admin.POST("/data/cleanup", handlers.CleanupHistoricalData(historicalDataService))
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

	go timeseriesAnalyzer.StartContinuousAnalysis(ctx)
	go threatPredictor.StartPredictionEngine(ctx)
	go riskScorePredictor.StartRiskPrediction(ctx)
	go trendAnalyzer.StartTrendMonitoring(ctx)
	go seasonalAnalyzer.StartSeasonalAnalysis(ctx)
	go dataIngestionService.StartDataProcessing(ctx)
	go reportingService.StartScheduledReporting(ctx)

	// Start server in goroutine
	go func() {
		log.Printf("Starting Predictive Analytics Engine on port %d", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down Predictive Analytics Engine...")

	// Cancel background processing
	cancel()

	// Graceful shutdown with timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("Predictive Analytics Engine forced to shutdown: %v", err)
	}

	log.Println("Predictive Analytics Engine shutdown completed")
}

// ThreatPrediction represents a predicted threat event
type ThreatPrediction struct {
	ID              string                 `json:"id"`
	ThreatType      string                 `json:"threat_type"`
	ThreatName      string                 `json:"threat_name"`
	Description     string                 `json:"description"`
	Severity        string                 `json:"severity"`
	Probability     float64                `json:"probability"`
	Confidence      float64                `json:"confidence"`
	TimeFrame       PredictionTimeFrame    `json:"time_frame"`
	PredictedAt     time.Time              `json:"predicted_at"`
	PredictedFor    time.Time              `json:"predicted_for"`
	ExpiresAt       time.Time              `json:"expires_at"`
	Model           string                 `json:"model"`
	ModelVersion    string                 `json:"model_version"`
	Features        map[string]interface{} `json:"features"`
	Indicators      []PredictiveIndicator  `json:"indicators"`
	AffectedAssets  []string               `json:"affected_assets"`
	AttackVectors   []string               `json:"attack_vectors"`
	MITRETechniques []string               `json:"mitre_techniques"`
	RiskScore       float64                `json:"risk_score"`
	ImpactScore     float64                `json:"impact_score"`
	Mitigation      []string               `json:"mitigation"`
	Status          PredictionStatus       `json:"status"`
	ValidationData  *PredictionValidation  `json:"validation_data,omitempty"`
	Metadata        map[string]interface{} `json:"metadata"`
}

// PredictionTimeFrame represents the time frame for a prediction
type PredictionTimeFrame struct {
	Duration    time.Duration `json:"duration"`
	StartTime   time.Time     `json:"start_time"`
	EndTime     time.Time     `json:"end_time"`
	Description string        `json:"description"`
}

// PredictionStatus represents the status of a threat prediction
type PredictionStatus string

const (
	PredictionStatusActive    PredictionStatus = "active"
	PredictionStatusValidated PredictionStatus = "validated"
	PredictionStatusFailed    PredictionStatus = "failed"
	PredictionStatusExpired   PredictionStatus = "expired"
	PredictionStatusCancelled PredictionStatus = "cancelled"
)

// PredictiveIndicator represents an indicator used for threat prediction
type PredictiveIndicator struct {
	Type        string                 `json:"type"`
	Value       interface{}            `json:"value"`
	Weight      float64                `json:"weight"`
	Confidence  float64                `json:"confidence"`
	Description string                 `json:"description"`
	Source      string                 `json:"source"`
	Context     map[string]interface{} `json:"context"`
}

// PredictionValidation represents validation data for a prediction
type PredictionValidation struct {
	Validated     bool      `json:"validated"`
	ValidatedAt   time.Time `json:"validated_at"`
	ValidatedBy   string    `json:"validated_by"`
	ActualOutcome string    `json:"actual_outcome"`
	Accuracy      float64   `json:"accuracy"`
	Notes         string    `json:"notes"`
}

// ForecastResult represents the result of a time-series forecast
type ForecastResult struct {
	ID               string                 `json:"id"`
	Metric           string                 `json:"metric"`
	Algorithm        string                 `json:"algorithm"`
	TimeRange        TimeRange              `json:"time_range"`
	ForecastPeriod   time.Duration          `json:"forecast_period"`
	DataPoints       []DataPoint            `json:"data_points"`
	ForecastPoints   []ForecastPoint        `json:"forecast_points"`
	Accuracy         float64                `json:"accuracy"`
	ConfidenceLevel  float64                `json:"confidence_level"`
	Seasonality      *SeasonalityInfo       `json:"seasonality,omitempty"`
	Trend            *TrendInfo             `json:"trend,omitempty"`
	AnomaliesDetected []AnomalyPoint        `json:"anomalies_detected"`
	ModelParameters  map[string]interface{} `json:"model_parameters"`
	GeneratedAt      time.Time              `json:"generated_at"`
	Metadata         map[string]interface{} `json:"metadata"`
}

// TimeRange represents a time range for analysis
type TimeRange struct {
	StartTime time.Time `json:"start_time"`
	EndTime   time.Time `json:"end_time"`
	Duration  time.Duration `json:"duration"`
}

// DataPoint represents a historical data point
type DataPoint struct {
	Timestamp time.Time   `json:"timestamp"`
	Value     float64     `json:"value"`
	Label     string      `json:"label,omitempty"`
	Metadata  interface{} `json:"metadata,omitempty"`
}

// ForecastPoint represents a forecasted data point
type ForecastPoint struct {
	Timestamp        time.Time `json:"timestamp"`
	Value            float64   `json:"value"`
	UpperBound       float64   `json:"upper_bound"`
	LowerBound       float64   `json:"lower_bound"`
	Confidence       float64   `json:"confidence"`
	TrendComponent   float64   `json:"trend_component"`
	SeasonalComponent float64  `json:"seasonal_component"`
}

// SeasonalityInfo represents seasonality information in forecasts
type SeasonalityInfo struct {
	Present       bool                   `json:"present"`
	Period        time.Duration          `json:"period"`
	Strength      float64                `json:"strength"`
	Patterns      map[string]interface{} `json:"patterns"`
}

// TrendInfo represents trend information in forecasts
type TrendInfo struct {
	Direction   string  `json:"direction"`
	Strength    float64 `json:"strength"`
	Slope       float64 `json:"slope"`
	Changepoints []time.Time `json:"changepoints"`
}

// AnomalyPoint represents an anomalous data point
type AnomalyPoint struct {
	Timestamp    time.Time `json:"timestamp"`
	Value        float64   `json:"value"`
	ExpectedValue float64  `json:"expected_value"`
	AnomalyScore float64   `json:"anomaly_score"`
	Severity     string    `json:"severity"`
}

// TrendAnalysis represents trend analysis results
type TrendAnalysis struct {
	ID              string                 `json:"id"`
	Metric          string                 `json:"metric"`
	TimeRange       TimeRange              `json:"time_range"`
	TrendDirection  string                 `json:"trend_direction"`
	TrendStrength   float64                `json:"trend_strength"`
	TrendSlope      float64                `json:"trend_slope"`
	ChangePoints    []ChangePoint          `json:"change_points"`
	Correlations    []TrendCorrelation     `json:"correlations"`
	Significance    float64                `json:"significance"`
	Confidence      float64                `json:"confidence"`
	Predictions     []TrendPrediction      `json:"predictions"`
	Insights        []string               `json:"insights"`
	GeneratedAt     time.Time              `json:"generated_at"`
	Metadata        map[string]interface{} `json:"metadata"`
}

// ChangePoint represents a significant change in trend
type ChangePoint struct {
	Timestamp    time.Time `json:"timestamp"`
	OldTrend     float64   `json:"old_trend"`
	NewTrend     float64   `json:"new_trend"`
	Significance float64   `json:"significance"`
	Confidence   float64   `json:"confidence"`
	Context      string    `json:"context"`
}

// TrendCorrelation represents correlation between trends
type TrendCorrelation struct {
	Metric       string  `json:"metric"`
	Correlation  float64 `json:"correlation"`
	Significance float64 `json:"significance"`
	LagPeriod    time.Duration `json:"lag_period"`
}

// TrendPrediction represents a prediction based on trend analysis
type TrendPrediction struct {
	Timestamp   time.Time `json:"timestamp"`
	Value       float64   `json:"value"`
	Confidence  float64   `json:"confidence"`
	Bounds      [2]float64 `json:"bounds"`
}

// SeasonalPattern represents a seasonal pattern in threat data
type SeasonalPattern struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	Description  string                 `json:"description"`
	Pattern      string                 `json:"pattern"`
	Period       time.Duration          `json:"period"`
	Strength     float64                `json:"strength"`
	Peaks        []SeasonalPeak         `json:"peaks"`
	Troughs      []SeasonalTrough       `json:"troughs"`
	Confidence   float64                `json:"confidence"`
	ThreatTypes  []string               `json:"threat_types"`
	Metadata     map[string]interface{} `json:"metadata"`
	DetectedAt   time.Time              `json:"detected_at"`
}

// SeasonalPeak represents a peak in seasonal pattern
type SeasonalPeak struct {
	Period      string    `json:"period"`
	Value       float64   `json:"value"`
	Timestamp   time.Time `json:"timestamp"`
	Duration    time.Duration `json:"duration"`
	Confidence  float64   `json:"confidence"`
}

// SeasonalTrough represents a trough in seasonal pattern
type SeasonalTrough struct {
	Period      string    `json:"period"`
	Value       float64   `json:"value"`
	Timestamp   time.Time `json:"timestamp"`
	Duration    time.Duration `json:"duration"`
	Confidence  float64   `json:"confidence"`
}

// PredictiveAlert represents an alert generated from predictions
type PredictiveAlert struct {
	ID               string                 `json:"id"`
	PredictionID     string                 `json:"prediction_id"`
	AlertType        string                 `json:"alert_type"`
	Title            string                 `json:"title"`
	Description      string                 `json:"description"`
	Severity         string                 `json:"severity"`
	Priority         string                 `json:"priority"`
	Probability      float64                `json:"probability"`
	Confidence       float64                `json:"confidence"`
	TimeFrame        PredictionTimeFrame    `json:"time_frame"`
	RecommendedActions []string             `json:"recommended_actions"`
	AffectedAssets   []string               `json:"affected_assets"`
	Status           string                 `json:"status"`
	CreatedAt        time.Time              `json:"created_at"`
	AcknowledgedAt   *time.Time             `json:"acknowledged_at,omitempty"`
	AcknowledgedBy   *string                `json:"acknowledged_by,omitempty"`
	ResolvedAt       *time.Time             `json:"resolved_at,omitempty"`
	Metadata         map[string]interface{} `json:"metadata"`
}

// ModelPerformance represents performance metrics for prediction models
type ModelPerformance struct {
	ModelID         string                 `json:"model_id"`
	ModelName       string                 `json:"model_name"`
	ModelType       string                 `json:"model_type"`
	Algorithm       string                 `json:"algorithm"`
	TrainingPeriod  TimeRange              `json:"training_period"`
	TestingPeriod   TimeRange              `json:"testing_period"`
	Accuracy        float64                `json:"accuracy"`
	Precision       float64                `json:"precision"`
	Recall          float64                `json:"recall"`
	F1Score         float64                `json:"f1_score"`
	AUC             float64                `json:"auc"`
	MAE             float64                `json:"mae"`
	RMSE            float64                `json:"rmse"`
	MAPE            float64                `json:"mape"`
	ConfusionMatrix [][]int                `json:"confusion_matrix"`
	FeatureImportance map[string]float64   `json:"feature_importance"`
	PredictionCount int64                  `json:"prediction_count"`
	LastEvaluated   time.Time              `json:"last_evaluated"`
	Metadata        map[string]interface{} `json:"metadata"`
}

// DataSource represents a data source for predictive analytics
type DataSource struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	Type         string                 `json:"type"`
	Description  string                 `json:"description"`
	URL          string                 `json:"url"`
	Format       string                 `json:"format"`
	UpdateFreq   time.Duration          `json:"update_frequency"`
	LastUpdated  *time.Time             `json:"last_updated,omitempty"`
	Status       string                 `json:"status"`
	Quality      DataQuality            `json:"quality"`
	Schema       map[string]interface{} `json:"schema"`
	Credentials  map[string]interface{} `json:"credentials,omitempty"`
	CreatedAt    time.Time              `json:"created_at"`
	UpdatedAt    time.Time              `json:"updated_at"`
	Metadata     map[string]interface{} `json:"metadata"`
}

// DataQuality represents quality metrics for a data source
type DataQuality struct {
	Score           float64   `json:"score"`
	Completeness    float64   `json:"completeness"`
	Accuracy        float64   `json:"accuracy"`
	Consistency     float64   `json:"consistency"`
	Timeliness      float64   `json:"timeliness"`
	LastAssessed    time.Time `json:"last_assessed"`
	Issues          []string  `json:"issues"`
	Recommendations []string  `json:"recommendations"`
}
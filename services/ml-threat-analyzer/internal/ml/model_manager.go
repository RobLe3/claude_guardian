package ml

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"path/filepath"
	"sync"
	"time"

	"github.com/iff-guardian/ml-threat-analyzer/internal/config"
	"github.com/iff-guardian/ml-threat-analyzer/internal/models"
)

// ModelManager manages ML models for threat detection
type ModelManager struct {
	config       *config.MLConfig
	models       map[string]*MLModel
	modelsMutex  sync.RWMutex
	trainingJobs map[string]*TrainingJob
	jobsMutex    sync.RWMutex
	metrics      *ModelMetrics
}

// MLModel represents a loaded ML model
type MLModel struct {
	Name            string                 `json:"name"`
	Type            string                 `json:"type"`
	Version         string                 `json:"version"`
	ModelPath       string                 `json:"model_path"`
	ConfigPath      string                 `json:"config_path"`
	LoadedAt        time.Time              `json:"loaded_at"`
	LastPrediction  time.Time              `json:"last_prediction"`
	PredictionCount int64                  `json:"prediction_count"`
	Accuracy        float64                `json:"accuracy"`
	Status          string                 `json:"status"`
	Metadata        map[string]interface{} `json:"metadata"`
	predictor       ModelPredictor         `json:"-"`
}

// ModelPredictor interface for different model types
type ModelPredictor interface {
	Predict(features []float64) (*PredictionResult, error)
	PredictProba(features []float64) ([]float64, error)
	GetFeatureNames() []string
	GetModelInfo() map[string]interface{}
	UpdateModel(data []TrainingExample) error
}

// PredictionResult represents the result of a model prediction
type PredictionResult struct {
	Prediction   interface{}            `json:"prediction"`
	Probabilities []float64             `json:"probabilities"`
	Confidence   float64                `json:"confidence"`
	Features     []string               `json:"features"`
	ModelName    string                 `json:"model_name"`
	Metadata     map[string]interface{} `json:"metadata"`
	TimestampMs  int64                  `json:"timestamp_ms"`
}

// TrainingJob represents an active model training job
type TrainingJob struct {
	ID          string                 `json:"id"`
	ModelName   string                 `json:"model_name"`
	Status      string                 `json:"status"`
	Progress    float64                `json:"progress"`
	StartTime   time.Time              `json:"start_time"`
	EndTime     *time.Time             `json:"end_time,omitempty"`
	Error       string                 `json:"error,omitempty"`
	Metrics     map[string]float64     `json:"metrics"`
	Config      map[string]interface{} `json:"config"`
}

// TrainingExample represents a training example for model updates
type TrainingExample struct {
	Features []float64              `json:"features"`
	Label    interface{}            `json:"label"`
	Weight   float64                `json:"weight"`
	Metadata map[string]interface{} `json:"metadata"`
}

// ModelMetrics tracks performance metrics for all models
type ModelMetrics struct {
	TotalPredictions int64                  `json:"total_predictions"`
	TotalErrors      int64                  `json:"total_errors"`
	AverageLatency   float64                `json:"average_latency_ms"`
	ModelAccuracies  map[string]float64     `json:"model_accuracies"`
	LastUpdated      time.Time              `json:"last_updated"`
	DetailedMetrics  map[string]interface{} `json:"detailed_metrics"`
}

// NewModelManager creates a new ML model manager
func NewModelManager(config *config.MLConfig) *ModelManager {
	return &ModelManager{
		config:       config,
		models:       make(map[string]*MLModel),
		trainingJobs: make(map[string]*TrainingJob),
		metrics: &ModelMetrics{
			ModelAccuracies: make(map[string]float64),
			DetailedMetrics: make(map[string]interface{}),
			LastUpdated:     time.Now(),
		},
	}
}

// LoadModels loads all configured ML models
func (mm *ModelManager) LoadModels() error {
	mm.modelsMutex.Lock()
	defer mm.modelsMutex.Unlock()

	log.Println("Loading ML models...")

	// Load threat classification model
	if err := mm.loadThreatClassificationModel(); err != nil {
		return fmt.Errorf("failed to load threat classification model: %w", err)
	}

	// Load behavioral analysis model
	if err := mm.loadBehavioralAnalysisModel(); err != nil {
		return fmt.Errorf("failed to load behavioral analysis model: %w", err)
	}

	// Load attack correlation model
	if err := mm.loadAttackCorrelationModel(); err != nil {
		return fmt.Errorf("failed to load attack correlation model: %w", err)
	}

	// Load anomaly detection model
	if err := mm.loadAnomalyDetectionModel(); err != nil {
		return fmt.Errorf("failed to load anomaly detection model: %w", err)
	}

	log.Printf("Successfully loaded %d ML models", len(mm.models))
	return nil
}

// loadThreatClassificationModel loads the main threat classification model
func (mm *ModelManager) loadThreatClassificationModel() error {
	model := &MLModel{
		Name:      "threat_classifier",
		Type:      "classification",
		Version:   "1.0.0",
		ModelPath: filepath.Join(mm.config.ModelsPath, "threat_classifier.onnx"),
		ConfigPath: filepath.Join(mm.config.ModelsPath, "threat_classifier.json"),
		LoadedAt:  time.Now(),
		Status:    "loading",
		Metadata: map[string]interface{}{
			"description": "Multi-class threat classification model",
			"classes": []string{"benign", "malware", "phishing", "injection", "privilege_escalation", "data_exfiltration"},
			"features": 256,
			"algorithm": "gradient_boosting",
		},
	}

	// Load model configuration
	configData, err := ioutil.ReadFile(model.ConfigPath)
	if err != nil {
		return fmt.Errorf("failed to read model config: %w", err)
	}

	var modelConfig map[string]interface{}
	if err := json.Unmarshal(configData, &modelConfig); err != nil {
		return fmt.Errorf("failed to parse model config: %w", err)
	}

	// Initialize model predictor based on type
	predictor, err := mm.createModelPredictor(model.Type, model.ModelPath, modelConfig)
	if err != nil {
		return fmt.Errorf("failed to create model predictor: %w", err)
	}

	model.predictor = predictor
	model.Status = "ready"
	model.Accuracy = 0.95 // From validation metrics

	mm.models[model.Name] = model
	return nil
}

// loadBehavioralAnalysisModel loads the behavioral analysis model
func (mm *ModelManager) loadBehavioralAnalysisModel() error {
	model := &MLModel{
		Name:      "behavior_analyzer",
		Type:      "anomaly_detection",
		Version:   "1.0.0",
		ModelPath: filepath.Join(mm.config.ModelsPath, "behavior_analyzer.onnx"),
		ConfigPath: filepath.Join(mm.config.ModelsPath, "behavior_analyzer.json"),
		LoadedAt:  time.Now(),
		Status:    "loading",
		Metadata: map[string]interface{}{
			"description": "User behavior anomaly detection model",
			"features": 128,
			"algorithm": "isolation_forest",
			"threshold": 0.1,
		},
	}

	// Load model configuration
	configData, err := ioutil.ReadFile(model.ConfigPath)
	if err != nil {
		return fmt.Errorf("failed to read model config: %w", err)
	}

	var modelConfig map[string]interface{}
	if err := json.Unmarshal(configData, &modelConfig); err != nil {
		return fmt.Errorf("failed to parse model config: %w", err)
	}

	predictor, err := mm.createModelPredictor(model.Type, model.ModelPath, modelConfig)
	if err != nil {
		return fmt.Errorf("failed to create model predictor: %w", err)
	}

	model.predictor = predictor
	model.Status = "ready"
	model.Accuracy = 0.92

	mm.models[model.Name] = model
	return nil
}

// loadAttackCorrelationModel loads the attack correlation model
func (mm *ModelManager) loadAttackCorrelationModel() error {
	model := &MLModel{
		Name:      "attack_correlator",
		Type:      "sequence_classification",
		Version:   "1.0.0",
		ModelPath: filepath.Join(mm.config.ModelsPath, "attack_correlator.onnx"),
		ConfigPath: filepath.Join(mm.config.ModelsPath, "attack_correlator.json"),
		LoadedAt:  time.Now(),
		Status:    "loading",
		Metadata: map[string]interface{}{
			"description": "Multi-stage attack correlation model",
			"sequence_length": 10,
			"features": 64,
			"algorithm": "lstm",
		},
	}

	configData, err := ioutil.ReadFile(model.ConfigPath)
	if err != nil {
		return fmt.Errorf("failed to read model config: %w", err)
	}

	var modelConfig map[string]interface{}
	if err := json.Unmarshal(configData, &modelConfig); err != nil {
		return fmt.Errorf("failed to parse model config: %w", err)
	}

	predictor, err := mm.createModelPredictor(model.Type, model.ModelPath, modelConfig)
	if err != nil {
		return fmt.Errorf("failed to create model predictor: %w", err)
	}

	model.predictor = predictor
	model.Status = "ready"
	model.Accuracy = 0.88

	mm.models[model.Name] = model
	return nil
}

// loadAnomalyDetectionModel loads the general anomaly detection model
func (mm *ModelManager) loadAnomalyDetectionModel() error {
	model := &MLModel{
		Name:      "anomaly_detector",
		Type:      "anomaly_detection",
		Version:   "1.0.0",
		ModelPath: filepath.Join(mm.config.ModelsPath, "anomaly_detector.onnx"),
		ConfigPath: filepath.Join(mm.config.ModelsPath, "anomaly_detector.json"),
		LoadedAt:  time.Now(),
		Status:    "loading",
		Metadata: map[string]interface{}{
			"description": "General anomaly detection model",
			"features": 32,
			"algorithm": "one_class_svm",
		},
	}

	configData, err := ioutil.ReadFile(model.ConfigPath)
	if err != nil {
		return fmt.Errorf("failed to read model config: %w", err)
	}

	var modelConfig map[string]interface{}
	if err := json.Unmarshal(configData, &modelConfig); err != nil {
		return fmt.Errorf("failed to parse model config: %w", err)
	}

	predictor, err := mm.createModelPredictor(model.Type, model.ModelPath, modelConfig)
	if err != nil {
		return fmt.Errorf("failed to create model predictor: %w", err)
	}

	model.predictor = predictor
	model.Status = "ready"
	model.Accuracy = 0.90

	mm.models[model.Name] = model
	return nil
}

// createModelPredictor creates a model predictor based on model type
func (mm *ModelManager) createModelPredictor(modelType, modelPath string, config map[string]interface{}) (ModelPredictor, error) {
	switch modelType {
	case "classification":
		return NewClassificationPredictor(modelPath, config)
	case "anomaly_detection":
		return NewAnomalyDetectionPredictor(modelPath, config)
	case "sequence_classification":
		return NewSequenceClassificationPredictor(modelPath, config)
	default:
		return nil, fmt.Errorf("unsupported model type: %s", modelType)
	}
}

// GetModel returns a loaded model by name
func (mm *ModelManager) GetModel(name string) (*MLModel, bool) {
	mm.modelsMutex.RLock()
	defer mm.modelsMutex.RUnlock()
	
	model, exists := mm.models[name]
	return model, exists
}

// GetLoadedModels returns the names of all loaded models
func (mm *ModelManager) GetLoadedModels() []string {
	mm.modelsMutex.RLock()
	defer mm.modelsMutex.RUnlock()
	
	names := make([]string, 0, len(mm.models))
	for name := range mm.models {
		names = append(names, name)
	}
	return names
}

// Predict makes a prediction using the specified model
func (mm *ModelManager) Predict(modelName string, features []float64) (*PredictionResult, error) {
	mm.modelsMutex.RLock()
	model, exists := mm.models[modelName]
	mm.modelsMutex.RUnlock()
	
	if !exists {
		return nil, fmt.Errorf("model not found: %s", modelName)
	}
	
	if model.Status != "ready" {
		return nil, fmt.Errorf("model not ready: %s", modelName)
	}

	startTime := time.Now()
	result, err := model.predictor.Predict(features)
	processingTime := time.Since(startTime)
	
	if err != nil {
		mm.updateErrorMetrics()
		return nil, fmt.Errorf("prediction failed: %w", err)
	}
	
	// Update model metrics
	mm.modelsMutex.Lock()
	model.LastPrediction = time.Now()
	model.PredictionCount++
	mm.modelsMutex.Unlock()
	
	// Update global metrics
	mm.updatePredictionMetrics(processingTime)
	
	result.ModelName = modelName
	result.TimestampMs = time.Now().UnixMilli()
	
	return result, nil
}

// StartModelMonitoring starts background model monitoring
func (mm *ModelManager) StartModelMonitoring(ctx context.Context) {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()
	
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			mm.performModelHealthCheck()
		}
	}
}

// performModelHealthCheck checks the health of all loaded models
func (mm *ModelManager) performModelHealthCheck() {
	mm.modelsMutex.Lock()
	defer mm.modelsMutex.Unlock()
	
	for name, model := range mm.models {
		// Check if model is responsive
		testFeatures := make([]float64, 10) // Dummy features
		_, err := model.predictor.Predict(testFeatures)
		
		if err != nil {
			log.Printf("Model health check failed for %s: %v", name, err)
			model.Status = "error"
		} else {
			if model.Status == "error" {
				model.Status = "ready"
				log.Printf("Model %s recovered from error state", name)
			}
		}
	}
}

// updatePredictionMetrics updates global prediction metrics
func (mm *ModelManager) updatePredictionMetrics(processingTime time.Duration) {
	mm.metrics.TotalPredictions++
	
	// Update moving average of latency
	latencyMs := float64(processingTime.Nanoseconds()) / 1e6
	if mm.metrics.TotalPredictions == 1 {
		mm.metrics.AverageLatency = latencyMs
	} else {
		// Exponential moving average
		alpha := 0.1
		mm.metrics.AverageLatency = alpha*latencyMs + (1-alpha)*mm.metrics.AverageLatency
	}
	
	mm.metrics.LastUpdated = time.Now()
}

// updateErrorMetrics updates error metrics
func (mm *ModelManager) updateErrorMetrics() {
	mm.metrics.TotalErrors++
	mm.metrics.LastUpdated = time.Now()
}

// GetMetrics returns current model metrics
func (mm *ModelManager) GetMetrics() *ModelMetrics {
	mm.modelsMutex.RLock()
	defer mm.modelsMutex.RUnlock()
	
	// Update model accuracies
	for name, model := range mm.models {
		mm.metrics.ModelAccuracies[name] = model.Accuracy
	}
	
	return mm.metrics
}

// SaveModelStates saves the current state of all models
func (mm *ModelManager) SaveModelStates() error {
	mm.modelsMutex.RLock()
	defer mm.modelsMutex.RUnlock()
	
	stateData := make(map[string]interface{})
	for name, model := range mm.models {
		stateData[name] = map[string]interface{}{
			"prediction_count": model.PredictionCount,
			"last_prediction": model.LastPrediction,
			"accuracy":        model.Accuracy,
			"status":          model.Status,
		}
	}
	
	stateJSON, err := json.MarshalIndent(stateData, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal model states: %w", err)
	}
	
	statePath := filepath.Join(mm.config.ModelsPath, "model_states.json")
	if err := ioutil.WriteFile(statePath, stateJSON, 0644); err != nil {
		return fmt.Errorf("failed to save model states: %w", err)
	}
	
	return nil
}
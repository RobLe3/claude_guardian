package config

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/viper"
)

// Config holds all configuration for our application
type Config struct {
	ServiceName string   `mapstructure:"service_name"`
	Environment string   `mapstructure:"environment"`
	Port        int      `mapstructure:"port"`
	LogLevel    string   `mapstructure:"log_level"`
	Database    Database `mapstructure:"database"`
	Redis       Redis    `mapstructure:"redis"`
	Metrics     Metrics  `mapstructure:"metrics"`
	Security    Security `mapstructure:"security"`
}

// Database configuration
type Database struct {
	URL             string `mapstructure:"url"`
	MaxOpenConns    int    `mapstructure:"max_open_conns"`
	MaxIdleConns    int    `mapstructure:"max_idle_conns"`
	ConnMaxLifetime int    `mapstructure:"conn_max_lifetime"`
}

// Redis configuration
type Redis struct {
	URL        string `mapstructure:"url"`
	MaxRetries int    `mapstructure:"max_retries"`
	PoolSize   int    `mapstructure:"pool_size"`
}

// Metrics configuration
type Metrics struct {
	Enabled bool   `mapstructure:"enabled"`
	Path    string `mapstructure:"path"`
}

// Security configuration
type Security struct {
	JWTSecret     string `mapstructure:"jwt_secret"`
	TokenExpiry   int    `mapstructure:"token_expiry"`
	RefreshExpiry int    `mapstructure:"refresh_expiry"`
}

// Load reads configuration from file and environment variables
func Load(serviceName string) (*Config, error) {
	config := &Config{
		ServiceName: serviceName,
		Environment: "development",
		Port:        8080,
		LogLevel:    "info",
		Database: Database{
			URL:             "postgres://postgres:password@localhost:5432/iff_guardian?sslmode=disable",
			MaxOpenConns:    25,
			MaxIdleConns:    25,
			ConnMaxLifetime: 300,
		},
		Redis: Redis{
			URL:        "redis://localhost:6379/0",
			MaxRetries: 3,
			PoolSize:   10,
		},
		Metrics: Metrics{
			Enabled: true,
			Path:    "/metrics",
		},
		Security: Security{
			JWTSecret:     "your-secret-key-change-in-production",
			TokenExpiry:   3600,    // 1 hour
			RefreshExpiry: 604800,  // 1 week
		},
	}

	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath("./config")
	viper.AddConfigPath("./config/environments")
	viper.AddConfigPath(".")

	// Environment-specific config
	env := os.Getenv("ENVIRONMENT")
	if env == "" {
		env = "development"
	}
	config.Environment = env

	// Try to read environment-specific config first
	viper.SetConfigName(env)
	if err := viper.ReadInConfig(); err != nil {
		// Fall back to default config
		viper.SetConfigName("config")
		if err := viper.ReadInConfig(); err != nil {
			// No config file found, use defaults and environment variables
		}
	}

	// Set up environment variable binding
	viper.AutomaticEnv()
	viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	viper.SetEnvPrefix("IFF")

	// Override service-specific settings
	switch serviceName {
	case "gateway":
		viper.SetDefault("port", 8080)
	case "auth-service":
		viper.SetDefault("port", 8081)
	case "detection-engine":
		viper.SetDefault("port", 8082)
	case "config-service":
		viper.SetDefault("port", 8083)
	case "monitoring-service":
		viper.SetDefault("port", 8084)
	}

	// Unmarshal configuration
	if err := viper.Unmarshal(config); err != nil {
		return nil, fmt.Errorf("unable to decode config: %w", err)
	}

	// Validate required fields
	if err := validateConfig(config); err != nil {
		return nil, fmt.Errorf("config validation failed: %w", err)
	}

	return config, nil
}

// validateConfig performs basic validation on the configuration
func validateConfig(cfg *Config) error {
	if cfg.ServiceName == "" {
		return fmt.Errorf("service_name is required")
	}
	
	if cfg.Port <= 0 || cfg.Port > 65535 {
		return fmt.Errorf("port must be between 1 and 65535")
	}
	
	if cfg.Database.URL == "" {
		return fmt.Errorf("database URL is required")
	}
	
	if cfg.Redis.URL == "" {
		return fmt.Errorf("redis URL is required")
	}
	
	return nil
}

// GetEnv returns the current environment
func (c *Config) GetEnv() string {
	return c.Environment
}

// IsProduction returns true if running in production
func (c *Config) IsProduction() bool {
	return strings.ToLower(c.Environment) == "production"
}

// IsDevelopment returns true if running in development
func (c *Config) IsDevelopment() bool {
	return strings.ToLower(c.Environment) == "development"
}
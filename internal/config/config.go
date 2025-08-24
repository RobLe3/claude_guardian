package config

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

type Config struct {
	Server   ServerConfig
	Database DatabaseConfig
	Redis    RedisConfig
	JWT      JWTConfig
	Security SecurityConfig
}

type ServerConfig struct {
	Host         string
	Port         string
	ReadTimeout  time.Duration
	WriteTimeout time.Duration
	IdleTimeout  time.Duration
}

type DatabaseConfig struct {
	Host     string
	Port     string
	User     string
	Password string
	DBName   string
	SSLMode  string
}

type RedisConfig struct {
	Host     string
	Port     string
	Password string
	DB       int
}

type JWTConfig struct {
	SecretKey        string
	RefreshSecretKey string
	AccessTokenTTL   time.Duration
	RefreshTokenTTL  time.Duration
	Algorithm        string
}

type SecurityConfig struct {
	BcryptCost       int
	RateLimitPerMin  int
	MaxLoginAttempts int
	LockoutDuration  time.Duration
}

func Load() (*Config, error) {
	cfg := &Config{
		Server: ServerConfig{
			Host:         getEnv("SERVER_HOST", "localhost"),
			Port:         getEnv("SERVER_PORT", "8080"),
			ReadTimeout:  getDurationEnv("SERVER_READ_TIMEOUT", 15*time.Second),
			WriteTimeout: getDurationEnv("SERVER_WRITE_TIMEOUT", 15*time.Second),
			IdleTimeout:  getDurationEnv("SERVER_IDLE_TIMEOUT", 60*time.Second),
		},
		Database: DatabaseConfig{
			Host:     getEnv("DB_HOST", "localhost"),
			Port:     getEnv("DB_PORT", "5432"),
			User:     getEnv("DB_USER", "iff_guardian"),
			Password: getEnv("DB_PASSWORD", "password"),
			DBName:   getEnv("DB_NAME", "iff_guardian"),
			SSLMode:  getEnv("DB_SSLMODE", "disable"),
		},
		Redis: RedisConfig{
			Host:     getEnv("REDIS_HOST", "localhost"),
			Port:     getEnv("REDIS_PORT", "6379"),
			Password: getEnv("REDIS_PASSWORD", ""),
			DB:       getIntEnv("REDIS_DB", 0),
		},
		JWT: JWTConfig{
			SecretKey:        getEnv("JWT_SECRET_KEY", "your-secret-key-change-in-production"),
			RefreshSecretKey: getEnv("JWT_REFRESH_SECRET_KEY", "your-refresh-secret-key-change-in-production"),
			AccessTokenTTL:   getDurationEnv("JWT_ACCESS_TOKEN_TTL", 15*time.Minute),
			RefreshTokenTTL:  getDurationEnv("JWT_REFRESH_TOKEN_TTL", 7*24*time.Hour),
			Algorithm:        getEnv("JWT_ALGORITHM", "RS256"),
		},
		Security: SecurityConfig{
			BcryptCost:       getIntEnv("BCRYPT_COST", 12),
			RateLimitPerMin:  getIntEnv("RATE_LIMIT_PER_MIN", 60),
			MaxLoginAttempts: getIntEnv("MAX_LOGIN_ATTEMPTS", 5),
			LockoutDuration:  getDurationEnv("LOCKOUT_DURATION", 15*time.Minute),
		},
	}

	if err := cfg.validate(); err != nil {
		return nil, fmt.Errorf("configuration validation failed: %w", err)
	}

	return cfg, nil
}

func (c *Config) validate() error {
	if c.JWT.SecretKey == "your-secret-key-change-in-production" {
		return fmt.Errorf("JWT secret key must be changed in production")
	}
	if c.JWT.RefreshSecretKey == "your-refresh-secret-key-change-in-production" {
		return fmt.Errorf("JWT refresh secret key must be changed in production")
	}
	if c.Security.BcryptCost < 10 {
		return fmt.Errorf("bcrypt cost must be at least 10")
	}
	return nil
}

func (c *Config) GetDSN() string {
	return fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=%s",
		c.Database.Host, c.Database.Port, c.Database.User,
		c.Database.Password, c.Database.DBName, c.Database.SSLMode)
}

func (c *Config) GetRedisAddr() string {
	return fmt.Sprintf("%s:%s", c.Redis.Host, c.Redis.Port)
}

func (c *Config) GetServerAddr() string {
	return fmt.Sprintf("%s:%s", c.Server.Host, c.Server.Port)
}

func getEnv(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}

func getIntEnv(key string, defaultValue int) int {
	if value, exists := os.LookupEnv(key); exists {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

func getDurationEnv(key string, defaultValue time.Duration) time.Duration {
	if value, exists := os.LookupEnv(key); exists {
		if duration, err := time.ParseDuration(value); err == nil {
			return duration
		}
	}
	return defaultValue
}
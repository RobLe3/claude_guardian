package auth

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"iff-guardian/internal/config"
	"iff-guardian/internal/models"
)

type TokenManager struct {
	config     *config.JWTConfig
	privateKey *rsa.PrivateKey
	publicKey  *rsa.PublicKey
}

type TokenClaims struct {
	UserID      uuid.UUID `json:"user_id"`
	Username    string    `json:"username"`
	Email       string    `json:"email"`
	SessionID   uuid.UUID `json:"session_id"`
	Roles       []string  `json:"roles"`
	TokenType   string    `json:"token_type"`
	jwt.RegisteredClaims
}

type TokenPair struct {
	AccessToken  string
	RefreshToken string
	ExpiresIn    int64
}

const (
	TokenTypeAccess  = "access"
	TokenTypeRefresh = "refresh"
)

func NewTokenManager(cfg *config.JWTConfig) (*TokenManager, error) {
	tm := &TokenManager{
		config: cfg,
	}

	// Generate RSA key pair for RS256
	if cfg.Algorithm == "RS256" {
		privateKey, err := generateRSAKeyPair()
		if err != nil {
			return nil, fmt.Errorf("failed to generate RSA key pair: %w", err)
		}
		tm.privateKey = privateKey
		tm.publicKey = &privateKey.PublicKey
	}

	return tm, nil
}

func (tm *TokenManager) GenerateTokenPair(user *models.User, sessionID uuid.UUID, roles []string) (*TokenPair, error) {
	now := time.Now()
	
	// Generate access token
	accessClaims := &TokenClaims{
		UserID:    user.ID,
		Username:  user.Username,
		Email:     user.Email,
		SessionID: sessionID,
		Roles:     roles,
		TokenType: TokenTypeAccess,
		RegisteredClaims: jwt.RegisteredClaims{
			IssuedAt:  jwt.NewNumericDate(now),
			ExpiresAt: jwt.NewNumericDate(now.Add(tm.config.AccessTokenTTL)),
			NotBefore: jwt.NewNumericDate(now),
			Issuer:    "iff-guardian",
			Subject:   user.ID.String(),
			Audience:  jwt.ClaimStrings{"iff-guardian-api"},
		},
	}

	accessToken, err := tm.signToken(accessClaims, tm.config.SecretKey)
	if err != nil {
		return nil, fmt.Errorf("failed to sign access token: %w", err)
	}

	// Generate refresh token
	refreshClaims := &TokenClaims{
		UserID:    user.ID,
		SessionID: sessionID,
		TokenType: TokenTypeRefresh,
		RegisteredClaims: jwt.RegisteredClaims{
			IssuedAt:  jwt.NewNumericDate(now),
			ExpiresAt: jwt.NewNumericDate(now.Add(tm.config.RefreshTokenTTL)),
			NotBefore: jwt.NewNumericDate(now),
			Issuer:    "iff-guardian",
			Subject:   user.ID.String(),
			Audience:  jwt.ClaimStrings{"iff-guardian-refresh"},
		},
	}

	refreshToken, err := tm.signToken(refreshClaims, tm.config.RefreshSecretKey)
	if err != nil {
		return nil, fmt.Errorf("failed to sign refresh token: %w", err)
	}

	return &TokenPair{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		ExpiresIn:    int64(tm.config.AccessTokenTTL.Seconds()),
	}, nil
}

func (tm *TokenManager) ValidateAccessToken(tokenString string) (*TokenClaims, error) {
	return tm.validateToken(tokenString, tm.config.SecretKey, TokenTypeAccess)
}

func (tm *TokenManager) ValidateRefreshToken(tokenString string) (*TokenClaims, error) {
	return tm.validateToken(tokenString, tm.config.RefreshSecretKey, TokenTypeRefresh)
}

func (tm *TokenManager) signToken(claims *TokenClaims, secret string) (string, error) {
	var token *jwt.Token
	
	switch tm.config.Algorithm {
	case "RS256":
		token = jwt.NewWithClaims(jwt.SigningMethodRS256, claims)
		return token.SignedString(tm.privateKey)
	case "HS256":
		token = jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
		return token.SignedString([]byte(secret))
	default:
		return "", fmt.Errorf("unsupported signing algorithm: %s", tm.config.Algorithm)
	}
}

func (tm *TokenManager) validateToken(tokenString, secret, expectedType string) (*TokenClaims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &TokenClaims{}, func(token *jwt.Token) (interface{}, error) {
		// Verify signing method
		switch tm.config.Algorithm {
		case "RS256":
			if _, ok := token.Method.(*jwt.SigningMethodRSA); !ok {
				return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
			}
			return tm.publicKey, nil
		case "HS256":
			if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
			}
			return []byte(secret), nil
		default:
			return nil, fmt.Errorf("unsupported signing algorithm: %s", tm.config.Algorithm)
		}
	})

	if err != nil {
		return nil, fmt.Errorf("failed to parse token: %w", err)
	}

	claims, ok := token.Claims.(*TokenClaims)
	if !ok || !token.Valid {
		return nil, fmt.Errorf("invalid token claims")
	}

	// Verify token type
	if claims.TokenType != expectedType {
		return nil, fmt.Errorf("invalid token type: expected %s, got %s", expectedType, claims.TokenType)
	}

	// Verify expiration
	if claims.ExpiresAt != nil && claims.ExpiresAt.Time.Before(time.Now()) {
		return nil, fmt.Errorf("token has expired")
	}

	return claims, nil
}

func (tm *TokenManager) GetPublicKeyPEM() (string, error) {
	if tm.publicKey == nil {
		return "", fmt.Errorf("public key not available")
	}

	publicKeyBytes, err := x509.MarshalPKIXPublicKey(tm.publicKey)
	if err != nil {
		return "", fmt.Errorf("failed to marshal public key: %w", err)
	}

	publicKeyPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "PUBLIC KEY",
		Bytes: publicKeyBytes,
	})

	return string(publicKeyPEM), nil
}

func generateRSAKeyPair() (*rsa.PrivateKey, error) {
	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return nil, fmt.Errorf("failed to generate RSA private key: %w", err)
	}

	// Validate key
	if err := privateKey.Validate(); err != nil {
		return nil, fmt.Errorf("invalid RSA key: %w", err)
	}

	return privateKey, nil
}

func (tm *TokenManager) GetTokenTTL() time.Duration {
	return tm.config.AccessTokenTTL
}

func (tm *TokenManager) GetRefreshTokenTTL() time.Duration {
	return tm.config.RefreshTokenTTL
}
package auth

import (
	"errors"
	"fmt"
	"regexp"

	"golang.org/x/crypto/bcrypt"
)

var (
	ErrPasswordTooShort    = errors.New("password must be at least 8 characters long")
	ErrPasswordTooWeak     = errors.New("password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character")
	ErrPasswordEmpty       = errors.New("password cannot be empty")
	ErrPasswordHashFailed  = errors.New("failed to hash password")
	ErrPasswordVerifyFailed = errors.New("failed to verify password")
)

type PasswordManager struct {
	cost int
}

type PasswordStrength struct {
	Score       int    `json:"score"`       // 0-4 (0 = very weak, 4 = very strong)
	HasLower    bool   `json:"has_lower"`
	HasUpper    bool   `json:"has_upper"`
	HasDigit    bool   `json:"has_digit"`
	HasSpecial  bool   `json:"has_special"`
	Length      int    `json:"length"`
	Feedback    string `json:"feedback"`
}

func NewPasswordManager(cost int) *PasswordManager {
	if cost < bcrypt.MinCost {
		cost = bcrypt.DefaultCost
	}
	if cost > bcrypt.MaxCost {
		cost = bcrypt.MaxCost
	}
	
	return &PasswordManager{
		cost: cost,
	}
}

func (pm *PasswordManager) HashPassword(password string) (string, error) {
	if password == "" {
		return "", ErrPasswordEmpty
	}

	if err := pm.ValidatePassword(password); err != nil {
		return "", err
	}

	hashedBytes, err := bcrypt.GenerateFromPassword([]byte(password), pm.cost)
	if err != nil {
		return "", fmt.Errorf("%w: %v", ErrPasswordHashFailed, err)
	}

	return string(hashedBytes), nil
}

func (pm *PasswordManager) VerifyPassword(hashedPassword, password string) error {
	if password == "" {
		return ErrPasswordEmpty
	}

	if hashedPassword == "" {
		return ErrPasswordVerifyFailed
	}

	err := bcrypt.CompareHashAndPassword([]byte(hashedPassword), []byte(password))
	if err != nil {
		if errors.Is(err, bcrypt.ErrMismatchedHashAndPassword) {
			return ErrPasswordVerifyFailed
		}
		return fmt.Errorf("%w: %v", ErrPasswordVerifyFailed, err)
	}

	return nil
}

func (pm *PasswordManager) ValidatePassword(password string) error {
	if len(password) < 8 {
		return ErrPasswordTooShort
	}

	strength := pm.AnalyzePasswordStrength(password)
	if strength.Score < 2 {
		return ErrPasswordTooWeak
	}

	return nil
}

func (pm *PasswordManager) AnalyzePasswordStrength(password string) PasswordStrength {
	strength := PasswordStrength{
		Length: len(password),
	}

	// Check character types
	strength.HasLower = regexp.MustCompile(`[a-z]`).MatchString(password)
	strength.HasUpper = regexp.MustCompile(`[A-Z]`).MatchString(password)
	strength.HasDigit = regexp.MustCompile(`[0-9]`).MatchString(password)
	strength.HasSpecial = regexp.MustCompile(`[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\?~` + "`" + `]`).MatchString(password)

	// Calculate score
	score := 0
	if strength.Length >= 8 {
		score++
	}
	if strength.Length >= 12 {
		score++
	}
	if strength.HasLower {
		score++
	}
	if strength.HasUpper {
		score++
	}
	if strength.HasDigit {
		score++
	}
	if strength.HasSpecial {
		score++
	}

	// Normalize score to 0-4 range
	if score > 4 {
		score = 4
	}

	strength.Score = score

	// Generate feedback
	switch score {
	case 0, 1:
		strength.Feedback = "Very weak password. Add more character types and length."
	case 2:
		strength.Feedback = "Weak password. Consider adding more character types or length."
	case 3:
		strength.Feedback = "Good password. Could be stronger with more length or character types."
	case 4:
		strength.Feedback = "Strong password."
	}

	return strength
}

func (pm *PasswordManager) NeedsRehash(hashedPassword string) bool {
	cost, err := bcrypt.Cost([]byte(hashedPassword))
	if err != nil {
		return true // If we can't determine cost, assume it needs rehashing
	}
	
	return cost != pm.cost
}

func (pm *PasswordManager) GetCost() int {
	return pm.cost
}
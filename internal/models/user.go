package models

import (
	"database/sql/driver"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
)

// User represents a user in the system
type User struct {
	ID                uuid.UUID  `json:"id" db:"id"`
	Username          string     `json:"username" db:"username"`
	Email             string     `json:"email" db:"email"`
	PasswordHash      string     `json:"-" db:"password_hash"`
	FirstName         string     `json:"first_name" db:"first_name"`
	LastName          string     `json:"last_name" db:"last_name"`
	IsActive          bool       `json:"is_active" db:"is_active"`
	IsEmailVerified   bool       `json:"is_email_verified" db:"is_email_verified"`
	FailedLoginCount  int        `json:"failed_login_count" db:"failed_login_count"`
	LockedUntil       *time.Time `json:"locked_until" db:"locked_until"`
	LastLoginAt       *time.Time `json:"last_login_at" db:"last_login_at"`
	LastLoginIP       string     `json:"last_login_ip" db:"last_login_ip"`
	PasswordChangedAt time.Time  `json:"password_changed_at" db:"password_changed_at"`
	CreatedAt         time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt         time.Time  `json:"updated_at" db:"updated_at"`
}

// Role represents a role in the RBAC system
type Role struct {
	ID          uuid.UUID   `json:"id" db:"id"`
	Name        string      `json:"name" db:"name"`
	DisplayName string      `json:"display_name" db:"display_name"`
	Description string      `json:"description" db:"description"`
	IsSystem    bool        `json:"is_system" db:"is_system"`
	Permissions Permissions `json:"permissions" db:"permissions"`
	CreatedAt   time.Time   `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time   `json:"updated_at" db:"updated_at"`
}

// Permission represents a specific permission
type Permission struct {
	Resource string   `json:"resource"`
	Actions  []string `json:"actions"`
}

// Permissions is a slice of Permission that implements database scanning
type Permissions []Permission

// UserRole represents the many-to-many relationship between users and roles
type UserRole struct {
	UserID    uuid.UUID `json:"user_id" db:"user_id"`
	RoleID    uuid.UUID `json:"role_id" db:"role_id"`
	GrantedBy uuid.UUID `json:"granted_by" db:"granted_by"`
	GrantedAt time.Time `json:"granted_at" db:"granted_at"`
}

// Session represents a user session
type Session struct {
	ID           uuid.UUID  `json:"id" db:"id"`
	UserID       uuid.UUID  `json:"user_id" db:"user_id"`
	RefreshToken string     `json:"-" db:"refresh_token"`
	UserAgent    string     `json:"user_agent" db:"user_agent"`
	IPAddress    string     `json:"ip_address" db:"ip_address"`
	IsActive     bool       `json:"is_active" db:"is_active"`
	ExpiresAt    time.Time  `json:"expires_at" db:"expires_at"`
	LastUsedAt   *time.Time `json:"last_used_at" db:"last_used_at"`
	CreatedAt    time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt    time.Time  `json:"updated_at" db:"updated_at"`
}

// AuditLog represents an audit log entry
type AuditLog struct {
	ID        uuid.UUID          `json:"id" db:"id"`
	UserID    *uuid.UUID         `json:"user_id" db:"user_id"`
	Action    string             `json:"action" db:"action"`
	Resource  string             `json:"resource" db:"resource"`
	Details   map[string]interface{} `json:"details" db:"details"`
	IPAddress string             `json:"ip_address" db:"ip_address"`
	UserAgent string             `json:"user_agent" db:"user_agent"`
	Success   bool               `json:"success" db:"success"`
	ErrorMsg  string             `json:"error_message" db:"error_message"`
	CreatedAt time.Time          `json:"created_at" db:"created_at"`
}

// UserWithRoles represents a user with their associated roles
type UserWithRoles struct {
	User  User   `json:"user"`
	Roles []Role `json:"roles"`
}

// CreateUserRequest represents a user creation request
type CreateUserRequest struct {
	Username  string `json:"username" validate:"required,min=3,max=50"`
	Email     string `json:"email" validate:"required,email"`
	Password  string `json:"password" validate:"required,min=8"`
	FirstName string `json:"first_name" validate:"required,min=1,max=100"`
	LastName  string `json:"last_name" validate:"required,min=1,max=100"`
}

// UpdateUserRequest represents a user update request
type UpdateUserRequest struct {
	FirstName *string `json:"first_name" validate:"omitempty,min=1,max=100"`
	LastName  *string `json:"last_name" validate:"omitempty,min=1,max=100"`
	Email     *string `json:"email" validate:"omitempty,email"`
	IsActive  *bool   `json:"is_active"`
}

// LoginRequest represents a login request
type LoginRequest struct {
	Username string `json:"username" validate:"required"`
	Password string `json:"password" validate:"required"`
}

// LoginResponse represents a login response
type LoginResponse struct {
	AccessToken  string    `json:"access_token"`
	RefreshToken string    `json:"refresh_token"`
	TokenType    string    `json:"token_type"`
	ExpiresIn    int64     `json:"expires_in"`
	User         User      `json:"user"`
	Roles        []Role    `json:"roles"`
}

// RefreshTokenRequest represents a token refresh request
type RefreshTokenRequest struct {
	RefreshToken string `json:"refresh_token" validate:"required"`
}

// ChangePasswordRequest represents a password change request
type ChangePasswordRequest struct {
	CurrentPassword string `json:"current_password" validate:"required"`
	NewPassword     string `json:"new_password" validate:"required,min=8"`
}

// AssignRoleRequest represents a role assignment request
type AssignRoleRequest struct {
	UserID uuid.UUID `json:"user_id" validate:"required"`
	RoleID uuid.UUID `json:"role_id" validate:"required"`
}

// Default system roles
const (
	RoleAdmin    = "admin"
	RoleUser     = "user"
	RoleObserver = "observer"
)

// Default permissions
var (
	AdminPermissions = Permissions{
		{Resource: "*", Actions: []string{"*"}},
	}
	
	UserPermissions = Permissions{
		{Resource: "profile", Actions: []string{"read", "update"}},
		{Resource: "sessions", Actions: []string{"read", "create", "delete"}},
	}
	
	ObserverPermissions = Permissions{
		{Resource: "profile", Actions: []string{"read"}},
		{Resource: "audit_logs", Actions: []string{"read"}},
	}
)

// Permissions database scanning methods
func (p *Permissions) Scan(value interface{}) error {
	if value == nil {
		return nil
	}
	
	switch v := value.(type) {
	case []byte:
		return json.Unmarshal(v, p)
	case string:
		return json.Unmarshal([]byte(v), p)
	default:
		return fmt.Errorf("cannot scan %T into Permissions", value)
	}
}

func (p Permissions) Value() (driver.Value, error) {
	if len(p) == 0 {
		return nil, nil
	}
	return json.Marshal(p)
}

// HasPermission checks if the user has the required permission
func (u *UserWithRoles) HasPermission(resource, action string) bool {
	for _, role := range u.Roles {
		for _, perm := range role.Permissions {
			if (perm.Resource == "*" || perm.Resource == resource) {
				for _, allowedAction := range perm.Actions {
					if allowedAction == "*" || allowedAction == action {
						return true
					}
				}
			}
		}
	}
	return false
}

// IsLocked checks if the user account is currently locked
func (u *User) IsLocked() bool {
	if u.LockedUntil == nil {
		return false
	}
	return time.Now().Before(*u.LockedUntil)
}

// ShouldLock determines if the user should be locked due to failed login attempts
func (u *User) ShouldLock(maxAttempts int) bool {
	return u.FailedLoginCount >= maxAttempts
}
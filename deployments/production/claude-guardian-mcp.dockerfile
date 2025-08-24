# =============================================================================
# Claude Guardian MCP Service - Production Docker Image
# Multi-stage build for optimized Go service
# =============================================================================

# Build stage
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git ca-certificates tzdata

# Set working directory
WORKDIR /build

# Copy Go modules
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download && go mod verify

# Copy source code
COPY . .

# Build the MCP service
RUN CGO_ENABLED=0 GOOS=linux go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a -installsuffix cgo \
    -o claude-guardian-mcp \
    ./services/mcp-service

# Production stage  
FROM alpine:3.18

# Install runtime dependencies
RUN apk --no-cache add \
    ca-certificates \
    tzdata \
    wget \
    curl \
    && update-ca-certificates

# Create non-root user
RUN addgroup -g 1000 -S cguser && \
    adduser -u 1000 -S cguser -G cguser

# Set working directory
WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/claude-guardian-mcp /app/claude-guardian-mcp

# Copy configuration files
COPY --from=builder /build/config /app/config
COPY --from=builder /build/deployments/production/init /app/init

# Create directories for logs and models
RUN mkdir -p /app/logs /app/models /app/data && \
    chown -R cguser:cguser /app

# Switch to non-root user
USER cguser

# Set environment variables
ENV GIN_MODE=release
ENV GO_ENV=production
ENV LOG_LEVEL=info

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8083/health || exit 1

# Expose MCP port
EXPOSE 8083

# Set entrypoint
ENTRYPOINT ["/app/claude-guardian-mcp"]
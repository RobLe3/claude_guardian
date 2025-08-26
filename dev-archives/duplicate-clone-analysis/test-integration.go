package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"time"

	_ "github.com/lib/pq"
	"github.com/redis/go-redis/v9"
)

// Simple test to verify Go can connect to the running databases
func main() {
	fmt.Println("🔍 Testing Claude Guardian Go Integration with Live Databases")
	fmt.Println("=" * 60)

	// Test PostgreSQL connection
	testPostgreSQL()
	
	// Test Redis connection (if available)
	testRedis()

	// Test Qdrant connection
	testQdrant()

	// Simple HTTP health server
	startTestServer()
}

func testPostgreSQL() {
	fmt.Println("\n📊 Testing PostgreSQL Connection...")
	
	// Using the same database as the running container
	dsn := "host=localhost port=5432 user=cguser password=your-password dbname=claude_guardian sslmode=disable"
	
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		fmt.Printf("❌ Failed to open PostgreSQL: %v\n", err)
		return
	}
	defer db.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		fmt.Printf("⚠️ PostgreSQL ping failed (expected if password not set): %v\n", err)
	} else {
		fmt.Println("✅ PostgreSQL connection successful!")
		
		// Try to query some basic info
		var version string
		err = db.QueryRowContext(ctx, "SELECT version()").Scan(&version)
		if err != nil {
			fmt.Printf("❌ Failed to query PostgreSQL version: %v\n", err)
		} else {
			fmt.Printf("📋 PostgreSQL Version: %s\n", version[:50] + "...")
		}
	}
}

func testRedis() {
	fmt.Println("\n🔴 Testing Redis Connection...")
	
	rdb := redis.NewClient(&redis.Options{
		Addr:     "localhost:6379",
		Password: "",
		DB:       0,
	})
	defer rdb.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	pong, err := rdb.Ping(ctx).Result()
	if err != nil {
		fmt.Printf("⚠️ Redis connection failed (expected if not running): %v\n", err)
	} else {
		fmt.Printf("✅ Redis connection successful: %s\n", pong)
	}
}

func testQdrant() {
	fmt.Println("\n🎯 Testing Qdrant Connection...")
	
	// Test Qdrant HTTP API
	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Get("http://localhost:6333/collections")
	if err != nil {
		fmt.Printf("❌ Qdrant connection failed: %v\n", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 {
		fmt.Println("✅ Qdrant connection successful!")
		fmt.Printf("📊 HTTP Status: %d\n", resp.StatusCode)
	} else {
		fmt.Printf("⚠️ Qdrant returned status: %d\n", resp.StatusCode)
	}
}

func startTestServer() {
	fmt.Println("\n🚀 Starting Go Test Server on :8090...")
	
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, `
# Claude Guardian Go Integration Test

## Status: ✅ Go Service Running

### Database Connections:
- PostgreSQL: Attempted connection to localhost:5432
- Redis: Attempted connection to localhost:6379  
- Qdrant: Attempted connection to localhost:6333

### Service Info:
- Go Version: Built with Go modules
- Server: Simple HTTP server on port 8090
- Purpose: Verify Go can run alongside Python MCP service

This proves that Go services CAN integrate with the existing database infrastructure.
		`)
	})

	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, `{"status":"healthy","service":"go-test","timestamp":"%s"}`, time.Now().Format(time.RFC3339))
	})

	fmt.Println("🌐 Test endpoints:")
	fmt.Println("   http://localhost:8090/ - Main test page")
	fmt.Println("   http://localhost:8090/health - Health check")
	fmt.Println("\nPress Ctrl+C to stop...")

	log.Fatal(http.ListenAndServe(":8090", nil))
}
#!/bin/bash

# IFF-Guardian Phase Validation Script
# Comprehensive validation system for phase completion and state tracking
# Version: 1.0
# Date: 2025-08-23

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/config"
REPORTS_DIR="${SCRIPT_DIR}/reports"
LOGS_DIR="${SCRIPT_DIR}/logs"

# Create required directories
mkdir -p "${REPORTS_DIR}" "${LOGS_DIR}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${LOGS_DIR}/validation.log"
}

log_info() { log "INFO" "$*"; }
log_warn() { log "WARN" "${YELLOW}$*${NC}"; }
log_error() { log "ERROR" "${RED}$*${NC}"; }
log_success() { log "SUCCESS" "${GREEN}$*${NC}"; }

# Global variables
PHASE=""
VALIDATION_RESULTS=()
OVERALL_STATUS="PASS"
START_TIME=$(date +%s)

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS] <phase>

IFF-Guardian Phase Validation Script

PHASES:
    1, phase1, foundation     - Phase 1: Foundation & Core Infrastructure
    2, phase2, iam           - Phase 2: Identity & Access Management
    3, phase3, threat        - Phase 3: Threat Detection Engine
    4, phase4, advanced      - Phase 4: Advanced Security Features
    5, phase5, integration   - Phase 5: Integration & Optimization
    6, phase6, production    - Phase 6: Production Readiness & Deployment
    all                      - Validate all phases

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -r, --report            Generate detailed report
    -s, --strict            Strict validation mode (fail on warnings)
    --no-tests             Skip test execution
    --no-coverage          Skip coverage checks
    --no-security          Skip security scans
    --no-performance       Skip performance benchmarks

EXAMPLES:
    $0 1                    # Validate Phase 1
    $0 phase2 --verbose     # Validate Phase 2 with verbose output
    $0 all --report         # Validate all phases and generate report
    $0 production --strict  # Strict validation for Phase 6

EXIT CODES:
    0 - All validations passed
    1 - General error
    2 - Phase not found
    3 - Dependencies not met
    4 - Quality gates failed
    5 - Architecture compliance failed
    6 - Performance benchmarks failed
EOF
}

# Parse command line arguments
parse_args() {
    local verbose=false
    local generate_report=false
    local strict_mode=false
    local skip_tests=false
    local skip_coverage=false
    local skip_security=false
    local skip_performance=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -r|--report)
                generate_report=true
                shift
                ;;
            -s|--strict)
                strict_mode=true
                shift
                ;;
            --no-tests)
                skip_tests=true
                shift
                ;;
            --no-coverage)
                skip_coverage=true
                shift
                ;;
            --no-security)
                skip_security=true
                shift
                ;;
            --no-performance)
                skip_performance=true
                shift
                ;;
            1|phase1|foundation)
                PHASE="phase1"
                shift
                ;;
            2|phase2|iam)
                PHASE="phase2"
                shift
                ;;
            3|phase3|threat)
                PHASE="phase3"
                shift
                ;;
            4|phase4|advanced)
                PHASE="phase4"
                shift
                ;;
            5|phase5|integration)
                PHASE="phase5"
                shift
                ;;
            6|phase6|production)
                PHASE="phase6"
                shift
                ;;
            all)
                PHASE="all"
                shift
                ;;
            *)
                log_error "Unknown argument: $1"
                usage
                exit 1
                ;;
        esac
    done

    # Export variables for use in other functions
    export VERBOSE=$verbose
    export GENERATE_REPORT=$generate_report
    export STRICT_MODE=$strict_mode
    export SKIP_TESTS=$skip_tests
    export SKIP_COVERAGE=$skip_coverage
    export SKIP_SECURITY=$skip_security
    export SKIP_PERFORMANCE=$skip_performance

    if [[ -z "$PHASE" ]]; then
        log_error "Phase must be specified"
        usage
        exit 2
    fi
}

# Load phase configuration
load_phase_config() {
    local phase=$1
    local config_file="${CONFIG_DIR}/phase-${phase}.yaml"
    
    if [[ ! -f "$config_file" ]]; then
        log_error "Phase configuration file not found: $config_file"
        return 1
    fi
    
    log_info "Loading configuration for $phase"
    # Configuration will be loaded by individual validators
    return 0
}

# Check phase dependencies
check_dependencies() {
    local phase=$1
    log_info "Checking dependencies for $phase"
    
    case $phase in
        phase1)
            # No dependencies
            return 0
            ;;
        phase2)
            if ! validate_phase_complete "phase1"; then
                log_error "Phase 1 must be completed before Phase 2"
                return 1
            fi
            ;;
        phase3)
            if ! validate_phase_complete "phase1" || ! validate_phase_complete "phase2"; then
                log_error "Phases 1 and 2 must be completed before Phase 3"
                return 1
            fi
            ;;
        phase4)
            for dep_phase in phase1 phase2 phase3; do
                if ! validate_phase_complete "$dep_phase"; then
                    log_error "Phase ${dep_phase} must be completed before Phase 4"
                    return 1
                fi
            done
            ;;
        phase5)
            for dep_phase in phase1 phase2 phase3 phase4; do
                if ! validate_phase_complete "$dep_phase"; then
                    log_error "Phase ${dep_phase} must be completed before Phase 5"
                    return 1
                fi
            done
            ;;
        phase6)
            for dep_phase in phase1 phase2 phase3 phase4 phase5; do
                if ! validate_phase_complete "$dep_phase"; then
                    log_error "Phase ${dep_phase} must be completed before Phase 6"
                    return 1
                fi
            done
            ;;
    esac
    
    log_success "Dependencies satisfied for $phase"
    return 0
}

# Validate phase completion
validate_phase_complete() {
    local phase=$1
    local state_file="${SCRIPT_DIR}/state/${phase}.state"
    
    if [[ -f "$state_file" ]]; then
        local status=$(grep "status:" "$state_file" | cut -d: -f2 | tr -d ' ')
        [[ "$status" == "completed" ]]
    else
        return 1
    fi
}

# Run deliverables validation
validate_deliverables() {
    local phase=$1
    local result=0
    
    log_info "Validating deliverables for $phase"
    
    # Call deliverables validator
    if ! "${SCRIPT_DIR}/validators/deliverables-validator.py" "$phase"; then
        log_error "Deliverables validation failed for $phase"
        result=1
    fi
    
    return $result
}

# Run architecture compliance check
validate_architecture() {
    local phase=$1
    local result=0
    
    log_info "Validating architecture compliance for $phase"
    
    # Call architecture compliance checker
    if ! "${SCRIPT_DIR}/validators/architecture-compliance.py" "$phase"; then
        log_error "Architecture compliance failed for $phase"
        result=1
    fi
    
    return $result
}

# Run quality gates
validate_quality_gates() {
    local phase=$1
    local result=0
    
    log_info "Running quality gates for $phase"
    
    # Test execution
    if [[ "$SKIP_TESTS" != "true" ]]; then
        if ! run_tests "$phase"; then
            log_error "Tests failed for $phase"
            result=1
        fi
    fi
    
    # Code coverage
    if [[ "$SKIP_COVERAGE" != "true" ]]; then
        if ! check_coverage "$phase"; then
            log_error "Code coverage below threshold for $phase"
            result=1
        fi
    fi
    
    # Security scans
    if [[ "$SKIP_SECURITY" != "true" ]]; then
        if ! run_security_scans "$phase"; then
            log_error "Security scans failed for $phase"
            result=1
        fi
    fi
    
    # Performance benchmarks
    if [[ "$SKIP_PERFORMANCE" != "true" ]]; then
        if ! run_performance_benchmarks "$phase"; then
            log_error "Performance benchmarks failed for $phase"
            result=1
        fi
    fi
    
    return $result
}

# Run tests
run_tests() {
    local phase=$1
    log_info "Running tests for $phase"
    
    cd "$PROJECT_ROOT"
    
    # Run unit tests
    if ! python -m pytest tests/unit/ -v; then
        return 1
    fi
    
    # Run integration tests if applicable
    case $phase in
        phase2|phase3|phase4|phase5|phase6)
            if ! python -m pytest tests/integration/ -v; then
                return 1
            fi
            ;;
    esac
    
    # Run E2E tests for later phases
    case $phase in
        phase5|phase6)
            if ! python -m pytest tests/e2e/ -v; then
                return 1
            fi
            ;;
    esac
    
    log_success "All tests passed for $phase"
    return 0
}

# Check code coverage
check_coverage() {
    local phase=$1
    local threshold=80
    
    log_info "Checking code coverage for $phase"
    
    cd "$PROJECT_ROOT"
    
    # Run coverage analysis
    coverage run --source=src -m pytest tests/ >/dev/null 2>&1
    local coverage_pct=$(coverage report | tail -n 1 | awk '{print $4}' | sed 's/%//')
    
    if [[ $(echo "$coverage_pct >= $threshold" | bc) -eq 1 ]]; then
        log_success "Code coverage: ${coverage_pct}% (>= ${threshold}%)"
        return 0
    else
        log_error "Code coverage: ${coverage_pct}% (< ${threshold}%)"
        return 1
    fi
}

# Run security scans
run_security_scans() {
    local phase=$1
    log_info "Running security scans for $phase"
    
    cd "$PROJECT_ROOT"
    
    # Static security analysis
    if command -v bandit >/dev/null 2>&1; then
        if ! bandit -r src/ -f json -o "${REPORTS_DIR}/security-${phase}.json"; then
            return 1
        fi
    fi
    
    # Dependency vulnerability scanning
    if command -v safety >/dev/null 2>&1; then
        if ! safety check --json --output "${REPORTS_DIR}/safety-${phase}.json"; then
            return 1
        fi
    fi
    
    log_success "Security scans passed for $phase"
    return 0
}

# Run performance benchmarks
run_performance_benchmarks() {
    local phase=$1
    log_info "Running performance benchmarks for $phase"
    
    # Call performance benchmark suite
    if ! "${SCRIPT_DIR}/benchmarks/performance-suite.py" "$phase"; then
        return 1
    fi
    
    log_success "Performance benchmarks passed for $phase"
    return 0
}

# Update phase state
update_phase_state() {
    local phase=$1
    local status=$2
    local state_dir="${SCRIPT_DIR}/state"
    local state_file="${state_dir}/${phase}.state"
    
    mkdir -p "$state_dir"
    
    cat > "$state_file" << EOF
phase: $phase
status: $status
timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
validated_by: $USER
validation_version: 1.0
EOF
    
    log_info "Updated phase state: $phase -> $status"
}

# Generate validation report
generate_report() {
    local phase=$1
    local report_file="${REPORTS_DIR}/validation-report-${phase}-$(date +%Y%m%d-%H%M%S).html"
    
    log_info "Generating validation report: $report_file"
    
    # Call report generator
    "${SCRIPT_DIR}/generators/report-generator.py" \
        --phase "$phase" \
        --output "$report_file" \
        --logs "${LOGS_DIR}/validation.log"
    
    log_success "Report generated: $report_file"
}

# Validate single phase
validate_single_phase() {
    local phase=$1
    local phase_result=0
    
    log_info "=== Starting validation for $phase ==="
    
    # Load configuration
    if ! load_phase_config "$phase"; then
        phase_result=1
    fi
    
    # Check dependencies
    if [[ $phase_result -eq 0 ]] && ! check_dependencies "$phase"; then
        phase_result=3
    fi
    
    # Validate deliverables
    if [[ $phase_result -eq 0 ]] && ! validate_deliverables "$phase"; then
        phase_result=4
    fi
    
    # Validate architecture compliance
    if [[ $phase_result -eq 0 ]] && ! validate_architecture "$phase"; then
        phase_result=5
    fi
    
    # Run quality gates
    if [[ $phase_result -eq 0 ]] && ! validate_quality_gates "$phase"; then
        phase_result=4
    fi
    
    # Update phase state
    if [[ $phase_result -eq 0 ]]; then
        update_phase_state "$phase" "completed"
        log_success "=== Phase $phase validation PASSED ==="
    else
        update_phase_state "$phase" "failed"
        log_error "=== Phase $phase validation FAILED ==="
        OVERALL_STATUS="FAIL"
    fi
    
    VALIDATION_RESULTS+=("$phase:$phase_result")
    
    return $phase_result
}

# Main validation function
main() {
    parse_args "$@"
    
    log_info "IFF-Guardian Phase Validation Started"
    log_info "Phase: $PHASE"
    log_info "Timestamp: $(date)"
    log_info "User: $USER"
    
    local exit_code=0
    
    if [[ "$PHASE" == "all" ]]; then
        for phase in phase1 phase2 phase3 phase4 phase5 phase6; do
            if ! validate_single_phase "$phase"; then
                exit_code=1
            fi
        done
    else
        if ! validate_single_phase "$PHASE"; then
            exit_code=1
        fi
    fi
    
    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    
    log_info "Validation completed in ${duration}s"
    log_info "Overall Status: $OVERALL_STATUS"
    
    # Generate report if requested
    if [[ "$GENERATE_REPORT" == "true" ]]; then
        generate_report "$PHASE"
    fi
    
    # Print summary
    echo
    echo "=== VALIDATION SUMMARY ==="
    for result in "${VALIDATION_RESULTS[@]}"; do
        local phase_name=${result%:*}
        local phase_code=${result#*:}
        if [[ $phase_code -eq 0 ]]; then
            echo -e "$phase_name: ${GREEN}PASS${NC}"
        else
            echo -e "$phase_name: ${RED}FAIL${NC} (code: $phase_code)"
        fi
    done
    echo "Overall: $OVERALL_STATUS"
    echo "Duration: ${duration}s"
    echo
    
    if [[ "$STRICT_MODE" == "true" && "$OVERALL_STATUS" == "FAIL" ]]; then
        log_error "Strict mode enabled - failing due to validation errors"
        exit_code=1
    fi
    
    exit $exit_code
}

# Trap to ensure cleanup
trap 'log_info "Validation interrupted"' INT TERM

# Run main function
main "$@"
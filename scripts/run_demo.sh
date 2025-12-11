#!/bin/bash
# Helper script to run demo with python3
# Usage: ./scripts/run_demo.sh [demo_simulation|e2e_test|simulate_driver|simulate_rider]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

case "$1" in
    demo_simulation|demo)
        python3 scripts/demo_simulation.py "${@:2}"
        ;;
    e2e_test|test)
        python3 tests/e2e_test_k8s.py "${@:2}"
        ;;
    driver)
        python3 scripts/simulate_driver_k8s.py "${@:2}"
        ;;
    rider)
        python3 scripts/simulate_rider_k8s.py "${@:2}"
        ;;
    verify)
        python3 scripts/verify_setup.py "${@:2}"
        ;;
    *)
        echo "Usage: $0 {demo_simulation|e2e_test|driver|rider|verify} [args...]"
        echo ""
        echo "Examples:"
        echo "  $0 demo_simulation"
        echo "  $0 e2e_test"
        echo "  $0 driver --driver-id drv-1 --station-id ST101"
        echo "  $0 rider --rider-id rider-1 --station-id ST101"
        echo "  $0 verify"
        exit 1
        ;;
esac


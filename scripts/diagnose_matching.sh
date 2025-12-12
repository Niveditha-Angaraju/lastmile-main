#!/bin/bash
# Diagnose why matches aren't being created

echo "=========================================="
echo "Matching Service Diagnostic"
echo "=========================================="
echo ""

echo "1. Checking matching service status..."
kubectl -n lastmile get pods -l app=matching-service
echo ""

echo "2. Checking matching service logs (last 30 lines)..."
kubectl -n lastmile logs -l app=matching-service --tail=30 | grep -E "RIDER|DRIVER|MATCH|ERROR" || echo "No relevant log entries"
echo ""

echo "3. Checking RabbitMQ queues..."
python3 scripts/fix_matching_issues.py
echo ""

echo "4. Checking if matching service is consuming..."
kubectl -n lastmile logs -l app=matching-service --tail=50 | grep -i "consuming\|started\|error" | tail -5
echo ""

echo "=========================================="
echo "Recommendations:"
echo "=========================================="
echo ""
echo "If no matches are created:"
echo "  1. Check matching service logs: kubectl -n lastmile logs -l app=matching-service --tail=100"
echo "  2. Restart matching service: kubectl -n lastmile rollout restart deployment/matching-service"
echo "  3. Verify RabbitMQ is accessible from matching service"
echo "  4. Check that destinations match between riders and drivers"
echo ""


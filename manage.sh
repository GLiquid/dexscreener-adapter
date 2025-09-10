#!/bin/bash

# DEX Screener Adapter Management Script

set -e

COMPOSE_FILE="docker-compose.yml"

print_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       Start all services"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  logs        Show logs for all services"
    echo "  status      Show service status"
    echo "  build       Build and start services"
    echo "  clean       Stop and remove all containers/volumes"
    echo "  test        Test API endpoints"
    echo "  monitor     Show real-time stats"
}

start_services() {
    echo "🚀 Starting DEX Screener Adapter services..."
    docker-compose up -d
    echo "✅ Services started successfully!"
    echo "📊 API available at: http://localhost"
    echo "🔍 Health check: http://localhost/health"
}

stop_services() {
    echo "🛑 Stopping services..."
    docker-compose down
    echo "✅ Services stopped!"
}

restart_services() {
    echo "🔄 Restarting services..."
    docker-compose restart
    echo "✅ Services restarted!"
}

show_logs() {
    echo "📋 Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f
}

show_status() {
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    echo " Container Stats:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

build_services() {
    echo "🔨 Building and starting services..."
    docker-compose up -d --build
    echo "✅ Build completed!"
}

clean_all() {
    echo "🧹 Cleaning up..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    echo "✅ Cleanup completed!"
}

test_api() {
    echo "🧪 Testing API endpoints..."
    
    # Wait for services to be ready
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    # Health check
    echo "🔍 Testing health endpoint..."
    curl -s http://localhost/health || echo "❌ Health check failed"
    
    # Test each network
    networks=("ethereum" "polygon" "arbitrum" "base")
    
    for network in "${networks[@]}"; do
        echo "🌐 Testing $network endpoints..."
        
        # Latest block
        response=$(curl -s "http://localhost/dex/$network/latest-block" || echo "error")
        if [[ $response == *"blockNumber"* ]]; then
            echo "✅ $network latest-block: OK"
        else
            echo "❌ $network latest-block: FAILED"
        fi
        
        sleep 1
    done
    
    echo "🎉 API testing completed!"
}

monitor_services() {
    echo "📊 Real-time monitoring (Ctrl+C to exit)..."
    while true; do
        clear
        echo "=== DEX Screener Adapter Monitor ==="
        echo "$(date)"
        echo ""
        
        # Service status
        docker-compose ps
        echo ""
        
        # Container stats
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
        echo ""
        
        # Recent logs
        echo "📋 Recent logs:"
        docker-compose logs --tail=5 | tail -10
        
        sleep 5
    done
}

case "${1:-}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    build)
        build_services
        ;;
    clean)
        clean_all
        ;;
    test)
        test_api
        ;;
    monitor)
        monitor_services
        ;;
    *)
        print_usage
        exit 1
        ;;
esac

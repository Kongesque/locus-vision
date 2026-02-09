#!/bin/bash
# Pi 5 App Benchmark - Evaluates app weight for Raspberry Pi 5 (8GB)
# Usage: ./scripts/benchmark.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   🔬 Edge Device Analysis${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Build first
echo -e "${YELLOW}Building production bundle...${NC}"
pnpm build > /dev/null 2>&1

# Metrics with Pi 5 thresholds
# Thresholds based on Pi 5 8GB specs: 2.4GHz Cortex-A76, 8GB RAM

echo -e "${BLUE}Analyzing metrics...${NC}"
echo ""

TOTAL_SCORE=0
METRICS_COUNT=5

# 1. Client bundle size (target: <500KB, excellent: <100KB)
CLIENT_SIZE=$(du -sk .svelte-kit/output/client 2>/dev/null | cut -f1)
if [ "$CLIENT_SIZE" -lt 100 ]; then
  CLIENT_SCORE=100
elif [ "$CLIENT_SIZE" -lt 250 ]; then
  CLIENT_SCORE=90
elif [ "$CLIENT_SIZE" -lt 500 ]; then
  CLIENT_SCORE=75
elif [ "$CLIENT_SIZE" -lt 1000 ]; then
  CLIENT_SCORE=50
else
  CLIENT_SCORE=25
fi
TOTAL_SCORE=$((TOTAL_SCORE + CLIENT_SCORE))
echo -e "📦 Client Bundle:    ${CLIENT_SIZE}KB $([ $CLIENT_SCORE -ge 75 ] && echo -e "${GREEN}($CLIENT_SCORE/100)${NC}" || echo -e "${YELLOW}($CLIENT_SCORE/100)${NC}")"

# 2. Server bundle size (target: <2MB, excellent: <500KB)
SERVER_SIZE=$(du -sk .svelte-kit/output/server 2>/dev/null | cut -f1)
if [ "$SERVER_SIZE" -lt 500 ]; then
  SERVER_SCORE=100
elif [ "$SERVER_SIZE" -lt 1000 ]; then
  SERVER_SCORE=85
elif [ "$SERVER_SIZE" -lt 2000 ]; then
  SERVER_SCORE=70
elif [ "$SERVER_SIZE" -lt 5000 ]; then
  SERVER_SCORE=50
else
  SERVER_SCORE=25
fi
TOTAL_SCORE=$((TOTAL_SCORE + SERVER_SCORE))
echo -e "🖥️  Server Bundle:    ${SERVER_SIZE}KB $([ $SERVER_SCORE -ge 75 ] && echo -e "${GREEN}($SERVER_SCORE/100)${NC}" || echo -e "${YELLOW}($SERVER_SCORE/100)${NC}")"

# 3. Total JS files count (fewer = faster startup)
JS_COUNT=$(find .svelte-kit/output/client -name "*.js" | wc -l | tr -d ' ')
if [ "$JS_COUNT" -lt 15 ]; then
  JS_SCORE=100
elif [ "$JS_COUNT" -lt 25 ]; then
  JS_SCORE=85
elif [ "$JS_COUNT" -lt 40 ]; then
  JS_SCORE=70
elif [ "$JS_COUNT" -lt 60 ]; then
  JS_SCORE=50
else
  JS_SCORE=30
fi
TOTAL_SCORE=$((TOTAL_SCORE + JS_SCORE))
echo -e "📄 JS Chunks:        ${JS_COUNT} files $([ $JS_SCORE -ge 75 ] && echo -e "${GREEN}($JS_SCORE/100)${NC}" || echo -e "${YELLOW}($JS_SCORE/100)${NC}")"

# 4. Dependencies count (fewer = smaller attack surface, faster installs)
DEP_COUNT=$(cat package.json | grep -c '"@\|"[a-z]' 2>/dev/null || echo 0)
if [ "$DEP_COUNT" -lt 15 ]; then
  DEP_SCORE=100
elif [ "$DEP_COUNT" -lt 25 ]; then
  DEP_SCORE=85
elif [ "$DEP_COUNT" -lt 35 ]; then
  DEP_SCORE=70
elif [ "$DEP_COUNT" -lt 50 ]; then
  DEP_SCORE=50
else
  DEP_SCORE=30
fi
TOTAL_SCORE=$((TOTAL_SCORE + DEP_SCORE))
echo -e "📚 Dependencies:     ${DEP_COUNT} packages $([ $DEP_SCORE -ge 75 ] && echo -e "${GREEN}($DEP_SCORE/100)${NC}" || echo -e "${YELLOW}($DEP_SCORE/100)${NC}")"

# 5. Estimated memory (based on bundle size heuristic)
# Rough estimate: 10x bundle size for runtime memory
EST_MEMORY=$((($CLIENT_SIZE + $SERVER_SIZE) * 10 / 1024))
if [ "$EST_MEMORY" -lt 50 ]; then
  MEM_SCORE=100
elif [ "$EST_MEMORY" -lt 100 ]; then
  MEM_SCORE=90
elif [ "$EST_MEMORY" -lt 200 ]; then
  MEM_SCORE=75
elif [ "$EST_MEMORY" -lt 500 ]; then
  MEM_SCORE=50
else
  MEM_SCORE=25
fi
TOTAL_SCORE=$((TOTAL_SCORE + MEM_SCORE))
echo -e "🧠 Est. Memory:      ~${EST_MEMORY}MB $([ $MEM_SCORE -ge 75 ] && echo -e "${GREEN}($MEM_SCORE/100)${NC}" || echo -e "${YELLOW}($MEM_SCORE/100)${NC}")"

# Calculate final score
FINAL_SCORE=$((TOTAL_SCORE / METRICS_COUNT))

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Grade
if [ "$FINAL_SCORE" -ge 90 ]; then
  GRADE="A+"
  COLOR=$GREEN
  VERDICT="Excellent for Pi 5! Ultra-lightweight."
elif [ "$FINAL_SCORE" -ge 80 ]; then
  GRADE="A"
  COLOR=$GREEN
  VERDICT="Great for Pi 5. Very responsive."
elif [ "$FINAL_SCORE" -ge 70 ]; then
  GRADE="B"
  COLOR=$GREEN
  VERDICT="Good for Pi 5. Should run smoothly."
elif [ "$FINAL_SCORE" -ge 60 ]; then
  GRADE="C"
  COLOR=$YELLOW
  VERDICT="Acceptable. May need optimization."
elif [ "$FINAL_SCORE" -ge 50 ]; then
  GRADE="D"
  COLOR=$YELLOW
  VERDICT="Heavy. Consider reducing bundle size."
else
  GRADE="F"
  COLOR=$RED
  VERDICT="Too heavy for Pi 5. Needs major optimization."
fi

echo -e "   ${COLOR}FINAL SCORE: ${FINAL_SCORE}/100 (${GRADE})${NC}"
echo -e "   ${VERDICT}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "Thresholds based on Raspberry Pi 5 (8GB) specs:"
echo -e "  • 2.4GHz Cortex-A76 quad-core"
echo -e "  • 8GB LPDDR4X RAM"
echo -e "  • Target: <100MB runtime memory, <1MB bundle"

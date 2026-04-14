#!/bin/bash

skills=(
  "summarize"
  "tavily-web-search-for-openclaw"
  "baoyu"
  "skill-creator"
  "self-improving-agent"
  "find-skills"
  "marketing-skills"
)

install_with_retry() {
  local skill=$1
  while true; do
    echo "Installing $skill..."
    if clawhub install "$skill"; then
      echo "✅ Successfully installed $skill"
      return 0
    else
      if clawhub install "$skill" 2>&1 | grep -q "rate limit"; then
        echo "⚠️ Rate limit hit for $skill. Waiting 1 hour to retry..."
        sleep 3600
      else
        echo "❌ Failed to install $skill (unexpected error)"
        return 1
      fi
    fi
  done
}

for skill in "${skills[@]}"; do
  if ! install_with_retry "$skill"; then
    echo "Error: Failed to install $skill after retries" >&2
    exit 1
  fi
done

echo "All skills installed successfully!"
clawhub list
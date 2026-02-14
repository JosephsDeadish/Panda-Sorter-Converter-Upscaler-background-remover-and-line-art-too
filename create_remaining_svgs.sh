#!/bin/bash

cd /home/runner/work/PS2-texture-sorter/PS2-texture-sorter/src/resources/icons/svg

# Success check animated
cat > success_check_animated.svg << 'EOF'
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <circle cx="12" cy="12" r="10" fill="none" stroke="#10B981" stroke-width="2">
    <animate attributeName="stroke-dasharray" from="0 63" to="63 0" dur="0.5s" fill="freeze"/>
  </circle>
  <path d="M8 12 L11 15 L16 9" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="12" stroke-dashoffset="12">
    <animate attributeName="stroke-dashoffset" from="12" to="0" dur="0.3s" begin="0.5s" fill="freeze"/>
  </path>
</svg>
EOF

# Warning triangle animated
cat > warning_triangle_animated.svg << 'EOF'
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <path d="M12 2 L22 20 L2 20 Z" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linejoin="round">
    <animate attributeName="opacity" values="0.6;1;0.6" dur="2s" repeatCount="indefinite"/>
  </path>
  <circle cx="12" cy="16" r="1" fill="#F59E0B">
    <animate attributeName="r" values="1;1.3;1" dur="2s" repeatCount="indefinite"/>
  </circle>
  <line x1="12" y1="9" x2="12" y2="13" stroke="#F59E0B" stroke-width="2" stroke-linecap="round">
    <animate attributeName="opacity" values="0.6;1;0.6" dur="2s" repeatCount="indefinite"/>
  </line>
</svg>
EOF

# Error cross animated
cat > error_cross_animated.svg << 'EOF'
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <circle cx="12" cy="12" r="10" fill="none" stroke="#EF4444" stroke-width="2">
    <animate attributeName="stroke-dasharray" from="0 63" to="63 0" dur="0.5s" fill="freeze"/>
  </circle>
  <line x1="8" y1="8" x2="16" y2="16" stroke="#EF4444" stroke-width="2" stroke-linecap="round" opacity="0">
    <animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="0.5s" fill="freeze"/>
  </line>
  <line x1="16" y1="8" x2="8" y2="16" stroke="#EF4444" stroke-width="2" stroke-linecap="round" opacity="0">
    <animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="0.5s" fill="freeze"/>
  </line>
</svg>
EOF

# Progress spinner animated
cat > progress_spinner_animated.svg << 'EOF'
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <circle cx="12" cy="12" r="10" fill="none" stroke="#E5E7EB" stroke-width="2"/>
  <path d="M12 2 A10 10 0 0 1 22 12" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linecap="round">
    <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
  </path>
</svg>
EOF

# Clock ticking animated
cat > clock_ticking_animated.svg << 'EOF'
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <circle cx="12" cy="12" r="10" fill="none" stroke="#64748B" stroke-width="2"/>
  <line x1="12" y1="12" x2="12" y2="7" stroke="#3B82F6" stroke-width="2" stroke-linecap="round">
    <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="12s" repeatCount="indefinite"/>
  </line>
  <line x1="12" y1="12" x2="16" y2="12" stroke="#10B981" stroke-width="2" stroke-linecap="round">
    <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
  </line>
</svg>
EOF

# File new animated
cat > file_new_animated.svg << 'EOF'
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <path d="M14 2 H6 C4.9 2 4 2.9 4 4 V20 C4 21.1 4.9 22 6 22 H18 C19.1 22 20 21.1 20 20 V8 L14 2 Z" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linejoin="round" opacity="0">
    <animate attributeName="opacity" from="0" to="1" dur="0.5s" fill="freeze"/>
  </path>
  <path d="M14 2 V8 H20" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linejoin="round" opacity="0">
    <animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="0.5s" fill="freeze"/>
  </path>
  <line x1="12" y1="11" x2="12" y2="17" stroke="#10B981" stroke-width="2" stroke-linecap="round" opacity="0">
    <animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="0.8s" fill="freeze"/>
  </line>
  <line x1="9" y1="14" x2="15" y2="14" stroke="#10B981" stroke-width="2" stroke-linecap="round" opacity="0">
    <animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="0.8s" fill="freeze"/>
  </line>
</svg>
EOF

# Color picker animated
cat > color_picker_animated.svg << 'EOF'
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <circle cx="12" cy="12" r="10" fill="none" stroke="#94A3B8" stroke-width="2"/>
  <path d="M12 12 L12 2" fill="none" stroke="#EF4444" stroke-width="2" stroke-linecap="round"/>
  <path d="M12 12 L19.6 8" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linecap="round"/>
  <path d="M12 12 L19.6 16" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round"/>
  <path d="M12 12 L12 22" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linecap="round"/>
  <circle cx="12" cy="12" r="2" fill="#8B5CF6">
    <animate attributeName="r" values="2;3;2" dur="2s" repeatCount="indefinite"/>
  </circle>
  <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="4s" repeatCount="indefinite"/>
</svg>
EOF

# Zoom in animated
cat > zoom_in_animated.svg << 'EOF'
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <circle cx="10" cy="10" r="7" fill="none" stroke="#3B82F6" stroke-width="2">
    <animate attributeName="r" values="7;8;7" dur="2s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"/>
  </circle>
  <line x1="15" y1="15" x2="20" y2="20" stroke="#3B82F6" stroke-width="2" stroke-linecap="round"/>
  <line x1="10" y1="7" x2="10" y2="13" stroke="#10B981" stroke-width="2" stroke-linecap="round">
    <animate attributeName="opacity" values="0.5;1;0.5" dur="2s" repeatCount="indefinite"/>
  </line>
  <line x1="7" y1="10" x2="13" y2="10" stroke="#10B981" stroke-width="2" stroke-linecap="round">
    <animate attributeName="opacity" values="0.5;1;0.5" dur="2s" repeatCount="indefinite"/>
  </line>
</svg>
EOF

# Chevron left animated
cat > chevron_left_animated.svg << 'EOF'
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <polyline points="15,18 9,12 15,6" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <animate attributeName="points" values="15,18 9,12 15,6;13,18 7,12 13,6;15,18 9,12 15,6" dur="1s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"/>
  </polyline>
</svg>
EOF

# Chevron right animated
cat > chevron_right_animated.svg << 'EOF'
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <polyline points="9,18 15,12 9,6" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <animate attributeName="points" values="9,18 15,12 9,6;11,18 17,12 11,6;9,18 15,12 9,6" dur="1s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"/>
  </polyline>
</svg>
EOF

echo "Created 10 additional animated SVGs"

#!/data/data/com.termux/files/usr/bin/bash

echo "🚀 Optimizando S20 FE para Free Fire..."

# Cerrar apps en segundo plano
echo "❌ Cerrando procesos..."
am kill-all

# Limpiar caché de Free Fire (opcional, no borra datos de la cuenta)
echo "🧹 Limpiando caché del juego..."
pm clear com.dts.freefireth

# Desactivar animaciones para respuesta más rápida
echo "⚡ Desactivando animaciones..."
settings put global window_animation_scale 0
settings put global transition_animation_scale 0
settings put global animator_duration_scale 0

# Forzar máximo rendimiento (CPU/GPU activos al máximo)
echo "💪 Forzando máximo rendimiento del CPU..."
cmd power stayon true

echo "✅ Optimización lista. Abre Free Fire y disfruta."


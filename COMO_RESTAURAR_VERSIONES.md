# 🔄 Guía de Restauración de Versiones

## 📌 Puntos de Restauración Importantes

Esta es la lista de versiones estables que puedes restaurar en cualquier momento:

### ✅ **VERSIÓN ACTUAL (Recomendada)**

- **Hash:** `e6b6581`
- **Fecha:** 2026-01-13 08:03 AM
- **Descripción:** Versión estable con búsqueda mejorada (rutas completas)
- **Incluye:**
  - ✅ Búsqueda global con rutas jerárquicas completas
  - ✅ Modo rápido de transcripción (Quick Mode)
  - ✅ Notificación de audio al completar transcripción
  - ✅ Espaciado UI optimizado
  - ✅ Límite de carga: 200MB (estable)

---

### 🎯 Otras Versiones Disponibles

#### **Versión: Quick Mode + Audio**

- **Hash:** `74bedca`
- **Fecha:** 2026-01-13 07:53 AM
- **Descripción:** Primera versión con modo rápido de transcripción
- **Diferencia:** No incluye búsqueda mejorada con rutas completas

#### **Versión: Audio Notification**

- **Hash:** `4578a7e`
- **Fecha:** 2026-01-13 07:37 AM
- **Descripción:** Sistema de audio HTML5 para notificaciones
- **Diferencia:** No incluye Quick Mode ni búsqueda mejorada

#### **Versión: Estable Pre-Features**

- **Hash:** `693b7f8`
- **Fecha:** 2026-01-13 06:50 AM
- **Descripción:** Versión estable antes de nuevas funcionalidades
- **Diferencia:** Sin Quick Mode, sin audio, sin búsqueda mejorada

#### **Versión: UI Assets Restaurados**

- **Hash:** `28e1531`
- **Fecha:** 2026-01-12 16:26 PM
- **Descripción:** Versión con todos los assets UI restaurados
- **Diferencia:** Versión del día anterior, sin nuevas features

---

## 🚀 Cómo Restaurar una Versión

### **Método 1: Por Hash (Más Preciso)**

Simplemente dime:
> "Restaura la versión `e6b6581`"

### **Método 2: Por Descripción**

Dime qué característica quieres:
> "Vuelve a la versión antes del Quick Mode"
> "Restaura la versión con audio pero sin Quick Mode"

### **Método 3: Por Fecha/Hora**

Dime cuándo funcionaba bien:
> "Vuelve a la versión de las 8:00 AM de hoy"
> "Restaura la versión de ayer por la tarde"

---

## 📋 Proceso Técnico (Lo que yo hago)

Cuando me pides restaurar una versión:

1. **Identifico el commit** usando el hash, fecha o descripción
2. **Ejecuto:** `git reset --hard [hash]`
3. **Despliego:** `git push --force`
4. **Esperas:** 2-3 minutos para que Streamlit Cloud actualice
5. **Recargas:** Ctrl+Shift+R en el navegador

---

## ⚠️ Importante

### **Backups ZIP (NO RECOMENDADO)**

- ❌ Los archivos `create_backup.py` y los ZIP en `/backups/` **NO son confiables**
- ❌ Son muy grandes (300+ GB) y se corrompen fácilmente
- ✅ **Usa Git en su lugar** - es instantáneo y nunca falla

### **Git es tu Mejor Amigo**

- ✅ Cada commit es un punto de restauración automático
- ✅ Puedo volver a cualquier versión en segundos
- ✅ Nunca pierdes código
- ✅ Historial completo de cambios

---

## 🎯 Mejores Prácticas

### **Antes de Hacer Cambios Grandes:**

Dime:
> "Guarda esta versión como punto de restauración"

Y yo haré un commit con un mensaje descriptivo que podrás usar después.

### **Si Algo Sale Mal:**

Dime:
> "Vuelve a la última versión estable"

Y restauraré el último punto de restauración marcado.

### **Para Ver Todas las Versiones:**

Dime:
> "Muéstrame las últimas 10 versiones"

Y te daré una lista con hashes, fechas y descripciones.

---

## 📞 Ejemplos de Uso

**Ejemplo 1:**
> **Tú:** "Guarda esta versión antes de hacer cambios"
> **Yo:** "✅ Guardado como commit `abc1234`: 'Versión estable pre-cambios UI'"

**Ejemplo 2:**
> **Tú:** "Algo se rompió, vuelve a la versión de esta mañana"
> **Yo:** "✅ Restaurando versión `e6b6581` (08:03 AM)..."

**Ejemplo 3:**
> **Tú:** "Muéstrame las versiones de ayer"
> **Yo:** [Lista de commits del 12 de enero]

---

## 🔧 Mantenimiento

Este documento se actualiza automáticamente cuando:

- Se agregan nuevas funcionalidades importantes
- Se marca un nuevo punto de restauración
- Se identifica una versión especialmente estable

**Última actualización:** 2026-01-13 09:53 AM

#!/usr/bin/env python3
"""
Misión 2030 Bot - Bot de seguimiento del plan de vida
Token: configurado via variable de entorno o directamente
"""

import logging
import json
import os
from datetime import datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ─── CONFIG ───────────────────────────────────────────────────────────────────
TOKEN = "8448517947:AAEmrhMbfhqcGHhtCfiLSI2KSTISO0RLupg"
CHAT_ID = 1002101175
DATA_FILE = "data.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── DATOS DEL PLAN ───────────────────────────────────────────────────────────
FASES = {
    1: "🔴 F1 · Cimientos (0-3 meses) — Primeros ingresos",
    2: "🟡 F2 · Estabilidad (3-9 meses) — Ingresos recurrentes",
    3: "🟢 F3 · Crecimiento (9-24 meses) — Escalar negocio",
    4: "🔵 F4 · Automatización (2-4 años) — Sistemas",
    5: "⭐ F5 · Libertad (4-5 años) — $20,000+/mes",
}

CHECKLIST_DIARIO = {
    "gym": "💪 Gym / ejercicio hoy",
    "contenido": "🎬 Crear o publicar contenido",
    "freelance": "💼 Trabajar en proyecto/cliente",
    "hija": "❤️ Hora sagrada con mi hija",
    "estudio": "📚 Estudiar (tecnología / negocio)",
    "meta_ingreso": "💰 Acción concreta hacia ingresos",
}

METAS_90_DIAS = [
    "Perfil activo en Workana/Fiverr/Upwork",
    "Primer cliente freelance conseguido",
    "Canal YouTube/TikTok con 4+ videos",
    "Primer ingreso freelance recibido",
    "Nicho exacto definido y documentado",
    "Rutina de gym 3x/semana establecida",
]

# ─── GESTIÓN DE DATOS ─────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "fase_actual": 1,
        "ingresos_mes": 0,
        "deuda_total": 0,
        "checklists": {},
        "metas_90": {m: False for m in METAS_90_DIAS},
        "registro_ingresos": [],
        "notas": [],
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_today():
    return datetime.now().strftime("%Y-%m-%d")

def get_checklist_hoy(data):
    hoy = get_today()
    if hoy not in data["checklists"]:
        data["checklists"][hoy] = {k: False for k in CHECKLIST_DIARIO}
        save_data(data)
    return data["checklists"][hoy]

def porcentaje_checklist(checklist):
    completados = sum(1 for v in checklist.values() if v)
    return int((completados / len(checklist)) * 100)

# ─── COMANDOS ─────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    fase = data["fase_actual"]
    texto = (
        "🎯 *MISIÓN 2030 — Activado*\n\n"
        f"Fase actual: {FASES[fase]}\n\n"
        "Comandos disponibles:\n"
        "/hoy — Checklist del día\n"
        "/resumen — Estado general del plan\n"
        "/ingreso — Registrar ingreso\n"
        "/metas — Ver metas 90 días\n"
        "/fase — Cambiar fase activa\n"
        "/semana — Resumen semanal\n"
        "/nota — Guardar una nota\n"
        "/ayuda — Ver todos los comandos\n\n"
        "💡 *Prioridad ahora:* Primeros ingresos en 90 días."
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

async def hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    checklist = get_checklist_hoy(data)
    pct = porcentaje_checklist(checklist)
    fecha = datetime.now().strftime("%A %d de %B")

    keyboard = []
    for key, label in CHECKLIST_DIARIO.items():
        estado = "✅" if checklist[key] else "⬜"
        keyboard.append([InlineKeyboardButton(
            f"{estado} {label}",
            callback_data=f"check_{key}"
        )])
    keyboard.append([InlineKeyboardButton("📊 Ver progreso", callback_data="ver_progreso")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"📋 *Checklist · {fecha}*\n"
        f"Progreso: {pct}% completado\n\n"
        "Toca cada ítem para marcarlo:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def toggle_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "ver_progreso":
        await resumen_callback(update, context)
        return

    key = query.data.replace("check_", "")
    data = load_data()
    checklist = get_checklist_hoy(data)

    if key in checklist:
        checklist[key] = not checklist[key]
        data["checklists"][get_today()] = checklist
        save_data(data)

    pct = porcentaje_checklist(checklist)
    keyboard = []
    for k, label in CHECKLIST_DIARIO.items():
        estado = "✅" if checklist[k] else "⬜"
        keyboard.append([InlineKeyboardButton(
            f"{estado} {label}",
            callback_data=f"check_{k}"
        )])
    keyboard.append([InlineKeyboardButton("📊 Ver progreso", callback_data="ver_progreso")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    fecha = datetime.now().strftime("%A %d de %B")

    emoji = "🔥" if pct == 100 else "💪" if pct >= 50 else "⚡"
    await query.edit_message_text(
        f"📋 *Checklist · {fecha}*\n"
        f"{emoji} Progreso: {pct}% completado\n\n"
        "Toca cada ítem para marcarlo:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def resumen_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = load_data()
    checklist = get_checklist_hoy(data)
    pct = porcentaje_checklist(checklist)
    fase = data["fase_actual"]
    ingresos = data.get("ingresos_mes", 0)

    texto = (
        f"📊 *Estado del Plan — {get_today()}*\n\n"
        f"Fase: {FASES[fase]}\n"
        f"Ingresos este mes: ${ingresos:,} USD\n"
        f"Checklist hoy: {pct}%\n\n"
        f"Usa /resumen para ver el detalle completo."
    )
    await query.answer(texto, show_alert=True)

async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    fase = data["fase_actual"]
    ingresos = data.get("ingresos_mes", 0)
    deuda = data.get("deuda_total", 0)

    # Calcular racha
    racha = 0
    fecha = datetime.now()
    for i in range(30):
        dia = (fecha.replace(day=fecha.day - i) if fecha.day > i
               else datetime.now()).strftime("%Y-%m-%d")
        check = data["checklists"].get(dia, {})
        if check and porcentaje_checklist(check) >= 80:
            racha += 1
        else:
            break

    # Metas 90 días
    metas = data.get("metas_90", {})
    metas_ok = sum(1 for v in metas.values() if v)
    total_metas = len(metas)

    # Checklist hoy
    checklist_hoy = get_checklist_hoy(data)
    pct_hoy = porcentaje_checklist(checklist_hoy)

    texto = (
        "📊 *RESUMEN — MISIÓN 2030*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 *Fase actual:*\n{FASES[fase]}\n\n"
        f"💰 *Ingresos este mes:* ${ingresos:,} USD\n"
        f"💳 *Deuda registrada:* ${deuda:,} USD\n\n"
        f"📋 *Checklist hoy:* {pct_hoy}%\n"
        f"🔥 *Racha de días ≥80%:* {racha} días\n\n"
        f"🎯 *Metas 90 días:* {metas_ok}/{total_metas} completadas\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Usa /metas para ver detalle de los 90 días."
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

async def ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "💰 *Registrar ingreso*\n\n"
            "Uso: `/ingreso [monto] [descripción]`\n"
            "Ejemplo: `/ingreso 150 Edición de video cliente Juan`",
            parse_mode="Markdown"
        )
        return

    try:
        monto = float(context.args[0])
        descripcion = " ".join(context.args[1:]) if len(context.args) > 1 else "Sin descripción"
        data = load_data()
        data["ingresos_mes"] = data.get("ingresos_mes", 0) + monto
        data["registro_ingresos"].append({
            "fecha": get_today(),
            "monto": monto,
            "descripcion": descripcion
        })
        save_data(data)

        total = data["ingresos_mes"]
        meta_mes = 500
        pct = min(int((total / meta_mes) * 100), 100)
        barra = "█" * (pct // 10) + "░" * (10 - pct // 10)

        await update.message.reply_text(
            f"✅ *Ingreso registrado*\n\n"
            f"💵 Monto: *${monto:,} USD*\n"
            f"📝 {descripcion}\n\n"
            f"📈 *Total este mes: ${total:,} USD*\n"
            f"Meta: ${meta_mes} USD\n"
            f"`[{barra}] {pct}%`\n\n"
            f"{'🔥 ¡Meta del mes alcanzada!' if total >= meta_mes else f'Faltan ${meta_mes - total:,.0f} para la meta'}",
            parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text("❌ El monto debe ser un número. Ej: `/ingreso 150 descripción`", parse_mode="Markdown")

async def metas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    metas_data = data.get("metas_90", {m: False for m in METAS_90_DIAS})

    keyboard = []
    for meta, completada in metas_data.items():
        estado = "✅" if completada else "⬜"
        keyboard.append([InlineKeyboardButton(
            f"{estado} {meta[:45]}",
            callback_data=f"meta_{METAS_90_DIAS.index(meta)}"
        )])

    completadas = sum(1 for v in metas_data.values() if v)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🎯 *METAS 90 DÍAS — Fase 1*\n\n"
        f"Completadas: {completadas}/{len(METAS_90_DIAS)}\n\n"
        "Toca para marcar como completada:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def toggle_meta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    idx = int(query.data.replace("meta_", ""))
    meta_key = METAS_90_DIAS[idx]

    data = load_data()
    if "metas_90" not in data:
        data["metas_90"] = {m: False for m in METAS_90_DIAS}

    data["metas_90"][meta_key] = not data["metas_90"].get(meta_key, False)
    save_data(data)

    metas_data = data["metas_90"]
    keyboard = []
    for meta, completada in metas_data.items():
        estado = "✅" if completada else "⬜"
        keyboard.append([InlineKeyboardButton(
            f"{estado} {meta[:45]}",
            callback_data=f"meta_{METAS_90_DIAS.index(meta)}"
        )])

    completadas = sum(1 for v in metas_data.values() if v)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"🎯 *METAS 90 DÍAS — Fase 1*\n\n"
        f"Completadas: {completadas}/{len(METAS_90_DIAS)}\n\n"
        "Toca para marcar como completada:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def fase_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(texto, callback_data=f"fase_{num}")]
                for num, texto in FASES.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🗺 *¿En qué fase estás ahora?*\n\nSelecciona tu fase actual:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def toggle_fase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    num = int(query.data.replace("fase_", ""))
    data = load_data()
    data["fase_actual"] = num
    save_data(data)
    await query.edit_message_text(
        f"✅ *Fase actualizada*\n\n{FASES[num]}\n\nUsa /resumen para ver tu estado completo.",
        parse_mode="Markdown"
    )

async def semana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    hoy = datetime.now()
    resumen_dias = []
    total_pct = 0
    dias_con_data = 0

    for i in range(7):
        try:
            delta = hoy.replace(day=hoy.day - i)
        except ValueError:
            continue
        dia_str = delta.strftime("%Y-%m-%d")
        dia_label = delta.strftime("%a %d")
        check = data["checklists"].get(dia_str, {})
        if check:
            pct = porcentaje_checklist(check)
            total_pct += pct
            dias_con_data += 1
            emoji = "🔥" if pct >= 80 else "✅" if pct >= 50 else "⚠️"
            resumen_dias.append(f"{emoji} {dia_label}: {pct}%")
        else:
            resumen_dias.append(f"⬛ {dia_label}: sin datos")

    promedio = int(total_pct / dias_con_data) if dias_con_data > 0 else 0
    ingresos_semana = sum(
        r["monto"] for r in data.get("registro_ingresos", [])
        if r["fecha"] >= (hoy.replace(day=hoy.day - 7)).strftime("%Y-%m-%d")
    )

    texto = (
        "📅 *RESUMEN SEMANAL*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        + "\n".join(reversed(resumen_dias)) +
        f"\n\n📊 Promedio semanal: {promedio}%\n"
        f"💰 Ingresos esta semana: ${ingresos_semana:,} USD\n\n"
        f"{'🔥 ¡Semana excelente!' if promedio >= 80 else '💪 Sigue construyendo.' if promedio >= 50 else '⚡ Esta semana hay que subir el nivel.'}"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

async def nota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "📝 *Guardar nota*\n\nUso: `/nota [tu nota]`\nEjemplo: `/nota Hoy conseguí un lead de cliente`",
            parse_mode="Markdown"
        )
        return
    texto_nota = " ".join(context.args)
    data = load_data()
    data["notas"].append({"fecha": get_today(), "nota": texto_nota})
    save_data(data)
    await update.message.reply_text(f"📝 *Nota guardada*\n\n_{texto_nota}_", parse_mode="Markdown")

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "🤖 *MISIÓN 2030 BOT — Comandos*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "/start — Bienvenida y estado\n"
        "/hoy — ✅ Checklist diario interactivo\n"
        "/resumen — 📊 Estado general del plan\n"
        "/semana — 📅 Resumen de los últimos 7 días\n"
        "/metas — 🎯 Metas de los 90 días críticos\n"
        "/ingreso [monto] [desc] — 💰 Registrar ingreso\n"
        "/fase — 🗺 Cambiar fase del plan\n"
        "/nota [texto] — 📝 Guardar una nota\n"
        "/ayuda — Este menú\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 *Prioridad #1:* Primer ingreso en 90 días.\n"
        "_Todo lo demás se construye sobre esa base._"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

async def recordatorio_manana(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=(
            "⚡ *5:30 AM — Hora de activar*\n\n"
            "Recuerda: tu hija está contando contigo.\n"
            "Usa /hoy para abrir el checklist del día.\n\n"
            "_Un día a la vez. Un peso a la vez._"
        ),
        parse_mode="Markdown"
    )

async def recordatorio_noche(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=(
            "🌙 *9:00 PM — Cierre del día*\n\n"
            "¿Cerraste el checklist? Usa /hoy\n"
            "¿Generaste algún ingreso? Usa /ingreso\n"
            "¿Algo importante del día? Usa /nota\n\n"
            "Mañana es otro día para construir."
        ),
        parse_mode="Markdown"
    )

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hoy", hoy))
    app.add_handler(CommandHandler("resumen", resumen))
    app.add_handler(CommandHandler("ingreso", ingreso))
    app.add_handler(CommandHandler("metas", metas))
    app.add_handler(CommandHandler("fase", fase_cmd))
    app.add_handler(CommandHandler("semana", semana))
    app.add_handler(CommandHandler("nota", nota))
    app.add_handler(CommandHandler("ayuda", ayuda))

    # Callbacks
    app.add_handler(CallbackQueryHandler(toggle_check, pattern="^check_"))
    app.add_handler(CallbackQueryHandler(toggle_check, pattern="^ver_progreso"))
    app.add_handler(CallbackQueryHandler(toggle_meta, pattern="^meta_"))
    app.add_handler(CallbackQueryHandler(toggle_fase, pattern="^fase_"))

    # Recordatorios diarios
    job_queue = app.job_queue
    job_queue.run_daily(recordatorio_manana, time=time(5, 30), name="manana")
    job_queue.run_daily(recordatorio_noche, time=time(21, 0), name="noche")

    logger.info("🚀 Misión 2030 Bot arrancado")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

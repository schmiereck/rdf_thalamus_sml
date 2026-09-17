#!/usr/bin/env bash
# SessionStart-Haken: Projekt aktualisieren und das Agenten-Board in den Kontext legen.
#
# WARUM: an diesem Projekt arbeiten mehrere Agents in getrennten Git-Worktrees (s. CLAUDE.md,
# Abschnitt "Agentenkoordination").  Ohne diesen Haken bekommt eine neue Sitzung Nachrichten und
# Statusaenderungen der anderen nur mit, wenn jemand daran denkt, sie zu lesen.
#
# NEU heisst: geaendert seit dem letzten Sitzungsstart.  Der Zeitstempel dafuer liegt AUSSERHALB
# beider Git-Repositories (~/.claude/), damit der Haken weder den Arbeitsbaum des Projekts noch
# den des Boards verschmutzt.
#
# Ausgabe: JSON mit hookSpecificOutput.additionalContext.  KEIN jq -- das ist auf diesem Rechner
# nicht installiert, und ein Haken, der an einem fehlenden Werkzeug scheitert, ist schlimmer als
# keiner.  Deshalb wird von Hand escaped.
set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
board="$(cd "$repo/.." 2>/dev/null && pwd)/rdf_thalamus_sml_coordination"
marke="${HOME}/.claude/board-seen-$(basename "$repo")"
GRENZE=8000          # Zeichen; darueber wird abgeschnitten, damit der Kontext nicht ueberlaeuft

txt=""
add() { txt="${txt}${1}"$'\n'; }

# ---------------------------------------------------------------- Projekt aktualisieren
add "## Projekt aktualisiert (SessionStart-Haken)"
if ! git -C "$repo" fetch --all --quiet 2>/dev/null; then
  add "git fetch fehlgeschlagen (offline?) -- der Stand unten kann veraltet sein."
fi
add "HEAD: $(git -C "$repo" log --oneline -1 2>/dev/null || echo unbekannt)"
_neu="$(git -C "$repo" log --oneline HEAD..@{upstream} 2>/dev/null | head -10)"
if [ -n "$_neu" ]; then
  add ""
  add "Auf dem Remote, noch NICHT lokal:"
  add "$_neu"
fi
_wt="$(git -C "$repo" worktree list 2>/dev/null | tail -n +2)"
if [ -n "$_wt" ]; then
  add ""
  add "Weitere Worktrees (dort arbeiten andere Agents):"
  add "$_wt"
  # Was steht auf deren Zweigen, das main nicht hat?
  for _b in $(git -C "$repo" worktree list --porcelain 2>/dev/null \
              | sed -n 's|^branch refs/heads/||p'); do
    [ "$_b" = "$(git -C "$repo" rev-parse --abbrev-ref HEAD 2>/dev/null)" ] && continue
    _o="$(git -C "$repo" log --oneline "HEAD..$_b" 2>/dev/null | head -5)"
    [ -n "$_o" ] && { add ""; add "Zweig $_b hat gegenueber HEAD:"; add "$_o"; }
  done
fi

# ---------------------------------------------------------------- Board
if [ -d "$board" ]; then
  git -C "$board" pull --rebase --quiet 2>/dev/null || true
  add ""
  add "## Agenten-Board: $board"
  add "Protokoll in dessen README.md.  Nachrichten sind UNVERAENDERLICH -- Korrekturen sind neue"
  add "Dateien, nie Bearbeitungen.  Nur die eigene status/<agent>.md wird fortgeschrieben."

  add ""
  add "### Status aller Agents"
  for s in "$board"/status/*.md; do
    [ -e "$s" ] || continue
    add ""
    add "----- $(basename "$s") -----"
    add "$(tr -d '\r' < "$s" | head -40)"
  done

  add ""
  add "### Nachrichten"
  _alle="$(ls -1 "$board"/messages/*.md 2>/dev/null | sort -r)"
  if [ -z "$_alle" ]; then
    add "(keine)"
  else
    if [ -f "$marke" ]; then
      _frisch="$(find "$board/messages" -name '*.md' -newer "$marke" 2>/dev/null | sort -r)"
    else
      _frisch="$_alle"                       # erster Lauf: alles gilt als neu
    fi
    add ""
    add "Alle Nachrichten, neueste zuerst:"
    printf '%s\n' "$_alle" | while IFS= read -r m; do
      [ -n "$m" ] && echo "  $(basename "$m")"
    done >/dev/null 2>&1
    _liste="$(printf '%s\n' "$_alle" | sed 's|.*/|  |')"
    add "$_liste"
    if [ -n "$_frisch" ]; then
      add ""
      add "NEU seit dem letzten Sitzungsstart -- vollstaendig:"
      printf '%s\n' "$_frisch" | while IFS= read -r m; do
        [ -n "$m" ] || continue
        echo ""
        echo "===== $(basename "$m") ====="
        tr -d '\r' < "$m" | head -60
      done > "${TMPDIR:-/tmp}/board-neu.$$" 2>/dev/null
      add "$(cat "${TMPDIR:-/tmp}/board-neu.$$" 2>/dev/null)"
      rm -f "${TMPDIR:-/tmp}/board-neu.$$"
    else
      add ""
      add "Keine neue Nachricht seit dem letzten Sitzungsstart."
    fi
  fi
  add ""
  add "PFLICHT bei Aufgabenwechsel oder Abschluss: eigene status/<agent>.md fortschreiben,"
  add "Uebergaben als NEUE Datei unter messages/ ablegen, dann im Board committen."
else
  add ""
  add "## Agenten-Board NICHT gefunden unter $board"
  add "CLAUDE.md verlangt es (Abschnitt Agentenkoordination) -- pruefen, ob es umgezogen ist."
fi

# Zeitstempel fortschreiben, damit "neu" beim naechsten Start wieder stimmt
mkdir -p "$(dirname "$marke")" 2>/dev/null
: > "$marke" 2>/dev/null

# ---------------------------------------------------------------- JSON ausgeben
if [ "${#txt}" -gt "$GRENZE" ]; then
  txt="${txt:0:$GRENZE}"$'\n'"[... abgeschnitten, vollstaendig im Board nachlesen]"
fi
esc="$(printf '%s' "$txt" | tr -d '\r' \
        | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\t/\\t/g' \
        | sed -e ':a' -e 'N' -e '$!ba' -e 's/\n/\\n/g')"
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"},"suppressOutput":true}\n' "$esc"

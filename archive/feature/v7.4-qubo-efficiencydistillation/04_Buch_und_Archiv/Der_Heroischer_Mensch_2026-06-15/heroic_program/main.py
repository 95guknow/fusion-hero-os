#!/usr/bin/env python3
"""
DER HEROISCHE MENSCH — Interaktives Programm (Finale stabile Version)
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich import box
import json
import os
import sys
from pathlib import Path
from datetime import datetime

console = Console()
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
EXPORT_DIR = BASE_DIR / "exports"
PHILOSOPHERS_FILE = DATA_DIR / "philosophers_nodes.json"
EXPORT_DIR.mkdir(exist_ok=True)

KEY_PROBLEMS = [
    {"name": "Quantenarme Sättigungsdepression", "original": "Endogene Depression",
     "quant_steps": ["Erkennen: Materiell überversorgt, sozial unterversorgt.", "Hinterfragen: Viele Lösungen sind mimetisch.", "Verinnerlichen: Mangel ist strukturell.", "Kooperieren: Stamm mit echten Verstehensmomenten aufbauen."],
     "mimetik": "Hoch — viele Depressionslösungen imitieren Nähe und Sinn.", "memetik": "Sehr hoch — 'mehr Konsum = weniger Depression' verbreitet sich extrem gut."},
    {"name": "Mimetischer Größenwahn / Surrogat-Selbst", "original": "Narzisstische PS",
     "quant_steps": ["Erkennen: Stark aufgeblähtes Selbstbild bei schwacher Bindung.", "Hinterfragen: Kompensation von altem Mangel.", "Verinnerlichen: Grandioses Selbst ist ein fragiles Surrogat.", "Kooperieren: Echte Begegnungen ohne Spiegelung."],
     "mimetik": "Sehr hoch — Grandiosität imitiert Stärke und Erfolg.", "memetik": "Extrem hoch in Social Media und Startup-Kultur."},
    {"name": "Quanten-oszillierende Bindungsstörung", "original": "Borderline",
     "quant_steps": ["Erkennen: Extreme Schwankungen zwischen Idealisierung und Entwertung.", "Hinterfragen: Schutz vor echtem Gesehenwerden.", "Verinnerlichen: Nie stabile Quanten gelernt.", "Kooperieren: Verlässlicher Stamm + Liebesquant aufbauen."],
     "mimetik": "Hoch — viele Beziehungen sind stark mimetisch.", "memetik": "Hoch in manchen trauma-informed Communities."},
    {"name": "Bindungslose Machtstrategie", "original": "Antisoziale PS",
     "quant_steps": ["Erkennen: Geringe Empathie + hohe instrumentelle Intelligenz.", "Hinterfragen: Oft Folge früherer Gewalt/Enttäuschung.", "Verinnerlichen: Zerstört langfristig jede echte Bindung.", "Kooperieren: Braucht starken äußeren Rahmen."],
     "mimetik": "Hoch — viele Machtstrategien imitieren Rationalität.", "memetik": "Sehr hoch in manchen Business- und Sigma-Male-Milieus."},
    {"name": "Chemischer Surrogat-Quant", "original": "Substanzabhängigkeit",
     "quant_steps": ["Erkennen: Substanz ersetzt echte Zustände.", "Hinterfragen: Effizientes Surrogat für Liebesquant.", "Verinnerlichen: Verhindert echte Quantenentwicklung.", "Kooperieren: Braucht Stamm."],
     "mimetik": "Extrem hoch — die Substanz imitiert echte Gefühle.", "memetik": "Sehr hoch bei funktionalen Suchtformen."}
]

def clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')
def print_header(title, style="bold cyan"): console.print(Panel.fit(f"[bold]{title}[/bold]", style=style, box=box.DOUBLE))
def print_section(title): console.print(f"\n[bold yellow]─── {title} ───[/bold yellow]\n")

def ask_choice(question, options, allow_back=True):
    console.print(f"\n[bold]{question}[/bold]\n")
    for i, opt in enumerate(options[:5], 1):
        console.print(f"  [cyan][{i}][/cyan] {opt}")
    if allow_back:
        console.print("  [dim][0] Zurück[/dim]")
    
    while True:
        try:
            raw = input("\nDeine Wahl: ").strip()
            if raw == "" and allow_back:
                return -1
            choice = int(raw)
            if allow_back and choice == 0:
                return -1
            if 1 <= choice <= min(5, len(options)):
                return choice - 1
            console.print("[red]Bitte eine Zahl zwischen 1 und", min(5, len(options)), "eingeben.[/red]")
        except ValueError:
            console.print("[red]Bitte eine Zahl eingeben.[/red]")

def load_philosophers():
    with open(PHILOSOPHERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("nodes", [])

def export_to_markdown(title, content, prefix="export"):
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    path = EXPORT_DIR / f"{prefix}_{ts}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n*Erstellt am {datetime.now().strftime('%d. %B %Y um %H:%M')}*\n\n{content}")
    console.print(f"\n[green]✅ Exportiert nach:[/green] {path}")

def run_quant_powerful():
    clear_screen()
    print_header("QUANT — Mächtiger Modus mit Rückkopplung", "bold magenta")
    console.print("Unterstützt [italic]iteratives Arbeiten[/italic] mit Rückkopplungsschleife.")
    input("\n[Enter] starten...")

    iteration = 1
    previous = ""
    field = ""
    love_related = False

    while True:
        clear_screen()
        print_header(f"QUANT — Iteration {iteration}", "bold blue")
        if previous:
            console.print(Panel(previous[:320], title="Vorherige Erkenntnisse", border_style="dim"))

        if iteration == 1:
            fields = ["Körper & Embodiment", "Sicherheit & Stabilität", "Paarbindung / Romantische Liebe (Liebesquant)", 
                      "Freundschaft & Stamm (Liebesquant)", "Bewährung & Leistung", "Ausdruck & Kreativität", "Sinn & spirituelle Verbindung"]
            idx = ask_choice("In welchem Bereich spürst du den stärksten Mangel?", fields)
            if idx == -1: return
            field = fields[idx]
            love_related = idx in [2, 3]
        else:
            console.print(f"Aktuelles Feld: [bold]{field}[/bold] (beibehalten)")

        lq = None
        if love_related:
            lq_idx = ask_choice("Wie hoch ist dein aktueller Liebesquant?", ["Sehr hoch", "Mittel", "Niedrig", "Sehr niedrig"])
            if lq_idx != -1: lq = ["Sehr hoch", "Mittel", "Niedrig", "Sehr niedrig"][lq_idx]

        state_idx = ask_choice("Wie ist dein aktueller Zustand?", ["Sehr schlecht", "Eher schlecht", "Mittel / schwankend", "Eher gut", "Sehr gut"])
        if state_idx == -1: return

        blocker_idx = ask_choice("Was blockiert dich am stärksten?", ["Zu wenig echte Verstehensmomente", "Fehlendes Wissen", "Emotionale Blockade", "Äußere Umstände", "Fehlender Stamm"])
        if blocker_idx == -1: return

        clear_screen()
        print_header(f"Zusammenfassung — Iteration {iteration}", "bold green")
        summary = f"[bold]Bereich:[/bold] {field}\n[bold]Zustand:[/bold] {['Sehr schlecht','Eher schlecht','Mittel / schwankend','Eher gut','Sehr gut'][state_idx]}"
        if lq: summary += f"\n[bold]Liebesquant:[/bold] {lq}"
        summary += f"\n[bold]Hauptblockade:[/bold] {['Zu wenig Verstehensmomente','Fehlendes Wissen','Emotionale Blockade','Äußere Umstände','Fehlender Stamm'][blocker_idx]}"
        console.print(Panel(summary, title="Zusammenfassung", border_style="green"))

        if ask_choice("Diese Iteration exportieren?", ["Ja", "Nein"]) == 0:
            export_to_markdown(f"Quant Iteration {iteration}", summary, "quant")

        action = ask_choice("Nächster Schritt?", ["Neue Iteration (Rückkopplung)", "Quant abschließen", "Zurück zum Menü"], allow_back=False)
        if action == 0:
            previous = summary
            iteration += 1
            continue
        elif action == 1:
            console.print("\n[bold green]✅ Quant mit Rückkopplung abgeschlossen.[/bold green]\n")
            input("[Enter]...")
            return
        else:
            return

def explore_knotenkarte():
    nodes = load_philosophers()
    while True:
        clear_screen()
        print_header("INTERAKTIVE KNOTENKARTE", "bold cyan")
        choice = ask_choice("Was möchtest du tun?", ["Nach Philosophen suchen", "Timeline (Philosophiesinnmatrix)", "Geographische Cluster", "Zurück"], allow_back=False)
        if choice == 0: search_philosophers(nodes)
        elif choice == 1: timeline_mode(nodes)
        elif choice == 2: geographical_clusters(nodes)
        else: return

def search_philosophers(nodes):
    clear_screen()
    term = Prompt.ask("Suchbegriff")
    results = [n for n in nodes if term.lower() in n['name'].lower() or term.lower() in n.get('era','').lower()]
    if not results:
        console.print("[red]Keine Treffer.[/red]")
        input("[Enter]...")
        return
    for i, n in enumerate(results[:6], 1):
        console.print(f"[cyan][{i}][/cyan] {n['name']} ({n['period']}) — {n['era']}")
    idx = ask_choice("Welchen Knoten genauer ansehen?", [n['name'] for n in results[:5]])
    if idx != -1:
        node = results[idx]
        console.print(Panel(node['relevance'], title=f"{node['name']} ({node['period']})", border_style="blue"))
        input("\n[Enter]...")

def timeline_mode(nodes):
    clear_screen()
    print_header("TIMELINE — Philosophiesinnmatrix", "bold magenta")
    console.print("Strukturiert nach Epochen mit kollektiven Sinnstrahlen.\n")
    input("[Enter] starten...")
    eras = {
        "Antike & Spätantike": ["plotinus","aristoteles","platon","augustinus"],
        "Mittelalter & Islam": ["thomas_von_aquin","avicenna","averroes"],
        "Frühe Neuzeit": ["spinoza","leibniz","descartes"],
        "Deutscher Idealismus & 19. Jh.": ["hegel","schopenhauer","kierkegaard","nietzsche"],
        "20. Jahrhundert": ["husserl","heidegger","wittgenstein","freud","lacan","arendt"]
    }
    for era, ids in eras.items():
        clear_screen()
        print_header(f"Epoche: {era}", "bold yellow")
        for nid in ids:
            n = next((x for x in nodes if x['id']==nid), None)
            if n: console.print(f"[bold]{n['name']}[/bold] ({n['period']})\n  {n['relevance'][:200]}...\n")
        if Prompt.ask("[Enter] nächste | [q] Ende", default="").lower() == 'q': break
    if ask_choice("Timeline exportieren?", ["Ja","Nein"])==0:
        export_to_markdown("Philosophiesinnmatrix Timeline", "Timeline der Epochen.", "timeline")

def geographical_clusters(nodes):
    clear_screen()
    print_header("GEOGRAPHISCHE & KULTURELLE CLUSTER", "bold green")
    clusters = {"Mediterrane Antike":["plotinus","aristoteles","platon"], "Christlich-Mittelalter":["augustinus","thomas_von_aquin"],
                "Islamisches Zeitalter":["avicenna","averroes"], "Frühe Neuzeit":["spinoza","leibniz","descartes"],
                "Deutscher Idealismus":["hegel","schopenhauer","kierkegaard","nietzsche"], "20. Jahrhundert":["husserl","heidegger","wittgenstein","arendt"]}
    names = list(clusters.keys())
    idx = ask_choice("Cluster wählen:", names)
    if idx == -1: return
    print_section(names[idx])
    for nid in clusters[names[idx]]:
        n = next((x for x in nodes if x['id']==nid), None)
        if n: console.print(f"• [bold]{n['name']}[/bold] ({n['period']})")
    input("\n[Enter]...")

def quant_on_central_problems():
    clear_screen()
    print_header("Quant auf zentrale Probleme der 4D-Matrix", "bold red")
    idx = ask_choice("Problem wählen:", [p["name"] for p in KEY_PROBLEMS])
    if idx == -1: return
    p = KEY_PROBLEMS[idx]
    clear_screen()
    print_header(p["name"], "bold red")
    console.print(f"[dim](Ursprünglich: {p['original']})[/dim]\n")
    print_section("Quant-Schritte")
    for i, s in enumerate(p["quant_steps"], 1): console.print(f"[cyan]{i}.[/cyan] {s}")
    print_section("Mimetik")
    console.print(f"[yellow]{p['mimetik']}[/yellow]")
    print_section("Memetik")
    console.print(f"[yellow]{p['memetik']}[/yellow]")
    if ask_choice("Exportieren?", ["Ja","Nein"])==0:
        export_to_markdown(p["name"], f"### Quant\n{chr(10).join(p['quant_steps'])}\n\nMimetik: {p['mimetik']}\nMemetik: {p['memetik']}", "problem")
    input("[Enter]...")

def analyze_own_problem():
    clear_screen()
    print_header("Eigenes Problem analysieren", "bold blue")
    txt = Prompt.ask("Beschreibe kurz dein Problem")
    lower = txt.lower()
    if any(w in lower for w in ["beziehung","liebe","stamm","einsam"]):
        name, mim, mem, q = "Liebesquant-Defizit", "Hoch", "Sehr hoch", "Fokussiere auf Qualität echter Verstehensmomente mit 1-2 Menschen."
    elif any(w in lower for w in ["erfolg","leistung","status"]):
        name, mim, mem, q = "Mimetischer Statushunger", "Sehr hoch", "Extrem hoch", "Unterscheide Leistung von innerem Wert."
    else:
        name, mim, mem, q = "Struktureller Quantenmangel", "Mittel-Hoch", "Hoch", "Identifiziere konkretes Mangelfeld und wende Quant an."
    clear_screen()
    print_header("Vorschlag", "bold green")
    console.print(Panel(f"[bold]Dein Problem:[/bold]\n{txt}", border_style="blue"))
    console.print(f"\n[bold green]Vorgeschlagener Name:[/bold green] {name}")
    console.print(f"[yellow]Mimetik:[/yellow] {mim}   [yellow]Memetik:[/yellow] {mem}")
    console.print(f"\n[cyan]Quant-Vorschlag:[/cyan] {q}\n")
    if ask_choice("Exportieren?", ["Ja","Nein"])==0:
        export_to_markdown("Eigene Analyse", f"**Problem:** {txt}\n\n**Name:** {name}\n**Mimetik:** {mim}\n**Memetik:** {mem}\n**Quant:** {q}", "eigenes_problem")
    input("[Enter]...")

def main_menu():
    while True:
        clear_screen()
        print_header("DER HEROISCHE MENSCH", "bold white on blue")
        console.print("[dim]Interaktives Programm — Moderne Version[/dim]\n")
        choice = ask_choice("Was möchtest du tun?", [
            "Theorie: Concept Space & Quantisierung",
            "Mächtiger Quant-Modus (Rückkopplung + Liebesquant)",
            "Interaktive Knotenkarte",
            "Quant auf zentrale Probleme der Matrix",
            "Eigenes Problem analysieren",
            "Beenden"
        ], allow_back=False)
        if choice == 0:
            clear_screen()
            print_header("Concept Space & Quantisierung", "bold cyan")
            console.print(Panel("Die Welt ist [bold]analog[/bold].\n\nQuantisierung = Schnitt ins Diskrete.\n\n[bold]q∘b[/bold] = menschlicher Modus.\n\nDer [bold]Quant[/bold] = 4-Schritt-Verfahren.", border_style="cyan"))
            input("[Enter]...")
        elif choice == 1: run_quant_powerful()
        elif choice == 2: explore_knotenkarte()
        elif choice == 3: quant_on_central_problems()
        elif choice == 4: analyze_own_problem()
        elif choice == 5:
            console.print("\n[bold]Der Stein rollt weiter.[/bold]\n")
            sys.exit(0)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n\n[bold]Programm unterbrochen.[/bold]\n")
        sys.exit(0)

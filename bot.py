import requests
import os
import time
import random
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track
from rich import box

ADDRESS_FILE = "address.txt"
OUTPUT_FILE = "results.json"
API_BASE = "https://api.prod.airdrop.heliax.net/api/v1/{}/eligibility/{}"
API_TYPES = ["ethereum", "scrimp", "kaito"]

HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,id;q=0.8",
    "origin": "https://register.anoma.foundation",
    "priority": "u=1, i",
    "referer": "https://register.anoma.foundation/",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}

console = Console()


def load_addresses(filename: str):
    if not os.path.exists(filename):
        console.print(f"[bold red][!] File {filename} tidak ditemukan.[/]")
        return []
    with open(filename, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    return lines


def is_valid_eth_address(addr: str) -> bool:
    return isinstance(addr, str) and addr.startswith("0x") and len(addr) == 42


def check_api(
    session: requests.Session, api_type: str, address: str, timeout: int = 15
):
    url = API_BASE.format(api_type, address)
    try:
        resp = session.get(url, headers=HEADERS, timeout=timeout)
        try:
            data = resp.json()
        except ValueError:
            data = {"raw_text": resp.text}
        return {"status_code": resp.status_code, "data": data}
    except requests.RequestException as e:
        return {"error": str(e)}


def main():
    addresses = load_addresses(ADDRESS_FILE)
    if not addresses:
        console.print(
            "[bold yellow]Tidak ada address untuk dicek. Pastikan file address.txt berisi satu address per baris.[/]"
        )
        return

    console.print(f"[bold cyan]🚀 Mulai cek {len(addresses)} address...[/]\n")
    results = {}
    session = requests.Session()

    for idx, addr in enumerate(addresses, start=1):
        console.rule(f"[bold green]Address {idx}/{len(addresses)}[/]")

        if not is_valid_eth_address(addr):
            console.print(
                Panel.fit(
                    f"[red]Invalid address format[/]\n{addr}",
                    title="❌ ERROR",
                    style="red",
                )
            )
            results[addr] = {"error": "invalid_address_format"}
        else:
            results[addr] = {"checked_at": datetime.utcnow().isoformat() + "Z"}
            table = Table(
                title=f"Eligibility Check x SHARE IT HUB", box=box.ROUNDED, style="cyan"
            )
            table.add_column("API", style="bold yellow")
            table.add_column("Status", style="bold white")
            table.add_column("Eligible", style="bold green")

            for api_type in API_TYPES:
                result = check_api(session, api_type, addr)
                results[addr][api_type] = result

                if "error" in result:
                    status = f"[red]ERROR[/]\n{result['error']}"
                    eligible = "-"
                else:
                    status_code = result.get("status_code")
                    status = (
                        f"[green]HTTP {status_code}[/]"
                        if status_code == 200
                        else f"[red]HTTP {status_code}[/]"
                    )
                    data = result.get("data", {})
                    eligible = (
                        str(data.get("eligible"))
                        if isinstance(data, dict) and "eligible" in data
                        else "-"
                    )

                table.add_row(api_type, status, eligible)

            console.print(
                Panel(
                    table,
                    title=f"[bold blue]{addr}[/]",
                    subtitle="Hasil cek",
                    border_style="bright_blue",
                )
            )

        delay = random.uniform(5, 10)
        console.print(f"[bold green]⏳ Delay {delay:.2f} detik...[/]\n")
        time.sleep(delay)

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
            json.dump(results, out, indent=2, ensure_ascii=False)
        console.print(f"[bold cyan]✅ Hasil disimpan ke [white]{OUTPUT_FILE}[/]")
    except Exception as e:
        console.print(f"[bold red][!] Gagal menyimpan hasil: {e}[/]")


if __name__ == "__main__":
    main()

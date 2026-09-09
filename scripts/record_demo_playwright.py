"""
ProcureAI — Automated Playwright Demo Script for Video Recording
================================================================
This script automates the complete 3-minute product demo in a real browser,
with realistic mouse animations, teleprompter cues, smooth scrolling, and 
step-by-step or timed execution so you can record your screen and voiceover effortlessly.

Usage:
    .venv/Scripts/python scripts/record_demo_playwright.py
    .venv/Scripts/python scripts/record_demo_playwright.py --speed fast
    .venv/Scripts/python scripts/record_demo_playwright.py --manual
"""

import os
import sys
import time
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

BASE_DIR = Path(__file__).resolve().parent.parent
CONTRACT_PATH = str(BASE_DIR / "data" / "synthetic" / "contracts" / "c001_apex_logistics_contract.pdf")
INVOICE_1 = str(BASE_DIR / "data" / "synthetic" / "invoices" / "c001_invoice_i001.pdf")
INVOICE_2 = str(BASE_DIR / "data" / "synthetic" / "invoices" / "c001_invoice_i002.pdf")

STEPS = [
    {
        "id": "hook",
        "title": "0:00 - 0:25 | The Problem & Introduction",
        "cue": "Every enterprise loses 2-5% of spend to silent invoice leakage. Meet ProcureAI: autonomous contract compliance.",
        "duration": 6
    },
    {
        "id": "upload",
        "title": "0:25 - 0:55 | Contract & Invoice Ingestion",
        "cue": "Drop the Apex Logistics 12-page contract and monthly invoices. One click triggers our 7-agent pipeline.",
        "duration": 8
    },
    {
        "id": "pipeline",
        "title": "0:55 - 1:25 | Multi-Agent LangGraph Execution",
        "cue": "Watch 7 stateful agents parse rules, normalize units, and evaluate compliance with deterministic math.",
        "duration": 12
    },
    {
        "id": "report_summary",
        "title": "1:25 - 1:55 | Audit Report & Evidence Grounding",
        "cue": "Audit complete! Identified exact leakage. Zero math hallucination—pure Python Decimal verification.",
        "duration": 10
    },
    {
        "id": "discrepancies",
        "title": "1:55 - 2:20 | Deep Dive: Volume Tier & Reverse Sweep",
        "cue": "Discrepancy 1: Volume tier overcharge. Discrepancy 2: Reverse Sweep caught a missed 12% SLA credit!",
        "duration": 14
    },
    {
        "id": "dispute_letter",
        "title": "2:20 - 2:40 | 1-Click Executive Dispute Letter",
        "cue": "One click generates a legal-ready dispute letter citing exact clauses, dates, and line items ready to email.",
        "duration": 10
    },
    {
        "id": "scorecard_analytics",
        "title": "2:40 - 2:55 | Supplier Scorecards & Leakage Analytics",
        "cue": "Continuous intelligence: Supplier scorecards, rate drift tracking, and CFO-level spend heatmaps.",
        "duration": 10
    },
    {
        "id": "closing",
        "title": "2:55 - 3:00 | Strong Wrap Up",
        "cue": "ProcureAI: Turn signed contracts into living guardrails and protect your bottom line. Thank you!",
        "duration": 6
    }
]


def inject_teleprompter(page: Page, title: str, cue: str, step_num: int, total_steps: int):
    """Renders a sleek on-screen teleprompter overlay for recording guidance."""
    js_code = f"""
    (() => {{
        let banner = document.getElementById('procureai-teleprompter');
        if (!banner) {{
            banner = document.createElement('div');
            banner.id = 'procureai-teleprompter';
            banner.style.position = 'fixed';
            banner.style.bottom = '20px';
            banner.style.right = '24px';
            banner.style.zIndex = '999999';
            banner.style.maxWidth = '460px';
            banner.style.background = 'rgba(15, 23, 42, 0.92)';
            banner.style.backdropFilter = 'blur(12px)';
            banner.style.border = '1px solid rgba(13, 148, 136, 0.4)';
            banner.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.4), 0 0 15px rgba(13, 148, 136, 0.2)';
            banner.style.borderRadius = '12px';
            banner.style.padding = '12px 16px';
            banner.style.fontFamily = 'system-ui, -apple-system, BlinkMacSystemFont, sans-serif';
            banner.style.color = '#ffffff';
            banner.style.transition = 'all 0.3s ease';
            banner.style.pointerEvents = 'none';
            document.body.appendChild(banner);
        }}
        banner.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 11px; font-weight: 700; color: #2dd4bf; text-transform: uppercase; letter-spacing: 0.05em;">
                    Step {step_num}/{total_steps} • {title}
                </span>
                <span style="font-size: 10px; background: rgba(13, 148, 136, 0.25); color: #5eead4; padding: 2px 6px; border-radius: 4px; font-weight: 600;">
                    LIVE DEMO
                </span>
            </div>
            <div style="font-size: 13px; font-weight: 500; color: #f1f5f9; line-height: 1.4;">
                🎙️ "{cue}"
            </div>
        `;
    }})();
    """
    try:
        page.evaluate(js_code)
    except Exception:
        pass


def smooth_scroll(page: Page, y_offset: int, duration_ms: int = 800):
    page.evaluate(f"""
        window.scrollTo({{
            top: {y_offset},
            behavior: 'smooth'
        }});
    """)
    page.wait_for_timeout(duration_ms)


def highlight_element(page: Page, selector: str):
    """Draws a subtle animated glow around an element to draw the viewer's eye."""
    try:
        page.evaluate(f"""
            (() => {{
                const el = document.querySelector('{selector}');
                if (el) {{
                    el.style.transition = 'all 0.4s ease';
                    el.style.outline = '3px solid #0d9488';
                    el.style.boxShadow = '0 0 20px rgba(13, 148, 136, 0.4)';
                    setTimeout(() => {{
                        el.style.outline = 'none';
                        el.style.boxShadow = 'none';
                    }}, 2500);
                }}
            }})();
        """)
    except Exception:
        pass


def run_demo(manual_mode: bool = False, speed_factor: float = 1.0, show_teleprompter: bool = True):
    print("=" * 60)
    print("🚀 Launching ProcureAI Automated Demo Walkthrough...")
    print(f"   Mode: {'MANUAL STEP-BY-STEP (Press ENTER in terminal to advance)' if manual_mode else 'TIMED AUTOMATIC'}")
    print(f"   Speed multiplier: {speed_factor}x")
    print(f"   Contract: {CONTRACT_PATH}")
    print("=" * 60)

    if not os.path.exists(CONTRACT_PATH) or not os.path.exists(INVOICE_1):
        print(f"❌ Error: Demo files not found in data/synthetic!")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--start-maximized",
                "--disable-infobars",
                "--no-default-browser-check"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            no_viewport=False
        )
        page = context.new_page()

        def step_pause(step_idx: int):
            step_info = STEPS[step_idx]
            if show_teleprompter:
                inject_teleprompter(page, step_info["title"], step_info["cue"], step_idx + 1, len(STEPS))
            print(f"\n[{step_idx + 1}/{len(STEPS)}] {step_info['title']}")
            print(f"   🎙️ CUE: {step_info['cue']}")
            
            if manual_mode:
                input("   👉 Press [ENTER] in this console when you are ready for the next action...")
            else:
                pause_time = int((step_info["duration"] / speed_factor) * 1000)
                page.wait_for_timeout(pause_time)

        # -------------------------------------------------------------
        # STEP 1: Land on App / Dashboard
        # -------------------------------------------------------------
        page.goto("http://localhost:5173", wait_until="networkidle")
        page.wait_for_timeout(1000)
        step_pause(0)

        # -------------------------------------------------------------
        # STEP 2: Navigate to Upload and Upload Files
        # -------------------------------------------------------------
        print("▶ Clicking New Audit / Upload...")
        new_audit_btn = page.locator("button:has-text('New Audit')").first
        if new_audit_btn.is_visible():
            new_audit_btn.click()
        else:
            page.locator("button:has-text('Upload')").first.click()
        
        page.wait_for_timeout(800)

        # Attach Contract PDF
        print(f"▶ Attaching contract: {CONTRACT_PATH}")
        page.set_input_files("#contract-input", CONTRACT_PATH)
        page.wait_for_timeout(1000)

        # Attach Invoice PDFs
        print(f"▶ Attaching invoices: {INVOICE_1}, {INVOICE_2}")
        page.set_input_files("#invoices-input", [INVOICE_1, INVOICE_2])
        page.wait_for_timeout(1500)

        # Supplier Name Override
        supplier_input = page.locator("input[placeholder*='Auto-extracted']")
        if supplier_input.is_visible():
            supplier_input.fill("Apex Logistics Ltd")
            page.wait_for_timeout(600)

        step_pause(1)

        # Click Run Audit
        print("▶ Triggering Run Audit...")
        run_btn = page.locator("button:has-text('Run Audit')").first
        highlight_element(page, "button:has-text('Run Audit')")
        page.wait_for_timeout(800)
        run_btn.click()

        # -------------------------------------------------------------
        # STEP 3: Live Agent Pipeline Execution
        # -------------------------------------------------------------
        page.wait_for_timeout(1200)
        step_pause(2)

        # Wait for Report to Load (Audit complete)
        print("▶ Waiting for audit completion...")
        try:
            page.wait_for_selector("text=Audit Summary", timeout=45000)
        except Exception:
            page.wait_for_selector("text=Compliance", timeout=45000)

        page.wait_for_timeout(1000)

        # -------------------------------------------------------------
        # STEP 4: Audit Report & Summary
        # -------------------------------------------------------------
        smooth_scroll(page, 150, 600)
        step_pause(3)

        # -------------------------------------------------------------
        # STEP 5: Expand Discrepancies
        # -------------------------------------------------------------
        smooth_scroll(page, 450, 700)
        page.wait_for_timeout(600)

        # Expand Discrepancy #1
        discrepancy_rows = page.locator("tr.cursor-pointer, div[role='button'], button:has-text('Details'), div.border-slate-200")
        print("▶ Expanding Discrepancy #1...")
        first_discrepancy = page.locator("tbody tr").first
        if first_discrepancy.is_visible():
            first_discrepancy.click()
        page.wait_for_timeout(1500)
        smooth_scroll(page, 550, 600)

        # Expand Discrepancy #2 (Reverse Sweep)
        print("▶ Expanding Discrepancy #2...")
        try:
            second_discrepancy = page.locator("tbody tr").nth(1)
            if second_discrepancy.is_visible():
                second_discrepancy.click()
                page.wait_for_timeout(1500)
        except Exception:
            pass

        step_pause(4)

        # -------------------------------------------------------------
        # STEP 6: 1-Click Dispute Letter Modal
        # -------------------------------------------------------------
        print("▶ Opening Dispute Letter Modal...")
        dispute_btn = page.locator("button:has-text('Dispute Letter'), button:has-text('Generate Dispute')").first
        if dispute_btn.is_visible():
            dispute_btn.click()
            page.wait_for_timeout(1200)
            step_pause(5)
            # Close modal
            close_btn = page.locator("button:has-text('Close'), button[aria-label='Close'], button:has(svg.lucide-x)").first
            if close_btn.is_visible():
                close_btn.click()
                page.wait_for_timeout(800)
        else:
            step_pause(5)

        # -------------------------------------------------------------
        # STEP 7: Scorecard & Analytics Views
        # -------------------------------------------------------------
        print("▶ Navigating to Supplier Scorecard...")
        scorecard_nav = page.locator("button:has-text('Scorecard')").first
        if scorecard_nav.is_visible():
            scorecard_nav.click()
            page.wait_for_timeout(2000)
            smooth_scroll(page, 200, 600)

        print("▶ Navigating to Analytics...")
        analytics_nav = page.locator("button:has-text('Analytics')").first
        if analytics_nav.is_visible():
            analytics_nav.click()
            page.wait_for_timeout(2500)
            smooth_scroll(page, 300, 700)

        step_pause(6)

        # -------------------------------------------------------------
        # STEP 8: Wrap-up & Return to Audit History
        # -------------------------------------------------------------
        print("▶ Returning to Audit History for wrap up...")
        history_nav = page.locator("button:has-text('Audit History')").first
        if history_nav.is_visible():
            history_nav.click()
            page.wait_for_timeout(1500)

        step_pause(7)

        print("\n🎉 Walkthrough successfully completed!")
        print("Browser will stay open for 10 seconds before closing.")
        page.wait_for_timeout(10000)
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ProcureAI Playwright Demo Bot")
    parser.add_argument("--manual", action="store_true", help="Manual mode (press Enter in terminal for each step)")
    parser.add_argument("--speed", type=str, default="normal", choices=["slow", "normal", "fast"], help="Playback speed")
    parser.add_argument("--no-teleprompter", action="store_true", help="Hide on-screen teleprompter overlay")
    args = parser.parse_args()

    speed_map = {"slow": 0.7, "normal": 1.0, "fast": 1.5}
    run_demo(
        manual_mode=args.manual,
        speed_factor=speed_map[args.speed],
        show_teleprompter=not args.no_teleprompter
    )

"""Capture the actual React UI with synthetic, browser-only API fixtures.

Start apps/web with npm run dev, then run with a Python environment containing
playwright: python scripts/capture_portfolio.py OUTPUT_DIRECTORY.
No production API, accounts, emails, or records are used.
"""

import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

CLIENT = """
const person = {id: 'demo-a', username: 'alex_demo', display_name: 'alex_demo'};
const friend = {id: 'demo-b', username: 'sam_demo', display_name: 'sam_demo'};
export const auth = {
  getSession: async () => ({data: {session: {user: person}}}),
  onAuthStateChange: () => ({data: {subscription: {unsubscribe() {}}}}),
  signOut: async () => {},
};
export async function api(path, method = 'GET', body) {
  const scene = window.demoScene || 'sealed';
  const resolved = scene === 'resolved';
  const review = scene === 'review';
  const revealed = scene !== 'sealed';
  const duel = {
    id: 'demo-duel', group_id: 'demo-group', gameweek: 'Demo GW8',
    claim_type: 'gameweek_points', member_a_id: person.id, member_b_id: friend.id,
    deadline_at: revealed ? '2026-10-17T10:00:00Z' : '2099-10-24T10:00:00Z',
    status: resolved ? 'resolved' : review ? 'awaiting_confirmation' : revealed ? 'awaiting_scores' : 'open',
    probabilities: revealed ? {'demo-a': 65, 'demo-b': 40} : {'demo-a': window.demoProbability ?? 65},
    scores: review || resolved ? [{id: 'demo-score', score_a: 68, score_b: 54,
      source_url: 'https://fantasy.premierleague.com/', created_at: '2026-10-18T12:00:00Z',
      entered_by: friend.id, responses: [{user_id: friend.id, action: 'confirm', reason: null, created_at: '2026-10-18T12:00:00Z'}]}] : [],
    void_reason: null,
  };
  if (method !== 'GET') {
    if (path.endsWith('/submissions')) window.demoProbability = body.probability_pct;
    else if (path.endsWith('/confirm')) window.demoScene = 'resolved';
    else throw new Error('This capture fixture supports predictions and confirmation only');
    return {};
  }
  if (path === '/me') return person;
  if (path === '/groups') return [{id: 'demo-group', name: 'Weekend rivals · demo', role: 'member'}];
  if (path.endsWith('/members')) return [person, friend];
  if (path.endsWith('/duels')) return [duel];
  if (path.endsWith('/history')) return Object.fromEntries([person, friend].map((p, i) => [p.id, {
    display_name: p.display_name, sample_size: resolved ? 1 : 0,
    wins: resolved && i === 0 ? 1 : 0, losses: resolved && i === 1 ? 1 : 0,
    mean_brier: resolved ? (i === 0 ? .1225 : .16) : null, history: [],
  }]));
  throw new Error('Unimplemented fixture: ' + path);
}
"""


async def capture(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        page = await browser.new_page(viewport={'width': 1280, 'height': 1050}, timezone_id='UTC')
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))

        async def route_request(route):
            url = route.request.url
            if '/src/client.ts' in url:
                await route.fulfill(content_type='application/javascript', body=CLIENT)
            elif url.startswith('http://127.0.0.1:5173/'):
                await route.continue_()
            else:
                await route.abort()

        await page.route('**/*', route_request)
        await page.goto('http://127.0.0.1:5173/')
        await page.get_by_role('heading', name='alex_demo vs sam_demo').wait_for()
        await page.evaluate("""() => {
          const banner = document.createElement('div'); banner.id = 'capture-caption';
          banner.style = 'position:sticky;top:0;z-index:100;background:#16231c;color:#e8f1ea;padding:18px 24px;font:600 17px system-ui;border-bottom:2px solid #8bc5a2';
          document.body.prepend(banner);
        }""")
        scenes = [
            ('01-sealed', '1 / 5 · Lock a prediction. The opponent stays sealed until the deadline.'),
            ('02-revealed', '2 / 5 · After the deadline, both predictions are visible.'),
            ('03-review', '3 / 5 · Review the official score and its source before confirming.'),
            ('04-resolved', '4 / 5 · Confirm the score. The resolved duel updates the record.'),
            ('05-calibration', '5 / 5 · Track calibration: 65% on a win gives (0.65 − 1)² = 0.1225.'),
        ]
        for index, (filename, caption) in enumerate(scenes):
            if index in (1, 2):
                await page.evaluate('(scene) => {window.demoScene = scene}', 'revealed' if index == 1 else 'review')
                await page.get_by_role('button', name='Refresh', exact=True).click()
            elif index == 3:
                await page.get_by_role('button', name='Confirm score', exact=True).click()
                await page.get_by_text('resolved', exact=True).wait_for()
            if index == 2:
                await page.get_by_text('Score record (1)', exact=True).click()
            await page.locator('#capture-caption').evaluate('(node, text) => node.textContent = "SYNTHETIC UI DEMO · " + text', caption)
            if index in (1, 2, 3):
                await page.locator('.duel').evaluate('(node) => window.scrollTo(0, node.getBoundingClientRect().top + scrollY - 110)')
            elif index == 4:
                await page.locator('.stats-grid').evaluate('(node) => window.scrollTo(0, node.getBoundingClientRect().top + scrollY - 160)')
            await page.wait_for_timeout(250)
            await page.screenshot(path=str(output / (filename + '.png')))
        await page.set_viewport_size({'width': 390, 'height': 844})
        await page.evaluate('window.scrollTo(0, 0)')
        await page.screenshot(path=str(output / 'mobile.png'), full_page=True)
        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile overflow'
        assert not errors, errors
        (output / 'capture.json').write_text(json.dumps({
            'type': 'actual React UI with substituted auth/API responses',
            'production_verified': False, 'real_users': False,
            'desktop': '1280x1050', 'mobile': '390x844',
            'console_errors': errors, 'mobile_horizontal_overflow': False,
        }, indent=2) + '\n')
        await browser.close()


if __name__ == '__main__':
    asyncio.run(capture(Path(sys.argv[1])))

import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createInterface } from 'node:readline';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const stage = process.argv[2] ?? 'F2';
assert.ok(['M0', 'F1', 'F2'].includes(stage), '用法：npm run e2e -- M0|F1|F2');
const directory = await mkdtemp(join(tmpdir(), 'task-list-e2e-'));
let server, browser;
async function start() {
  server = spawn(process.env.PYTHON ?? 'python3', [
    '-u', 'server.py', '--stage', stage, '--port', '0', '--db', join(directory, 'tasks.sqlite3'),
  ], { cwd: fileURLToPath(new URL('.', import.meta.url)), stdio: ['ignore', 'pipe', 'inherit'] });
  const lines = createInterface({ input: server.stdout });
  try {
    const [url] = await Promise.race([
      once(lines, 'line'),
      once(server, 'exit').then(([code]) => { throw new Error(`服务启动失败 (${code})`); }),
    ]);
    assert.match(url, /^http:\/\/127\.0\.0\.1:\d+$/);
    return url;
  } finally {
    lines.close();
  }
}
async function stop() {
  if (server?.pid && server.exitCode === null && server.signalCode === null) {
    const exited = once(server, 'exit');
    server.kill();
    await exited;
  }
}
try {
  const url = await start();
  browser = await chromium.launch(process.env.CHROME_BIN
    ? { executablePath: process.env.CHROME_BIN } : { channel: 'chrome' });
  const page = await browser.newPage();
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const [initial] = await Promise.all([
    page.waitForResponse(r => r.url() === `${url}/api/tasks`), page.goto(url),
  ]);
  assert.equal(initial.status(), 200);
  assert.deepEqual(await initial.json(), { stage, tasks: [] });
  await page.getByText('暂无任务', { exact: true }).waitFor();
  const title = page.getByRole('textbox', { name: '任务名称' });
  const filters = page.getByRole('combobox', { name: '筛选' });
  assert.equal(await title.isVisible(), stage !== 'M0');
  assert.equal(await filters.isVisible(), stage === 'F2');
  console.log('PASS AC-M0-01 浏览器读取真实 API 并显示空清单');

  const task = name => page.getByRole('listitem').filter({ hasText: name });
  async function add(name) {
    await title.fill(name);
    await page.getByRole('button', { name: '新增任务' }).click();
    await task(name).waitFor();
  }
  if (stage !== 'M0') {
    await add('购买牛奶');
    await page.reload();
    await task('购买牛奶').waitFor();
    await stop();
    await page.goto(await start());
    await task('购买牛奶').waitFor();
    console.log('PASS AC-F1-01 新增任务，刷新并重启服务后仍可见');
  }
  if (stage === 'F2') {
    await add('整理书架');
    const checkbox = task('购买牛奶').getByRole('checkbox');
    const [update] = await Promise.all([
      page.waitForResponse(r => r.request().method() === 'PATCH'), checkbox.check(),
    ]);
    assert.equal(update.status(), 200);
    await page.reload();
    await checkbox.waitFor();
    assert.equal(await checkbox.isChecked(), true);
    assert.equal(await task('整理书架').getByRole('checkbox').isChecked(), false);
    console.log('PASS AC-F2-01 完成状态刷新后仍保留');
    for (const [filter, expected] of [
      ['已完成', ['购买牛奶']], ['未完成', ['整理书架']], ['全部', ['购买牛奶', '整理书架']],
    ]) {
      await filters.selectOption({ label: filter });
      assert.deepEqual(await page.getByRole('listitem').allTextContents(), expected);
    }
    console.log('PASS AC-F2-02 三种筛选均显示正确任务');
  }
  assert.deepEqual(errors, []);
} finally {
  await browser?.close();
  await stop();
  await rm(directory, { recursive: true, force: true });
}

import { element, folio, paintEvidence, paintExtras, stageTable, states } from './evidence.js';

const $ = id => document.getElementById(id);
const sample = $('sample');
const selectionButtons = [...document.querySelectorAll('[data-stage]')];
const metrics = { expected: '应到期位', covered: '已覆盖', missing: '缺刊', disputed: '争议', supplements: '增刊件' };
let ledger = null;
let stage = 'balance';
let currentSource = null;
let activeRun = null;
let selected = null;
let busy = false;
let revision = 0;

async function api(path, payload) {
  const response = await fetch(path, payload === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || '读取失败，请重试');
  }
  return response.json();
}

function paintRows() {
  if (!ledger) return;
  const rows = ledger.slots.filter(row => ($('chain').value === 'all' || row.chain === $('chain').value)
    && ($('filter').value === 'all' || row.status === $('filter').value));
  $('register').replaceChildren();
  if (!rows.length) {
    const cell = $('register').insertRow().insertCell();
    cell.colSpan = 5;
    cell.textContent = '试试其他筛选条件。';
  }
  for (const slot of rows) {
    const row = $('register').insertRow();
    row.dataset.status = slot.status;
    row.classList.toggle('selected', selected === slot);
    row.insertCell().textContent = slot.chain;
    row.insertCell().textContent = folio(slot);
    row.insertCell().append(element('span', states[slot.status], 'seal'));
    row.insertCell().append(element('code', slot.evidence.map(item => item.accession).join(' / ') || '—'));
    const button = element('button', '看原件');
    button.type = 'button';
    button.setAttribute('aria-label', `查看 ${slot.chain} ${folio(slot)}`);
    button.addEventListener('click', () => {
      selected = slot;
      document.querySelector('.selected')?.classList.remove('selected');
      row.classList.add('selected');
      paintEvidence(slot);
    });
    row.insertCell().append(button);
  }
  $('sum').textContent = `显示 ${rows.length} / ${ledger.totals.expected} 期 · ${ledger.status === 'MATCHED' ? '期位与行数已对平' : '存在勾稽差额'}`;
}

function setArchive(run) {
  activeRun = run;
  $('rerun').disabled = !run || busy;
  $('export').hidden = !run;
  $('run-metadata').textContent = run ? `${run.id.slice(0, 12)} · ${run.manifest.generated_at}` : '未归档';
  if (run) $('export').href = `/api/runs/${run.id}/export`;
}

async function readStage(name) {
  stage = name;
  for (const link of selectionButtons) {
    if (link.dataset.stage === name) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  }
  if (name === 'balance' || name === 'runs') {
    $('stage').hidden = true;
    return;
  }
  $('stage').hidden = false;
  $('stage-title').textContent = selectionButtons.find(link => link.dataset.stage === name).textContent;
  $('stage-body').textContent = '读取阶段材料…';
  $('stage').scrollIntoView({ block: 'nearest' });
  if (!currentSource) {
    $('stage-body').textContent = '请先核算清册。';
    return;
  }
  const initialRevision = revision;
  try {
    const data = currentSource.sample ? await api(`/api/${name}/${currentSource.sample}`)
      : await api(`/api/${name}`, currentSource);
    if (initialRevision === revision && stage === name) $('stage-body').replaceChildren(stageTable(name, data));
  } catch (error) {
    if (initialRevision === revision && stage === name) $('stage-body').textContent = error.message;
  }
}

async function preview() {
  const token = ++revision;
  const choice = sample.value;
  $('custom').hidden = choice !== 'custom';
  $('status').textContent = '正在勾稽…';
  $('run-feedback').textContent = '';
  $('save').disabled = true;
  currentSource = null;
  ledger = null;
  setArchive(null);
  $('totals').replaceChildren();
  $('register').replaceChildren();
  $('sum').textContent = '';
  $('extras').replaceChildren();
  paintEvidence(null);
  try {
    let source = { sample: choice };
    if (choice === 'custom') {
      const text = $('source-data').value.trim();
      if (!text) throw new Error('请输入清册 JSON');
      try { source = { data: JSON.parse(text) }; }
      catch { throw new Error('JSON 格式有误，请检查后重试'); }
    }
    const get = name => source.sample ? api(`/api/${name}/${choice}`) : api(`/api/${name}`, source);
    const [data, claims, intake] = await Promise.all([get('balance'), get('combined'), get('receipts')]);
    if (token !== revision) return;
    ledger = data;
    currentSource = source;
    selected = null;
    $('chain').replaceChildren(new Option('全部', 'all'), ...[...new Set(data.slots.map(slot => slot.chain))].map(key => new Option(key, key)));
    $('totals').replaceChildren(...Object.entries(metrics).map(([key, label]) => {
      const metric = element('div', undefined, 'kpi');
      metric.dataset.metric = key;
      metric.append(element('span', label), element('strong', data.totals[key]));
      return metric;
    }));
    const years = data.years.map(row => row.year);
    $('edition-note').textContent = `${Math.min(...years)}—${Math.max(...years)} 年 · ${data.row_totals.input} 条来刊记录`;
    paintRows();
    paintExtras(claims.supplements, data.quarantine, intake.duplicates);
    $('status').textContent = '清册已核算';
    if (stage !== 'balance' && stage !== 'runs') readStage(stage);
  } catch (error) {
    if (token !== revision) return;
    $('status').textContent = error.message;
    $('edition-note').textContent = '等待有效清册';
    if (stage !== 'balance' && stage !== 'runs') readStage(stage);
  } finally {
    if (token === revision) $('save').disabled = !currentSource || busy;
  }
}

async function save(reuse) {
  if (!currentSource || busy || (reuse && !activeRun)) return;
  const token = revision;
  busy = true;
  $('save').disabled = $('rerun').disabled = true;
  $('run-feedback').textContent = '正在归档…';
  try {
    const run = await api(reuse ? `/api/runs/${activeRun.id}/rerun` : '/api/runs', reuse ? {} : currentSource);
    if (token !== revision) return;
    setArchive(run);
    $('run-feedback').textContent = reuse ? '重跑一致' : (run.reused ? '已定位原归档' : '证据已归档');
  } catch (error) {
    if (token === revision) $('run-feedback').textContent = error.message;
  } finally {
    busy = false;
    $('save').disabled = !currentSource;
    $('rerun').disabled = !activeRun;
  }
}

for (const link of selectionButtons) {
  link.addEventListener('click', event => {
    const name = link.dataset.stage;
    if (name !== 'balance' && name !== 'runs') event.preventDefault();
    readStage(name);
  });
}
$('chain').addEventListener('change', paintRows);
$('filter').addEventListener('change', paintRows);
sample.addEventListener('change', preview);
$('preview').addEventListener('click', preview);
$('save').addEventListener('click', () => save(false));
$('rerun').addEventListener('click', () => save(true));
$('print').addEventListener('click', () => window.print());
preview();

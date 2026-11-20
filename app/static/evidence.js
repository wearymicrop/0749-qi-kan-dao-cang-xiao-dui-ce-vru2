export const states = { covered: '已覆盖', missing: '缺刊', disputed: '争议' };
const labels = JSON.parse(document.querySelector('#reason-labels').textContent);

export function element(tag, text, className) {
  const result = document.createElement(tag);
  if (text !== undefined) result.textContent = text;
  if (className) result.className = className;
  return result;
}

export function folio(slot) {
  return `${slot.year} · ${slot.volume} 卷 ${String(slot.issue).padStart(2, '0')} 期`;
}

export function paintEvidence(slot) {
  const panel = document.querySelector('#evidence');
  document.querySelector('#evidence-ref').textContent = slot?.chain || '';
  if (!slot) {
    panel.textContent = '请选择一个期位。';
    return;
  }
  panel.replaceChildren(element('h3', folio(slot)), element('p', labels[slot.code] || states[slot.status]));
  for (const row of slot.evidence) {
    const record = element('article');
    record.append(element('div', `原始行 ${row.line} · ${row.accession}`, 'accession'),
      element('p', row.raw.title), element('p', `原录 ${row.raw.volume} 卷 ${row.raw.issue} 期`));
    panel.append(record);
  }
}

export function paintExtras(supplements, isolated, duplicates) {
  const panel = document.querySelector('#extras');
  panel.replaceChildren();
  const groups = [
    ['增刊单列', supplements, row => `${row.title} · ${row.issue}`],
    ['待复查', isolated, row => `${labels[row.code]} · ${row.raw?.title || row.accession || '来刊数据'}`],
    ['重复回传', duplicates, row => `${row.accession} · 原始行 ${row.original_line}`],
  ];
  for (const [title, rows, display] of groups) {
    const group = element('details');
    group.append(element('summary', `${title} ${rows.length} 条`));
    for (const row of rows) group.append(element('p', `第 ${row.line} 行 · ${display(row)}`));
    panel.append(group);
  }
}

const stageColumns = {
  orders: ['订阅链', '年度', '卷号', '期位范围'],
  receipts: ['原始行', '验收号', '刊名', '采信结论'],
  numbering: ['原始行', '验收号', '原录', '解析结果'],
  combined: ['原始行', '订阅链', '验收号', '展开期位'],
  titles: ['订阅链', '刊名', '起年', '止年'],
};

function stageRows(stage, data) {
  switch (stage) {
    case 'orders': return data.years.map(row => [row.chain, row.year, row.volume, `${row.first}–${row.last}`]);
    case 'receipts': return [...data.accepted, ...data.conflicts, ...data.duplicates, ...data.isolated]
      .sort((a,b) => a.line - b.line).map(row => [row.line, row.accession || '—', row.title || '—', labels[row.code] || '已采信']);
    case 'numbering': return [...data.parsed, ...data.isolated].sort((a,b) => a.line - b.line)
      .map(row => [row.line, row.accession, `${row.volume} / ${row.issue}`, row.numbers ? `${row.numbers.volume} 卷 ${row.numbers.first}–${row.numbers.last}` : labels[row.code]]);
    case 'combined': return [...data.coverage, ...data.supplements, ...data.isolated].sort((a,b) => a.line - b.line)
      .map(row => [row.line, row.chain, row.accession, row.issues?.join('、') || labels[row.code] || '增刊单列']);
    case 'titles': return data.periods.map(row => [row.chain, row.title, row.from_year, row.to_year]);
    default: return [];
  }
}

export function stageTable(stage, data) {
  const table = element('table');
  const headings = table.createTHead().insertRow();
  for (const label of stageColumns[stage]) {
    const heading = element('th', label);
    heading.scope = 'col';
    headings.append(heading);
  }
  const body = table.createTBody();
  for (const values of stageRows(stage, data)) {
    const row = body.insertRow();
    for (const value of values) row.append(element('td', value));
  }
  return table;
}

export const states = { covered: '已覆盖', missing: '缺刊', disputed: '争议' };
const labels = JSON.parse(document.querySelector('#reason-labels').textContent);
const changeLabels = { NUMBERING_CHANGED: '期号改跨年连排', TITLE_CHANGED: '启用新刊名' };
const roleLabels = { adopted: '本次采用', retained: '继续留存' };

export function element(tag, text, className) {
  const result = document.createElement(tag);
  if (text !== undefined) result.textContent = text;
  if (className) result.className = className;
  return result;
}

function list(items, render) {
  const box = element('dl', undefined, 'spec-list');
  for (const item of items) {
    const row = element('div', undefined, 'spec-row');
    row.append(...render(item));
    box.append(row);
  }
  return box;
}

export function paintSpecs(result) {
  const listBox = document.querySelector('#specs-list');
  const banner = document.querySelector('#specs-banner');
  const adopted = document.querySelector('#specs-adopted');
  const governing = document.querySelector('#specs-governing');
  const affected = document.querySelector('#specs-affected');
  const basis = document.querySelector('#specs-basis');
  const unresolved = document.querySelector('#specs-unresolved');
  for (const node of [listBox, banner, adopted, governing, affected, basis, unresolved]) node.replaceChildren();
  if (!result) return;
  const report = result.specs;
  const current = report.adopted;
  adopted.textContent = `${current.id} · 第 ${current.revision} 版`;
  if (report.fallback) {
    banner.append(element('strong', '本次说明切换失败，已回退旧版'),
      element('span', `${report.fallback.rejected} · ${labels[report.fallback.code] || report.fallback.code}`));
    banner.classList.add('warn');
  } else if (report.rejected.length) {
    banner.append(element('span', `已弃用 ${report.rejected.length} 份说明，旧版仍留存`));
    banner.classList.add('warn');
  } else {
    banner.append(element('span', report.mode === 'legacy'
      ? '按单一订购与刊名清册核算（未分出版说明）'
      : '两套说明并存，按生效年度归卷'));
  }
  listBox.append(list(report.specs, doc => [
    element('dt', roleLabels[doc.role] || doc.role),
    element('dd', `${doc.id} · 第 ${doc.revision} 版 · ${doc.effective_from} 年起`,
      doc.role === 'adopted' ? 'adopted' : ''),
    element('dd', `${doc.chains.join('、')} · ${doc.years[0]}–${doc.years.at(-1)} 年`
      + (doc.transition_until ? ` · 旧刊名过渡至 ${doc.transition_until} 年` : ''), 'muted'),
  ]));
  governing.textContent = report.governing.length
    ? `逐年归属：${report.governing.map(row => `${row.year}→${row.spec}`).join('，')}`
    : '';
  if (report.affected.count) {
    affected.append(list(report.affected.years, row => [
      element('dt', `${row.chain} · ${row.year} 年`),
      element('dd', `${row.slots} 个期位 · ${row.reasons.map(key => changeLabels[key] || key).join('、')}`),
    ]));
  } else {
    affected.append(element('p', '本次说明切换未改动任何期位。', 'muted'));
  }
  const basisRows = Object.entries(report.basis_counts);
  if (basisRows.length) {
    basis.append(list(basisRows, ([key, count]) => [
      element('dt', report.basis_labels[key] || key), element('dd', `${count} 件`),
    ]));
  } else {
    basis.append(element('p', '尚无已归链的来刊原件。', 'muted'));
  }
  if (result.transition.length) {
    basis.append(list(result.transition, row => [
      element('dt', `第 ${row.line} 行 · ${row.accession}`),
      element('dd', `旧刊名「${row.title}」回挂 ${row.chain} · 过渡至 ${row.expires} 年`, 'basis-transition'),
    ]));
  }
  const open = [
    ...result.disputes.map(row => ({
      title: `${row.chain} · ${row.year} 年 ${row.issue} 期`,
      detail: `${labels[row.code] || row.code} · 涉及原件 ${row.evidence.join('、')}`,
    })),
    ...result.quarantine.map(row => ({
      title: `第 ${row.line} 行 · ${row.accession || row.raw?.accession || '—'}`,
      detail: labels[row.code] || row.code,
    })),
  ];
  if (open.length) {
    unresolved.append(list(open, row => [element('dt', row.title), element('dd', row.detail)]));
  } else {
    unresolved.append(element('p', '已无待核清争议。', 'muted'));
  }
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
  const heading = element('h3', folio(slot));
  panel.replaceChildren(heading, element('p', labels[slot.code] || states[slot.status],
    `basis-${slot.status === 'covered' ? 'ok' : 'note'}`));
  const meta = element('p', `归属说明 ${slot.spec || '—'}`);
  meta.className = 'slot-spec';
  panel.append(meta);
  for (const reason of slot.changed || []) {
    panel.append(element('p', changeLabels[reason] || reason, 'slot-change'));
  }
  for (const row of slot.evidence) {
    const record = element('article');
    record.append(element('div', `原始行 ${row.line} · ${row.accession}`, 'accession'),
      element('p', row.raw.title), element('p', `原录 ${row.raw.volume} 卷 ${row.raw.issue} 期`),
      element('p', `归链依据：${row.basis_label}${row.expires ? ` · 过渡至 ${row.expires} 年` : ''}`,
        `basis-${row.basis === 'TRANSITION_TITLE' ? 'transition' : 'current'}`));
    panel.append(record);
  }
  if (!slot.evidence.length) panel.append(element('p', '该期位尚无到藏原件。'));
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
  specs: ['出版说明', '修订版', '生效年', '年度', '订阅链', '过渡截止'],
  orders: ['订阅链', '年度', '卷号', '期位范围'],
  receipts: ['原始行', '验收号', '刊名', '采信结论'],
  numbering: ['原始行', '验收号', '原录', '解析结果'],
  combined: ['原始行', '订阅链', '验收号', '展开期位'],
  titles: ['订阅链', '刊名', '起年', '止年'],
};

function stageRows(stage, data) {
  switch (stage) {
    case 'specs': return data.specs.map(row => [row.id, `第 ${row.revision} 版`,
      row.effective_from, `${row.years[0]}–${row.years.at(-1)}`, row.chains.join('、'),
      row.transition_until || '—']);
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

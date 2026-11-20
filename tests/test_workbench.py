def test_workbench_exposes_actions_and_both_samples(client):
    response = client.get('/')
    assert response.status_code == 200
    assert all(text in response.text for text in ['期刊到藏校对册', '证据寄送', '归档本次勾稽',
                                                  '十一月补刊清单', '验收清册', '续订改版清册', '出版说明裁决'])
    assert client.get('/static/desk.js').status_code == 200


def test_workbench_renders_adjudication_and_basis(client):
    result = client.get('/api/balance/renewal').json()
    report = result['specs']
    assert report['adopted']['id'] == 'CST-2026'
    assert report['affected']['count'] == 4
    assert report['basis_counts'] == {'CURRENT_TITLE': 8, 'TRANSITION_TITLE': 2}
    slot = next(row for row in result['slots'] if row['year'] == 2027 and row['issue'] == 9)
    assert slot['evidence'][0]['basis_label'] == '过渡期旧刊名'
    assert result['disputes'] == [{'chain': 'CST', 'year': 2026, 'issue': 8, 'code': 'CLAIM_OVERLAP',
                                   'evidence': [6, 7], 'changed': ['NUMBERING_CHANGED', 'TITLE_CHANGED']}]


def test_specs_stage_matches_balance_report(client):
    assert client.get('/api/specs/renewal').json() == client.get('/api/balance/renewal').json()['specs']
    assert client.get('/api/specs/dirty').json()['mode'] == 'legacy'

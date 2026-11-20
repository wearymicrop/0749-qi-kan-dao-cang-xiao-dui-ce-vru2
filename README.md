# 期刊到藏校对册

馆藏编校人员用订购定义和来刊清册核对各订阅链。校对页以年度、卷号和期号展示应到、到藏、缺刊或争议及原始行，可按状态或订阅链筛选。

## 启动

```bash
docker compose config --quiet
docker compose up --build
docker compose exec -T app pytest -q
```

工作台默认地址为 `http://localhost:18443/`，接口文档在 `/docs`。使用 `SERIAL_LEDGER_PORT` 调整对外端口。归档写入 Compose 命名卷，普通停止及重启均保留。宿主运行可用 `python -m pip install -r requirements.txt` 和 `uvicorn app.main:app --port 18443`，本地数据库默认写入 `instance/`。

## 样例校对

1. 打开默认十一月补刊清单。预期 14 个期位，覆盖 7、缺刊 4、争议 3。另登记 3 件增刊。
2. 筛选争议，打开海岸观测 2025 年第 17 卷第 2 期。第 2、3 行同时覆盖该期，第 1 期仍然只有合期一项依据。
3. 切换验收清册，核对 14 个期位全部覆盖。可选择自备清册并粘贴同结构的 JSON。
4. 归档后进入证据寄送，重跑或下载凭证。凭证保存输入、规则版本、计算结果和原始行。

年度内可采用从 1 复位或跨年连排的期号。刊名按出版年度生效并映射到稳定订阅链。项目接受单年度内的合期，跨年度合期请先登记出版方确认的各卷记录。刊名沿革粒度为年。

七个模块与测试见 [深度登记](docs/DEPTH.md)，字段与接口见 [数据字典](docs/DATA-DICTIONARY.md)。

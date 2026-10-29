<div align="center">

# Slate

### A dependency-free Python toolkit for typed data validation & transformation

*Validate untrusted JSON / config / API payloads with a small, declarative, zero-dependency API — collect every error, coerce loose types, and trust the result.*

[![Python](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-blueviolet)](https://github.com/WsNodeX/slate)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](https://github.com/WsNodeX/slate)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/WsNodeX/slate)

[Why](#-why-slate) · [Features](#-features) · [Install](#-install) · [Quick Start](#-quick-start) · [Architecture](#-architecture) · [API](#-core-api) · [Roadmap](#-roadmap) · [Article](#-article-from-zero-to-a-validation-framework)

</div>

---

## ✨ Why Slate

Every backend receives data it does not control: HTTP request bodies, webhook
callbacks, uploaded config files, rows scraped from a third-party page. The first
line of defence is *validation* — but hand-rolled `if "email" in body and
isinstance(body["email"], str)` checks rot quickly, fail fast on the first
problem, and tell the caller nothing useful.

Slate gives you a single declarative grammar for a **data contract**:

* **Declarative** — describe the shape once, as a class.
* **Total validation** — it reports *all* problems at once, with a JSON-path
  location for each, instead of bailing on the first.
* **Lenient coercion** — `"123"` becomes `123`, `"yes"` becomes `True`, ISO
  strings become `datetime`, so loosely typed inputs still parse.
* **Zero dependencies** — pure standard library; drop the `slate/` folder into
  any project, no `pip install`, no supply-chain surface.
* **Serializable results** — `.dump()` recovers a clean, JSON-ready object.

## 🚀 Features

- Scalar fields: `Str`, `Int`, `Float`, `Bool`, `Const`, `Any`, `Nil`, `Enum`, `DateTime`, `Email`.
- Containers: `List`, `Dict`, `Tuple`, `Optional`, `Union`, `Nested`.
- Constraint DSL: `min_len` / `max_len`, `ge` / `le` / `gt` / `lt`, `multiple_of`, `pattern`, `unique`, `strip` / `lower` / `upper`.
- Declarative `Model` with `@validator` (per-field) and `@model_validator` (cross-field) hooks.
- Aliases, defaults, `default_factory`, optional fields.
- `TypeAdapter` for validating a single value without declaring a model.
- A small `slate` CLI (`demo`, `validate`, `version`).
- Fully typed, ships `py.typed`, 85 unit tests, CI on Python 3.9 – 3.13.

## 📦 Install

```bash
pip install slate
```

Or, because Slate has **no dependencies**, just copy the `slate/` package
directory into your project:

```bash
cp -r slate /path/to/your/project/
```

From source:

```bash
git clone https://github.com/WsNodeX/slate.git
cd slate
python -m unittest discover -s tests   # all green
```

## ⚡ Quick Start

```python
from slate import Model, Str, Int, Email, List, validator

class User(Model):
    name = Str(min_len=1, max_len=50, strip=True)
    age = Int(ge=0, le=150)
    email = Email()
    roles = List(Str(), min_len=1)

    @validator("name")
    def lower(cls, value):
        return value.lower()

payload = {
    "name": "  Ada  ",
    "age": 36,
    "email": "ada@example.com",
    "roles": ["admin", "author"],
}

result = User.validate(payload)
if result.valid:
    print(result.value.dump())
```

**Expected output:**

```text
{'name': 'ada', 'age': 36, 'email': 'ada@example.com', 'roles': ['admin', 'author']}
```

A payload with problems reports every issue, located by field:

```python
bad = User.validate({"name": "", "age": -5, "email": "nope", "roles": ["a", 7]})
print(bad.valid)          # False
for err in bad.errors:
    print(err.path, "->", err.message)
```

```text
False
name -> length 0 is less than minimum 1
age -> must be greater than or equal to 0
email -> string does not match pattern ^[^@\s]+@[^@\s]+\.[^@\s]+$
roles[1] -> not a valid string
```

## 🏗️ Architecture

```
                 raw mapping
                      │
                      ▼
        ┌──────────────────────────────┐
        │       Model.validate         │   declarative schema layer
        │  resolve alias / defaults    │
        │  dispatch each field         │
        └──────────────┬───────────────┘
                       │  per field
                       ▼
        ┌──────────────────────────────┐
        │       Field.validate         │
        │   1. missing → default       │
        │   2. _coerce  (type)         │
        │   3. _check   (constraints)  │
        └──────────────┬───────────────┘
                       │  aggregates children
                       ▼
        ┌──────────────────────────────┐
        │      ValidationResult        │
        │  .valid  .value  .errors[]   │   path-located, typed
        └──────────────────────────────┘
```

| Layer | Module | Responsibility |
|-------|--------|----------------|
| Errors & results | `slate.errors` | `ValidationResult`, `ErrorDetail`, `ValidationError`, the `MISSING` sentinel |
| Scalar fields | `slate.types` | `Str`, `Int`, `Float`, `Bool`, `Enum`, `DateTime`, `Email`, … |
| Containers | `slate.collections` | `List`, `Dict`, `Tuple`, `Optional`, `Union`, `Nested` |
| Models | `slate.model` | `Model` metaclass, `@validator`, `@model_validator`, `dump()` |
| Adapters | `slate.adapters` | `TypeAdapter` for single-value validation |
| CLI | `slate.cli` | `slate demo | validate | version` |

## 🔌 Core API

| Symbol | Purpose |
|--------|---------|
| `Model` | Base class for declarative schemas. `validate(data) → ValidationResult`, `parse(data) → instance`, `dump()`, `schema()`. |
| `Str / Int / Float / Bool` | Scalar fields with `min_len`, `max_len`, `pattern`, `strip`, `ge/le/gt/lt`, `multiple_of`, … |
| `Const(v)` | Accept only the constant `v`. |
| `Enum(values)` | Accept a value from a list or an `enum.Enum`. |
| `DateTime` | Parse ISO-8601 strings into `datetime`. |
| `Email` | `Str` constrained to a loose email pattern. |
| `List(item, …)` | Sequence of `item`; supports `min_len`, `max_len`, `unique`. |
| `Dict(k, v)` | Mapping with independently typed keys/values. |
| `Tuple(*types)` | Fixed-length, positionally typed tuple. |
| `Optional(inner)` | Accept `None` / a missing key gracefully. |
| `Union(*types)` | Accept the first type that validates. |
| `Nested(Model)` | Embed another model as a field. |
| `TypeAdapter(field)` | Validate one value without a model (`parse` / `validate`). |
| `@validator("name")` | Post-process / check a single field after coercion. |
| `@model_validator` | Enforce a cross-field invariant over all values. |

## 🧭 Roadmap

- [ ] JSON-Schema exporter (`Model.to_json_schema()`)
- [ ] `Decimal` field with currency-safe parsing
- [ ] Async `validate_async` for I/O-bound custom checks
- [ ] Recursive / self-referential models
- [ ] A `slate serve` mode that validates requests against a schema over HTTP
- [ ] Benchmark suite vs. other validation libraries

## 🤝 Contributing

Slate is intentionally small and dependency-free. The fastest way to contribute
is a new field type or a constraint, each with a unit test in `tests/` and a line
in `README.md`. Run the suite with:

```bash
python -m unittest discover -s tests
```

## 📄 License

Released under the [MIT License](LICENSE).

---

## 📝 Article: From Zero to a Validation Framework

> The section below doubles as a publishable long-form post for 掘金 / 知乎 /
> 小红书 / B 站. It explains the *why* and the *how* in reader-friendly terms and
> can be posted as-is or expanded using the checklist at the end.

### 1. 痛点：你写的校验代码，迟早会反噬你

凡是写过后端的人，都逃不开一件事：**校验别人塞给你的数据**。

请求体是 JSON，webhook 是 JSON，配置文件是 JSON，爬虫抓回来还是 JSON。而你永远不能相信它们。于是项目里慢慢长出这样的代码：

```python
if not body.get("email"):
    return error("email required")
if not isinstance(body["age"], int):
    return error("age must be int")
if body["age"] < 0:
    return error("age must be >= 0")
# ... 再来 30 行
```

三宗罪：

1. **fail-fast 但信息少**：用户一口气填了 5 个错，接口只告诉他第一个，体验极差。
2. **类型松但易错**：`age` 传字符串 `"18"` 就崩；前端传 `is_active: "true"` 你还得自己转。
3. **不可复用、不可文档化**：同样的规则在注册、资料编辑、管理后台各写一遍，改一处忘三处。

本质问题只有一个：**把"数据长什么样"这件事，散落成了命令式的 if。**

### 2. 核心原理：把"契约"变成声明，把"报错"变成集合

Slate 的思路是把校验拆成三层，互不耦合：

- **字段（Field）**：单点的"能不能收下这个值"。它干两件事——*强制类型*（coerce）和*检查约束*（check）。
- **模型（Model）**：把一组字段组织成 schema，并处理缺省、别名、嵌套。
- **结果（ValidationResult）**：不抛异常，而是返回一个对象，里面装着"清洗后的干净值"和"带路径的全部错误"。

关键设计决定：

> **永远收集所有错误，而不是遇到第一个就 return。**

实现上，`Field.validate` 内部先判断值是否缺失（缺失 → 用 default 或报 required），再做强制类型，再做约束检查，最后返回 `ValidationResult(value=..., errors=[...])`。`Model` 则对每个字段调一次 `field.validate`，把带字段名的错误聚到一起。

### 3. 关键实现点（值得抄的几处）

**(a) 强制类型要"宽容"但"可预期"。** 比如 `Int` 接受整数、可整的浮点、整数字符串；但**显式拒绝布尔**——因为 Python 里 `True == 1`，不拦住就会把 `true` 当 `1` 收下，埋下玄学 bug。

**(b) 路径定位（JSON-path）。** 嵌套错误要能精确定位：`address.city`、`roles[1]`。容器字段在递归校验子元素时，把父路径拼到子路径前面，这样无论嵌套多深，报错都能指到具体字段。

**(c) 声明式模型用元类收集字段。** 你在类里写的 `name = Str(...)` 不是实例属性，而是被元类在类创建时"收编"成 `_fields` 字典，于是它既能在类层面描述 schema，又不会和实例状态打架。

**(d) 两类校验钩子。** `@validator("field")` 在单个字段清洗完后跑（可改写值，如统一小写）；`@model_validator` 在所有字段都过完后跑（可跨字段，如"两次密码是否一致"）。两者抛 `ValueError` 就被收集成一条错误，不会中断其余检查。

### 4. 与同类方案对比

| 维度 | Slate | pydantic | 手写 if |
|------|-------|----------|---------|
| 依赖 | 0（仅标准库） | 较多 | 0 |
| 收集全部错误 | ✅ | ✅ | ❌ |
| 类型强制 | 宽容可预期 | 宽松/严格可选 | 手动 |
| 嵌套路径报错 | ✅ | ✅ | ❌ |
| 上手成本 | 极低 | 中 | 低但易烂 |
| 适合场景 | 轻量服务/教学/嵌入 | 大型项目 | 一次性脚本 |

Slate 不打算取代 pydantic——它是**当你不想引入重依赖、或想彻底看清校验到底怎么运作时**的那一个选择，也是理解"pydantic 背后到底发生了什么"的最佳练手项目。

### 5. 如何扩展

- 加字段：继承 `Field`，实现 `_coerce` 和 `_check` 两个方法即可。
- 加约束：在现有字段上挂新参数（如 `Decimal` 的 `places`）。
- 接外部系统：用 `Model.schema()` 导出结构，喂给前端表单或代码生成器（`tools/schema_dump.py` 就是例子）。
- 上 HTTP：在 handler 最前面 `result = Model.validate(body)`，无效就直接 422，后面逻辑闭眼信任 `result.value`。

### 6. 如何把本文扩展成一篇发布稿

- **标题方向**：《我手写了一个零依赖的 Python 数据校验库，顺便讲清楚 pydantic 的原理》《后端第一道防线：从 if 校验到声明式契约》。
- **加图**：架构图可用本文的 ASCII 图，或换成 draw.io / Excalidraw 矢量图（发到 GitHub 时记得用 jsDelivr CDN 绝对路径，避免裂图）。
- **加 demo**：把 `examples/demo.py` 和 `examples/api_example.py` 的运行截图贴进去，配预期输出。
- **加心法**：结尾升华一句——"校验不是拦用户的，是保护系统的；把契约写清楚，bug 就少一半"。
- **平台适配**：小红书偏短句+emoji 卡片；掘金偏完整技术长文；B 站可做"从零实现"的配套视频。

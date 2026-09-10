abc
# DocifyCode データベース仕様書

DocifyCodeFrontend / AICodeBot / DocifyCodeGenerativeService の3サービスが共有するMongoDBデータストアの構成、コレクション定義、およびフィールド仕様をまとめたリファレンス。

- **対象システム**: DocifyCode / AICodeBot
- **データストア**: MongoDB (replicaSet: rs0)
- **作成日**: 2026-09-01

---

## 目次

1. [概要](#1-概要)
2. [技術構成](#2-技術構成)
3. [接続構成](#3-接続構成)
4. [共通仕様](#4-共通仕様)
5. [コレクション一覧](#5-コレクション一覧)
6. [コレクション詳細](#6-コレクション詳細)
7. [リレーションシップ](#7-リレーションシップ)
8. [付記事項](#8-付記事項)

---

## 1. 概要

DocifyCodeは、Webアプリケーション本体である **DocifyCodeFrontend**、外部Issue/PR起点の自動化を担う **AICodeBot**、AI生成処理を担うワーカーサービス **DocifyCodeGenerativeService** の3サービスから構成される。これら3サービスは単一のMongoDBインスタンスをデータストアとして共有しており、サービス間の主な連携はMQTT経由のメッセージングと、MongoDB上のバッファコレクション(`ai_generation_request_buffer` / `ai_generation_result_buffer`)を介して行われる。

スキーマはRDBのDDLに相当するものを持たず、3リポジトリ共通のGitサブモジュール **cec_docifycode_common**(「DocifyCodeCommon」)内のPydantic v2モデルによってアプリケーション層でのみ定義・検証されている。マイグレーションフレームワーク(Alembic等)やJSON Schemaによる明示的なスキーマ強制、およびコード上でのインデックス作成(`create_index`)は確認されなかった。存在するのは各コレクション既定の `_id` インデックスのみである。

---

## 2. 技術構成

| 用途 | 技術 | 備考 |
|---|---|---|
| 主データストア | MongoDB(motor 非同期 / pymongo 同期) | DocifyCodeFrontend・AICodeBot・DocifyCodeGenerativeServiceの3サービス共通。replicaSet=rs0構成で稼働。 |
| スキーマ定義 | Pydantic v2(`cec_docifycode_common/models/`) | コレクションごとに1モデルファイル。DDL・マイグレーションフレームワークは未使用。 |
| データアクセス層 | BaseRepository(`repositories/` 非同期・`repositories/sync/` 同期) | Motorコレクションに対する汎用CRUDを提供する共通基底クラス。 |
| ローカルキャッシュ(AICodeBotのみ) | SQLite(`cache_database.sqlite`) | ワーカー内ローカルキャッシュで非共有。テーブル名 `ai_generation_cache` は同名のMongoコレクションとは独立した別物。 |
| サービス間連携 | MQTT(paho-mqtt / Mosquitto) | データストアではないが、AI生成リクエスト/結果のバッファコレクションと連動して稼働する。 |
| 未使用の依存関係 | azure-cosmos(**未使用**) | DocifyCodeFrontend/requirements.txt にのみ記載。実コードでのimportはなく、モックデータ生成用サンプルコード内にのみ登場する。 |

---

## 3. 接続構成

| 環境 / サービス | 設定ファイル | 接続文字列 | データベース名 |
|---|---|---|---|
| Azure環境(docifycode) | `azure/.env.docifycode` | `mongodb://mongodb:27017/?replicaSet=rs0` | `azure_docifycode_db_2` |
| Azure環境(aicodebot) | `azure/.env.aicodebot` | `mongodb://mongodb:27017/?replicaSet=rs0` | `azure_docifycode_db_2` |
| ローカル環境(サンプル) | `local/.env.*.sample` | `mongodb://mongodb:27017/?replicaSet=rs0` | `local_docifycode_db` |
| DocifyCodeFrontend(ローカル起動) | `DocifyCodeFrontend/.env` | `mongodb://localhost:27017/?directConnection=true` | `azure_docifycode_db_2` |
| DocifyCodeGenerativeService | `.env.example` | `mongodb://mongodb:27017` | `new_app_db` |

MongoDBはシングルノードのレプリカセット(`rs0`)として稼働する(`DocifyCodeExecutionEnvironment/mongodb/docker-compose.yml`、イメージ `docifycode/mongodb:1.0.0`、ポート27017、ボリューム `./data:/data/db`)。これはDocifyCodeFrontendのトランザクション処理(`app/services/detail_design/interface_sync.py` の `client.start_session()`)がレプリカセット構成を要求するためであり、移行手順は `replica_set_migration.md` に記録済み(適用済み)。同等のcompose定義が `DocifyCodeFrontend/Middleware/mongoDB` 配下にも重複して存在する。

---

## 4. 共通仕様

全モデルは `BaseDocument` を継承する。Git同期対象のドキュメント(設計書・ソースコード・テスト関連)はさらに `BaseGitSyncedDocument` を継承し、同期用フィールドが追加される。

### BaseDocument(全コレクション共通)

| フィールド名 | 型 | 説明 |
|---|---|---|
| `_id` | ObjectId | 主キー。MongoDB自動採番(エイリアス: id)。 |
| `created_at` | str (ISO8601) | 作成日時。 |
| `updated_at` | str (ISO8601) | 更新日時。 |
| `deleted_at` | Optional[str] | 論理削除日時。null の場合は未削除。 |

### BaseGitSyncedDocument(追加フィールド)

| フィールド名 | 型 | 説明 |
|---|---|---|
| `commit_id` | str | 同期対象のGitコミットID。 |
| `sync_status` | enum SyncStatus | `push` / `pull` / `pull_push` / `delete_push` / `delete_pull` / `synced` / `none` |

### 主な列挙型・サブタイプ

| 名称 | 値 / 用途 |
|---|---|
| PermissionLevel | `admin` / `user` — access_right.permissions |
| ContentType | `markdown` / `image` / `text` — requirement_document.rd_content.type |
| AIGenerationCacheItemType | `code_summary_file_info` / `code_file_summary` — ai_generation_cache.content_type |
| LogLevel | Emergency 〜 Debug(syslogレベル相当)— log.level |
| git.repo_provider | `github` / `gitbucket` / `gitlab` — project.setting_item.git内 |
| git.ref_type | `branch` / `tag` / `sha1` — project.setting_item.git内 |
| GenerationTarget / TaskExecutionStatus | 生成対象種別・タスク実行ステータスの列挙型。値の詳細は `cec_docifycode_common/models/enums.py` を参照。 |

---

## 5. コレクション一覧

全27コレクション(論理エイリアス・注意対象を含む)。

| コレクション名 | 分類 | 概要 |
|---|---|---|
| `user` | アカウント・権限 | アプリケーション利用者情報 |
| `group` | アカウント・権限 | ユーザーグループ |
| `access_right` | アカウント・権限 | グループ/ログインID単位の権限付与 |
| `local_login` | アカウント・権限 | ローカル(非SSO)ログイン認証情報 |
| `project` | プロジェクト | 管理対象プロジェクト(リポジトリ)のトップレベル集約。ほぼ全コレクションから参照される中心エンティティ |
| `source_code` | ソースコード・設計書 | 解析済みソースファイルとクラス/メソッド構造 |
| `source_code_summaries` | ソースコード・設計書 | ブランチ/コミット単位のAI生成コードベース要約 |
| `basic_design` | ソースコード・設計書 | AI生成された基本設計書 |
| `detail_design` | ソースコード・設計書 | AI生成された詳細設計書 |
| `detail_design_document` ⚠️要確認 | ソースコード・設計書 | 定数のみ定義され実読み書きが確認できないコレクション |
| `requirement_document` | ソースコード・設計書 | 要件定義ドキュメント/ファイル |
| `unit_test_design` | 単体テスト | メソッド単位のテスト設計(デシジョンテーブル/テストパターン) |
| `unit_test_code` | 単体テスト | メソッド単位の生成済みテストコード |
| `unit_test`(論理エイリアス) | 単体テスト | design/codeへのマッピング用の論理名 |
| `comment` | コラボレーション・履歴 | プロジェクトへのコメント |
| `issue` | コラボレーション・履歴 | ソースファイル単位で検出された課題・指摘 |
| `activity` | コラボレーション・履歴 | 監査・操作アクティビティログ |
| `log` | コラボレーション・履歴 | 汎用システムログ |
| `data_management` | コラボレーション・履歴 | 仮想フォルダツリーのメタデータ |
| `task_execution_history` | タスク実行管理 | AI生成タスク実行のトップレベル記録 |
| `task_execution_details` | タスク実行管理 | タスク実行のステップごとのログ・状態 |
| `task_state_parts` | タスク実行管理 | 巨大なtask_stateを分割保存するチャンク |
| `ai_codebot_request_details` | タスク実行管理 | 外部Issue/PR起点のAICodeBotリクエスト追跡 |
| `ai_logs` | AI連携バッファ・ログ | 生成ステップごとのLLM呼び出しトレース・トークン使用量 |
| `ai_generation_request_buffer` | AI連携バッファ・ログ | Worker連携用の送信リクエストバッファ |
| `ai_generation_result_buffer` | AI連携バッファ・ログ | Worker連携用の結果バッファ |
| `ai_generation_cache` | AI連携バッファ・ログ | LLM出力の永続共有キャッシュ |

---

## 6. コレクション詳細

### 01 アカウント・権限

#### `user` — ユーザー
`models/user.py`。システム利用者のアカウント情報。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `user_id` | str (UUID7) | ユーザーID |
| `user_name` | str | 表示名 |
| `email` | str | メールアドレス |
| `group` | [str] | 所属グループ名の一覧 |
| `personal_projects` | [str] | 個人プロジェクトID一覧 → `project` |

#### `group` — グループ
`models/group.py`。権限管理の単位となるユーザーグループ。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `group_id` | str | グループID(`_id`と同一のエイリアス) |
| `name` | str | グループ名 |
| `description` | str | 説明 |

#### `access_right` — アクセス権限
`models/access_right.py`。グループまたはログインID単位の権限付与レコード。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `group_name` | str | 対象グループ名 → `group` |
| `login_id` | str | 対象ログインID |
| `permissions` | enum PermissionLevel | `admin` / `user` |

#### `local_login` — ローカルログイン
`models/local_login.py`。SSOを利用しないローカル認証用の資格情報。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `login_id` | str | ログインID(メールアドレス) |
| `password` | str(ハッシュ化) | ハッシュ化済みパスワード |
| `user_name` | str | 表示名 |

### 02 プロジェクト

#### `project` — プロジェクト(中心エンティティ)
`models/project.py`。管理対象プロジェクト(リポジトリ)のトップレベル集約。`project_id` は他のほぼ全コレクションからテナントキーとして参照される。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `project_id` | str (UUID7) | プロジェクトID(パーティションキー相当) |
| `setting_item.project_name` / `description` / `language` / `framework` / `base_specification` / `folder_excluded_mapping` | str 他 | プロジェクト基本設定 |
| `setting_item.git` | object | `repository`, `branch`, `commit_id: [{commit_id,time}]`, `sync_status`, `repo_provider`(github/gitbucket/gitlab), `ref_type`(branch/tag/sha1) |
| `setting_item.ai_programming` | object(暗号化) | `user_name`, `password`(暗号化), `token`(暗号化) |
| `setting_item.directory` | object | `rd, bd, pd, src, utd, utc` の各ディレクトリパス |
| `setting_item.jira` / `setting_item.redmine` | object(暗号化) | `url, project_name, user_name, password` |
| `share` | [str] | 共有先メールアドレス一覧 |
| `process_history_id` | str | 直近処理履歴ID → `task_execution_history` |
| `current_task` | enum GenerationTarget | 現在実行中の生成対象種別 |
| `status_manage` | object | `status`, `error_info` |

### 03 ソースコード・設計書

#### `source_code` — ソースコード(GitSynced)
`models/source_code.py`。解析済みソースファイルと、抽出されたクラス/メソッド構造。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `project_id` | str | → `project` |
| `file_path` / `file_name` | str | ファイルパス・ファイル名 |
| `folder_id` | str | → `data_management.folders` |
| `source_code` | str | ソースコード本文 |
| `classes` | [Class] | `class_id, class_name, class_content, methods:[Method{method_id,method_name,method_content}]` |
| `global_methods` | [Method] | クラスに属さないグローバル関数 |
| `detail_design_document_ids` | [str] | → `detail_design` |
| `unit_test_ids` | [str] | → `unit_test_design` / `unit_test_code` |
| `issue_ids` | [str] | → `issue` |

#### `source_code_summaries` — ソースコード要約
`models/source_code_summaries.py`。ブランチ/コミット単位で生成されるAIコードベース要約。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `process_history_id` | str | → `task_execution_history` |
| `project_id` | str | → `project` |
| `branch` | str | 対象ブランチ |
| `revision_number` | str | Gitコミットのリビジョン番号 |
| `summary_content` | CodeBaseInfo | 要約内容(`content_models/code_base_info.py` で定義される構造) |

#### `basic_design` — 基本設計書(GitSynced)
`models/basic_design.py`。AIにより生成された基本設計書の内容。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `process_history_id` | str | → `task_execution_history` |
| `project_id` | str | パーティションキー相当 → `project` |
| `contents` | dict | 未型付けJSON。論理構造は `content_models/basic_design_data.py` の BasicDesignData に準拠 |

#### `detail_design` — 詳細設計書(GitSynced)
`models/detail_design.py`。AIにより生成された詳細設計書の内容。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `process_history_id` | str | → `task_execution_history` |
| `project_id` | str | → `project` |
| `contents` | dict | 未型付けJSON。論理構造は `content_models/detailed_design_data.py` に準拠 |

#### `detail_design_document`(要確認・未使用の可能性)
専用モデルは存在しない。`repositories/detail_design_repository.py` 内で定数として参照されるのみで、実際の読み書きロジックは確認できず、デッドコード(未使用)の可能性が高い。実装の見直し・削除を検討されたい。

#### `requirement_document` — 要件定義書(GitSynced)
`models/requirement_document.py`。要件定義ドキュメント/ファイル(テキストまたは画像)。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `project_id` | str | → `project` |
| `file_name` / `file_path` | str | ファイル名・パス |
| `rd_content` | object | `type`(enum ContentType: markdown/image/text), `content` |

### 04 単体テスト

#### `unit_test_design` — 単体テスト設計(GitSynced)
`models/unit_test.py`(UnitTestDesign)。メソッド単位のテスト設計(デシジョンテーブル・テストパターン)。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `process_history_id` | str | → `task_execution_history` |
| `project_id` | str | → `project` |
| `source_code_id` | str | → `source_code` |
| `source_code_path` / `class_id` / `method_id` | str | 対象クラス/メソッドの特定情報 |
| `file_name` / `file_path` / `folder_id` | str | 出力ファイル情報(`folder_id` → `data_management`) |
| `collection_name` | Literal | 固定値によるコレクション種別識別子 |
| `unit_test_design_json` / `decision_table` / `test_pattern` | str / dict | テスト設計内容 |

#### `unit_test_code` — 単体テストコード(GitSynced)
`models/unit_test.py`(UnitTestCode)。メソッド単位の生成済み単体テストコード。`unit_test_design` と同一の識別フィールド群を持つ。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `process_history_id` / `project_id` / `source_code_id` / `source_code_path` / `class_id` / `method_id` / `file_name` / `file_path` / `folder_id` / `collection_name` | — | `unit_test_design` と同一(上記参照) |
| `ut_code_content` | str | 生成された単体テストコード本文 |

#### `unit_test`(論理エイリアス)
専用モデルを持たない論理名。`UNIT_TEST_COLLECTION_MAP` により `unit_test_design` / `unit_test_code` へのコレクション名変換に用いられる(`get_repository_for_document` 内)。

### 05 コラボレーション・履歴

#### `comment` — コメント
`models/comment.py`。プロジェクトに対するコメント。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `project_id` | str | → `project` |
| `user_id` | str | → `user` |
| `user_name` | str | 投稿者表示名 |
| `content` | str | コメント本文 |

#### `issue` — 課題・指摘
`models/issue.py`。ソースファイル単位で検出された課題・指摘事項。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `source_code_id` | str | → `source_code` |
| `project_id` | str | パーティションキー相当 → `project` |
| `issue_info` | object | `issue_title, issue_content` |

#### `activity` — アクティビティログ
`models/activity.py`。監査・操作履歴。日本語メッセージテンプレートを用いる。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `project_id` | str | → `project` |
| `user_id` | str | → `user` |
| `activity_type` | str | アクティビティ種別 |
| `description` | str | 内容説明 |

#### `log` — システムログ
`models/log.py`。汎用システムログエントリ。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `date` | str | 日時 |
| `type` | str | ログ種別 |
| `level` | enum LogLevel | Emergency〜Debug(syslogレベル相当) |
| `detail` | dict | 詳細情報(任意構造) |

#### `data_management` — フォルダ管理
`models/data_management.py`。ソースコード/UTD/UTC等、ドキュメント種別ごとの仮想フォルダツリーのメタデータ。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `project_id` | str | → `project` |
| `type` | enum DataManagementType | 対象ドキュメント種別(source_code / utd / utc 等) |
| `folders` | [FolderInfo] | `folder_id, folder_name, parent_folder_id` による木構造 |

### 06 タスク実行管理

#### `task_execution_history` — タスク実行履歴
`models/task_execution_history.py`。AI生成タスク実行のトップレベル記録。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `process_history_id` | str | 処理履歴ID |
| `project_id` | str | → `project` |
| `status` | enum TaskExecutionStatus | 実行ステータス |
| `generation_target` | enum GenerationTarget | 生成対象種別 |
| `task_options` | dict | タスク実行オプション |
| `generation_management` | object | `execute_count, final_status, thread_id, execution_detail_ids:[str], executed_at, completed_at`(`execution_detail_ids` → `task_execution_details`) |
| `revision_number` | str | 対象リビジョン番号 |
| `user_name` | str | 実行ユーザー名 |
| `token_password` | str(暗号化) | 実行時に用いる認証トークン/パスワード |

#### `task_execution_details` — タスク実行詳細
`models/task_execution_details.py`。タスク実行のステップごとのログおよび状態。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `task_execution_history_id` | str | → `task_execution_history` |
| `status` | enum TaskExecutionStatus | 実行ステータス |
| `project_id` | str | → `project` |
| `logs` | [LogEntry] | `timestamp, message` |
| `error_logs` | [ErrorLogEntry] | `error_type, error_message, stack_trace, timestamp, additional_info` |
| `task_state` | Optional[dict] | タスクの内部状態(未分割時) |
| `is_task_state_partitioned` | bool | trueの場合 `task_state_parts` に分割保存 |

#### `task_state_parts` — タスク状態分割データ
`models/task_state_part.py`。サイズが大きいtask_stateをチャンク分割して保存する。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `process_history_id` | str | → `task_execution_history` |
| `execution_detail_id` | str | → `task_execution_details` |
| `checksum` | str | 整合性検証用チェックサム |
| `part_idx` | int | 分割順序インデックス |
| `contents` | str | 分割データ本文 |

#### `ai_codebot_request_details` — AICodeBotリクエスト詳細
`models/ai_codebot_request_details.py`。外部Issue/PR(GitHub/GitLab等)を起点とするAICodeBotリクエストの追跡。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `task_id` | str | タスクID |
| `status` | str | 処理ステータス |
| `project_id` | str | → `project` |
| `issue_type` / `issue_id` | str | 起点となる外部Issue/PRの種別・ID |
| `server_type` / `url` | str | 外部サーバー種別・URL |
| `git_group` / `git_repo` | str | 対象Gitグループ・リポジトリ |
| `error_logs` | [ErrorLogEntry] | エラー発生時のログ |

### 07 AI連携バッファ・ログ

#### `ai_logs` — AI呼び出しログ
`models/ai_log.py`。生成ステップごとのLLM呼び出しトレースとトークン使用量。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `project_id` | str | → `project` |
| `processing_history_id` | str | → `task_execution_history` |
| `step_count` | int | ステップ数 |
| `llm_info` | dict | 使用LLMの情報 |
| `total_token_usage` | dict | 合計トークン使用量 |
| `ai_traces` | list | 個々のLLM呼び出しトレース |

#### `ai_generation_request_buffer` — AI生成リクエストバッファ
`models/ai_generation_request.py`。Appからワーカーサービスへ送信するAI生成リクエストのバッファ(MQTT連携を補助)。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `processing_history_id` | str | → `task_execution_history` |
| `llm_info` | dict | 使用LLMの情報 |
| `request_content` | Any | リクエスト本体 |

#### `ai_generation_result_buffer` — AI生成結果バッファ
`models/ai_generation_result.py`。ワーカーサービスからAppへ返却するAI生成結果のバッファ。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `processing_history_id` | str | → `task_execution_history` |
| `result` | Any | 生成結果本体 |

#### `ai_generation_cache` — AI生成結果キャッシュ
`models/ai_generation_cache_item.py`。LLM出力の永続・共有キャッシュ。AICodeBotのローカルSQLiteキャッシュ(同名・別実体)とは独立している。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `project_id` | str | → `project` |
| `content_type` | enum AIGenerationCacheItemType | `code_summary_file_info` / `code_file_summary` |
| `version` | str | キャッシュ対象のバージョン |
| `llm_identifier` | str | 使用LLMの識別子 |
| `hash` | str | 入力データのハッシュ値 |
| `cache_contents` | [{input_data, generated_content}] | キャッシュされた入出力ペアの一覧 |

---

## 7. リレーションシップ

MongoDBはドキュメント指向DBのため外部キー制約は存在しないが、アプリケーション層では文字列IDによる参照関係が徹底されている。**ほぼ全コレクションが `project_id` を保持し、project を中心としたテナント構造**になっている。

```
                         ┌─────────────────────┐
                         │  アカウント・権限     │
                         └──────────┬──────────┘
                                    │ project_id
┌──────────────────┐               │               ┌──────────────────────┐
│ AI連携            │               │               │ ソースコード          │
│ バッファ・ログ     │───────────────┼───────────────│ ・設計書              │
└──────────────────┘         ┌──────┴──────┐        └──────────────────────┘
                              │   project   │
┌──────────────────┐         └──────┬──────┘        ┌──────────────────────┐
│ タスク実行管理     │───────────────┼───────────────│ 単体テスト            │
└──────────────────┘               │               └──────────────────────┘
                                    │
                         ┌──────────┴──────────┐
                         │ コラボレーション・履歴 │
                         └─────────────────────┘
```

project を中心に、各カテゴリのほぼ全コレクションが `project_id` によってテナントキーとして紐づく。これとは別に、以下の個別FK参照がコレクション間を直接結んでいる。

### 個別のFK参照

| 参照元 | フィールド | 参照先 |
|---|---|---|
| `source_code` | `detail_design_document_ids` | `detail_design` |
| `source_code` | `unit_test_ids` | `unit_test_design` / `unit_test_code` |
| `source_code` | `issue_ids` | `issue` |
| `issue` | `source_code_id` | `source_code` |
| `unit_test_design` / `unit_test_code` | `source_code_id` | `source_code` |
| `task_execution_details` | `task_execution_history_id` | `task_execution_history` |
| `task_state_parts` | `execution_detail_id` | `task_execution_details` |
| `source_code` / `unit_test_design` / `unit_test_code` | `folder_id` | `data_management.folders[]` |

---

## 8. 付記事項

- **インデックス未定義**: アプリケーションコード内に `create_index` の呼び出しは存在せず、確認できるのは各コレクション既定の `_id` インデックスのみ。`project_id` による絞り込みが全コレクションで多用されているにもかかわらず、明示的なセカンダリインデックスは未定義であり、データ量増加時のパフォーマンスリスクとして留意されたい。

- **`detail_design_document` コレクションは実質未使用の可能性**: `repositories/detail_design_repository.py` で定数として参照されるのみで、実際の読み書きロジックが確認できない。デッドコードとして削除するか、意図を確認する必要がある。

- **`mongo-init.js` は現行スキーマを反映していない汎用テンプレート**: `DocifyCodeFrontend/Middleware/mongoDB/script/mongo-init.js` には `users` コレクションへの一意インデックス作成スクリプトが存在するが、実運用の.envファイルに対応する環境変数(`MONGO_APP_*`)は定義されておらず、実際のコレクション名(`user`)や制約とも一致しない。ボイラープレートとして残存している可能性が高い。

- **`azure-cosmos` は未使用の依存関係**: DocifyCodeFrontend/requirements.txt に記載があるが、実コードでのimport・使用箇所はなく、モックデータ生成用サンプルコード内にのみ登場する。将来的な移行検討の名残、または削除漏れと考えられる。

- **レプリカセット構成が必須**: MongoDBはレプリカセット(`rs0`)として稼働している。DocifyCodeFrontendのトランザクション処理(`interface_sync.py`、`client.start_session()`)がこの構成を要求するため。移行手順は `replica_set_migration.md` に記録済み(適用済み)。

- **`ai_generation_cache` は名称が同一でも実体が異なる2系統が存在**: Mongoコレクション(共有・永続)と、AICodeBotローカルのSQLiteテーブル(ワーカー内キャッシュ、非共有)の双方に同名の概念が存在するが、両者は独立しており、データは同期されない。

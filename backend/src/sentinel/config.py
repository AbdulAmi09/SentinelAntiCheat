from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(__import__("pathlib").Path(__file__).resolve().parents[2] / ".env"), env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    db_path: str = "./sentinel.db"
    model_version: str = "v0.2"
    feature_schema_version: str = "v1"
    report_schema_version: str = "v1"
    legal_disclaimer_text: str = (
        "Statistical anomaly assessment only. This report is not a final cheating determination "
        "and requires qualified human review before any action."
    )
    fide_floor_z_otb: float = 5.0
    fide_floor_z_online: float = 4.25
    federation_threshold_z_otb: float = 5.0
    federation_threshold_z_online: float = 4.25
    calibration_profile_path: str | None = None
    risk_baseline_z: float = 4.0
    min_elevated_triggers: int = 3
    forced_move_gap_cp: int = 50
    stockfish_path: str | None = None
    analysis_depth: int = 22
    multipv: int = 3
    maia_model_path: str | None = None
    maia_models_dir: str | None = None
    maia_lc0_path: str | None = None
    maia_model_version: str = "maia-v1.0"
    maia_nodes: int = 1
    maia_threads: int = 1
    maia_backend: str = "blas"
    maia_backend_opts: str = ""
    maia_temperature: float = 0.0
    maia_temp_decay_moves: int = 0
    polyglot_book_path: str | None = None
    syzygy_path: str | None = None
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_schema: str = "public"
    persistence_fail_hard: bool = False
    redis_url: str | None = None
    redis_password: str | None = None
    redis_prefix: str = "sentinel:"
    cors_allow_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    ml_fusion_enabled: bool = True
    xgboost_model_path: str | None = None
    isolation_forest_model_path: str | None = None
    ml_fusion_weight_heuristic: float = 0.4
    ml_fusion_weight_primary: float = 0.45
    ml_fusion_weight_secondary: float = 0.15
    ml_fusion_min_moves: int = 20
    rbac_enabled: bool = True
    tenant_enforcement_enabled: bool = True
    encryption_key: str | None = None
    llm_provider: str = "none"
    llm_api_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_timeout_seconds: int = 45
    report_pdf_engine: str = "auto"
    camera_raw_storage_enabled: bool = False
    consent_required_for_raw: bool = True


settings = Settings()

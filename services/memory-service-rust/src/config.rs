use anyhow::Result;
use serde::Deserialize;

#[derive(Clone, Debug, Deserialize)]
pub struct Config {
    pub database_url: String,
    pub redis_url: String,
    pub jwt_secret: String,
    pub rust_log: String,
}

impl Config {
    pub fn from_env() -> Result<Self> {
        dotenvy::dotenv().ok();

        Ok(Config {
            database_url: std::env::var("DATABASE_URL")
                .expect("DATABASE_URL must be set"),
            redis_url: std::env::var("REDIS_URL")
                .unwrap_or_else(|_| "redis://localhost:6379".to_string()),
            jwt_secret: std::env::var("NINAIVALAIGAL_JWT_SECRET")
                .expect("NINAIVALAIGAL_JWT_SECRET must be set"),
            rust_log: std::env::var("RUST_LOG")
                .unwrap_or_else(|_| "info".to_string()),
        })
    }
}

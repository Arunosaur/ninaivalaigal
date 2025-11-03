use crate::error::AppError;
use axum::{
    extract::Request,
    http::StatusCode,
    middleware::Next,
    response::Response,
};
use jsonwebtoken::{decode, DecodingKey, Validation, Algorithm};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Claims {
    pub sub: String,      // user_id
    pub email: String,
    pub exp: usize,       // expiration time
    pub iat: usize,       // issued at
    #[serde(default)]
    pub user_id: Option<String>,
}

#[derive(Clone)]
pub struct AuthenticatedUser {
    pub user_id: Uuid,
    pub email: String,
}

/// JWT validation middleware
pub async fn validate_jwt(
    mut req: Request,
    next: Next,
) -> Result<Response, AppError> {
    // Extract Authorization header
    let auth_header = req
        .headers()
        .get("Authorization")
        .and_then(|h| h.to_str().ok())
        .ok_or_else(|| AppError::Auth("Missing Authorization header".to_string()))?;

    // Extract token
    let token = auth_header
        .strip_prefix("Bearer ")
        .ok_or_else(|| AppError::Auth("Invalid Authorization header format".to_string()))?;

    // Get JWT secret from environment
    let secret = std::env::var("NINAIVALAIGAL_JWT_SECRET")
        .map_err(|_| AppError::Auth("JWT secret not configured".to_string()))?;

    // Decode and validate token
    let token_data = decode::<Claims>(
        token,
        &DecodingKey::from_secret(secret.as_ref()),
        &Validation::new(Algorithm::HS256),
    )
    .map_err(|e| AppError::Auth(format!("Invalid token: {}", e)))?;

    // Extract user ID
    let user_id_str = token_data
        .claims
        .user_id
        .as_ref()
        .unwrap_or(&token_data.claims.sub);

    let user_id = Uuid::parse_str(user_id_str)
        .map_err(|e| AppError::Auth(format!("Invalid user ID format: {}", e)))?;

    // Add authenticated user to request extensions
    let user = AuthenticatedUser {
        user_id,
        email: token_data.claims.email.clone(),
    };

    req.extensions_mut().insert(user);

    Ok(next.run(req).await)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_user_id() {
        let user_id = Uuid::new_v4();
        let result = Uuid::parse_str(&user_id.to_string());
        assert!(result.is_ok());
    }
}

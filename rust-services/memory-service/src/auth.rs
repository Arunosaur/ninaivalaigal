use std::sync::Arc;

use axum::body::Body;
use axum::extract::State;
use axum::http::{header::AUTHORIZATION, HeaderMap, Request, StatusCode};
use axum::middleware::Next;
use axum::response::Response;
use jsonwebtoken::{decode, Algorithm, DecodingKey, Validation};
use serde::Deserialize;
use tracing::{debug, error, warn};
use uuid::Uuid;

use crate::AppState;

#[derive(Clone, Debug)]
pub struct AuthenticatedUser {
    pub user_id: Uuid,
    pub email: String,
}

#[derive(Clone)]
pub struct JwtVerifier {
    decoding_key: DecodingKey,
    validation: Validation,
}

#[derive(Debug, Deserialize)]
struct Claims {
    user_id: String,
    email: String,
    #[serde(rename = "exp")]
    _exp: usize,
}

impl JwtVerifier {
    pub fn new(secret: &str) -> Self {
        let mut validation = Validation::new(Algorithm::HS256);
        validation.validate_exp = true;

        Self {
            decoding_key: DecodingKey::from_secret(secret.as_bytes()),
            validation,
        }
    }

    pub fn verify(&self, token: &str) -> Result<AuthenticatedUser, StatusCode> {
        match decode::<Claims>(token, &self.decoding_key, &self.validation) {
            Ok(data) => {
                let claims = data.claims;
                let user_id = Uuid::parse_str(&claims.user_id).map_err(|error| {
                    warn!(%error, "invalid user_id in token");
                    StatusCode::UNAUTHORIZED
                })?;

                Ok(AuthenticatedUser {
                    user_id,
                    email: claims.email,
                })
            }
            Err(error) => {
                debug!(?error, "failed to decode jwt");
                Err(StatusCode::UNAUTHORIZED)
            }
        }
    }
}

pub async fn require_jwt(
    State(state): State<Arc<AppState>>,
    mut request: Request<Body>,
    next: Next,
) -> Result<Response, StatusCode> {
    let token = extract_token(request.headers())?;

    match state.auth().verify(token) {
        Ok(user) => {
            debug!(user_id = %user.user_id(), email = %user.email, "jwt verified");
            request.extensions_mut().insert(user);
            Ok(next.run(request).await)
        }
        Err(status) => {
            error!("unauthorised request");
            Err(status)
        }
    }
}

fn extract_token(headers: &HeaderMap) -> Result<&str, StatusCode> {
    let header_value = headers
        .get(AUTHORIZATION)
        .and_then(|value| value.to_str().ok())
        .ok_or(StatusCode::UNAUTHORIZED)?;

    let bearer_prefix = "Bearer ";
    if header_value.starts_with(bearer_prefix) {
        Ok(&header_value[bearer_prefix.len()..])
    } else {
        Err(StatusCode::UNAUTHORIZED)
    }
}

impl AuthenticatedUser {
    pub fn user_id(&self) -> Uuid {
        self.user_id
    }
}
